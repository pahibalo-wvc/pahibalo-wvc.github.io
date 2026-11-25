"""Check the built site before sharing it. Adapted from KJ Digital's tools/check_sites.py.

    python build.py
    python check.py

Needs: pip install playwright, and Microsoft Edge.

1. Links: every href/src inside dist/ points at a file that exists.
2. Writing: no "signs of AI writing" words or dashes in the visible text (Wikipedia list, see the
   human-writing-profile rules). Prints the word and the page so a person can rewrite the sentence.
3. In a real browser at 375x667 and 1280x800, light and dark:
   no sideways scroll (WCAG 1.4.10), text contrast 4.5:1 or 3:1 for large text (1.4.3),
   tap targets 44px tall, one h1 and no skipped heading levels, images with alt/width/height that load,
   and no JavaScript errors.
"""
import html as htmllib
import re
import sys
import urllib.parse
from pathlib import Path

DIST = Path(__file__).resolve().parent / "dist"
def sample_pages():
    """Home, search, every hub, every root page, and the first page in each area folder.
    New areas and pages are picked up on their own."""
    out = ["index.html", "search.html?q=leave"]
    out += [f"{p.name}" for p in sorted(DIST.glob("*.html")) if p.name not in ("index.html", "search.html", "404.html")]
    for folder in sorted(d for d in DIST.iterdir() if d.is_dir() and d.name not in ("img", "fonts", "css", "js")):
        out.append(f"{folder.name}/index.html") if (folder / "index.html").exists() else None
        first = next((p for p in sorted(folder.glob("*.html")) if p.name != "index.html"), None)
        if first:
            out.append(f"{folder.name}/{first.name}")
    out.append("forms/leave-pass.html")
    return list(dict.fromkeys(out))
SIZES = [(375, 667), (1280, 800)]

AI_WORDS = r"""additionally|align(?:s|ed)? with|bolster|crucial|delve|emphasi[sz]|enduring|enhanc|foster|garner|
highlight(?:s|ing|ed)?\b|interplay|intricate|\bkey\b|landscape|meticulous|pivotal|showcas|tapestry|testament|underscor|
valuable|vibrant|undoubtedly|furthermore|moreover|utili[sz]e|facilitate|demonstrate|ultimately|realm|journey(?!map)|navigat|
embark|unlock|beacon|multifaceted|robust|leverage|seamless|notably|in today's world|worth noting|serves as|stands as|
boasts|nestled|in the heart of|groundbreaking|renowned|diverse array|commitment to|whether you're|look no further|
elevate|empower|curated|one-stop|hassle|game.?changer|dive in|—|–"""
AI_RE = re.compile(AI_WORDS.replace("\n", ""), re.I)
# Planning notes that must never reach a public page (vault rule: no personal names on pages).
_PN = Path(__file__).resolve().parent / "private_names.txt"   # local only, not uploaded (D71)
_NAMES = [n.strip() for n in _PN.read_text(encoding="utf-8").splitlines() if n.strip()] if _PN.exists() else []
INTERNAL_RE = re.compile(r"\b(" + "|".join(map(re.escape, _NAMES + ["Claude", "Opus", "masterplan", "Open Questions"])) + r")\b|\bTODO\b|\(D\d+\)", re.I)  # (D28) = decision IDs
# Site voice (D53): no contractions, no exclamation marks, no rhetorical questions.
STYLE_RE = re.compile(r"\b\w+['’](?:t|re|ll|ve|d|m)\b|\b(?:it|that|there|here|what|who|let|he|she)['’]s\b|[A-Za-z]![\s\"”]|[a-z][^.?!\n]{0,60}\?(?=\s+[A-Z])", re.I)
# Old names that D57 replaced. A few mentions are allowed when they explain the change.
OLD_NAMES = re.compile(r"Excuse Slip|Lost and Found Item Report|Certificate of Good Standing|Commencement|Pagbaligya|Pagbalandra|"
                       r"Pagbantala|Coop and Canteen|Campus Grocery|Food Nearby|Accounts and Tools|\blaniog\b|GWA calc\b|"
                       r"Discipline Office room|Request DOcuments|SCALE and LEAP|SCALE LEAP")
OLD_OK = re.compile(r"formerly Discipline Office|used to be the Discipline Office|old Discipline Office|called the Anecdotal Report|"
                    r"says \W?Anecdotal Report|formerly SCALE|used to be called SCALE|paper copies still say SCALE|SCALE stood for|"
                    r"SCALE \(Service|\(SCALE\)")
VAULT = DIST.parent.parent / "PAHIBALO Vault"


def check_names():
    """D57 renames: old names must not come back on any page."""
    found = []
    for f in sorted(DIST.rglob("*.html")):
        t = f.read_text(encoding="utf-8")
        t = re.sub(r"<(script|style|svg)\b.*?</\1>", " ", t, flags=re.S)
        t = htmllib.unescape(re.sub(r"<[^>]+>", " ", t))
        for m in OLD_NAMES.finditer(t):
            ctx = t[max(0, m.start() - 50):m.end() + 50]
            if not OLD_OK.search(ctx):
                found.append(f"old name: {f.relative_to(DIST)}: '{m.group(0)}' in \"{re.sub(chr(10), ' ', ctx).strip()}\"")
    return found


def page_text(f: Path) -> str:
    t = f.read_text(encoding="utf-8")
    t = re.sub(r"<(script|style|svg)\b.*?</\1>", " ", t, flags=re.S)
    return htmllib.unescape(re.sub(r"<[^>]+>", " ", t))


def check_corrections():
    """The PAHIBALO team's corrections of 2026-11-24 must hold on every page:
    the APF goes to the SAU Chief; the Material Rental and Out of School Work forms are gone;
    the Registrar page has no fees; every competition page says what it is and what skills it tests."""
    bad = []
    for f in sorted(DIST.rglob("*.html")):
        rel = f.relative_to(DIST).as_posix()
        t = page_text(f)
        if re.search(r"Assistant CID Chief", t):
            bad.append(f"correction: {rel} still says the APF goes to the Assistant CID Chief (it goes to the SAU Chief)")
        if re.search(r"Material Rental|Out of School Work", t, re.I):
            bad.append(f"correction: {rel} mentions a removed form (Material Rental or Out of School Work)")
    for gone in ("forms/material-rental-forms.html", "forms/out-of-school-work-forms.html"):
        if (DIST / gone).exists():
            bad.append(f"correction: {gone} should not exist")
    reg = DIST / "offices" / "registrar-unit.html"
    if reg.exists():
        main = reg.read_text(encoding="utf-8").split('<main id="main">', 1)[-1].split("</main>", 1)[0]
        if re.search(r"₱|<th>\s*Fee", main):
            bad.append("correction: offices/registrar-unit.html still shows a fee table or price")
    apf = DIST / "forms" / "activity-proposal-form.html"
    if apf.exists() and "SAU Chief" not in page_text(apf):
        bad.append("correction: the APF page does not say it goes to the SAU Chief")
    for f in sorted((DIST / "competitions").glob("*.html")):
        if f.name == "index.html":
            continue
        heads = re.findall(r"<h2[^>]*>(.*?)</h2>", f.read_text(encoding="utf-8"))
        for need in ("What it is", "Skills it tests"):
            if need not in heads:
                bad.append(f"correction: competitions/{f.name} has no '{need}' block")
    if re.search(r"Material Rental|Out of School Work", (DIST / "search-index.js").read_text(encoding="utf-8"), re.I):
        bad.append("correction: search-index.js still lists a removed form")
    return bad


def check_external():
    """D58: links that leave the site open in a new tab, and no form templates are hosted on the site."""
    bad = [f"hosted file: {p.relative_to(DIST)} (templates live on Google Drive)" for p in DIST.rglob("*.pdf")]
    for f in DIST.rglob("*.html"):
        for a in re.findall(r"<a [^>]*href=\"https?://[^\"]+\"[^>]*>", f.read_text(encoding="utf-8")):
            if 'target="_blank"' not in a:
                bad.append(f"new tab: {f.relative_to(DIST)}: {a[:90]}")
    return bad


def photo_gaps() -> set[str]:
    """Pages allowed to have one photo: listed under '## Pages with one photo' in the vault's public
    'Photo Exceptions' note, one bullet per page address, added only after a real search found nothing more (D57)."""
    t = (VAULT / "Photo Exceptions.md").read_text(encoding="utf-8")
    sec = t.split("## Pages with one photo", 1)[1].split("\n## ", 1)[0] if "## Pages with one photo" in t else ""
    return set(re.findall(r"`([\w./-]+\.html)`", sec))


# The PAHIBALO team's photo rules (2026-11-24). "2 informative pictures per page" is only a guide now.
#   orgs: 2 or more photos (the logo does not count), events and competitions: 3 or more,
#   offices: 1 or more (only photos from Facebook posts or the virtual tour), forms: no pictures at all.
# A page listed under "Pages with one photo" in Handoff is allowed fewer, after a real search found nothing more.
PHOTO_MIN = {"orgs": 2, "events": 3, "competitions": 3, "offices": 1}
ORG_BLOCKS = ("What it is", "What members do", "How to join", "When it is active")


def check_photos():
    """Informative pictures carry data-info; blurred backgrounds and icons do not count.
    Other areas (guides, Starter Kit, dorm, places, tools) keep 2 as a guide: listed in the report, not counted."""
    ok_few, probs, guide = photo_gaps(), [], []
    for f in sorted(DIST.rglob("*.html")):
        rel = f.relative_to(DIST).as_posix()
        if rel in ("404.html", "search.html"):
            continue
        html = f.read_text(encoding="utf-8")
        main = html.split('<main id="main">', 1)[-1].split("</main>", 1)[0]
        area = rel.split("/")[0] if "/" in rel else ""
        if rel.endswith("index.html"):
            if area == "forms" and "row-thumb" in main:
                probs.append("photos: forms/index.html shows a picture on a form card (forms have no preview pictures)")
            continue
        imgs = re.findall(r"<img [^>]*data-info[^>]*>", main)
        n = len([i for i in imgs if "ph-logo" not in i])
        if area == "forms":
            if n:
                probs.append(f"photos: {rel} has {n} picture(s); forms have no pictures (the Registrar page keeps its own)")
            continue
        need = PHOTO_MIN.get(area)
        if need is None:
            if n < 2:
                guide.append(f"{rel} ({n})")
            continue
        if n < need and rel not in ok_few:
            probs.append(f"photos: {rel} has {n} (needs {need}; log it in the vault's Photo Exceptions note only after a real search)")
        if area == "orgs":
            heads = re.findall(r"<h2[^>]*>(.*?)</h2>", main)
            probs += [f"org info: {rel} has no '{b}' block" for b in ORG_BLOCKS if b not in heads]
    print(f"Photo guide (not counted): {len(guide)} other pages under 2 pictures: {', '.join(guide) or 'none'}")
    return probs


def check_links():
    bad = []
    for f in DIST.rglob("*.html"):
        if f.name == "404.html":
            continue  # uses <base href="/"> on purpose
        for h in re.findall(r'(?:href|src)="([^"#?]+)', f.read_text(encoding="utf-8")):
            if h.startswith(("http", "mailto:", "data:")):
                continue
            if not (f.parent / urllib.parse.unquote(h)).resolve().exists():
                bad.append(f"link: {f.relative_to(DIST)} -> {h}")
    return bad


def check_words():
    found = []
    for f in sorted(DIST.rglob("*.html")):
        t = f.read_text(encoding="utf-8")
        t = re.sub(r"<(script|style|svg)\b.*?</\1>", " ", t, flags=re.S)
        t = htmllib.unescape(re.sub(r"<[^>]+>", " ", t))
        t = t.replace("Leadership Enhancement", "")  # part of SCALE's official name, not a style choice
        t = t.replace("Empowerment and Safety", "").replace("Reflect and Empower", "")  # the SCO's own framework names
        t = t.replace("Human Christmas Tree Showcase", "")  # the official name of an SA contest
        for kind, rx in (("words", AI_RE), ("internal", INTERNAL_RE), ("style", STYLE_RE)):
            for m in rx.finditer(t):
                ctx = re.sub(r"\s+", " ", t[max(0, m.start() - 40):m.end() + 40]).strip()
                found.append(f"{kind}: {f.relative_to(DIST)}: '{m.group(0)}' in \"{ctx}\"")
    return sorted(set(found))


JS = r"""
() => {
  const out = [], W = innerWidth;
  if (document.documentElement.scrollWidth > W + 1) out.push('reflow: page is ' + document.documentElement.scrollWidth + 'px wide');
  const lum = c => { const v = c.map(x => { x /= 255; return x <= .03928 ? x / 12.92 : Math.pow((x + .055) / 1.055, 2.4); }); return .2126*v[0] + .7152*v[1] + .0722*v[2]; };
  const parse = s => { let m = s.match(/rgba?\(([^)]+)\)/); if (m) { const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; }
    m = s.match(/color\(srgb ([^)]+)\)/); if (m) { const p = m[1].split(/[ \/]+/).filter(Boolean).map(Number); return [p[0]*255, p[1]*255, p[2]*255, p.length > 3 ? p[3] : 1]; } return null; };
  const mix = (t, b) => [0,1,2].map(i => t[i]*t[3] + b[i]*(1 - t[3]));
  // Background colours behind an element. A section marked data-photo has a photo behind it, so
  // anything see-through on it (frosted glass) is tested over both a black and a white photo:
  // the worst of the two counts. Grain and torn-edge images on paper are textures, not photos.
  function bgsOf(el) {
    const layers = [];
    let bases = [[255, 255, 255]];
    for (let e = el; e; e = e.parentElement) {
      const cs = getComputedStyle(e);
      const c = parse(cs.backgroundColor);
      if (c && c[3] > 0) { layers.push(c); if (c[3] >= 1) break; }
      if (e.hasAttribute && e.hasAttribute('data-photo')) { bases = [[0, 0, 0], [255, 255, 255]]; break; }
    }
    return bases.map(b => { let base = b; for (let i = layers.length - 1; i >= 0; i--) base = mix(layers[i], base); return base; });
  }
  const ratioOf = (fg, bg) => { const f = mix(fg, bg), L1 = lum(f), L2 = lum(bg); return (Math.max(L1, L2) + .05) / (Math.min(L1, L2) + .05); };
  document.querySelectorAll('body *').forEach(el => {
    if (['SCRIPT','STYLE','svg','OPTION','use'].includes(el.tagName)) return;
    if (![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) return;
    const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
    if (!r.width || !r.height || cs.visibility === 'hidden' || +cs.opacity === 0 || el.closest('[hidden]') || el.closest('.sr,.skip')) return;
    if (el.closest('[aria-hidden=true]')) return;
    const fg = parse(cs.color); if (!fg) return;
    const ratio = Math.min(...bgsOf(el).map(bg => ratioOf(fg, bg)));
    const size = parseFloat(cs.fontSize), bold = parseInt(cs.fontWeight) >= 700;
    const need = (size >= 24 || (bold && size >= 18.66)) ? 3 : 4.5;
    if (ratio < need) out.push('contrast: ' + ratio.toFixed(2) + ':1 (needs ' + need + ') "' + el.textContent.trim().slice(0, 40) + '"');
  });
  document.querySelectorAll('.btn, button, .chips a, .tags a, .row, .folder, .crumb a, .foot-links a, .bot a, input:not([type=radio]), select, summary, .brand, .topnav a, .related a, .task-list a, .h-row a, .more-link, .peek-all, .hub-search, .seg span, .task, .kit-list a, .gfilter button, .stop-list a, .j-stage-link, .maps-btn, a.coupon, .place-card').forEach(el => {
    const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
    if (!r.width || cs.display === 'none' || cs.visibility === 'hidden' || el.closest('[hidden]')) return;
    if (r.height < 43.5) out.push('tap: ' + Math.round(r.height) + 'px tall: ' + (el.textContent.trim() || el.getAttribute('aria-label') || el.tagName).slice(0, 30));
  });
  const hs = [...document.querySelectorAll('h1,h2,h3,h4')].filter(h => h.getBoundingClientRect().width && !h.closest('[hidden]'));
  const h1s = hs.filter(h => h.tagName === 'H1').length; if (h1s !== 1) out.push('headings: ' + h1s + ' h1');
  let last = 0; hs.forEach(h => { const n = +h.tagName[1]; if (last && n > last + 1) out.push('headings: h' + last + ' -> h' + n + ' "' + h.textContent.trim().slice(0, 30) + '"'); last = n; });
  document.querySelectorAll('img').forEach(im => {
    const name = im.getAttribute('src');
    if (!im.hasAttribute('alt')) out.push('img: no alt ' + name);
    if (!im.getAttribute('width') || !im.getAttribute('height')) out.push('img: no width/height ' + name);
    if (im.complete && im.naturalWidth === 0) out.push('img: broken ' + name);
  });
  return out;
}
"""


def check_browser():
    from playwright.sync_api import sync_playwright
    probs = []
    with sync_playwright() as p:
        br = p.chromium.launch(channel="msedge", headless=True)
        for scheme in ("light", "dark"):
            for w, h in SIZES:
                for page in sample_pages():
                    path, _, query = page.partition("?")
                    pg = br.new_page(viewport={"width": w, "height": h}, color_scheme=scheme)
                    errs = []
                    pg.on("pageerror", lambda e: errs.append(str(e)))
                    pg.goto((DIST / path).as_uri() + ("?" + query if query else ""), wait_until="load")
                    pg.add_style_tag(content="*{transition:none!important;animation:none!important}")
                    pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')")
                    pg.wait_for_timeout(400)
                    probs += [f"{scheme} {w}px {page}: {m}" for m in pg.evaluate(JS)]
                    probs += [f"{scheme} {w}px {page}: js error {e}" for e in errs]
                    pg.close()
        br.close()
    return probs


if __name__ == "__main__":
    only = sys.argv[1:]
    results = []
    if not only or "links" in only:
        results += check_links()
    if not only or "words" in only:
        results += check_words()
        results += check_names()
        results += check_corrections()
    if not only or "links" in only:
        results += check_external()
    if not only or "photos" in only:
        results += check_photos()
    if not only or "browser" in only:
        results += check_browser()
    for r in dict.fromkeys(results):
        print(r)
    print(f"\nTOTAL {len(dict.fromkeys(results))}")
