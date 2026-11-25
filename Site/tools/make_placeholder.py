"""Placeholder pictures for photos that are not final yet (PAHIBALO team's request: the SCO room photo).

    python tools/make_placeholder.py

Writes assets/img/photos/placeholder-<name>.webp. A note uses it like any photo; build.py marks
placeholders so check.py does not count them as informative pictures.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "assets" / "img" / "photos"
FONT = "C:/Windows/Fonts/segoeuib.ttf"
SMALL = "C:/Windows/Fonts/segoeui.ttf"

PLACEHOLDERS = {"sco-room": "Student Conduct Office", "generic": "PSHS-WVC"}


def make(name, label):
    w, h = 1200, 800
    im = Image.new("RGB", (w, h), (247, 240, 225))
    d = ImageDraw.Draw(im)
    for x in range(0, w, 6):   # faint paper lines
        d.line((x, 0, x, h), fill=(244, 236, 219))
    for i in range(0, w + h, 40):   # dashed frame
        pass
    d.rounded_rectangle((40, 40, w - 40, h - 40), radius=28, outline=(160, 140, 110), width=6)
    cx, cy = w // 2, h // 2 - 80   # a simple camera
    d.rounded_rectangle((cx - 130, cy - 80, cx + 130, cy + 90), radius=24, outline=(120, 100, 75), width=10)
    d.rectangle((cx - 50, cy - 110, cx + 50, cy - 80), fill=(120, 100, 75))
    d.ellipse((cx - 55, cy - 50, cx + 55, cy + 60), outline=(120, 100, 75), width=10)
    f1, f2 = ImageFont.truetype(FONT, 64), ImageFont.truetype(SMALL, 40)
    for text, font, y in (("Photo coming soon", f1, cy + 140), (label, f2, cy + 230)):
        tw = d.textlength(text, font=font)
        d.text(((w - tw) / 2, y), text, font=font, fill=(70, 60, 45))
    OUT.mkdir(parents=True, exist_ok=True)
    im.save(OUT / f"placeholder-{name}.webp", "WEBP", quality=80)
    im.resize((600, 400)).save(OUT / f"placeholder-{name}-600.webp", "WEBP", quality=74)
    print("placeholder", name)


if __name__ == "__main__":
    for k, v in PLACEHOLDERS.items():
        make(k, v)
