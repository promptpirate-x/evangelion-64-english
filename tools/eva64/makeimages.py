"""Draw English replacements for text-only images in Evangelion 64.

Reads games\\eva64\\scripts\\images_en.tsv (tab separated):
    file  name  text  size  weight  width%  align  x  baseline
Several lines may name the same file; each adds one piece of text to that image.
A line whose text is "@frame" keeps the original picture's outer border, as wide as
the number in its size column (for boxed labels).
Writes games\\eva64\\work\\images_en\\<file>_<name>.png at the size of the original
image. build.py inserts every PNG found in that folder, so hand-edited images
can be dropped there too.

Colours follow the original image: its most common pixel value becomes the
background and its most common contrasting value becomes the lettering, so
cards that are stored dark-on-light or in grey stay that way.

PNG grey level = pixel value x 17 for 4-bit images. Run it through makeimages.bat.
"""
import collections

from PIL import Image, ImageDraw

import eva64lib as L
import makefont

SPEC = L.GAME_DIR / "scripts" / "images_en.tsv"
OUT = L.WORK_DIR / "images_en"
LEVELS = 15     # steps of edge softening between background and lettering (3 = coarse, 15 = smoothest)


def colours(img):
    """(background, lettering) pixel values, 0..15, taken from the original image."""
    w, h, _, _, _, px = img
    rows = L.unpack_4bpp(px, w, h)
    counts = collections.Counter(v for row in rows for v in row)
    # background = the commonest value around the edge (bold lettering can outnumber it overall)
    edge = list(rows[0]) + list(rows[-1]) + [r[0] for r in rows] + [r[-1] for r in rows]
    bg = collections.Counter(edge).most_common(1)[0][0]
    far = [(c, v) for v, c in counts.items() if abs(v - bg) >= 6]
    fg = max(far)[1] if far else 15 - bg
    return bg, fg


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rom = L.find_rom().read_bytes()
    offsets = L.yay0_offsets(rom)
    jobs = collections.OrderedDict()
    for n, line in enumerate(SPEC.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) not in (9, 10):
            raise SystemExit(f"{SPEC.name} line {n}: expected 9 or 10 columns, found {len(parts)}")
        jobs.setdefault((int(parts[0]), parts[1]), []).append((n, parts[2:]))
    for (file_no, name), pieces in jobs.items():
        img = L.parse_image(L.yay0_decode(rom, offsets[file_no])[0])
        if img is None or img[3] != name or img[4] != 4:
            raise SystemExit(f"{SPEC.name}: file {file_no} is not a 4-bit image called {name}")
        w, h = img[0], img[1]
        bg, fg = colours(img)
        used = {v for row in L.unpack_4bpp(img[5], w, h) for v in row}
        values = [[bg] * w for _ in range(h)]
        frame = 0
        for n, piece in pieces:
            text, size, weight, width, align, x, baseline = piece[:7]
            # 10th column: a pixel value (hard edges in that value), "hard" (hard edges in the
            # usual lettering value) or "soft3" (coarse 3-step edge softening, for fade-in cards)
            option = piece[7].strip() if len(piece) > 7 else ""
            levels = 3 if option == "soft3" else LEVELS
            forced = None if option in ("", "soft3") else fg if option == "hard" else int(option)
            ink = Image.new("L", (w, h), 0)
            draw = ImageDraw.Draw(ink)
            if text.startswith("@frame"):
                frame = int(size)      # keep this many pixels of the original around the edge
                continue
            if text.startswith("@bitmap:"):
                # paste a ready-made picture from scripts\ (grey level = pixel value x 17, 0 = see-through)
                # with its top-left corner at (x, baseline)
                bmp = Image.open(L.GAME_DIR / "scripts" / text[8:]).convert("L")
                bp = bmp.load()
                for yy in range(bmp.height):
                    for xx in range(bmp.width):
                        v = (bp[xx, yy] + 8) // 17
                        if v and 0 <= int(x) + xx < w and 0 <= int(baseline) + yy < h:
                            values[int(baseline) + yy][int(x) + xx] = v
                continue
            anchor = {"left": "ls", "right": "rs", "center": "ms"}[align]
            size = int(size)
            # shrink the lettering a point at a time until it fits the image
            while True:
                font = makefont.load_font(size, float(weight), float(width))
                box = draw.textbbox((int(x), int(baseline)), text, font=font, anchor=anchor)
                fits = box[0] >= 1 and box[2] <= w - 1 and box[1] >= 1 and box[3] <= h - 1
                if fits or size <= 8:
                    break
                size -= 1
            if not fits:
                print(f"WARNING line {n}: {text!r} does not fit the {w}x{h} image (box {box})")
            draw.text((int(x), int(baseline)), text, font=font, fill=255, anchor=anchor)
            # Soft edges are only safe where the picture's values are a plain dark-to-light
            # ramp. Some cards use value groups as separate layers or colours, and an
            # in-between value there shows up as specks. So: a piece with a value given in the
            # 10th column gets hard edges in exactly that value, and otherwise an in-between
            # shade is used only if the original picture itself uses that value.
            target = fg if forced is None else forced
            box = ink.getbbox()
            if box:
                px = ink.load()
                for yy in range(box[1], box[3]):
                    for xx in range(box[0], box[2]):
                        v = px[xx, yy]
                        if v == 0:
                            continue
                        if forced is None:
                            shade = round(bg + (target - bg) * (round(v / 255 * levels) / levels))
                            if shade in used or shade == target:
                                if shade != bg:
                                    values[yy][xx] = shade
                                continue
                        if v >= 128:
                            values[yy][xx] = target
        out = Image.frombytes("L", (w, h), bytes(v * 17 for row in values for v in row))
        if frame:
            orig = Image.frombytes("L", (w, h), b"".join(bytes(r) for r in L.image_rows_gray(img)))
            inner = out.crop((frame, frame, w - frame, h - frame))
            out = orig
            out.paste(inner, (frame, frame))
        out.save(OUT / f"{file_no:04d}_{name}.png")
    print(f"{len(jobs)} images written to {OUT}")


if __name__ == "__main__":
    main()
