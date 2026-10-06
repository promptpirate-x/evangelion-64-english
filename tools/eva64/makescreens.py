"""Redraw the text on Evangelion 64's full-screen instruction pictures in English.

These 320x240 pictures hold control tables with button icons and a faint
watermark behind them, so they cannot be drawn from scratch. Instead each line of
games\\eva64\\scripts\\screens_en.tsv names a rectangle on one picture:

    file  name  x0  y0  x1  y1  size  align  text

The Japanese lettering inside the rectangle is erased (bright pixels and their
dark outline are filled in from the surrounding background, so icons outside
the rectangle and the watermark are kept), then the English text is drawn
centred vertically in it, shrunk if needed to fit. \\n makes a second line.
Empty text only erases. An align value ending in "!" (e.g. center!) paints the whole
rectangle one flat shade first, for cells where the normal erase leaves lettering behind.

The pictures are 8-bit; their pixel values run from dark (0) to white (255).
Output goes to games\\eva64\\work\\images_en for build.py to insert, and a
before/after sheet to games\\eva64\\work\\screens_preview. Run through makescreens.bat.
"""
import collections

from PIL import Image, ImageDraw

import eva64lib as L
import makefont

SPEC = L.GAME_DIR / "scripts" / "screens_en.tsv"
OUT = L.WORK_DIR / "images_en"
PREVIEW = L.WORK_DIR / "screens_preview"
BRIGHT = 120      # lettering is brighter than this
DARK = 18         # outline is darker than this
WEIGHT = 700
WIDTH = 68


def erase(px, w, h, x0, y0, x1, y1):
    """Remove lettering inside the rectangle, keeping the background behind it."""
    # the cell background is the commonest shade that is not outline-black or lettering-white
    mids = [px[x, y] for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if DARK <= px[x, y] <= 215]
    back = collections.Counter(int(v / 6) for v in mids).most_common(1)[0][0] * 6 + 3 if mids else 30
    bright = max(BRIGHT, back + 55)

    def is_bright(x, y):
        return px[x, y] > bright
    text = set()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            v = px[x, y]
            if v > bright:
                text.add((x, y))
            elif v < DARK and back >= DARK:
                near = any(0 <= x + dx < w and 0 <= y + dy < h and is_bright(x + dx, y + dy)
                           for dy in (-2, -1, 0, 1, 2) for dx in (-2, -1, 0, 1, 2))
                if near:
                    text.add((x, y))
    # the soft edge of the lettering is mid-grey: take one more pixel all round
    for (x, y) in list(text):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if x0 <= x + dx <= x1 and y0 <= y + dy <= y1:
                    text.add((x + dx, y + dy))
    # Fill short gaps by blending the kept pixels either side (keeps the watermark's
    # shading); fill longer runs with the cell's background shade (no streaks).
    for y in range(y0, y1 + 1):
        x = x0
        while x <= x1:
            if (x, y) not in text:
                x += 1
                continue
            start = x
            while x <= x1 and (x, y) in text:
                x += 1
            left = px[start - 1, y] if start - 1 >= x0 else None
            right = px[x, y] if x <= x1 else None
            span = x - start
            for rx in range(start, x):
                if left is not None and right is not None and span <= 6:
                    px[rx, y] = int((left * (x - rx) + right * (rx - start + 1)) / (span + 1))
                else:
                    px[rx, y] = back


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PREVIEW.mkdir(parents=True, exist_ok=True)
    rom = L.find_rom().read_bytes()
    offsets = L.yay0_offsets(rom)
    jobs = collections.OrderedDict()
    for n, line in enumerate(SPEC.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) == 8:
            parts.append("")
        if len(parts) != 9:
            raise SystemExit(f"{SPEC.name} line {n}: expected 9 columns, found {len(parts)}")
        jobs.setdefault((int(parts[0]), parts[1]), []).append((n, parts[2:]))
    for (file_no, name), pieces in jobs.items():
        img = L.parse_image(L.yay0_decode(rom, offsets[file_no])[0])
        if img is None or img[3] != name or img[4] != 8:
            raise SystemExit(f"{SPEC.name}: file {file_no} is not an 8-bit image called {name}")
        w, h = img[0], img[1]
        before = Image.frombytes("L", (w, h), img[5])
        im = before.copy()
        px = im.load()
        for n, (x0, y0, x1, y1, size, align, text) in pieces:
            if align.endswith("!"):
                # stubborn cell (bright watermark behind the lettering): paint it one flat shade
                box = (int(x0), int(y0), int(x1) + 1, int(y1) + 1)
                shades = sorted(im.crop(box).getdata())
                im.paste(shades[int(len(shades) * 0.3)], box)
            else:
                erase(px, w, h, int(x0), int(y0), int(x1), int(y1))
        draw = ImageDraw.Draw(im)
        for n, (x0, y0, x1, y1, size, align, text) in pieces:
            if not text:
                continue
            x0, y0, x1, y1, size = int(x0), int(y0), int(x1), int(y1), int(size)
            align = align.rstrip("!")
            lines = text.split("\\n")
            while True:
                font = makefont.load_font(size, WEIGHT, WIDTH)
                widths = [draw.textlength(t, font=font) for t in lines]
                line_h = size + 2
                if (max(widths) <= x1 - x0 - 2 and line_h * len(lines) <= y1 - y0 + 3) or size <= 7:
                    break
                size -= 1
            if max(widths) > x1 - x0 - 2:
                print(f"WARNING line {n}: {text!r} does not fit its rectangle even at size {size}")
            top = (y0 + y1 + 1) / 2 - line_h * len(lines) / 2
            for i, t in enumerate(lines):
                if align == "left":
                    x, anchor = x0 + 2, "ls"
                elif align == "right":
                    x, anchor = x1 - 1, "rs"
                else:
                    x, anchor = (x0 + x1 + 1) / 2, "ms"
                baseline = top + i * line_h + size * 0.92
                draw.text((x, baseline), t, font=font, fill=255, anchor=anchor, stroke_width=1, stroke_fill=3)
        # fewer shades in the redrawn areas, so the picture compresses into the original's space
        old = before.load()
        for y in range(h):
            for x in range(w):
                if px[x, y] != old[x, y]:
                    px[x, y] = min(255, int((px[x, y] + 12) / 25) * 25)
        im.save(OUT / f"{file_no:04d}_{name}.png")
        both = Image.new("L", (w * 2 + 4, h), 128)
        both.paste(before, (0, 0))
        both.paste(im, (w + 4, 0))
        both.resize((both.width * 2, both.height * 2), Image.LANCZOS).save(PREVIEW / f"{file_no:04d}_{name}.png")
    print(f"{len(jobs)} screens written to {OUT}; before/after sheets in {PREVIEW}")


if __name__ == "__main__":
    main()
