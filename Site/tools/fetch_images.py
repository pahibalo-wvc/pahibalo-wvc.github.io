"""Download the images listed in a JSON file {name: url} into a folder under _downloads/.

    python tools/fetch_images.py _downloads/fb-orgs.json _downloads/fb-orgs

The links are the largest image on each Facebook photo page (or a place's own page).
Signed Facebook links expire after a few weeks, so download soon after collecting them.
Existing files are kept, never overwritten. Each file's source goes in the vault's Credits note.
"""
import json
import sys
import urllib.request
from pathlib import Path

from PIL import Image


def main(listing: str, folder: str):
    out = Path(folder)
    out.mkdir(parents=True, exist_ok=True)
    for name, url in json.loads(Path(listing).read_text(encoding="utf-8")).items():
        ext = ".png" if ".png" in url.split("?")[0] else ".jpg"
        path = out / f"{name}{ext}"
        if path.exists():
            print("kept", path.name)
            continue
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            path.write_bytes(r.read())
        with Image.open(path) as im:   # also proves the file is a real image
            print(f"{path.name:28} {im.size[0]}x{im.size[1]}  {path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main(*sys.argv[1:3])
