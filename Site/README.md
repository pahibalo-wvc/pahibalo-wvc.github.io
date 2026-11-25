# PAHIBALO site

The website is built from the Obsidian vault in `../PAHIBALO Vault`. The vault holds every word and fact, the list of site areas and the grade groups. This folder only turns it into web pages.

## Build and check
```
pip install markdown pyyaml jinja2 playwright pillow "opencv-python-headless<5"
python tools/edit_photos.py     # photos from _downloads/ into assets/img/photos/ (faces blurred, sizes made)
python tools/prep_photos.py     # small blurred copies for page header backgrounds
python tools/make_brand.py      # the home logo sticker with its small Pisay pin
python tools/fb_receiver.py     # receives Facebook photo links from the browser (see the pahibalo-photos skill)
python tools/fb_sheet.py <list> <folder>   # downloads a received list and makes a contact sheet
python build.py                 # writes the site into dist/
python check.py                 # links, writing, old names, new-tab links, photos per page, contrast, taps, headings, JS
```
Preview with `python -m http.server 8765 --directory dist` (opening the files directly also works). To host, upload the whole `dist/` folder to a static host (Cloudflare Pages or GitHub Pages). Not hosted yet.

## Adding things
| To add | Do this |
|---|---|
| A page in an existing area | Make a note with that area's `type` (copy a template from `Templates/`). Give it an `icon` (forms and offices each have their own) and a `grade` if it is for certain years. |
| A whole new area | Add a row to the `Site Areas` note: type, name, folder, hub, tag, icon, fill colour, border colour, header photo, menu number, count word, card facts. |
| A single page | Make a note with `publish: "name.html"`. Optional: `layout` (page, tasks, about, gwa, journey), `footer: yes`, `menu_order`, `menu_label`, `photo`, `icon`. |
| A photo | Put the original in `_downloads/`, add a line to `tools/edit_photos.py` (crop, rotate, faces), run it, then add `"name|alt text|caption"` to the note's `photos` list. Add `|office` (or another area) at the end to change the border colour. Use `header_photo: "name"` for the header. |
| A photo that is not final | `python tools/make_placeholder.py` makes a "Photo coming soon" picture; use `placeholder-<name>` like any photo. Placeholders do not count as photos. |
| An org logo | Add it to `edit_photos.py` as `logo-<org>` and set `logo: "logo-<org>"` on the note. |
| A place nearby | A `Place - ` note with `kind`, `address`, `hours`, `bestsellers`, `maps_link`. Add its coordinates to `tools/make_maps.py` for the small map. |
| A form template | Upload it to the team Google Drive, share it "anyone with the link can view", put the link in `template_link` and set `template_status: "have"`. Never put template files in this folder (D58). |
| A new icon | Add a `<symbol id="i-name">` to `templates/_icons.svg`. |

## Where to edit what
| To change | Edit |
|---|---|
| Home page words, quick links, tiles, footer line | `Site Settings` note |
| Areas, menu order, colours, picture borders, grade groups | `Site Areas` note |
| Tasks on "I need to…" | `I Need To` note |
| GWA units | `Guide - Curriculum and Units` (the calculator reads them and checks each total) |
| Notes only editors should see | wrap them in `%% … %%`; the site hides them |
| Look and feel | `assets/css/site.css` |
| Search, hub filters, calculator | `assets/js/site.js` |

## The look (v4.1, "bulletin board", friendly edition)
- Things students handle at Pisay: form sheets with codes, door plaques, ID cards, tickets, index cards, cork boards, tape and pins. Each area has its own header shape.
- Friendly: soft edges, soft shadows, rounded everyday pieces. No typewriter font.
- Fonts (self-hosted, SIL Open Font License): Bricolage Grotesque for headings, Atkinson Hyperlegible for text and labels, Caveat for handwritten notes like "to inform.".
- Every picture has a border colour that says what it shows (legend in `Site Areas`).
- Motion is short, plays once and is off for "reduce motion".

## Photo rules (D60)
Photos with a lot of text or a QR code are for facts only, never shown. Room and building photos are website pictures. Faces are blurred or cropped (`auto_faces=True` plus manual boxes; check every output). Office cards have no thumbnails; org cards show logos.

## Folders
- `templates/`: page layouts. `base.html` is the frame; `_macros.html` has shared pieces (rows, page headers, galleries).
- `assets/`: copied into `dist/` as they are.
- `tools/`: photo, map, placeholder, logo and Facebook download scripts.
- Photo rules in `check.py`: orgs 2, events and competitions 3, offices 1, forms 0; other pages show in a "photo guide" line that is not counted. Pages logged under "Pages with one photo" in the vault's Handoff are allowed fewer.
- `_downloads/`: original photos and images. Sources are on the Credits page.
- `_for Drive/`: retyped blank forms waiting to be uploaded to the team Drive. Not published.
- `_safe to delete/`: old files from earlier builds.
- `dist/`: the built site. Never edit it by hand; it is rebuilt each time.

## Writing rules for site text
PAHIBALO team's writing style: plain student voice, no contractions, exclamation marks or rhetorical questions, concrete facts, nothing invented. `check.py` flags AI-sign words, old names and internal notes.
