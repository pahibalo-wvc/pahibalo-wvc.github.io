"""python tools/fb_sheet.py <list> <folder under _downloads> [thumb px]: download a received list (see fb_receiver.py) and make a numbered contact sheet in _downloads/fb-lists/sheets/ to view and pick from."""
import json, sys, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SITE = Path(__file__).resolve().parent.parent
SHEETS = SITE / "_downloads" / "fb-lists" / "sheets"
name, folder = sys.argv[1], sys.argv[2]
tw = int(sys.argv[3]) if len(sys.argv) > 3 else 300
out = SITE / "_downloads" / folder
out.mkdir(parents=True, exist_ok=True)
SHEETS.mkdir(parents=True, exist_ok=True)
items = json.loads((SITE / "_downloads" / "fb-lists" / f"{name}.json").read_text(encoding="utf-8"))
paths = []
for k, url in items.items():
    if not url:
        continue
    p = out / f"{k}.jpg"
    if not p.exists():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                p.write_bytes(r.read())
        except Exception as e:
            print("fail", k, e); continue
    paths.append(p)
cols = 5
th = int(tw * 0.75)
rows = (len(paths) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * (th + 14)), "white")
d = ImageDraw.Draw(sheet)
for i, p in enumerate(paths):
    im = Image.open(p).convert("RGB"); w, h = im.size
    im.thumbnail((tw - 4, th))
    x, y = (i % cols) * tw, (i // cols) * (th + 14)
    sheet.paste(im, (x + (tw - im.width) // 2, y))
    d.text((x + 3, y + th + 1), f"{p.stem} {w}x{h}", fill="black", font=ImageFont.load_default())
sp = SHEETS / f"{name}.jpg"; sheet.save(sp, quality=78); print(sp, len(paths))
