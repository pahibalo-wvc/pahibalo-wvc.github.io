"""Make the PAHIBALO WVC logo: Laniog D.'s logo art, unchanged, with a small round Pisay pin (the PSHS
flame mark) on the empty right edge. The "WVC" part is a sticker on the wordmark next to the logo (site.css, .wvc).

    python tools/make_brand.py

Input:  assets/img/pahibalo-logo.webp (the original art, kept as it is) and assets/img/pshs-logo.webp
Output: assets/img/pahibalo-logo-wvc.webp (400 px) and pahibalo-logo-wvc-96.webp (for the header and footer)
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = Path(__file__).resolve().parent.parent
IMG = HERE / "assets" / "img"
S = 400

logo = Image.open(IMG / "pahibalo-logo.webp").convert("RGBA").resize((S, S), Image.LANCZOS)
mark = Image.open(IMG / "pshs-logo.webp").convert("RGBA")

# a small round Pisay pin on the empty right edge of the art, clear of the mascots and the lettering
R, cx, cy = 30, 357, 196
pin = Image.new("RGBA", (S, S), (0, 0, 0, 0))
sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ImageDraw.Draw(sh).ellipse((cx - R + 3, cy - R + 6, cx + R + 3, cy + R + 6), fill=(20, 20, 40, 120))
pin.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4)))
ImageDraw.Draw(pin).ellipse((cx - R, cy - R, cx + R, cy + R), fill=(255, 252, 244, 255), outline=(29, 78, 158, 255), width=4)
m = mark.resize((2 * R - 14, 2 * R - 15), Image.LANCZOS)
pin.alpha_composite(m, (cx - m.width // 2, cy - m.height // 2))
out = logo.copy()
out.alpha_composite(pin)
out.convert("RGB").save(IMG / "pahibalo-logo-wvc.webp", "WEBP", quality=88, method=6)
out.resize((96, 96), Image.LANCZOS).convert("RGB").save(IMG / "pahibalo-logo-wvc-96.webp", "WEBP", quality=88, method=6)
print("made pahibalo-logo-wvc.webp and pahibalo-logo-wvc-96.webp")
