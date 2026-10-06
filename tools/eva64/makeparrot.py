"""Make the small emblem pictures for the translator credit on the first opening card.

That card can show two colours besides black: white (pixel value 11) and red (value 6).

  credit_parrot.png   from games\\eva64\\scripts\\credit_source.png, the user's own parrot
                      picture with a see-through background: shrunk and reduced to white
                      plus the four extra card colours defined in build.py (CREDIT_COLOURS).
  credit_emoji.png    a parrot emoji and a pirate flag side by side, drawn from the
                      open-licensed Noto Emoji font (tools\\fonts).

Both go to games\\eva64\\scripts; images_en.tsv places one with an "@bitmap" row.
Grey level in these files = pixel value x 17; 0 is see-through.
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

import eva64lib as L

S = L.GAME_DIR / "scripts"
EMOJI_FONT = L.WORKSPACE / "tools" / "fonts" / "NotoEmoji-VF.ttf"
HEIGHT = 58
WHITE, RED = 11, 6


def is_pink(rgb):
    r, g, b = rgb[:3]
    return r > 180 and b > 110 and r - g > 40 and g < 200


def parrot():
    """Shrink the picture and reduce it to the colours the card offers: black (see-through),
    white (value 11) and the four extra palette entries that build.py sets (values 12-15)."""
    import build
    src = Image.open(S / "credit_source.png").convert("RGBA")
    box = src.getchannel("A").point(lambda v: 255 if v > 127 else 0).getbbox()
    src = src.crop(box)
    width = round(src.width * HEIGHT / src.height)
    small = src.resize((width, HEIGHT), Image.LANCZOS)
    mask = small.getchannel("A").point(lambda v: 255 if v > 127 else 0)
    values = [0, WHITE] + sorted(build.CREDIT_COLOURS)
    colours = [(0, 0, 0), (255, 255, 255)] + [build.CREDIT_COLOURS[v] for v in sorted(build.CREDIT_COLOURS)]
    pal = Image.new("P", (1, 1))
    flat = [c for rgb in colours for c in rgb]
    pal.putpalette(flat + flat[:3] * (256 - len(colours)))
    reduced = small.convert("RGB").quantize(palette=pal, dither=Image.FLOYDSTEINBERG)
    inner = mask.filter(ImageFilter.MinFilter(3))
    out = Image.new("L", (width, HEIGHT), 0)
    o, r, m, i = out.load(), reduced.load(), mask.load(), inner.load()
    grey = max(build.CREDIT_COLOURS)       # the beak grey doubles as the outline of the black hat
    for y in range(HEIGHT):
        for x in range(width):
            if not m[x, y]:
                continue
            v = values[r[x, y]] if r[x, y] < len(values) else 0
            if v == 0 and i[x, y] == 0:
                v = grey                   # edge of a black part: outline it so it shows on the black card
            o[x, y] = v * 17
    out.save(S / "credit_parrot.png")
    print(f"wrote credit_parrot.png ({width}x{HEIGHT})")

def glyph(ch, size):
    font = ImageFont.truetype(str(EMOJI_FONT), size)
    try:
        font.set_variation_by_axes([700])
    except OSError:
        pass
    box = font.getbbox(ch)
    img = Image.new("L", (box[2] - box[0] + 2, box[3] - box[1] + 2), 0)
    ImageDraw.Draw(img).text((1 - box[0], 1 - box[1]), ch, font=font, fill=255)
    return img.point(lambda v: 255 if v >= 128 else 0)


def emoji():
    bird = glyph("\U0001F99C", 42)          # parrot
    flag = glyph("\U0001F3F4", 42)          # black flag
    skull = glyph("☠", 19)             # skull and crossbones
    height = max(bird.height, flag.height)
    out = Image.new("L", (bird.width + 6 + flag.width, height), 0)
    out.paste(bird.point(lambda v: WHITE * 17 if v else 0), (0, height - bird.height))
    fx, fy = bird.width + 6, height - flag.height
    out.paste(flag.point(lambda v: RED * 17 if v else 0), (fx, fy))
    # the skull sits on the cloth of the flag, in white
    sx, sy = fx + (flag.width - skull.width) // 2 + 4, fy + (flag.height - skull.height) // 2 - 5
    out.paste(Image.new("L", skull.size, WHITE * 17), (sx, sy), skull)
    out.save(S / "credit_emoji.png")
    print(f"wrote credit_emoji.png ({out.width}x{out.height})")


if __name__ == "__main__":
    parrot()
    emoji()
