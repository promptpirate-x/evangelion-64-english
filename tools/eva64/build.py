"""Rebuild the Evangelion 64 ROM with replaced strings.

  build.py                       rebuild with no changes (must match the original exactly)
  build.py <changes.tsv> <name>  apply the changes and write work\\build\\<name>.z64
  build.py <changes.tsv> <name> en   same, with the English font (run makefont.bat first);
                                 text then uses scripts\\charmap_en.txt
  Use "trace" or "en-trace" instead for a diagnostic build that records every string the
  game draws (for the test harness only; never release one).

A changes file is UTF-8, tab separated, two columns: string id (from
work\\extract\\text\\strings_jp.tsv) and the new text. Lines starting with #
are ignored. Text uses the characters of scripts\\charmap_jp.txt, a normal
space for the blank glyph and \\n for a line break.

The original ROM is only ever read. Output goes to games\\eva64\\work\\build.
Run it through build.bat.
"""
import hashlib
import json
import struct
import sys

import eva64lib as L
import extract as X

OUT = L.WORK_DIR / "build"
FONT_EN = L.WORK_DIR / "font" / "font_en.json"
CHARMAP_EN = L.GAME_DIR / "scripts" / "charmap_en.txt"
IMAGES_EN = L.WORK_DIR / "images_en"

# Each text block lives in a part of the ROM that the game copies into memory
# at a fixed address: memory address = 0x80000000 + rom offset - delta.
# Only code and tables inside the same part can point at its strings.
BLOCK_DELTA = {1: 0xA9510, 2: 0x14FA40}
# ROM range of the overlay each block belongs to (ovl3 and ovl7 in the decomp project's
# evangelion.yaml). Both load at memory address 0x80025C00.
BLOCK_OVERLAY = {1: (0xCF110, 0x113B10), 2: (0x175640, 0x1A1880)}
# The game's overlay table (10 words per overlay: rom start/end, ram start/end, text,
# data and bss ranges) and which entry each block's overlay is.
OVERLAY_TABLE = 0x3FB50
BLOCK_OVERLAY_INDEX = {1: 2, 2: 6}
# Unused (0xFF-filled) ROM space where enlarged overlay copies are written.
NEW_OVERLAY_ROM = 0x1C40000
# The largest original overlay ends here in memory; pools must stay below it.
OVERLAY_RAM_LIMIT = 0x80084DD0


def align4(n):
    return (n + 3) & ~3


def u32(rom, off):
    return struct.unpack(">I", rom[off:off + 4])[0]


def find_refs(rom, strings):
    """Return {string offset: [(kind, location)]}.

    kind "word": a 4-byte memory address stored at `location`.
    kind "code": a MIPS `lui` at `location` followed by `addiu` at location+4,
    which together load the address.
    """
    by_ram = {}
    for block, off, _ in strings:
        by_ram[(block, 0x80000000 + off - BLOCK_DELTA[block])] = off
    refs = {off: [] for _, off, _ in strings}
    for block in BLOCK_DELTA:
        lo, hi = BLOCK_OVERLAY[block]
        for loc in range(lo, hi - 4, 4):
            w = u32(rom, loc)
            off = by_ram.get((block, w))
            if off is not None:
                refs[off].append(("word", loc))
            if w >> 26 == 0x0F:  # lui rt, hi
                w2 = u32(rom, loc + 4)
                rt = (w >> 16) & 31
                if w2 >> 26 == 0x09 and ((w2 >> 21) & 31) == rt:  # addiu x, rt, lo
                    imm = w2 & 0xFFFF
                    addr = ((w & 0xFFFF) << 16) + (imm - 0x10000 if imm & 0x8000 else imm)
                    off = by_ram.get((block, addr))
                    if off is not None:
                        refs[off].append(("code", loc))
    return refs


def write_ref(rom, kind, loc, addr):
    if kind == "word":
        rom[loc:loc + 4] = struct.pack(">I", addr)
    else:
        lo = addr & 0xFFFF
        hi = ((addr + 0x8000) >> 16) & 0xFFFF
        rom[loc + 2:loc + 4] = struct.pack(">H", hi)
        rom[loc + 6:loc + 8] = struct.pack(">H", lo)


def n64_checksum(rom):
    """Header checksum for boot chip CIC-6102, the most common one."""
    seed = 0xF8CA4DDC
    t1 = t2 = t3 = t4 = t5 = t6 = seed
    M = 0xFFFFFFFF
    for (d,) in struct.iter_unpack(">I", rom[0x1000:0x101000]):
        if ((t6 + d) & M) < t6:
            t4 = (t4 + 1) & M
        t6 = (t6 + d) & M
        t3 ^= d
        s = d & 31
        r = ((d << s) | (d >> (32 - s))) & M
        t5 = (t5 + r) & M
        if t2 > d:
            t2 ^= r
        else:
            t2 ^= t6 ^ d
        t1 = (t1 + (t5 ^ d)) & M
    return t6 ^ t4 ^ t3, t5 ^ t2 ^ t1


def load_changes(path, tokens):
    changes = {}
    for n, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        sid, _, text = line.partition("\t")
        try:
            changes[int(sid)] = X.encode(text, tokens)
        except (KeyError, ValueError) as e:
            raise SystemExit(f"{path.name} line {n}: cannot encode {text!r} ({e!r}); a character is not in the font")
    return changes


# The game's text routines take a "letter spacing" value from each caller and add
# it after every character (-2 in narration, -5 on the briefing screen). That suits
# 24-pixel Japanese glyphs but crushes narrow Latin letters. These patches make the
# routines ignore it (spacing 0), so the width table alone decides spacing. The size
# of the texture the text is drawn into is left alone: callers work that size out
# themselves from the same spacing value, and changing it garbles the picture.
# rom offset: (original instruction, replacement)
SPACING_PATCHES = {
    0x12078: (0x00022E03, 0x00002821),  # measure one line:   sra a1,v0,24 -> move a1,zero
    0x120C0: (0x00024603, 0x00004021),  # measure many lines: sra t0,v0,24 -> move t0,zero
    0x12558: (0x0002AE03, 0x0000A821),  # draw text, pen step: sra s5,v0,24 -> move s5,zero
    # Project64's video plugin smooths the bottom edge of the text picture with whatever
    # lies in memory just after it, which showed as a row of specks under the subtitles.
    # Allocate and clear four extra blank pixel rows after every text picture (both spots
    # were unused "nop" instructions just before the size is multiplied out).
    0x1236C: (0x00000000, 0x24420004),  # text wrapper, before allocating: addiu v0,v0,4
    0x12508: (0x00000000, 0x24420004),  # draw text, before clearing:      addiu v0,v0,4
    # The game saves to a "16K EEPROM" chip and stops with an error screen if the cartridge
    # reports the smaller 4K kind. Emulators that do not recognise a modified ROM (they go
    # by a hash of the whole file) default to 4K. Treat a 4K answer as 16K: in the probe,
    # and in the library's read and write routines, which refuse blocks past 64 on a 4K chip.
    0x235E0: (0x24100001, 0x24100002),  # probe: 4K type reported as 16K: addiu s0,zero,2
    0x30464: (0x2C420040, 0x2C420100),  # write: block limit 64 -> 256:   sltiu v0,v0,0x100
    0x30684: (0x2C420040, 0x2C420100),  # read:  block limit 64 -> 256:   sltiu v0,v0,0x100
}


def apply_spacing_patches(rom):
    for off, (old, new) in SPACING_PATCHES.items():
        if u32(rom, off) != old:
            raise SystemExit(f"code at {off:#x} is not what the spacing patch expects")
        rom[off:off + 4] = struct.pack(">I", new)


# Diagnostic only, never for release: make the text-drawing routine record the address
# of every string it is asked to draw, so the test harness can log which strings appear.
# The routine's first two instructions are replaced by a jump to a small piece of code
# written over unused EEPROM error-message strings. That code keeps a call counter at
# memory 0x80000284 and the last 16 string addresses at 0x80000290.
TRACE_ENTRY = 0x12260            # draw wrapper, memory 0x800A7660
TRACE_CAVE = 0x65D70             # memory 0x800FB170
TRACE_COUNT_RAM = 0x284
TRACE_RING_RAM = 0x290


# Routines traced: (ROM offset of the routine, tag). Tag 0 records the first argument as it
# is (the text routine's string address). Other tags record tag*0x10000000 + argument:
# tag 1 and 2 are the game's two "play sound effect" routines, whose argument is the sound
# number (0-188 = effects bank, 189-495 = voice bank clip number + 189).
TRACE_HOOKS = [(TRACE_ENTRY, 0), (0x6354, 1), (0x6430, 2)]


def apply_trace_patch(rom):
    if u32(rom, TRACE_ENTRY) != 0x27BDFFC8 or rom[TRACE_CAVE:TRACE_CAVE + 4] != b"[ EE":
        raise SystemExit("trace patch: the ROM is not what was expected")
    cave = TRACE_CAVE
    for entry, tag in TRACE_HOOKS:
        first, second = u32(rom, entry), u32(rom, entry + 4)
        if first >> 26 in (1, 2, 3, 4, 5, 6, 7) or second >> 26 in (1, 2, 3, 4, 5, 6, 7):
            raise SystemExit(f"trace patch: routine at {entry:#x} starts with a jump and cannot be hooked")
        code = [
            0x3C018000,                                   # lui   at, 0x8000
            0x8C280000 | TRACE_COUNT_RAM,                 # lw    t0, count(at)
            0x3109000F,                                   # andi  t1, t0, 15
            0x00094880,                                   # sll   t1, t1, 2
            0x01214821,                                   # addu  t1, t1, at
        ]
        if tag:
            code += [
                0x3C0A0000 | (tag << 12),                 # lui   t2, tag<<12
                0x01445025,                               # or    t2, t2, a0
                0xAD2A0000 | TRACE_RING_RAM,              # sw    t2, ring(t1)
            ]
        else:
            code += [0xAD240000 | TRACE_RING_RAM]         # sw    a0, ring(t1)
        code += [
            0x25080001,                                   # addiu t0, t0, 1
            0xAC280000 | TRACE_COUNT_RAM,                 # sw    t0, count(at)
            first,                                        # original first instruction
            0x08000000 | (((0x80095400 + entry + 8) >> 2) & 0x3FFFFFF),  # j back
            second,                                       # original second instruction (delay slot)
        ]
        if cave + 4 * len(code) > 0x65E58:
            raise SystemExit("trace patch: not enough unused space for the hooks")
        rom[cave:cave + 4 * len(code)] = b"".join(struct.pack(">I", w) for w in code)
        rom[entry:entry + 8] = struct.pack(">II", 0x08000000 | (((0x80095400 + cave) >> 2) & 0x3FFFFFF), 0)
        cave += 4 * len(code)


def apply_images(rom):
    """Insert every PNG in work\\images_en (named <file number>_<name>.png) over the
    original image file. Each must compress into the space the original occupied."""
    if not IMAGES_EN.exists():
        return
    from PIL import Image
    offsets = L.yay0_offsets(rom)
    done = 0
    for path in sorted(IMAGES_EN.glob("*.png")):
        number, _, name = path.stem.partition("_")
        n = int(number)
        off = offsets[n]
        data, clen = L.yay0_decode(rom, off)
        img = L.parse_image(data)
        if img is None or img[3] != name:
            raise SystemExit(f"{path.name}: file {n} in the ROM is not an image called {name}")
        w, h, _, _, bpp, _ = img
        png = Image.open(path).convert("L")
        if png.size != (w, h):
            raise SystemExit(f"{path.name}: is {png.size[0]}x{png.size[1]}, the game image is {w}x{h}")
        grey = png.tobytes()
        if bpp == 4:
            vals = [(v + 8) // 17 for v in grey]
            pixels = bytes((vals[i] << 4) | vals[i + 1] for i in range(0, len(vals), 2))
        else:
            pixels = grey
        packed = L.yay0_encode(data[:16] + pixels)
        slot = (offsets[n + 1] - off) if n + 1 < len(offsets) else (clen + 7) & ~7
        if len(packed) > slot:
            raise SystemExit(f"{path.name}: compresses to {len(packed)} bytes but only {slot} are available; simplify the image")
        rom[off:off + slot] = packed + bytes(slot - len(packed))
        done += 1
    print(f"images: {done} replaced")


def apply_font(rom, font):
    """Replace glyphs and repack the whole font area, updating the glyph table."""
    entries = L.glyph_entries(rom)
    # A compressed size of 0 in the table means the glyph is stored raw (288 bytes).
    sizes = [csize or L.GLYPH_BYTES for _, csize, _ in entries]
    area = max(off + size for (off, _, _), size in zip(entries, sizes))
    blobs = [(bytes(rom[L.FONT_BASE + off:L.FONT_BASE + off + size]), csize) for (off, csize, _), size in zip(entries, sizes)]
    for slot_text, glyph in font.items():
        slot = int(slot_text)
        rom[L.WIDTH_TABLE + slot] = glyph["width"]
        if glyph["pixels"] is not None:
            packed = L.yay0_encode(bytes.fromhex(glyph["pixels"]))
            packed += bytes(-len(packed) % 8)
            blobs[slot] = (packed, len(packed))
    total = sum(len(b) for b, _ in blobs)
    if total > area:
        raise SystemExit(f"font needs {total} bytes but the font area only has {area}")
    rom[L.FONT_BASE:L.FONT_BASE + area] = bytes(area)
    pos = 0
    for slot, (blob, csize) in enumerate(blobs):
        rom[L.FONT_BASE + pos:L.FONT_BASE + pos + len(blob)] = blob
        rom[L.GLYPH_TABLE + slot * 12:L.GLYPH_TABLE + slot * 12 + 8] = struct.pack(">II", pos, csize)
        pos += len(blob)
    print(f"font: {len(font)} slots replaced, font area {total} of {area} bytes used")


def build(rom_in, changes, font=None, trace=False):
    rom = bytearray(rom_in)
    strings = X.find_strings(rom_in)
    refs = find_refs(rom_in, strings)
    unknown = set(changes) - set(range(1, len(strings) + 1))
    if unknown:
        raise SystemExit(f"unknown string ids: {sorted(unknown)}")

    # A changed string that still fits where the original was is written in place.
    # A longer one goes into a new "pool" placed in memory straight after the
    # overlay's working memory (bss), and everything that points at it is updated.
    pools = {block: [] for block in BLOCK_DELTA}
    for n, (block, off, codes) in enumerate(strings, 1):
        if n not in changes:
            continue
        new = changes[n]
        slot = align4(off + (len(codes) + 1) * 2) - off
        size = (len(new) + 1) * 2
        if size <= slot:
            rom[off:off + slot] = bytes(slot)
            rom[off:off + size - 2] = b"".join(struct.pack(">H", c) for c in new)
        elif not refs[off]:
            raise SystemExit(f"string {n:04d} has nothing pointing at it, so it cannot move; it must fit in {slot // 2 - 1} characters")
        else:
            pools[block].append((n, off, new))

    moved = 0
    free_rom = NEW_OVERLAY_ROM
    for block, pool in pools.items():
        if not pool:
            continue
        entry = OVERLAY_TABLE + BLOCK_OVERLAY_INDEX[block] * 0x28
        rom_start, rom_end, ram_start, ram_end, _, _, _, _, bss_start, bss_end = struct.unpack(">10I", rom[entry:entry + 0x28])
        if (rom_start, rom_end) != BLOCK_OVERLAY[block] or ram_start + (rom_end - rom_start) != bss_start:
            raise SystemExit(f"overlay table entry for block {block} is not what was expected")
        blob = bytearray()
        for n, off, new in pool:
            addr = bss_end + len(blob)
            for kind, loc in refs[off]:
                if kind == "code" and struct.unpack(">H", rom[loc + 2:loc + 4])[0] != ((addr + 0x8000) >> 16) & 0xFFFF:
                    raise SystemExit(f"string {n:04d}: pool address {addr:#x} needs a different upper half than the code loads")
                write_ref(rom, kind, loc, addr)
            blob += b"".join(struct.pack(">H", c) for c in new) + b"\0\0"
            blob += bytes(-len(blob) % 4)
            moved += 1
        text_end = None
        if font and block == 1:
            # extra colours for the translator's emblem on the first credit card
            code = credit_palette_code(rom, bss_end + len(blob))
            blob += code
            text_end = bss_end + len(blob)
        new_ram_end = bss_end + len(blob)
        if new_ram_end > OVERLAY_RAM_LIMIT:
            raise SystemExit(f"block {block} text pool is too large")
        # The loader copies (rom_end - rom_start) bytes to ram_start and then clears the
        # bss range, so the copy is: original overlay, zeros where bss sits, then the pool.
        image = bytes(rom[rom_start:rom_end]) + bytes(bss_end - bss_start) + bytes(blob)
        image += bytes(-len(image) % 16)
        if any(b != 0xFF for b in rom[free_rom:free_rom + len(image)]):
            raise SystemExit("the ROM area chosen for the enlarged overlay is not empty")
        rom[free_rom:free_rom + len(image)] = image
        rom[entry:entry + 16] = struct.pack(">4I", free_rom, free_rom + len(image), ram_start, new_ram_end)
        if text_end:
            # the loader clears the processor's instruction cache for the "text" range only;
            # stretch that range over the added code so a real console runs it correctly
            rom[entry + 0x14:entry + 0x18] = struct.pack(">I", text_end)
        print(f"block {block}: {len(pool)} strings in a {len(blob)}-byte pool at memory {bss_end:#x}; overlay copy at ROM {free_rom:#x}")
        free_rom += len(image)

    if font:
        apply_font(rom, font)
        apply_spacing_patches(rom)
        apply_images(rom)
    if trace:
        apply_trace_patch(rom)
    if not (pools[1] and not trace and keep_original_checksum(rom, rom_in)):
        c1, c2 = n64_checksum(rom)
        rom[0x10:0x18] = struct.pack(">II", c1, c2)
    return bytes(rom), len(strings), moved


# The first credit card of the opening ("Produced by BANDAI Co., Ltd.", image id 0x9B) is one
# 16-value picture shown as three sprites. Each sprite has its own 16-entry palette and
# blanks two of the value groups 1-5, 6-10, 11-15 with the game's "set palette entry"
# routine at 0x800379B0 (sprite, entry, RGBA5551 colour), so each shows one group. The
# first sprite shows values 11-15 and is drawn untinted, so its entries can be any colour.
# The translator's emblem uses 12-15; this adds a small routine after the text pool that
# sets them, and calls it right after the first sprite's blanking loop. The two
# instructions it replaces (set a1 = 2, call the image loader 0x80036494) are done by the
# routine itself on the way out.
CREDIT_HOOK = 0xE2470                      # ROM, in the original place of the ovl3 overlay
CREDIT_COLOURS = {                         # palette entry: (red, green, blue), 0-255
    12: (140, 205, 50),                    # feathers, light
    13: (70, 135, 25),                     # feathers, dark
    14: (245, 140, 185),                   # glasses and bow
    15: (165, 165, 170),                   # beak
}
SET_PALETTE_ENTRY = 0x800379B0
LOAD_IMAGE = 0x80036494


def rgba5551(rgb):
    r, g, b = (v >> 3 for v in rgb)
    return (r << 11) | (g << 6) | (b << 1) | 1


def credit_palette_code(rom, addr):
    """Machine code (MIPS) for the palette routine, to sit at memory address `addr`. Patches the call into `rom`."""
    if u32(rom, CREDIT_HOOK) != 0x24050002 or u32(rom, CREDIT_HOOK + 4) != (0x0C000000 | ((LOAD_IMAGE >> 2) & 0x3FFFFFF)):
        raise SystemExit("credit card code is not what was expected")
    table = addr + 19 * 4
    words = [
        0x27BDFFE0,                                    # addiu sp, sp, -0x20
        0xAFBF001C,                                    # sw    ra, 0x1c(sp)
        0xAFB00018,                                    # sw    s0, 0x18(sp)
        0x3C100000 | (((table + 0x8000) >> 16) & 0xFFFF),   # lui   s0, table (upper half)
        0x26100000 | (table & 0xFFFF),                 # addiu s0, s0, table (lower half)
        0x96050000,                                    # loop: lhu a1, 0(s0)      entry number
        0x10A00005,                                    # beqz  a1, done
        0x96060002,                                    # lhu   a2, 2(s0)          colour
        0x0C000000 | ((SET_PALETTE_ENTRY >> 2) & 0x3FFFFFF),  # jal set palette entry
        0x8E44000C,                                    # lw    a0, 0xc(s2)        the sprite just set up
        0x1000FFFA,                                    # b     loop
        0x26100004,                                    # addiu s0, s0, 4
        0x8FBF001C,                                    # done: lw ra, 0x1c(sp)
        0x8FB00018,                                    # lw    s0, 0x18(sp)
        0x2404009B,                                    # addiu a0, zero, 0x9b     what the replaced
        0x24050002,                                    # addiu a1, zero, 2        instructions did:
        0x24060018,                                    # addiu a2, zero, 0x18     load the image again
        0x08000000 | ((LOAD_IMAGE >> 2) & 0x3FFFFFF),  # j     image loader (returns to the caller)
        0x27BD0020,                                    # addiu sp, sp, 0x20
    ]
    code = b"".join(struct.pack(">I", w) for w in words)
    for entry, rgb in sorted(CREDIT_COLOURS.items()):
        code += struct.pack(">HH", entry, rgba5551(rgb))
    code += struct.pack(">HH", 0, 0)
    rom[CREDIT_HOOK:CREDIT_HOOK + 8] = struct.pack(">II", 0x0C000000 | ((addr >> 2) & 0x3FFFFFF), 0)
    return code


# Emulators pick a game's settings (save type, memory size) by the checksum in the ROM
# header, so a ROM with a new checksum is not recognised and may not boot. The checksum
# covers ROM 0x1000-0x101000. Once block 1's overlay has been moved to the end of the ROM,
# its old place (0xCF110-0x113B10) is never read by the game, and the last words of the
# checksummed range fall inside it. Four of those words are solved for so that the real
# checksum comes out equal to the original's: the header stays as it was and is still valid
# for the console's boot check.
CHECKSUM_FILL = 0x100FF0


def keep_original_checksum(rom, rom_in):
    try:
        import z3
    except ImportError:
        print("checksum: z3 is not installed, so the header checksum is recalculated instead")
        return False
    target = struct.unpack(">II", rom_in[0x10:0x18])
    M = 0xFFFFFFFF
    t1 = t2 = t3 = t4 = t5 = t6 = 0xF8CA4DDC
    for (d,) in struct.iter_unpack(">I", bytes(rom[0x1000:CHECKSUM_FILL])):
        if ((t6 + d) & M) < t6:
            t4 = (t4 + 1) & M
        t6 = (t6 + d) & M
        t3 ^= d
        s = d & 31
        r = ((d << s) | (d >> (32 - s))) & M
        t5 = (t5 + r) & M
        t2 ^= r if t2 > d else t6 ^ d
        t1 = (t1 + (t5 ^ d)) & M
    T1, T2, T3, T4, T5, T6 = (z3.BitVecVal(v, 32) for v in (t1, t2, t3, t4, t5, t6))
    words = [z3.BitVec(f"d{i}", 32) for i in range(4)]
    solver = z3.Solver()
    solver.set("timeout", 300000)
    for d in words:
        r = z3.RotateLeft(d, d & 31)
        n6 = T6 + d
        T4 = z3.If(z3.ULT(n6, T6), T4 + 1, T4)
        T6 = n6
        T3 = T3 ^ d
        T5 = T5 + r
        T2 = z3.If(z3.UGT(T2, d), T2 ^ r, T2 ^ T6 ^ d)
        T1 = T1 + (T5 ^ d)
    solver.add(T6 ^ T4 ^ T3 == target[0], T5 ^ T2 ^ T1 == target[1])
    if solver.check() != z3.sat:
        print("checksum: no filler found, so the header checksum is recalculated instead")
        return False
    model = solver.model()
    rom[CHECKSUM_FILL:CHECKSUM_FILL + 16] = struct.pack(">4I", *(model[d].as_long() for d in words))
    if n64_checksum(rom) != target:
        raise SystemExit("checksum: filler did not reproduce the original checksum")
    print("checksum: kept equal to the original's (emulators will recognise the ROM)")
    return True


def main():
    rom_path = L.find_rom()
    rom_in = rom_path.read_bytes()
    if hashlib.sha1(rom_in).hexdigest() != L.ROM_SHA1:
        raise SystemExit("ROM hash does not match the expected original")
    c1, c2 = n64_checksum(rom_in)
    if struct.pack(">II", c1, c2) != rom_in[0x10:0x18]:
        raise SystemExit("checksum routine does not reproduce the original header checksum")
    print("checksum routine reproduces the original header checksum")

    tokens = X.load_charmap()
    OUT.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) == 1:
        out, count, moved = build(rom_in, {})
        same = out == rom_in
        print(f"rebuilt {count} strings with no changes: {'BYTE-IDENTICAL to the original' if same else 'DIFFERENT from the original'}")
        return 0 if same else 1
    mode = sys.argv[3] if len(sys.argv) == 4 else ""
    if len(sys.argv) not in (3, 4) or mode not in ("", "en", "trace", "en-trace"):
        raise SystemExit(__doc__)
    english = mode.startswith("en")
    trace = mode.endswith("trace")
    font = None
    if english:
        if not FONT_EN.exists():
            raise SystemExit("English font not found; run makefont.bat first")
        font = json.loads(FONT_EN.read_text(encoding="utf-8"))
        tokens = X.load_charmap(CHARMAP_EN)
    changes = load_changes(L.GAME_DIR / sys.argv[1], tokens)
    out, count, moved = build(rom_in, changes, font, trace)
    target = OUT / f"{sys.argv[2]}.z64"
    target.write_bytes(out)
    diff = sum(1 for a, b in zip(out, rom_in) if a != b)
    print(f"{len(changes)} strings changed, {moved} strings moved, {diff} bytes differ from the original")
    print(f"header checksum {out[0x10:0x18].hex()}")
    print(f"wrote {target} ({len(out)} bytes)")
    if out[0x10:0x18] != rom_in[0x10:0x18]:
        note = OUT / f"{sys.argv[2]}_project64_settings.txt"
        note.write_text(project64_entries(out, sys.argv[2]), encoding="utf-8")
        print(f"checksum differs from the original, so Project64 will not recognise this ROM; see {note}")
    return 0


def project64_entries(rom, name):
    """Text to paste into Project64's settings files so it treats this build like the original game."""
    key = "[%08X-%08X-C:%02X]" % (*struct.unpack(">II", rom[0x10:0x18]), rom[0x3E])
    return (
        "Project64 picks per-game settings by the ROM's header checksum. This build has a new\n"
        "checksum, so paste the two blocks below at the END of the named files in Project64's\n"
        "Config folder (close Project64 first, and keep a copy of each file before editing).\n\n"
        "===== add to Project64.rdb =====\n"
        f"{key}\nGood Name=Neon Genesis Evangelion (J) [{name}]\nInternal Name=EVANGELION\nStatus=Compatible\n"
        "32bit=Yes\nAudioResetOnLoad=Yes\nClear Frame=1\nCulling=1\nRDRAM Size=4\nSave Type=16kbit Eeprom\n\n"
        "===== add to Video.rdb =====\n"
        f"{key}\nGood Name=Neon Genesis Evangelion (J) [{name}]\nInternal Name=EVANGELION\ndepthmode=1\n"
    )


if __name__ == "__main__":
    sys.exit(main())
