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
TITLE = "X14S | Where sport meets technology"
DESCRIPTION = "Field hockey coaching as well as video and performance analysis."

# Sections shown on the page, in order: (markdown file name, menu label).
SECTIONS = [
    ("about", "About"),
    ("team", "Team"),
    ("media", "Media"),
    ("partners", "Partners"),
    ("recommended", "Coach&#8217;s picks"),
]

# Media entries older than this year are tucked into a collapsed block.
FOLD_BEFORE_YEAR = 2020

# Folders copied as they are. Same layout as the old site, so every image URL
# that already exists (including ones pasted into old articles) keeps working.
STATIC_DIRS = ["images", "media/images", "team/images"]

# Links to these hosts get rel="sponsored" (affiliate and partner links).
SPONSORED_HOSTS = ("amzn.to", "amazon.", "go.nordvpn.net", "bethechange.swiss")


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
        heading = "" if sid == "about" else f"<h2>{label}</h2>\n"
        cls = ' class="hero"' if sid == "about" else ""
        sections.append(
            f'<section id="{sid}"{cls}>\n<div class="wrap">\n{heading}{body}\n</div>\n</section>'
        )
        if sid != "about":
            nav.append(f'<a href="#{sid}">{label}</a>')

    today = datetime.date.today()
    footer = md(read_md("footer").replace("{{year}}", str(today.year)))

    page = (ROOT / "template.html").read_text(encoding="utf-8")
    for key, value in {
        "{{title}}": TITLE,
        "{{description}}": DESCRIPTION,
        "{{url}}": SITE_URL,
        "{{nav}}": "\n".join(nav),
        "{{main}}": "\n".join(sections),
        "{{footer}}": footer,
        "{{updated}}": today.isoformat(),
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
