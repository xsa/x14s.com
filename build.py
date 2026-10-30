#!/usr/bin/env python3
"""Build the X14S one-page site from the markdown files in content/.

Usage:
    pip install -r requirements.txt
    python build.py            # writes the finished site into ./site
    python -m http.server -d site 8000   # optional local preview

Everything you normally edit lives in content/*.md. This script, template.html
and style.css only need attention if you want to change the design.
"""
import datetime
import html
import re
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).parent.resolve()
CONTENT = ROOT / "content"
OUT = ROOT / "site"

SITE_URL = "https://www.x14s.com"
# Visit counts with GoatCounter (free, open source, no cookies). Put your GoatCounter
# account name here, for example "x14s" for https://x14s.goatcounter.com. Empty = no analytics.
GOATCOUNTER = "x14s"
TITLE = "X14S | Where sport meets technology"
DESCRIPTION = "Field hockey coaching as well as video and performance analysis."

# Sections shown on the page, in order: (markdown file name, menu label).
SECTIONS = [
    ("about", "About"),
    ("services", "Services"),
    ("team", "Team"),
    ("media", "Media"),
    ("partners", "Partners"),
    ("recommended", "Coach&#8217;s picks"),
]

# Sections whose "### " groups are shown as cards.
CARD_SECTIONS = ("services", "recommended")

# Media entries older than this year are tucked into a collapsed block.
FOLD_BEFORE_YEAR = 2020

# Folders copied as they are. Same layout as the old site, so every image URL
# that already exists (including ones pasted into old articles) keeps working.
STATIC_DIRS = ["images", "media/images", "team/images"]

# Links to these hosts get rel="sponsored" (affiliate and partner links).
SPONSORED_HOSTS = ("amzn.to", "amazon.", "link.amazon", "go.nordvpn.net", "bethechange.swiss")


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
SHORTCODES = {
    "globe_with_meridians": "\U0001F310",
    "newspaper": "\U0001F4F0",
    "tv": "\U0001F4FA",
    "calendar": "\U0001F4C6",
    "field_hockey": "\U0001F3D1",
    "books": "\U0001F4DA",
    "tools": "\U0001F6E0️",
}


def emojify(text: str) -> str:
    """Turn :flag_be: style shortcodes (used by the old MkDocs site) into emoji."""

    def sub(m):
        name = m.group(1)
        if name.startswith("flag_") and len(name) == 7:
            return "".join(chr(0x1F1E6 + ord(c) - ord("a")) for c in name[5:])
        return SHORTCODES.get(name, m.group(0))

    return re.sub(r":([a-z0-9_]+):", sub, text)


def read_md(name: str) -> str:
    text = (CONTENT / f"{name}.md").read_text(encoding="utf-8")
    if text.startswith("---"):  # drop optional front matter
        parts = text.split("---", 2)
        if len(parts) == 3:
            text = parts[2]
    return emojify(text.strip() + "\n")


def md(text: str) -> str:
    return markdown.markdown(
        text,
        extensions=["attr_list", "md_in_html", "sane_lists", "tables"],
        output_format="html",
    )


def inline(text: str) -> str:
    """Render markdown and drop the wrapping <p> (for one-line fragments)."""
    out = md(text).strip()
    return re.sub(r"^<p>(.*)</p>$", r"\1", out, flags=re.S)


FLAG_RE = re.compile("[\U0001F1E6-\U0001F1FF]{2}")


def flagify(page: str) -> str:
    """Show flag emoji as small images, so they also display on Windows."""

    def sub(m):
        cc = "".join(chr(ord(c) - 0x1F1E6 + 97) for c in m.group(0))
        if (ROOT / "images" / "flags" / f"{cc}.svg").exists():
            return f'<img class="flag" src="images/flags/{cc}.svg" alt="{m.group(0)}">'
        return m.group(0)  # no icon available: keep the emoji

    return FLAG_RE.sub(sub, page)


def fix_links(page: str) -> str:
    """Add rel attributes to external links; affiliate links are 'sponsored'."""

    def sub(m):
        tag, href = m.group(0), m.group(1)
        if not href.startswith("http") or " rel=" in tag:
            return tag
        host = re.sub(r"^https?://([^/]+).*", r"\1", href)
        rel = "sponsored noopener" if any(h in host for h in SPONSORED_HOSTS) else "noopener"
        return tag[:-1] + f' rel="{rel}">'

    return re.sub(r'<a href="([^"]+)"[^>]*>', sub, page)


# --------------------------------------------------------------------------
# Media section
# --------------------------------------------------------------------------
SMALL_WORDS = {
    "le", "la", "les", "de", "du", "des", "en", "et", "à", "au", "aux", "un",
    "une", "sur", "par", "the", "of", "a", "an", "to", "for", "in", "on", "and",
    "or", "d", "l",
}
ACRONYMS = {
    "HC": "HC", "USTS": "USTS", "LEAD": "LEAD", "US": "US", "SHC": "SHC",
    "FH": "FH", "LNA": "LNA", "LNB": "LNB", "WK": "WK", "EK": "EK",
    "FHANALYTICS": "FHAnalytics", "I": "I", "II": "II", "III": "III",
}


def smart_title(title: str) -> str:
    """Soften ALL CAPS titles (the old site used them). Normal case is left alone."""
    if not title.isupper():
        return title
    out = []
    for i, word in enumerate(title.split(" ")):
        core = re.sub(r"[^\wÀ-ÿ]", "", word).upper()
        if core in ACRONYMS:
            out.append(word.upper().replace(core, ACRONYMS[core], 1))
            continue
        low = word.lower()
        out.append(low if (i > 0 and low in SMALL_WORDS) else low[:1].upper() + low[1:])
    return " ".join(out)


ENTRY_RE = re.compile(r"^###\s+(?:(\S+)\s+)?(\d{4})-(\d{2})-(\d{2})\s*[:|]?\s*(.*)$")
LINK_RE = re.compile(r'^"?\[(.+?)\]\((\S+?)\)"?$')
RULE_RE = re.compile(r"^(\*\s*\*\s*\*|-{3,}|\*{3,})$")
IMAGE_ONLY_RE = re.compile(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)|!\[[^\]]*\]\([^)]*\)")


def parse_media(text: str):
    """Return (intro_markdown, {year: [entry, ...]}). Reads the old and the new format."""
    intro, years, cur = [], {}, None
    for line in text.splitlines():
        stripped = line.strip()
        if RULE_RE.match(stripped) or line.startswith("# ") or line.startswith("## "):
            continue
        m = ENTRY_RE.match(line)
        if m:
            _, year, month, day, rest = m.groups()
            link = LINK_RE.match(rest.strip())
            title, url = (link.group(1), link.group(2)) if link else (rest.strip(' "'), "")
            cur = {"date": f"{year}-{month}-{day}", "title": title, "url": url, "body": []}
            years.setdefault(year, []).append(cur)
        elif cur is None:
            intro.append(line)
        else:
            cur["body"].append(line)
    return "\n".join(intro).strip(), years


def entry_html(e, collapse: bool = True) -> str:
    meta, body = "", []
    for line in e["body"]:
        m = re.match(r"^source:\s*(.*)$", line.strip(), flags=re.I)
        if m:
            meta = m.group(1)
        else:
            body.append(line)
    body_md = "\n".join(body).strip()

    title = html.escape(smart_title(e["title"]), quote=False)
    if e["url"]:
        title_html = f'<a class="entry-title" href="{e["url"]}">{title}</a>'
    else:
        title_html = f'<span class="entry-title">{title}</span>'

    out = [
        '<article class="entry">',
        f'<div class="entry-head"><time datetime="{e["date"]}">{e["date"]}</time> {title_html}</div>',
    ]
    if meta:
        out.append(f'<p class="entry-meta">{inline(meta)}</p>')
    if body_md:
        images = IMAGE_ONLY_RE.findall(body_md)
        text_md = IMAGE_ONLY_RE.sub("", body_md).strip()
        if images:  # photos are always visible
            out.append('<div class="entry-photos">' + md("\n\n".join(images)) + "</div>")
        if text_md:  # excerpt text is styled as a quote, collapsed for recent entries
            quote = f'<blockquote class="excerpt">{md(text_md)}</blockquote>'
            out.append(
                f'<details class="preview"><summary>Preview</summary>{quote}</details>'
                if collapse
                else quote
            )
    out.append("</article>")
    return "\n".join(out)


def render_media(text: str) -> str:
    intro, years = parse_media(text)
    parts = [md(intro)] if intro else []
    recent = [(y, es) for y, es in years.items() if int(y) >= FOLD_BEFORE_YEAR]
    older = [(y, es) for y, es in years.items() if int(y) < FOLD_BEFORE_YEAR]

    def block(items, collapse=True):
        return "\n".join(
            f'<h3 class="year">{y}</h3>\n' + "\n".join(entry_html(e, collapse) for e in es)
            for y, es in items
        )

    parts.append(block(recent))
    if older:
        lo, hi = min(y for y, _ in older), max(y for y, _ in older)
        parts.append(
            f'<details class="archive"><summary>Earlier coverage, {lo} to {hi}</summary>'
            f"{block(older, collapse=False)}</details>"
        )
    return "\n".join(parts)


def cardify(html):
    """Wrap each <h3> group in a card. An <hr> ends the cards; whatever follows stays outside."""
    tail = ""
    m = re.search(r"<hr\s*/?>", html)
    if m:
        html, tail = html[:m.start()], html[m.end():]
    chunks = html.split("<h3")
    intro, groups = chunks[0], chunks[1:]
    if not groups:
        return intro + tail
    cards = "".join(f'<div class="card"><h3{g}</div>\n' for g in groups)
    return f'{intro}<div class="cards">\n{cards}</div>{tail}'



# --------------------------------------------------------------------------
# CV as a PDF (shareable link: /Xavier-Santolaria-CV.pdf)
# --------------------------------------------------------------------------
CV_PDF_NAME = "Xavier-Santolaria-CV.pdf"

CV_CSS = """
@page { size: A4; margin: 16mm 15mm 18mm; }
* { box-sizing: border-box; }
body { font: 10pt/1.45 "Helvetica Neue", Helvetica, Arial, "Liberation Sans", sans-serif; color: #1c2024; margin: 0; }
a { color: #1f7a4d; text-decoration: none; }
header { display: flex; gap: 6mm; align-items: flex-start; border-bottom: 2px solid #1f7a4d; padding-bottom: 5mm; margin-bottom: 4mm; }
header img.portrait { width: 30mm; height: 37mm; object-fit: cover; border-radius: 2mm; }
header p { margin: 0 0 2mm; }
header strong { font-size: 18pt; letter-spacing: 0.02em; }
h3 { font-size: 11pt; text-transform: uppercase; letter-spacing: 0.1em; color: #1f7a4d; margin: 6mm 0 2mm; border-bottom: 0.3mm solid #d5dbe0; padding-bottom: 1mm; break-after: avoid; }
h4 { font-size: 10.5pt; margin: 4mm 0 0.5mm; break-after: avoid; }
ul { margin: 1mm 0; padding-left: 5mm; }
li { margin: 0.8mm 0; }
table { border-collapse: collapse; margin: 0.5mm 0 0 4mm; width: calc(100% - 4mm); table-layout: fixed; border-left: 0.5mm solid #d5dbe0; }
thead { display: none; }
td { padding: 0.6mm 3mm; vertical-align: top; }
td:first-child { white-space: nowrap; width: 30mm; color: #5d6670; }
table, li, h4 { break-inside: avoid; }
img.flag { height: 3.2mm; width: auto; vertical-align: -0.5mm; }
"""


def build_cv_pdf(team_html: str, updated: str) -> None:
    """Render the Team section's CV to a one-file PDF. Skipped when Playwright is not installed."""
    person = re.search(r'<div class="person">\s*<p>(<img[^>]*>)</p>\s*<div>(.*?)</div>\s*</div>', team_html, re.S)
    cv = re.search(r'<details class="cv">\s*<summary>.*?</summary>(.*?)</details>', team_html, re.S)
    if not (person and cv):
        print("CV PDF skipped: could not find the profile block or the CV in content/team.md")
        return
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("CV PDF skipped: Playwright is not installed (it is installed on GitHub Actions)")
        return

    doc = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Xavier Santolaria, CV</title>'
        f"<style>{CV_CSS}</style></head><body>"
        f"<header>{person.group(1)}<div>{person.group(2)}</div></header>{cv.group(1)}</body></html>"
    )
    doc = flagify(doc)
    tmp = OUT / "_cv.html"
    tmp.write_text(doc, encoding="utf-8")
    footer = (
        '<div style="width:100%;font:7pt Helvetica,Arial,sans-serif;color:#5d6670;padding:0 15mm;'
        'display:flex;justify-content:space-between"><span>Xavier Santolaria | x14s.com</span>'
        f'<span>Updated {updated} | page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>'
    )
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.goto(tmp.resolve().as_uri())
            page.pdf(
                path=str(OUT / CV_PDF_NAME), format="A4", print_background=True,
                display_header_footer=True, header_template="<div></div>", footer_template=footer,
                margin={"top": "16mm", "bottom": "18mm", "left": "15mm", "right": "15mm"},
            )
            browser.close()
        print(f"Built {OUT / CV_PDF_NAME}")
    except Exception as exc:  # browser missing, sandbox problems, and so on
        print(f"CV PDF skipped: {exc}")
    finally:
        tmp.unlink(missing_ok=True)


# --------------------------------------------------------------------------
# Page assembly
# --------------------------------------------------------------------------
def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    nav, sections = [], []
    for sid, label in SECTIONS:
        if not (CONTENT / f"{sid}.md").exists():
            print(f"skipped: content/{sid}.md not found")
            continue
        text = read_md(sid)
        body = render_media(text) if sid == "media" else md(text)
        if sid == "about" and (CONTENT / "numbers.md").exists():
            body += "\n" + md(read_md("numbers"))
        if sid in CARD_SECTIONS:
            body = cardify(body)
        heading = "" if sid == "about" else f"<h2>{label}</h2>\n"
        cls = ' class="hero"' if sid == "about" else ""
        sections.append(
            f'<section id="{sid}"{cls}>\n<div class="wrap">\n{heading}{body}\n</div>\n</section>'
        )
        if sid != "about":
            nav.append(f'<a href="#{sid}">{label}</a>')

    today = datetime.date.today()
    footer = md(read_md("footer").replace("{{year}}", str(today.year)))

    analytics = ""
    if GOATCOUNTER:
        analytics = (f'<script data-goatcounter="https://{GOATCOUNTER}.goatcounter.com/count" '
                     'async src="//gc.zgo.at/count.js"></script>')
        footer += '\n<p>Privacy friendly visit counts (<a href="https://www.goatcounter.com">GoatCounter</a>), no cookies, no personal data.</p>'

    page = (ROOT / "template.html").read_text(encoding="utf-8")
    for key, value in {
        "{{title}}": TITLE,
        "{{description}}": DESCRIPTION,
        "{{url}}": SITE_URL,
        "{{nav}}": "\n".join(nav),
        "{{main}}": "\n".join(sections),
        "{{footer}}": footer,
        "{{updated}}": today.isoformat(),
        "{{analytics}}": analytics,
    }.items():
        page = page.replace(key, value)
    (OUT / "index.html").write_text(fix_links(flagify(page)), encoding="utf-8")

    # Static files
    shutil.copy(ROOT / "style.css", OUT / "style.css")
    for name in ("CNAME", "robots.txt"):
        if (ROOT / name).exists():
            shutil.copy(ROOT / name, OUT / name)
    for d in STATIC_DIRS:
        if (ROOT / d).is_dir():
            shutil.copytree(ROOT / d, OUT / d, dirs_exist_ok=True)

    team_html = next((s for s in sections if s.startswith('<section id="team"')), "")
    build_cv_pdf(team_html, today.isoformat())

    # Old addresses forward to the matching part of the single page.
    def redirect(path: str, target: str):
        p = OUT / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            "<!doctype html><meta charset=utf-8>"
            f'<meta http-equiv="refresh" content="0; url={target}">'
            f'<link rel="canonical" href="{SITE_URL}{target}">'
            f"<script>location.replace('{target}')</script>"
            f'<a href="{target}">Continue</a>',
            encoding="utf-8",
        )

    redirect("media/index.html", "/#media")
    redirect("team/xs/index.html", "/#team")
    redirect("team/index.html", "/#team")
    redirect("404.html", "/")

    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{SITE_URL}/</loc><lastmod>{today.isoformat()}</lastmod></url></urlset>\n",
        encoding="utf-8",
    )
    print(f"Built {OUT / 'index.html'}")


if __name__ == "__main__":
    build()
