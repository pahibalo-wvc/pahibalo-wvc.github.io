"""Edit the site's photos from the originals in _downloads/ into assets/img/photos/.

    python tools/edit_photos.py            # all photos
    python tools/edit_photos.py sco-room   # only the ones named

Each photo gets two WebP copies: <name>.webp (about 1200 px on the long side) and <name>-600.webp.
Originals in _downloads/ are never changed.

Order of edits for each photo (so face boxes stay in original pixels):
  1. faces   hide faces: a list of (x, y, w, h, mode) boxes in ORIGINAL pixels.
             mode: "blur" (default, heavy blur in a soft oval), "pixel" (big squares),
                   "cover" (soft paper-coloured oval patch) or "sticker" (the PAHIBALO logo sticker).
             Each box is padded about 20% so hair and chin are covered.
  2. rotate  quarter turns counterclockwise (90, 180, 270), for phone photos taken sideways.
  3. tilt    small straightening in degrees (+ = counterclockwise); the edges are cropped clean.
  4. crop    (left, top, right, bottom) after rotate and tilt.
  5. tune    optional brightness / contrast / colour factors (1.0 = no change).
Faces that are too small to recognise can stay. If a face cannot be hidden without ruining the
photo, crop it out or leave the photo out (vault rule). Check every output by eye.

To add a photo: put the original in _downloads/, add a line to PHOTOS, run this script, then use
the name in a note's `photos` list ("name|alt text|caption") or as `header_photo`.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

HERE = Path(__file__).resolve().parent.parent
RAW = HERE / "_downloads"
OUT = HERE / "assets" / "img" / "photos"
STICKER = HERE / "assets" / "img" / "pahibalo-logo.webp"
SIZES = (1200, 600)

# name: dict(src, rotate, tilt, crop, faces, tune, sizes)
PHOTOS: dict[str, dict] = {
    # --- the PAHIBALO team's own photos (2026-11-23)
    "quad-love-pisay":   dict(src="own/quad-love-pisay.jpg"),
    "quad-wide":         dict(src="own/quad-wide.jpg"),
    "quad-tower":        dict(src="own/quad-tower.jpg", crop=(0, 120, 677, 1500)),
    "grounds":           dict(src="own/grounds.jpg"),
    "sco-room":          dict(src="own/sco-room.jpg"),
    "sco-posters":       dict(src="own/sco-posters.jpg"),
    "sco-poster-close":  dict(src="own/sco-poster-close.jpg"),
    "library-tall":      dict(src="own/library-tall.jpg"),
    "library-wide":      dict(src="own/library-wide.jpg"),
    "library-card":      dict(src="own/library-card.jpg", rotate=90, crop=(520, 40, 982, 645), tune=(1.04, 1.12, 1.0)),
    "registrar-counter": dict(src="own/registrar-counter.jpg"),
    "mis-office":        dict(src="own/mis-office.jpg"),
    # --- the team's second batch (2026-11-24). Only rooms and buildings become pictures; photos of signs,
    #     forms, flowcharts and QR codes are used for facts only (PAHIBALO team's rule). Not final: may be replaced.
    "registrar-entrance": dict(src="own/batch-2/01-imJ8u4NB.jpg"),
    "cid-office":        dict(src="own/batch-2/03-ood8NeAc.jpg"),
    "cid-door":          dict(src="own/batch-2/04-0sNgMWWW.jpg"),
    "clinic-door":       dict(src="own/batch-2/05-V8WaoKws.jpg"),
    "sau-door":          dict(src="own/batch-2/07-pCBwpZhw.jpg"),
    "ssd-door":          dict(src="own/batch-2/08-1F82Qqsy.jpg"),   # people behind the window are dark shapes, no faces
    "map-vmc-cafe":      dict(src="maps/map-vmc-cafe.png"),
    "map-wash-and-sip":  dict(src="maps/map-wash-and-sip.png"),
    "map-crispy-king":   dict(src="maps/map-crispy-king.png"),
    "map-sea-garden":    dict(src="maps/map-sea-garden.png"),
    "vmc-cafe-1":        dict(src="places/vmc-1.jpg"),
    "vmc-cafe-2":        dict(src="places/vmc-2.jpg"),
    "sea-garden-1":      dict(src="places/seagarden-1.jpg"),
    # --- event photos from Facebook posts (Banaag, Student Alliance, SDC, Sci-Link), 2026-11-24, see Credits.
    #     Faces are found automatically and blurred; band boxes cover rows of faces the detector misses.
    **{n: dict(src=f"fb-events/{n}.jpg", auto_faces=True) for n in (
        "ev-mahuesci-stage", "ev-mahuesci-backdrop", "ev-press-conference",
        "ev-research-2", "ev-research-3", "ev-wika-stage", "ev-wika-show", "ev-afterburn-gym")},
    # the student with the microphone was missed by the detector; the name on the left ID is hidden too
    "ev-research-1":     dict(src="fb-events/ev-research-1.jpg", auto_faces=True,
                              faces=[(330, 135, 105, 105, "blur"), (108, 318, 52, 30, "pixel")]),
    # ev-mahuesci-cheer is not used: too many painted faces to hide without ruining it
    "ev-toast-1":        dict(src="fb-events/ev-toast-1.jpg", auto_faces=True),
    "ev-toast-2":        dict(src="fb-events/ev-toast-2.jpg", auto_faces=True),
    # not used: ev-sa-staffday (collage, patchy after blurring) and ev-sa-what (mostly text, info only)
    **{n: dict(src=f"fb-events/{n}.jpg") for n in (
        "ev-wika-title", "ev-xmas-poster", "ev-xmas-night", "ev-xmas-day", "ev-sdc-intramurals", "ev-sdc-afterburn",
        "ev-dspc-winners", "ev-dspc-first")},
    # --- org logos and covers from each org's own Facebook page (2026-11-24, see Credits)
    **{f"logo-{o}": dict(src=f"fb-orgs/{o}-logo.{e}", sizes=(600, 300)) for o, e in
       [("banaag", "jpg"), ("siklab", "jpg"), ("sa", "png"), ("sidlak", "jpg"), ("cyborg", "jpg"),
        ("sdc", "jpg"), ("scilink", "jpg"), ("mun", "jpg")]},
    # COMELEC, from its own Facebook page (2026-11-25)
    "logo-comelec":      dict(src="fb-orgs3/comelec/profile.jpg", sizes=(600, 300)),
    "cover-comelec":     dict(src="fb-orgs3/comelec/cover.jpg"),
    # Cinematograpisay (SineSci), from its own Facebook page (2026-11-25)
    "logo-sinesci":      dict(src="fb-orgs3/sinesci/profile.jpg", sizes=(600, 300)),
    "cover-sinesci":     dict(src="fb-orgs3/sinesci/cover.jpg"),
    "org-sinesci-stage": dict(src="fb-orgs3/sinesci/p08.jpg", auto_faces=True, faces=[(717, 140, 190, 200)]),
    "org-sinesci-crowd": dict(src="fb-orgs3/sinesci/p21.jpg", auto_faces=True),
    "cover-banaag":      dict(src="fb-orgs/banaag-cover.png"),
    "cover-siklab":      dict(src="fb-orgs/siklab-cover.png"),
    "cover-sa":          dict(src="fb-orgs/sa-cover.png"),
    "cover-sidlak":      dict(src="fb-orgs/sidlak-cover.png"),
    "cover-cyborg":      dict(src="fb-orgs/cyborg-cover.jpg"),
    "cover-sdc":         dict(src="fb-orgs/sdc-cover.png"),   # runners on the oval, faces too small to recognise
    "cover-scilink":     dict(src="fb-orgs/scilink-cover.png"),
    "cover-mun":         dict(src="fb-orgs/mun-cover.png"),
    "logo-pahibalo":     dict(src="fb/avatar.jpg", sizes=(600, 300)),
    # --- frames from the PSHS-WVC "Virtual Campus Tour" video (PISAY-WVC TV on YouTube, December 2021), 2026-11-24.
    #     Rooms named from the video's own narration. Only frames without the hosts' faces, or with faces blurred.
    "tour-clinic-beds":  dict(src="tour/frames/s0536.jpg"),
    "tour-clinic-dental": dict(src="tour/frames/s0540.jpg"),
    "tour-guidance":     dict(src="tour/frames/s0542.jpg"),
    "tour-dorm-building": dict(src="tour/frames/s0556.jpg"),
    "tour-dorm-room":    dict(src="tour/frames/s0560.jpg"),
    "tour-dorm-kitchen": dict(src="tour/frames/s0568.jpg"),
    "tour-dorm-rec":     dict(src="tour/frames/s0570.jpg"),
    "tour-dorm-study":   dict(src="tour/frames/s0576.jpg"),
    "tour-dorm-swings":  dict(src="tour/frames/s0578.jpg"),
    "tour-admin-building": dict(src="tour/frames/s0101.jpg", auto_faces=True,
                                faces=[(582, 356, 38, 48, "blur"), (672, 356, 38, 48, "blur")]),
    "tour-research-lab": dict(src="tour/frames/t0038.jpg"),
    "tour-molecular-lab": dict(src="tour/frames/t0042.jpg"),
    "tour-chem-stockroom": dict(src="tour/frames/t0048.jpg"),
    "tour-gym":          dict(src="tour/frames/t0079.jpg"),
    "tour-gym-game":     dict(src="tour/frames/t0076.jpg", auto_faces=True),
    "tour-planetarium":  dict(src="tour/frames/t0063.jpg"),
    "tour-auditorium":   dict(src="tour/frames/t0121.jpg"),
    "tour-oval":         dict(src="tour/frames/t0131.jpg"),
    "tour-covered-walk": dict(src="tour/frames/t0107.jpg"),
    "tour-entrance":     dict(src="tour/frames/t0142.jpg"),
    "tour-slrc":         dict(src="tour/frames/t0054.jpg"),
    "tour-old-auditorium": dict(src="tour/frames/t0026.jpg"),
    "tour-computer-lab": dict(src="tour/frames/t0025.jpg"),
    "tour-classroom":    dict(src="tour/frames/t0024.jpg"),
    # --- org and event photos from each org's own Facebook page and Facebook post search (2026-11-24, see Credits).
    #     Every one has faces found automatically and blurred; checked by eye.
    **{n: dict(src=s, auto_faces=True) for n, s in {
        "org-siklab-huSciYa-hall": "fb-orgs2/siklab/siklab-02.jpg",
        "org-siklab-huSciYa-all":  "fb-orgs2/siklab/siklab-03.jpg",
        "org-banaag-festival":     "fb-orgs2/banaag/banaag-11_1720179626785591.jpg",
        "ev-mahuesci-costume":     "fb-orgs2/banaag/banaag-08_1720179766785577.jpg",
        "ev-mahuesci-cheer2":      "fb-orgs2/banaag/banaag-12_1720179613452259.jpg",
        "ev-mahuesci-opening":     "fb-orgs2/banaag/banaag-20_1719285600208327.jpg",
        "ev-research-exhibit":     "fb-orgs2/banaag/banaag-21_1718271966976357.jpg",
        "ev-research-talk":        "fb-orgs2/banaag/banaag-24_1718271876976366.jpg",
        "org-cyborg-robot-demo":   "fb-orgs2/cyborg/cyborg-12_122229764516100203.jpg",
        "org-cyborg-robot":        "fb-orgs2/cyborg/cyborg-13_122229764426100203.jpg",
        "org-cyborg-booth":        "fb-orgs2/cyborg/cyborg-16_122229764270100203.jpg",
        "org-mun-committee":       "fb-orgs2/mun/mun-19_1104833009034336.jpg",
        "org-mun-unesco":          "fb-orgs2/mun/mun-20_1104832972367673.jpg",
        "org-mun-best":            "fb-orgs2/mun/mun-24_1104832429034394.jpg",
        "org-sa-staffday-band":    "fb-orgs2/sa/sa-22_1570157708490133.jpg",
        "org-sa-staffday-crowd":   "fb-orgs2/sa/sa-28_1570157688490135.jpg",
        "ev-dspc-delegation":      "fb-orgs2/scilink/scilink-19_1185335084154038.jpg",
        "org-scilink-football":    "fb-orgs2/scilink/scilink-22_1185091824178364.jpg",
        "org-scilink-football2":   "fb-orgs2/scilink/scilink-26_1185091377511742.jpg",
        "org-sidlak-mpl":          "fb-orgs2/sidlak/sidlak-21_122126326677032141.jpg",
        "org-sdc-football":        "fb-search/s-welcoming/s-welcoming-04_1668860935250794.jpg",
        "org-sdc-afterburn2":      "fb-search/s-welcoming/s-welcoming-08_1653550670115154.jpg",
    }.items()},
    # manual boxes for faces the detector missed (checked by eye)
    "ev-research-talk":      dict(src="fb-orgs2/banaag/banaag-24_1718271876976366.jpg", auto_faces=True,
                                  faces=[(790, 290, 220, 250, "blur"), (250, 770, 160, 90, "pixel")]),
    "org-sa-staffday-band":  dict(src="fb-orgs2/sa/sa-22_1570157708490133.jpg", auto_faces=True,
                                  faces=[(305, 345, 52, 60), (412, 390, 52, 60), (546, 372, 52, 60), (609, 372, 52, 60), (796, 390, 52, 60)]),
    # --- 2026-11-25: Sinadya 2025 (SA page) and the Christmas tree lighting (Astra WVC page)
    "ev-sinadya-p01":        dict(src="fb-events3/sinadya/p01.jpg"),   # stage only, no people
    **{f"ev-sinadya-{k}": dict(src=f"fb-events3/sinadya/{k}.jpg", auto_faces=True) for k in ("p06", "p09")},
    "ev-sinadya-p17":        dict(src="fb-events3/sinadya/p17.jpg", auto_faces=True,
                                  faces=[(1190, 307, 90, 102), (1357, 256, 102, 102), (1664, 205, 179, 205)]),
    "ev-xmas-tree":          dict(src="fb-events3/xmas-astra/p01.jpg", faces=[(1137, 744, 56, 56)]),   # audience seen from behind
    "ev-xmas-parade":        dict(src="fb-events3/xmas-astra/p21.jpg", auto_faces=True),
    # Akwe 2024 (Sci-Link), Paskwa sa Pisay and Dorm Christmas Party (Sci-Link), Ugnayan 2025 bands (Sci-Link)
    **{f"ev-akwe-{k}": dict(src=f"fb-events3/akwe-sl2/{k}.jpg", auto_faces=True) for k in ("p46", "p47")},
    "ev-akwe-p38":           dict(src="fb-events3/akwe-sl2/p38.jpg", auto_faces=True, faces=[(914, 1000, 121, 138)]),
    "ev-akwe-p39":           dict(src="fb-events3/akwe-sl2/p39.jpg", auto_faces=True, faces=[(1618, 431, 173, 207)]),
    "ev-paskwa-p01":         dict(src="fb-events3/paskwa/p01.jpg"),   # sign only
    "ev-paskwa-p02":         dict(src="fb-events3/paskwa/p02.jpg", auto_faces=True),
    "ev-dormxmas-p03":       dict(src="fb-events3/dormxmas/p03.jpg", auto_faces=True),
    "ev-dormxmas-p08":       dict(src="fb-events3/dormxmas/p08.jpg", auto_faces=True, faces=[(331, 252, 262, 286)]),
    **{f"ev-bands-{k}": dict(src=f"fb-events3/bands2/{k}.jpg", auto_faces=True) for k in ("p03", "p08")},
    # Dormers' Day 2025 (Cinematograpisay)
    "ev-dormersday-p03":     dict(src="fb-events3/dormersday/p03.jpg", auto_faces=True, faces=[(850, 260, 160, 160)]),
    "ev-dormersday-p08":     dict(src="fb-events3/dormersday/p08.jpg", auto_faces=True, faces=[(890, 110, 200, 220)]),
    "ev-dormersday-p11":     dict(src="fb-events3/dormersday/p11.jpg", auto_faces=True, faces=[(985, 330, 180, 200)]),
    "ev-toast-pinning":      dict(src="fb-events3/toast26/p15.jpg", auto_faces=True,
                                  faces=[(1870, 150, 175, 240), (1190, 330, 210, 210)]),   # Toast to Excellence 2026 (Cinematograpisay)
    # Batch 2027 Recollection, May 2024 (Astra WVC)
    "ev-recol-p09":          dict(src="fb-events3/recol/p09.jpg", auto_faces=True),
    "ev-recol-p08":          dict(src="fb-events3/recol/p08.jpg", auto_faces=True, faces=[(989, 890, 169, 169)]),
    "ev-recol-p10":          dict(src="fb-events3/recol/p10.jpg", auto_faces=True, faces=[(378, 746, 154, 184)]),
    "ev-recol-p14":          dict(src="fb-events3/recol/p14.jpg", auto_faces=True, faces=[(850, 610, 125, 160)]),
    # El Filibusterismo Play Fest (Astra WVC)
    **{f"ev-elfili-{k}": dict(src=f"fb-events3/elfili/{k}.jpg", auto_faces=True) for k in ("p08", "p09")},
    "ev-elfili-p04":         dict(src="fb-events3/elfili/p04.jpg", auto_faces=True, faces=[(705, 555, 70, 75), (675, 580, 63, 84)]),
    "ev-elfili-p07":         dict(src="fb-events3/elfili/p07.jpg", auto_faces=True, faces=[(635, 595, 90, 105)]),
    "ev-bands-p14":          dict(src="fb-events3/bands2/p14.jpg", auto_faces=True, faces=[(962, 600, 121, 138)]),
    "ev-bands-p17":          dict(src="fb-events3/bands2/p17.jpg", auto_faces=True,
                                  faces=[(490, 445, 121, 138), (1370, 514, 138, 138), (1145, 480, 104, 121), (852, 514, 104, 138),
                                         (1101, 605, 113, 129), (1407, 621, 97, 129)]),
    # the PSHS-WVC seal from the video's last frame, for the header (Pisay branding)
    "pisay-seal":        dict(src="tour/frames/t0143.jpg", crop=(345, 60, 945, 660), sizes=(600, 300), circle=True),
    # --- earlier site photos
    "building":          dict(src="do/do7.img"),
    "cover-art":         dict(src="fb/cover.png"),
}


def oval_mask(size, box):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).ellipse(box, fill=255)
    return m.filter(ImageFilter.GaussianBlur(max(4, (box[2] - box[0]) // 10)))


def hide_faces(im: Image.Image, faces) -> Image.Image:
    for f in faces or []:
        x, y, w, h = f[:4]
        mode = f[4] if len(f) > 4 else "blur"
        px, py = int(w * .2), int(h * .2)
        box = (max(0, x - px), max(0, y - py), min(im.width, x + w + px), min(im.height, y + h + py))
        mask = oval_mask(im.size, box)
        if mode == "pixel":
            part = im.crop(box)
            n = max(6, (box[2] - box[0]) // 7)
            part = part.resize((max(1, part.width // n), max(1, part.height // n)), Image.BILINEAR).resize(part.size, Image.NEAREST)
            layer = im.copy(); layer.paste(part, box[:2])
        elif mode == "cover":
            layer = Image.new("RGB", im.size, (246, 238, 222))
        elif mode == "sticker":
            layer = im.copy()
            s = Image.open(STICKER).convert("RGBA")
            side = max(box[2] - box[0], box[3] - box[1])
            s = s.resize((side, side), Image.LANCZOS)
            layer.paste(s, (box[0] - (side - (box[2] - box[0])) // 2, box[1] - (side - (box[3] - box[1])) // 2), s)
            mask = Image.new("L", im.size, 0); mask.paste(255, box)
        else:  # blur
            radius = max(12, (box[2] - box[0]) // 4)
            layer = im.filter(ImageFilter.GaussianBlur(radius))
        im = Image.composite(layer, im, mask)
    return im


def detect_faces(im: Image.Image) -> list[tuple]:
    """Suggest face boxes with OpenCV's built-in face detectors (front and side). Always check the output by eye;
    add missed faces by hand in 'faces' and they are blurred too. Needs: pip install opencv-python-headless."""
    import cv2
    import numpy as np
    g = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2GRAY)
    g = cv2.equalizeHist(g)
    small = max(10, im.width // 60)
    boxes = []
    for name in ("haarcascade_frontalface_default.xml", "haarcascade_profileface.xml"):
        c = cv2.CascadeClassifier(cv2.data.haarcascades + name)
        for flip in (False, True) if "profile" in name else (False,):
            img = cv2.flip(g, 1) if flip else g
            for (x, y, w, h) in c.detectMultiScale(img, scaleFactor=1.06, minNeighbors=4, minSize=(small, small)):
                boxes.append((int(im.width - x - w) if flip else int(x), int(y), int(w), int(h), "blur"))
    return boxes


def straighten(im: Image.Image, deg: float) -> Image.Image:
    if not deg:
        return im
    w, h = im.size
    r = im.rotate(deg, resample=Image.BICUBIC, expand=False)
    a = math.radians(abs(deg))  # largest upright rectangle inside the turned photo
    cw = (w * math.cos(a) - h * math.sin(a)) / math.cos(2 * a) if w >= h else w
    ch = (h * math.cos(a) - w * math.sin(a)) / math.cos(2 * a) if w >= h else h
    cw, ch = int(min(w, abs(cw))), int(min(h, abs(ch)))
    return r.crop(((w - cw) // 2, (h - ch) // 2, (w + cw) // 2, (h + ch) // 2))


def edit(name: str, spec: dict):
    im = ImageOps.exif_transpose(Image.open(RAW / spec["src"])).convert("RGB")
    faces = list(spec.get("faces") or [])
    if spec.get("auto_faces"):
        found = detect_faces(im)
        faces += found
        print(f"  {name}: {len(found)} faces found automatically")
    im = hide_faces(im, faces)
    if spec.get("rotate"):
        im = im.rotate(spec["rotate"], expand=True)
    im = straighten(im, spec.get("tilt", 0))
    if spec.get("crop"):
        im = im.crop(spec["crop"])
    if spec.get("tune"):
        b, c, s = spec["tune"]
        im = ImageEnhance.Color(ImageEnhance.Contrast(ImageEnhance.Brightness(im).enhance(b)).enhance(c)).enhance(s)
    if spec.get("circle"):  # round badge with a see-through corner (logos and seals)
        mask = Image.new("L", (im.width * 4, im.height * 4), 0)
        ImageDraw.Draw(mask).ellipse((6, 6, im.width * 4 - 6, im.height * 4 - 6), fill=255)
        im = im.convert("RGBA"); im.putalpha(mask.resize(im.size, Image.LANCZOS))
    OUT.mkdir(parents=True, exist_ok=True)
    for i, size in enumerate(spec.get("sizes", SIZES)):
        out = im.copy()
        out.thumbnail((size, size), Image.LANCZOS)
        path = OUT / (f"{name}.webp" if i == 0 else f"{name}-{size}.webp")
        out.save(path, "WEBP", quality=80 if i == 0 else 74, method=6)
        print(f"{path.name:34} {out.size[0]}x{out.size[1]:<5} {path.stat().st_size // 1024} KB")


def main(only: list[str]):
    for name, spec in PHOTOS.items():
        if not only or name in only:
            edit(name, spec)


if __name__ == "__main__":
    main(sys.argv[1:])
