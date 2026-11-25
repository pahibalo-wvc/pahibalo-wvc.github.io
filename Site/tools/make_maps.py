"""Small static maps for Places nearby, drawn from OpenStreetMap tiles (no map embed on the page).

    python tools/make_maps.py

Each map is saved as _downloads/maps/<name>.png with a pin on the place; edit_photos.py turns it into WebP.
Map data and tiles: (c) OpenStreetMap contributors, ODbL / CC BY-SA. The credit is on the Credits page.
Tiles are fetched once and cached in _downloads/maps/tiles/, so a rebuild does not hit the tile server again.
"""
import math
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "_downloads" / "maps"
CACHE = OUT / "tiles"
UA = {"User-Agent": "PAHIBALO-student-guide-build/1.0 (static site, one-time tile fetch)"}
ZOOM = 17
W, H = 900, 560

PLACES = {  # name: (lat, lon) from the place's Google Maps listing
    "map-vmc-cafe": (10.7636875, 122.5781875),
    "map-wash-and-sip": (10.7552095, 122.5877764),
    "map-crispy-king": (10.7517857, 122.5896259),
    "map-sea-garden": (10.7611631, 122.595054),
}


def to_px(lat, lon, z):
    n = 2 ** z * 256
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def tile(z, x, y):
    path = CACHE / f"{z}-{x}-{y}.png"
    if not path.exists():
        req = urllib.request.Request(f"https://tile.openstreetmap.org/{z}/{x}/{y}.png", headers=UA)
        path.write_bytes(urllib.request.urlopen(req, timeout=30).read())
    return Image.open(path).convert("RGB")


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    for name, (lat, lon) in PLACES.items():
        cx, cy = to_px(lat, lon, ZOOM)
        left, top = cx - W / 2, cy - H / 2
        img = Image.new("RGB", (W, H))
        for tx in range(int(left // 256), int((left + W) // 256) + 1):
            for ty in range(int(top // 256), int((top + H) // 256) + 1):
                img.paste(tile(ZOOM, tx, ty), (int(tx * 256 - left), int(ty * 256 - top)))
        d = ImageDraw.Draw(img)
        px, py = W / 2, H / 2
        d.ellipse((px - 22, py - 60, px + 22, py - 16), fill=(184, 50, 42), outline="white", width=4)   # pin head
        d.polygon([(px - 14, py - 26), (px + 14, py - 26), (px, py)], fill=(184, 50, 42))
        d.ellipse((px - 7, py - 45, px + 7, py - 31), fill="white")
        d.rectangle((W - 232, H - 24, W, H), fill=(255, 255, 255))
        d.text((W - 226, H - 19), "(c) OpenStreetMap contributors", fill=(40, 40, 40))
        img.save(OUT / f"{name}.png")
        print(name, img.size)


if __name__ == "__main__":
    main()
