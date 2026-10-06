"""Stage 2 extraction for Neon Genesis Evangelion (N64).

Reads the ROM in games\\eva64\\original (never writes there) and fills
games\\eva64\\work\\extract with:

  text\\strings_jp.tsv      every font-drawn string, decoded with the charmap
  font\\font_jp.png         the whole font, 16 glyphs per row
  images\\all\\*.png         every image file in the ROM (greyscale view)
  images\\index.tsv         one line per image: where it is and its size
  images\\changed_by_korean\\  JP and KR versions of images the Korean patch changed

Run it through extract.bat.
"""
import hashlib
import shutil
import sys

import eva64lib as L

CHARMAP_FILE = L.GAME_DIR / "scripts" / "charmap_jp.txt"
KOREAN_ROM = L.WORK_DIR / "korean" / "eva_k_1.z64"
OUT = L.WORK_DIR / "extract"

# The two parts of the program data that hold font-drawn strings. Found by
# scanning the whole program area for runs of valid character codes; these
# were the only places that decoded to real Japanese.
TEXT_BLOCKS = [(0x112220, 0x112DA0), (0x190950, 0x191C64)]


def load_charmap(path=CHARMAP_FILE):
    tokens = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        tokens += line.split(" ")
    if len(tokens) != L.GLYPH_COUNT or len(set(tokens)) != L.GLYPH_COUNT:
        raise SystemExit(f"charmap must hold {L.GLYPH_COUNT} unique entries, has {len(tokens)} ({len(set(tokens))} unique)")
    return tokens


def decode(codes, tokens):
    out = []
    for c in codes:
        if c == L.CODE_NEWLINE:
            out.append("\\n")
        else:
            t = tokens[c - L.CODE_BASE]
            out.append(" " if t == "SP" else t)
    return "".join(out)


def encode(text, tokens):
    lookup = {(" " if t == "SP" else t): i + L.CODE_BASE for i, t in enumerate(tokens)}
    codes = []
    i = 0
    while i < len(text):
        if text.startswith("\\n", i):
            codes.append(L.CODE_NEWLINE)
            i += 2
        elif text[i] == "{":
            j = text.index("}", i) + 1
            codes.append(lookup[text[i:j]])
            i = j
        else:
            codes.append(lookup[text[i]])
            i += 1
    return codes


def valid(code):
    return code == L.CODE_NEWLINE or L.CODE_BASE <= code < L.CODE_BASE + L.GLYPH_COUNT


def find_strings(rom):
    """Strings start on a 4-byte boundary, hold at least two visible characters and end with 0000."""
    found = []
    for block, (start, end) in enumerate(TEXT_BLOCKS, 1):
        i = start
        while i < end:
            codes = []
            j = i
            while True:
                c = (rom[j] << 8) | rom[j + 1]
                if not valid(c):
                    break
                codes.append(c)
                j += 2
            visible = sum(1 for c in codes if c > L.CODE_BASE)
            if c == L.CODE_END and visible >= 2:
                found.append((block, i, codes))
                i = (j + 2 + 3) & ~3
            else:
                i += 4
    return found


def extract_text(rom, kr, tokens):
    out = OUT / "text"
    out.mkdir(parents=True, exist_ok=True)
    strings = find_strings(rom)
    lines = ["id\tblock\trom_offset\tcodes\tkorean_changed\ttext"]
    chars = 0
    bad = 0
    for n, (block, off, codes) in enumerate(strings, 1):
        text = decode(codes, tokens)
        if encode(text, tokens) != codes:
            bad += 1
        chars += sum(1 for c in codes if c > L.CODE_BASE)
        size = len(codes) * 2
        changed = "" if kr is None else ("yes" if rom[off:off + size] != kr[off:off + size] else "no")
        lines.append(f"{n:04d}\t{block}\t{off:06X}\t{len(codes)}\t{changed}\t{text}")
    (out / "strings_jp.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"text: {len(strings)} strings, {chars} visible characters -> {out / 'strings_jp.tsv'}")
    print(f"text: decode->encode round trip failures: {bad}")
    return bad


def extract_font(rom):
    out = OUT / "font"
    out.mkdir(parents=True, exist_ok=True)
    L.font_sheet(rom, out / "font_jp.png", cols=16, scale=2)
    widths = list(rom[L.WIDTH_TABLE:L.WIDTH_TABLE + L.GLYPH_COUNT])
    (out / "widths_jp.txt").write_text("\n".join(f"{i}\t{w}" for i, w in enumerate(widths)) + "\n", encoding="utf-8")
    print(f"font: {L.GLYPH_COUNT} glyphs -> {out / 'font_jp.png'}")


def extract_images(rom, kr):
    all_dir = OUT / "images" / "all"
    kr_dir = OUT / "images" / "changed_by_korean"
    for d in (all_dir, kr_dir):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    font_end = L.FONT_BASE + max(o + c for o, c, _ in L.glyph_entries(rom))
    offsets = L.yay0_offsets(rom)
    index = ["file\trom_offset\tcompressed_bytes\tname\twidth\theight\tbpp\tflags\tkorean_changed"]
    images = 0
    changed_images = 0
    other_changed = []
    for n, off in enumerate(offsets):
        data, clen = L.yay0_decode(rom, off)
        changed = kr is not None and rom[off:off + clen] != kr[off:off + clen]
        img = L.parse_image(data)
        if img is None:
            if changed and off >= font_end:
                other_changed.append(off)
            continue
        images += 1
        w, h, flags, name, bpp, _ = img
        stem = f"{n:04d}_{name}"
        L.write_png_gray(all_dir / f"{stem}.png", w, h, L.image_rows_gray(img))
        index.append(f"{n:04d}\t{off:06X}\t{clen}\t{name}\t{w}\t{h}\t{bpp}\t{flags:08X}\t{'yes' if changed else ('' if kr is None else 'no')}")
        if changed:
            changed_images += 1
            shutil.copyfile(all_dir / f"{stem}.png", kr_dir / f"{stem}_jp.png")
            if kr[off:off + 4] == b"Yay0":
                kimg = L.parse_image(L.yay0_decode(kr, off)[0])
                if kimg is not None:
                    L.write_png_gray(kr_dir / f"{stem}_kr.png", kimg[0], kimg[1], L.image_rows_gray(kimg))
    (OUT / "images" / "index.tsv").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(f"images: {images} of {len(offsets)} files are images -> {all_dir}")
    if kr is not None:
        print(f"images: {changed_images} changed by the Korean patch -> {kr_dir}")
        print(f"other (non-image, non-font) files changed by the Korean patch: {len(other_changed)} {[hex(o) for o in other_changed[:20]]}")


def main():
    rom_path = L.find_rom()
    rom = rom_path.read_bytes()
    sha1 = hashlib.sha1(rom).hexdigest()
    if sha1 != L.ROM_SHA1:
        raise SystemExit(f"ROM hash {sha1} is not the expected {L.ROM_SHA1}")
    print(f"ROM ok: {rom_path.name}")
    kr = KOREAN_ROM.read_bytes() if KOREAN_ROM.exists() else None
    if kr is None:
        print("Korean reference ROM not found; skipping the comparison columns")
    tokens = load_charmap()
    bad = extract_text(rom, kr, tokens)
    extract_font(rom)
    extract_images(rom, kr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
