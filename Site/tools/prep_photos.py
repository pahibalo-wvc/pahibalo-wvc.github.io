"""Make the web photos from the originals in _downloads/.

    python tools/prep_photos.py

Each photo gets a sharp copy (for frames) and a small pre-blurred copy "<name>-blur.webp"
(for frosted-glass backgrounds; blurring ahead of time keeps phones fast).
To add a photo: put the original in _downloads/, add a line to PHOTOS, run this, then use
the name in the "Photo" column of the Site Areas note.
"""
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter

HERE = Path(__file__).resolve().parent.parent
RAW = HERE / "_downloads"
OUT = HERE / "assets" / "img"

# name: (original file, crop box or None, sharp widths)
PHOTOS = {
    "building":  ("do/do7.img",            None,                [800, 1600]),
    "walkway":   ("fbschool/cover.jpg",    (0, 172, 960, 318),  [960]),   # cropped below the banner text
    "garden":    ("fbschool/cover.jpg",    (0, 0, 300, 318),    [300]),
    "campus":    ("fbschool/cover.jpg",    (0, 0, 960, 318),    []),      # blur only: its banner text is unreadable once blurred
    "cover-art": ("fb/cover.png",          None,                [960]),
    "grounds":   ("own/grounds.jpg",       None,                [960]),   # PAHIBALO team photo: tables by the court
    "quad-wide": ("own/quad-wide.jpg",     None,                []),      # PAHIBALO team photos: blurred header backgrounds
    "quad-tower": ("own/quad-tower.jpg",   (0, 300, 677, 1200), []),
    "library":   ("own/library-wide.jpg",  None,                []),
}


def save(im: Image.Image, name: str, quality: int):
    path = OUT / f"{name}.webp"
    im.save(path, "WEBP", quality=quality, method=6)
    print(f"{path.name:28} {im.size[0]}x{im.size[1]:<5} {path.stat().st_size // 1024} KB")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (src, crop, widths) in PHOTOS.items():
        im = Image.open(RAW / src).convert("RGB")
        if crop:
            im = im.crop(crop)
        for w in widths:
            s = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS) if im.width > w else im
            save(s, name if w == max(widths) else f"{name}-{w}", 74)
        # soft background: small, blurred, a little brighter and more saturated so glass on top glows
        small = im.resize((320, round(im.height * 320 / im.width)), Image.LANCZOS)
        small = small.filter(ImageFilter.GaussianBlur(7))
        small = ImageEnhance.Color(small).enhance(1.25)
        save(ImageEnhance.Brightness(small).enhance(1.05), f"{name}-blur", 62)


if __name__ == "__main__":
    main()
