"""PAHIBALO site builder.

Turns the Obsidian vault (the source of truth) into a static site in dist/.

    python build.py

Needs Python 3.10+ and:  pip install markdown pyyaml jinja2
Photos: run tools/edit_photos.py first (it makes assets/img/photos/*.webp).

Where things live:
  ../PAHIBALO Vault/          every word and fact
      Site Areas.md           areas (forms, orgs, ...): folder, icon, colours, photo, menu order; grade groups
      Site Settings.md        home page words, quick links, tiles, footer line
      any note + "publish:"   a standalone page at that address (layout: page, tasks, about, gwa or journey)
  templates/                  page layouts (Jinja2 HTML)
  assets/                     css, js, fonts, images (copied as they are)
  tools/edit_photos.py        edits the team's photos (faces, crop, rotate, sizes)
  tools/prep_photos.py        makes the blurred header backgrounds
No area, menu item or colour is written in this file: add a row to Site Areas instead.
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import date
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

HERE = Path(__file__).resolve().parent
VAULT = HERE.parent / "PAHIBALO Vault"
DIST = HERE / "dist"
# Personal names that must never show on a page. Kept in a local file that is not uploaded (D71);
# the public vault no longer contains them, so the build on GitHub works without the file.
_PN = HERE / "private_names.txt"
PRIVATE_NAMES = [n.strip() for n in _PN.read_text(encoding="utf-8").splitlines() if n.strip()] if _PN.exists() else []
IMG = HERE / "assets" / "img"

PREFIX = re.compile(r"^[A-Z][A-Za-z]* - ")   # vault naming: "Form - Leave Pass", "Event - Prom", ...
WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]")
UNKNOWN = re.compile(r"\((unknown|to collect|to confirm)\)")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+\.)\s")
GAP_WORDS = {"unknown": "not known yet", "to collect": "still collecting", "to confirm": "not confirmed yet"}
ICONS = set(re.findall(r'id="i-([\w-]+)"', (HERE / "templates" / "_icons.svg").read_text(encoding="utf-8")))
TEMPLATE_TEXT = {  # what a form page says when the template cannot be opened yet
    "drive-private": "The template is on the PAHIBALO Drive but not shared yet. Ask the office for a blank copy.",
    "waiting-upload": "Not online yet. Ask the office for a blank copy.",
    "missing": "Not uploaded yet. We are still collecting it.",
}


def gap(m) -> str:
    return f'<span class="unk">{GAP_WORDS[m.group(1)]}</span>'


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def short_name(stem: str) -> str:
    return PREFIX.sub("", stem)


def nice_date(iso: str) -> str:
    try:
        d = date.fromisoformat(iso)
        return f"{d.day} {d:%b %Y}"
    except ValueError:
        return iso


def yes(v) -> bool:
    return str(v).strip().lower() in ("yes", "true", "1")


def table(body: str, after: str = "") -> list[dict]:
    """The first Markdown table after a heading (or the first one in the note) as a list of dicts."""
    if after:
        body = body.split(after, 1)[1] if after in body else ""
    rows = []
    for ln in body.splitlines():
        if ln.startswith("|"):
            rows.append(ln)
        elif rows:
            break
    if len(rows) < 3:
        return []
    head = [c.strip().lower() for c in rows[0].strip().strip("|").split("|")]
    return [dict(zip(head, (c.strip() for c in ln.strip().strip("|").split("|")))) for ln in rows[2:]]


# ------------------------------------------------------------------ vault
class Note:
    def __init__(self, path: Path):
        self.stem = path.stem
        raw = path.read_text(encoding="utf-8")
        m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", raw, re.S)
        self.fm = (yaml.safe_load(m.group(1)) or {}) if m else {}
        self.body = m.group(2) if m else raw
        self.type = str(self.fm.get("type", "")).strip()
        self.title = str(self.fm.get("title") or short_name(self.stem))
        self.summary = str(self.fm.get("summary") or "")
        self.aliases = [str(a) for a in self.fm.get("aliases") or []]
        self.grade = [str(g).lower() for g in self.fm.get("grade") or []]
        self.tags = [str(t) for t in self.fm.get("tags") or []]
        self.updated = str(self.fm.get("last_updated") or self.fm.get("date") or "")
        self.url: str | None = None
        self.tasks: list[str] = []

    def get(self, key, default=""):
        v = self.fm.get(key)
        return default if v is None else v

    @property
    def area(self) -> dict:
        return AREAS.get(self.type, FALLBACK_AREA)

    @property
    def icon(self) -> str:
        i = str(self.fm.get("icon") or "")
        return i if i in ICONS else self.area["icon"]

    @property
    def groups(self) -> list[dict]:
        return [g for g in GROUPS if set(g["grades"]) & set(self.grade)]

    @property
    def photos(self) -> list[dict]:
        out = []
        for line in self.fm.get("photos") or []:
            parts = [p.strip() for p in str(line).split("|")]
            f, alt, cap = (parts + ["", "", ""])[:3]
            kind = parts[3] if len(parts) > 3 and parts[3] else self.area["tag"]
            out.append(dict(file=f, alt=alt, caption=cap, kind=area_by_tag(kind)["tag"], **photo_size(f)))
        return out

    @property
    def thumb(self) -> dict | None:
        """The picture used on this page's card: its logo, header photo or first photo.
        Forms have no card picture (PAHIBALO team, 2026-11-24: no preview pictures on forms)."""
        if self.type == "form":
            return None
        if self.get("logo"):
            return dict(file=str(self.get("logo")), logo=True, kind=self.area["tag"], **photo_size(str(self.get("logo"))))
        if self.get("header_photo"):
            return dict(file=str(self.get("header_photo")), kind=self.area["tag"], **photo_size(str(self.get("header_photo"))))
        return self.photos[0] if self.photos else None


notes = {p.stem: Note(p) for p in sorted(VAULT.glob("*.md"))}
settings = notes["Site Settings"].fm


# ------------------------------------------------------------------ photos (made by tools/edit_photos.py)
def photo_size(name: str) -> dict:
    """Width and height of assets/img/photos/<name>.webp, so every <img> has them (no layout jump)."""
    path = IMG / "photos" / f"{name}.webp"
    if not path.exists():
        raise SystemExit(f"Photo {name!r} is missing: run tools/edit_photos.py (looked for {path.relative_to(HERE)})")
    from PIL import Image
    with Image.open(path) as im:
        w, h = im.size
    small = (IMG / "photos" / f"{name}-600.webp").exists()
    return dict(w=w, h=h, small=small)


# ------------------------------------------------------------------ areas and grade groups (from "Site Areas")
def read_areas() -> dict[str, dict]:
    areas = {}
    for cells in table(notes["Site Areas"].body):
        hub = WIKILINK.search(cells["hub note"])
        icon = cells["icon"] if cells["icon"] in ICONS else "guide"
        if cells["icon"] not in ICONS:
            print(f"Site Areas: no icon called {cells['icon']!r}, using 'guide'")
        facts = [tuple(x.strip() for x in f.split("=", 1)) for f in cells.get("card facts", "").split(";") if "=" in f]
        menu = cells["menu"].strip()
        areas[cells["type"]] = dict(
            type=cells["type"], name=cells["name"], folder=cells["folder"].strip("/"), tag=cells["tag"], icon=icon,
            colour=cells["colour"], border=cells.get("border") or "#5d88b6", photo=cells["photo"] or "building",
            menu=int(menu) if menu.isdigit() else 0, noun=cells["count word"],
            hub=hub.group(1) if hub else cells["hub note"].strip().lower(), facts=facts)
    return areas


AREAS = read_areas()
FALLBACK_AREA = dict(type="", name="Pages", folder="pages", tag="page", icon="guide", colour="#DCEAF7", border="#5d88b6",
                     photo="building", menu=0, noun="pages", hub="-", facts=[])
GROUPS = [dict(name=g["group"], key=slugify(g["group"]), grades=[x.strip().lower() for x in g["grades"].split(",")],
               aka=g.get("also called", ""), colour=g["colour"])
          for g in table(notes["Site Areas"].body, "## Grade groups")]


def area_by_tag(tag: str) -> dict:
    return next((a for a in AREAS.values() if a["tag"] == tag or a["type"] == tag), FALLBACK_AREA)


# Hubs: one list page per distinct hub (several types can share one, like dorm + commute).
HUBS: dict[str, dict] = {}
for a in AREAS.values():
    if a["hub"] == "-":
        continue
    key = a["folder"]
    if key not in HUBS:
        note = notes.get(a["hub"]) if a["hub"] != "auto" else None
        HUBS[key] = dict(key=key, name=note.title if note else a["name"], note=note, types=[], url=f"{key}/index.html",
                         icon=a["icon"], tag=a["tag"], photo=a["photo"], menu=a["menu"], noun=a["noun"],
                         summary=(note.summary if note else f"Every page in {a['name']}."))
        if note:
            note.url = HUBS[key]["url"]
    HUBS[key]["types"].append(a["type"])


def hub_of(n: Note) -> dict | None:
    return next((h for h in HUBS.values() if n.type in h["types"]), None)


# Pages: notes of an area type, plus any note with a "publish" address.
pages = [n for n in notes.values() if n.type in AREAS]
for n in notes.values():
    if n.get("publish"):
        n.url = str(n.get("publish"))
    elif n.type in AREAS:
        n.url = f"{n.area['folder']}/{slugify(short_name(n.stem))}.html"
notes["Home"].url = "index.html"

by_type: dict[str, list[Note]] = {}
for n in sorted(pages, key=lambda n: n.title.lower()):
    by_type.setdefault(n.type, []).append(n)


def parent_of(n: Note) -> "Note | None":
    """A note with a `parent` property ("[[Comp - Biology]]") sits under that page: the hub leaves it out
    and its back link goes to the parent."""
    m = WIKILINK.search(str(n.get("parent") or ""))
    return notes.get(m.group(1)) if m else None


def hub_items(h: dict) -> list[Note]:
    return [p for t in h["types"] for p in by_type.get(t, []) if not parent_of(p)]


# "I Need To" lines ("- do this → [[Page]]") become task rows and extra search words.
tasks: list[dict] = []
for line in notes["I Need To"].body.splitlines():
    m = re.match(r"^- (.+?) → (.+)$", line.strip())
    if not m:
        continue
    targets = [notes[t] for t, _ in WIKILINK.findall(m.group(2)) if t in notes and notes[t].url]
    tasks.append(dict(text=m.group(1)[0].upper() + m.group(1)[1:], targets=targets))
    for t in targets:
        t.tasks.append(m.group(1))


# ------------------------------------------------------------------ relations
def forms_owned_by(office: str) -> list[Note]:
    return [n for n in by_type.get("form", []) if n.get("owner_office") == office]


def linked(n: Note, prefix: str) -> list[Note]:
    out: list[Note] = []
    for t, _ in WIKILINK.findall(n.body):
        if t.startswith(prefix) and t in notes and notes[t] not in out:
            out.append(notes[t])
    return out


def connection(n: Note) -> str:
    """The 'Owns / Needs / From' line on Directory rows (D44)."""
    if n.type == "office" and (owned := forms_owned_by(n.stem)):
        more = f" +{len(owned) - 3}" if len(owned) > 3 else ""
        return "Owns: " + ", ".join(o.title for o in owned[:3]) + more
    if n.type == "competition" and (need := linked(n, "Form - ")):
        return "Needs: " + ", ".join(f.title for f in need)
    if n.get("owner_office") in notes and n.type == "form":
        return "From: " + notes[n.get("owner_office")].title
    if n.type == "place" and n.get("kind"):
        return str(n.get("kind"))
    if n.type == "event" and n.get("when") and not UNKNOWN.search(str(n.get("when"))):
        return "When: " + str(n.get("when"))
    return ""


def resolve(link: str):
    """'[[Note|Label]]' -> (Note, label)."""
    m = WIKILINK.search(str(link))
    if not m or m.group(1) not in notes:
        raise SystemExit(f"Site Settings: can't find the note in {link!r}")
    n = notes[m.group(1)]
    return n, m.group(2) or n.title


# ------------------------------------------------------------------ markdown
MD = markdown.Markdown(extensions=["tables", "sane_lists"])


def strip_chrome(body: str) -> str:
    """Drop what the page layout already shows (title, back link, summary, footer) and editor-only notes."""
    body = re.sub(r"^\s*# .*\n", "", body, count=1)
    body = re.sub(r"^\s*Back to \[\[Home\]\]\s*\n", "", body, flags=re.M)
    body = re.sub(r"> \[!summary\][^\n]*\n(?:>[^\n]*\n?)*", "", body)
    body = re.sub(r"\n---\s*\nLast updated:.*$", "", body, flags=re.S)
    body = re.sub(r"\s*\(?[Ss]ee \[\[Open Questions\]\][^.\n)]*\)?\.?", "", body)  # internal to-do list
    body = re.sub(r"%%.*?%%", "", body, flags=re.S)                                  # Obsidian comments
    return body.strip()


def sections(body: str) -> tuple[str, list[tuple[str, str]]]:
    parts = re.split(r"^## (.+)$", body, flags=re.M)
    return parts[0], [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts), 2)]


def link_html(target: str, label: str | None, root: str) -> str:
    n = notes.get(target.strip())
    text = escape(label or (n.title if n else short_name(target)))
    if not (n and n.url):
        return str(text)  # unpublished note (research notes, plans): plain text
    return f'<a class="wl" href="{root}{n.url}">{text}</a>'


def autolink(text: str) -> str:
    text = re.sub(r"(?<![\w/@.])([\w.+-]+@[\w-]+(?:\.[\w-]+)+)", r'<a href="mailto:\1">\1</a>', text)
    sites = r"(?:sites\.google\.com|(?:www\.)?facebook\.com|publiscience\.org|pshswvc\.com|wvc\.pshs\.edu\.ph|maps\.app\.goo\.gl|(?:www\.)?youtube\.com)"
    # (?<!...\() : a web address that is already the target of a Markdown link "[post](https://...)" is left alone
    return re.sub(rf"(?<![\w/@.\">(])((?:https?://)?{sites}(?:/[\w./%-]*[\w/])?)",
                  lambda m: f'<a href="{m.group(1) if m.group(1).startswith("http") else "https://" + m.group(1)}">{m.group(1)}</a>',
                  text)


def new_tab(html: str) -> str:
    """Every link that leaves the site (Drive, forms, Facebook, maps) opens in a new tab (D58)."""
    def fix(m):
        attrs = m.group(1).replace(' rel="noopener"', "")
        return f'<a {attrs} target="_blank" rel="noopener">'
    return re.sub(r'<a (?![^>]*target=)([^>]*href="https?://[^"]*"[^>]*)>', fix, html)


def base_filter(spec: str):
    """Obsidian Bases filters we understand: prop == "x", prop != "x", tags.contains("x")."""
    conds = []
    for k, op, v in re.findall(r'-\s*([\w.]+)\s*(==|!=)\s*"([^"]+)"', spec):
        conds.append(lambda n, k=k, op=op, v=v: ((n.type if k == "type" else str(n.get(k))) == v) == (op == "=="))
    for k, v in re.findall(r'-\s*([\w]+)\.contains\("([^"]+)"\)', spec):
        conds.append(lambda n, k=k, v=v: v in (n.tags if k == "tags" else [str(x) for x in n.get(k) or []]))
    return lambda n: all(c(n) for c in conds)


def md(text: str, root: str) -> Markup:
    blocks: dict[str, str] = {}

    def base_block(m):  # Obsidian Bases view -> the same list on the site (D34)
        keep = base_filter(m.group(1))
        items = [n for n in pages if keep(n)]
        key = f"\x00{len(blocks)}\x00"
        blocks[key] = env.get_template("_rows.html").render(items=sorted(items, key=lambda n: n.title.lower()), root=root)
        return f"\n\n{key}\n\n"

    text = re.sub(r"```base\n(.*?)```", base_block, text, flags=re.S)
    lines: list[str] = []
    for ln in text.split("\n"):  # Obsidian allows a list right after a sentence; Markdown needs a blank line
        if LIST_ITEM.match(ln) and lines and lines[-1].strip() and not LIST_ITEM.match(lines[-1]):
            lines.append("")
        lines.append(ln)
    text = WIKILINK.sub(lambda m: link_html(m.group(1), m.group(2), root), "\n".join(lines))
    MD.reset()
    html = MD.convert(autolink(text))
    for key, val in blocks.items():
        html = html.replace(f"<p>{key}</p>", val)
    return Markup(new_tab(UNKNOWN.sub(gap, html)))


def inline(value, root: str) -> Markup:
    """A short property value for the facts card: links, web addresses and (unknown) marks."""
    if isinstance(value, list):
        value = ", ".join(str(v) for v in value) if value else "(unknown)"
    v = str(value or "(unknown)")
    if re.match(r"^https?://", v):
        return Markup(f'<a href="{escape(v)}" target="_blank" rel="noopener">{escape(re.sub(r"^https?://(www\.)?", "", v).rstrip("/"))}</a>')
    v = WIKILINK.sub(lambda m: link_html(m.group(1), m.group(2), root), str(escape(v)))
    v = re.sub(r"(?<![\w/@.])([\w.+-]+@[\w-]+(?:\.[\w-]+)+)", r'<a href="mailto:\1">\1</a>', v)
    return Markup(UNKNOWN.sub(gap, v))


def clean_source(src) -> str:
    """'PSHS-WVC Student Handbook 2018 ([[Src - WVC Student Handbook 2018]]) (2018)' -> 'PSHS-WVC Student Handbook 2018'."""
    s = re.sub(r"\s*\(\[\[[^\]]*\]\]\)", "", str(src or ""))       # the vault's link to its research note
    s = re.sub(r"(\b(\d{4})\b[^;()]*?)\s*\(\2\)", r"\1", s)         # a year written twice
    s = re.sub(r"\(masterplan\)", "", s)
    if PRIVATE_NAMES:                                                # no personal names on pages (vault rule)
        s = re.sub(r"\b(?:" + "|".join(map(re.escape, PRIVATE_NAMES)) + r")\b", "PAHIBALO team", s)
    return WIKILINK.sub(lambda m: "PAHIBALO research notes on " + short_name(m.group(2) or m.group(1)).lower()
                        if m.group(1).startswith("Src - ") else short_name(m.group(2) or m.group(1)), s).strip()


def plain(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = WIKILINK.sub(lambda m: m.group(2) or short_name(m.group(1)), text)
    return re.sub(r"\s+", " ", re.sub(r"[#>*_`|\-]+", " ", text)).strip()


# ------------------------------------------------------------------ GWA units
def gwa_sets() -> dict:
    """Units per grade, read from 'Guide - Curriculum and Units' so the fact lives once.
    Each grade line is checked against the total written in the note."""
    out = {}
    for line in notes["Guide - Curriculum and Units"].body.splitlines():
        m = re.match(r"^- \*\*(G\d+) \(([\d.]+)[^)]*\):\*\*\s*(.+)$", line.strip())
        if not m:
            continue
        grade, total, subjects = m.group(1), float(m.group(2)), []
        for part in m.group(3).split(" · "):
            part = part.strip()
            if each := re.match(r"^(.+)\(([\d.]+) each\)$", part):
                subjects += [dict(n=s.strip(), u=float(each.group(2))) for s in each.group(1).split(",")]
            elif ng := re.match(r"^(.+?) ([\d.]+) \(Complete[^)]*\)$", part):
                # No number grade (Complete or Incomplete): in the card's total units, not in the GWA.
                subjects.append(dict(n=ng.group(1)[0].upper() + ng.group(1)[1:], u=float(ng.group(2)), ng=True))
            elif opt := re.match(r"^optional (.+?) ([\d.]+)\s*\(.+\)$", part):
                subjects.append(dict(n=opt.group(1).capitalize() + " (if taken)", u=float(opt.group(2)), opt=True))
            elif one := re.match(r"^(.+?)\s+([\d.]+)$", part):
                subjects.append(dict(n=one.group(1)[0].upper() + one.group(1)[1:], u=float(one.group(2))))
            else:
                raise SystemExit(f"GWA: can't read {part!r} in {grade}")
        got = round(sum(s["u"] for s in subjects if not s.get("opt")), 2)
        if abs(got - total) > 0.05:
            raise SystemExit(f"GWA: {grade} units add up to {got}, but the note says {total}")
        out[grade] = subjects
    return out


# ------------------------------------------------------------------ Journeymap
def journey() -> list[dict]:
    """Three stages, two stops each. A page shows at a stop when its grade list includes that year and
    spans at most three years (pages for every year are not repeated at each stop)."""
    stages = []
    for g in GROUPS:
        stops = []
        for y in g["grades"]:
            items = [n for n in pages if y in n.grade and len(n.grade) <= 3]
            stops.append(dict(year=y, num=y[1:], pages=sorted(items, key=lambda n: (n.type != "event", n.type, n.title))))
        wide = [n for n in pages if set(g["grades"]) & set(n.grade) and len(n.grade) > 3 and len(n.grade) < 6]
        stages.append(dict(g, stops=stops, wide=sorted(wide, key=lambda n: n.title)))
    every = sorted([n for n in pages if len(n.grade) == 6], key=lambda n: n.title)
    return dict(stages=stages, every=every)


# ------------------------------------------------------------------ menus and templates
def link_item(link: str) -> dict:
    n, label = resolve(link)
    h = next((h for h in HUBS.values() if h["note"] is n), None)
    return dict(url=n.url, label=label, icon=(h or n.area)["icon"] if h or n.type in AREAS else n.get("icon") or "link", note=n)


menu = [(h["menu"], dict(url=h["url"], label=h["name"], icon=h["icon"])) for h in HUBS.values() if h["menu"]]
menu += [(int(n.get("menu_order")), dict(url=n.url, label=n.get("menu_label") or n.title, icon=n.get("icon") or "link"))
         for n in notes.values() if n.get("publish") and str(n.get("menu_order")).isdigit()]
nav = [m for _, m in sorted(menu, key=lambda x: x[0])]
nav += [link_item(x) for x in settings.get("menu_extra") or []]
# The top menu shows the first few tabs (Site Settings: menu_top_count); a "More" tab opens the full list.
nav_top = nav[:int(settings.get("menu_top_count") or len(nav))]
# Pinned tabs sit at the right end of the top menu, next to More (Site Settings: menu_pinned).
nav_pinned = [link_item(x) for x in settings.get("menu_pinned") or []]
nav_top = [m for m in nav_top if m["url"] not in {p["url"] for p in nav_pinned}]
footer_links = [dict(url=h["url"], label=h["name"], icon=h["icon"]) for h in HUBS.values() if not h["menu"]]
footer_links += [dict(url=n.url, label=n.get("menu_label") or n.title, icon=n.get("icon") or "link")
                 for n in notes.values() if yes(n.get("footer")) and n.url]
sheet_links = nav + [f for f in footer_links if f["url"] not in {x["url"] for x in nav}]
area_css = "".join(f".t-{a['tag']}{{background:{a['colour']}}}.k-{a['tag']}{{--k:{a['border']};--kf:{a['colour']}}}"
                   for a in AREAS.values())  # card fills and picture borders
area_css += "".join(f".gg-{g['key']}{{--g:{g['colour']}}}" for g in GROUPS)

env = Environment(loader=FileSystemLoader(HERE / "templates"), autoescape=select_autoescape(["html"]),
                  trim_blocks=True, lstrip_blocks=True)
env.globals.update(settings=settings, nav=nav, nav_top=nav_top, nav_pinned=nav_pinned,sheet_links=sheet_links, footer_links=footer_links, area_css=Markup(area_css), HUBS=HUBS,
                   GROUPS=GROUPS, AREAS=AREAS, nice_date=nice_date, connection=connection, area_by_tag=area_by_tag)
env.filters["gaps"] = lambda s: Markup(UNKNOWN.sub(gap, str(escape(s or ""))))  # "(unknown)" -> grey pill


def write(path: str, template: str, **ctx):
    root = "../" * path.count("/")
    html = env.get_template(template).render(root=root, page_url=path, **ctx)
    out = DIST / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(new_tab(html), encoding="utf-8")


# ------------------------------------------------------------------ page builders
def build_note(n: Note):
    root = "../" * n.url.count("/")
    intro, secs = sections(strip_chrome(n.body))
    tip = next((c for h, c in secs if h.lower().startswith("tip from a senior") and c.strip() and not UNKNOWN.search(c)), None)
    keep = [(h, c) for h, c in secs if not h.lower().startswith("tip from a senior")
            and not ("template_link" in n.fm and h.lower().startswith("template"))]
    related = next((c for h, c in keep if h.lower() == "related"), None)
    keep = [(h, md(c, root), h.lower().startswith("common mistakes")) for h, c in keep if h.lower() != "related"]
    hub = hub_of(n)
    par = parent_of(n)
    back = dict(url=par.url, name=par.title) if par and par.url else (dict(url=hub["url"], name=hub["name"]) if hub else None)
    owner = notes.get(n.get("owner_office"))
    facts = [(label, inline(n.get(key), root)) for label, key in n.area["facts"] if key in n.fm]
    if owner and owner.url and n.type != "office":
        facts.append(("Office", Markup(f'<a class="wl" href="{root}{owner.url}">{escape(owner.title)}</a>')))
    link = str(n.get("template_link"))
    status = str(n.get("template_status") or "")
    if link.startswith("templates/"):
        raise SystemExit(f"{n.stem}: templates are no longer hosted on the site (D58); link the Drive copy instead")
    if not link.startswith("http") or status in TEMPLATE_TEXT:
        link = ""
    maps = str(n.get("maps_link") or "")
    write(n.url, f"{n.get('layout') or 'note'}.html", n=n, hub=hub, back=back, intro=md(intro, root) if intro.strip() else "",
          secs=keep, related=md(related, root) if related else "", tip=md(tip, root) if tip else "", facts=facts,
          has_template="template_link" in n.fm, template_link=link, template_drive="drive.google" in link,
          template_school=status == "school-account",
          template_note=TEMPLATE_TEXT.get(status, TEMPLATE_TEXT["missing"]), maps=maps if maps.startswith("http") else "",
          source=clean_source(n.get("source")), active=hub["url"] if hub else "", owner=owner)


def build_hub(h: dict):
    body = strip_chrome(h["note"].body) if h["note"] else ""
    body = re.sub(r"```base\n.*?```", "", body, count=1, flags=re.S)  # the main list is drawn by the layout
    items = hub_items(h)
    groups = [g for g in GROUPS if any(g in p.groups for p in items)]
    write(h["url"], "hub.html", h=h, items=items, groups=groups, body=md(body, "../") if body else "", active=h["url"],
          layout_kind="places" if "place" in h["types"] else "")


def build_published(n: Note):
    """A standalone page: any note with a 'publish' address (layout: page, tasks, about, gwa, journey)."""
    layout = n.get("layout") or "page"
    root = "../" * n.url.count("/")
    extra = (dict(tasks=tasks) if layout == "tasks" else dict(sets=gwa_sets()) if layout == "gwa"
             else dict(j=journey()) if layout == "journey" else {})
    write(n.url, f"{layout}.html", n=n, body=md(strip_chrome(n.body), root), active=n.url, **extra)


def search_index() -> list[dict]:
    def words(s):  # gaps in the same plain words as the pages
        return UNKNOWN.sub(lambda m: GAP_WORDS[m.group(1)], s)
    return [dict(t=n.title, u=n.url, y=n.type, h=(hub_of(n) or {}).get("key", ""), tg=n.area["tag"], i=n.icon,
                 s=words(n.summary), a=n.aliases + n.tasks, g=n.grade, gg=[g["key"] for g in n.groups],
                 c=connection(n), b=plain(strip_chrome(n.body))[:600],
                 p=(n.thumb["file"] if n.thumb else ""), pl=bool(n.thumb and n.thumb.get("logo")))
            for n in pages]


def home_tiles() -> list[dict]:
    tiles = []
    for link in settings["tiles"]:
        n, label = resolve(link)
        h = next((h for h in HUBS.values() if h["note"] is n), None)
        count = len(hub_items(h)) if h else 0
        tiles.append(dict(url=n.url, label=label, icon=(h or n.area)["icon"] if (h or n.type in AREAS) else n.get("icon") or "link",
                          tag=(h or n.area)["tag"], sub=f"{count} {h['noun']}" if h else n.get("tile_text") or n.summary))
    return tiles


def write_crawler_files():
    """robots.txt, sitemap.xml and the GitHub Pages marker. While Site Settings says search_engines: "off",
    every page carries a noindex tag (base.html) and there is no sitemap; "on" lists the site (D70, D71)."""
    on = str(settings.get("search_engines", "off")).lower() == "on"
    url = str(settings.get("site_url") or "").rstrip("/") + "/"
    (DIST / ".nojekyll").write_text("", encoding="utf-8")  # GitHub Pages: serve the files as they are
    robots = "User-agent: *\nAllow: /\n" + (f"Sitemap: {url}sitemap.xml\n" if on and url.startswith("http") else "")
    (DIST / "robots.txt").write_text(robots, encoding="utf-8")
    if on and url.startswith("http"):
        pages_out = sorted(p.relative_to(DIST).as_posix() for p in DIST.rglob("*.html") if p.name != "404.html")
        rows = "".join(f"<url><loc>{escape(url + p.replace('index.html', ''))}</loc></url>" for p in pages_out)
        (DIST / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>'
                                          f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{rows}</urlset>',
                                          encoding="utf-8")


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(HERE / "assets", DIST)
    (DIST / "search-index.js").write_text(
        "window.PAHI_INDEX=" + json.dumps(search_index(), ensure_ascii=False, separators=(",", ":")) + ";", encoding="utf-8")
    kit = sorted(by_type.get("kit", []), key=lambda n: (n.stem != "Kit - First Week Guide", n.title))
    # "Around campus": only photos that show a real room or building on campus, one per office, captioned with that office
    gallery = [n.photos[0] | dict(page=n) for n in sorted(by_type.get("office", []), key=lambda n: n.title)
               if n.photos and not n.photos[0]["file"].startswith("placeholder-")][:8]
    write("index.html", "home.html", tiles=home_tiles(), quick=[resolve(q) for q in settings["quick_links"]],
          tasks=tasks, kit=kit, recent=sorted(pages, key=lambda n: (n.updated, n.title), reverse=True)[:6],
          total=len(pages), active="index.html", gallery=gallery, j=journey(),
          orgs=[n for n in by_type.get("org", []) if n.thumb])
    write("search.html", "search.html", active="search.html")
    write("404.html", "404.html")
    for n in notes.values():
        if n.get("publish"):
            build_published(n)
        elif n.type in AREAS:
            build_note(n)
    for h in HUBS.values():
        build_hub(h)
    write_crawler_files()
    print(f"Built {len(list(DIST.rglob('*.html')))} pages into {DIST.name}/ ({len(AREAS)} areas, {len(HUBS)} hubs)")


if __name__ == "__main__":
    main()
