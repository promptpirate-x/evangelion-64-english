"""Build before/after comparison pictures from two harness runs of the same plan.

  compare_shots.py <plan> <out folder>

Takes games\eva64\work\harness\original\<plan>\*.png (Japanese) and the same names from
games\eva64\work\harness\eva64_en\<plan>\ (English), and writes <out folder>\<name>.png with
the two side by side, Japanese on the left, plus a contact sheet of all pairs.
"""
import sys

from PIL import Image, ImageDraw

import eva64lib as L


def main():
    plan, out = sys.argv[1], L.WORKSPACE.parent / sys.argv[2] if not sys.argv[2][1:2] == ":" else None
    from pathlib import Path
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    jp_dir = L.WORK_DIR / "harness" / "original" / plan
    en_dir = L.WORK_DIR / "harness" / "eva64_en" / plan
    pairs = []
    for jp in sorted(jp_dir.glob("*.png")):
        en = en_dir / jp.name
        if not en.exists():
            continue
        a, b = Image.open(jp).convert("RGB"), Image.open(en).convert("RGB")
        w, h = a.size
        pair = Image.new("RGB", (w * 2 + 8, h), (30, 30, 30))
        pair.paste(a, (0, 0))
        pair.paste(b, (w + 8, 0))
        name = jp.stem.split("_", 1)[1] if "_" in jp.stem else jp.stem
        pair.save(out / f"{name}.png")
        pairs.append((name, pair))
    if pairs:
        pw, ph = pairs[0][1].size
        scale = 0.5
        tw, th = int(pw * scale), int(ph * scale)
        sheet = Image.new("RGB", (tw, (th + 18) * len(pairs)), (30, 30, 30))
        d = ImageDraw.Draw(sheet)
        for i, (name, pair) in enumerate(pairs):
            d.text((4, i * (th + 18) + 2), name, fill=(255, 255, 0))
            sheet.paste(pair.resize((tw, th), Image.LANCZOS), (0, i * (th + 18) + 16))
        sheet.save(out / "all_pairs.png")
    print(f"{len(pairs)} pairs written to {out}")


if __name__ == "__main__":
    main()
