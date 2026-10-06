"""Shared code for the Neon Genesis Evangelion (N64) translation tools.

Standard library only. All paths are resolved relative to this file so the
whole workspace can be moved to another drive.
"""
import re
import struct
import zlib
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
WORKSPACE = TOOL_DIR.parent.parent
GAME_DIR = WORKSPACE / "games" / "eva64"
ORIGINAL_DIR = GAME_DIR / "original"
WORK_DIR = GAME_DIR / "work"

ROM_SHA1 = "a9ba0a4afeed48080f54aa237850f3676b3d9980"

# First Yay0 file in the ROM. Everything before it is program code and data.
DATA_START = 0x1BB280

# Font: one 24x24 4bpp glyph per Yay0 file, listed in a table of
# (offset from FONT_BASE, compressed size, unpacked size) triples.
FONT_BASE = 0x1BB280
GLYPH_TABLE = 0x3FD90
GLYPH_COUNT = 538
GLYPH_SIZE = 24
GLYPH_BYTES = 0x120
WIDTH_TABLE = 0x3EAB0

# Text: 16-bit codes. Code = glyph number + CODE_BASE.
CODE_BASE = 0x10
CODE_END = 0x0000
CODE_NEWLINE = 0x0001


def find_rom():
    roms = sorted(ORIGINAL_DIR.glob("*.z64"))
    if len(roms) != 1:
        raise SystemExit(f"Expected exactly one .z64 in {ORIGINAL_DIR}, found {len(roms)}")
    return roms[0]


def yay0_decode(data, off):
    """Decompress the Yay0 file at `off`. Returns (bytes, compressed_length)."""
    if data[off:off + 4] != b"Yay0":
        raise ValueError(f"no Yay0 header at {off:#x}")
    size, link, chunk = struct.unpack(">III", data[off + 4:off + 16])
    out = bytearray()
    mp = off + 16
    lp = off + link
    cp = off + chunk
    mask = 0
    bits = 0
    while len(out) < size:
        if bits == 0:
            mask = struct.unpack(">I", data[mp:mp + 4])[0]
            mp += 4
            bits = 32
        if mask & 0x80000000:
            out.append(data[cp])
            cp += 1
        else:
            v = (data[lp] << 8) | data[lp + 1]
            lp += 2
            dist = (v & 0xFFF) + 1
            n = v >> 12
            if n == 0:
                n = data[cp] + 0x12
                cp += 1
            else:
                n += 2
            for _ in range(n):
                out.append(out[-dist])
        mask = (mask << 1) & 0xFFFFFFFF
        bits -= 1
    return bytes(out[:size]), max(cp, lp, mp) - off


def yay0_encode(data, chain=96):
    """Compress to Yay0. Finds matches through a table of earlier 3-byte sequences."""
    data = bytes(data)
    n = len(data)
    masks = []
    links = bytearray()
    chunks = bytearray()
    cur = 0
    bits = 0
    pos = 0
    table = {}

    def remember(p):
        if p + 3 <= n:
            table.setdefault(data[p:p + 3], []).append(p)

    def longest(p):
        best_len = 0
        best_dist = 0
        max_len = min(0x111, n - p)
        if max_len < 3:
            return 0, 0
        for start in reversed(table.get(data[p:p + 3], [])[-chain:]):
            if p - start > 0x1000:
                break
            length = 3
            while length < max_len and data[start + length] == data[p + length]:
                length += 1
            if length > best_len:
                best_len = length
                best_dist = p - start
                if length == max_len:
                    break
        return best_len, best_dist

    while pos < n:
        best_len, best_dist = longest(pos)
        if best_len >= 3 and pos + 1 < n:
            # lazy matching: a literal now is worth it if the next position matches much longer
            remember(pos)
            next_len, _ = longest(pos + 1)
            table[data[pos:pos + 3]].pop()
            if next_len > best_len + 1:
                best_len = 0
        cur <<= 1
        if best_len >= 3:
            if best_len >= 0x12:
                links += struct.pack(">H", best_dist - 1)
                chunks.append(best_len - 0x12)
            else:
                links += struct.pack(">H", ((best_len - 2) << 12) | (best_dist - 1))
            for p in range(pos, pos + best_len):
                remember(p)
            pos += best_len
        else:
            cur |= 1
            chunks.append(data[pos])
            remember(pos)
            pos += 1
        bits += 1
        if bits == 32:
            masks.append(cur)
            cur = 0
            bits = 0
    if bits:
        masks.append(cur << (32 - bits))
    mask_bytes = b"".join(struct.pack(">I", m) for m in masks)
    link_off = 16 + len(mask_bytes)
    chunk_off = link_off + len(links)
    out = b"Yay0" + struct.pack(">III", n, link_off, chunk_off) + mask_bytes + bytes(links) + bytes(chunks)
    if yay0_decode(out + bytes(8), 0)[0] != data:
        raise RuntimeError("Yay0 encoder self-check failed")
    return out

def yay0_offsets(rom):
    return [m.start() for m in re.finditer(b"Yay0", rom) if m.start() >= DATA_START]


def write_png_gray(path, width, height, rows):
    """Write an 8-bit greyscale PNG. `rows` is a list of byte sequences."""
    raw = b"".join(b"\x00" + bytes(r) for r in rows)

    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body))

    Path(path).write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def unpack_4bpp(pixels, width, height):
    """4-bit pixels to rows of 0..15."""
    rows = []
    for y in range(height):
        row = bytearray(width)
        for x in range(width):
            b = pixels[(y * width + x) >> 1]
            row[x] = (b >> 4) if (x & 1) == 0 else (b & 15)
        rows.append(row)
    return rows


def parse_image(data):
    """Return (width, height, flags, name, bpp, pixels) if `data` is a game image, else None."""
    if len(data) < 16:
        return None
    w, h, flags = struct.unpack(">HHI", data[:8])
    name = data[8:16].rstrip(b"\0")
    if not name or not all(0x20 <= c < 0x7F for c in name):
        return None
    if not (0 < w <= 640 and 0 < h <= 480):
        return None
    body = len(data) - 16
    if body == w * h // 2:
        bpp = 4
    elif body == w * h:
        bpp = 8
    else:
        return None
    return w, h, flags, name.decode("ascii"), bpp, data[16:]


def image_rows_gray(img):
    """Greyscale rows for viewing. 4bpp index n becomes n*17 (lossless); 8bpp is kept as is."""
    w, h, _, _, bpp, px = img
    if bpp == 4:
        return [bytes(v * 17 for v in row) for row in unpack_4bpp(px, w, h)]
    return [px[y * w:(y + 1) * w] for y in range(h)]


def glyph_entries(rom):
    return [struct.unpack(">III", rom[GLYPH_TABLE + i * 12:GLYPH_TABLE + i * 12 + 12]) for i in range(GLYPH_COUNT)]


def glyph_pixels(rom, entry):
    off, csize, _ = entry
    if csize:
        return yay0_decode(rom, FONT_BASE + off)[0]
    return rom[FONT_BASE + off:FONT_BASE + off + GLYPH_BYTES]


def font_sheet(rom, path, cols=16, scale=3, first=0, count=None):
    """Contact sheet of the font, `cols` glyphs per row, read left to right."""
    entries = glyph_entries(rom)
    last = GLYPH_COUNT if count is None else min(GLYPH_COUNT, first + count)
    cell = GLYPH_SIZE * scale + 3
    rows = []
    for r0 in range(first, last, cols):
        block = [bytearray([70]) * (cols * cell) for _ in range(cell)]
        for c, entry in enumerate(entries[r0:min(r0 + cols, last)]):
            g = unpack_4bpp(glyph_pixels(rom, entry), GLYPH_SIZE, GLYPH_SIZE)
            for y in range(GLYPH_SIZE * scale):
                for x in range(GLYPH_SIZE * scale):
                    block[y][c * cell + x] = g[y // scale][x // scale] * 17
        rows += block
    write_png_gray(path, cols * cell, len(rows), rows)
