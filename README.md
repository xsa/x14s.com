# x14s.com

One-page site for X14S (field hockey coaching, video and performance analysis).
Content is plain markdown. A small Python script turns it into a single static page.

## Day to day

Edit a file in `content/`, commit, push. GitHub Actions rebuilds and publishes.

| File | Section on the page |
|---|---|
| `content/about.md` | Top of the page (tagline, quote, clubs worked with) |
| `content/team.md` | Team, with the full CV in a collapsible block |
| `content/services.md` | Services offered, with the contact line |
| `content/media.md` | Media archive |
| `content/partners.md` | Partner logos |
| `content/recommended.md` | Gear, books, recovery |
| `content/footer.md` | Footer (`{{year}}` fills in the current year) |

Section order and menu labels are in `build.py` (`SECTIONS`). Do not put a top-level title in these files, the page adds it.

## Add a media entry

Paste this at the top of `content/media.md` (newest first):

    ### 2026-11-15 [Title of the article](https://link-to-the-article)
    source: [outlet.com](https://www.outlet.com/) 🇨🇭 📰

    Optional preview text, kept for articles whose link may disappear.
    An image can go here too: ![caption](media/images/photo.jpg)

Rules of thumb:

- The date must be `YYYY-MM-DD`. Years are grouped automatically.
- Under the `source:` line, images are always shown, and the text becomes a collapsed "Preview" displayed as an italic quote.
- Entries before 2020 are folded into "Earlier coverage". Change `FOLD_BEFORE_YEAR` in `build.py` to move that line.
- Old MkDocs style entries (`### 2018-06-18: "[TITLE](url)"` and `:flag_ch:` shortcodes) still work, so `docs/media/index.md` from the old repo can be pasted straight into `content/media.md`.

## Preview on your computer

    pip install -r requirements.txt
    python build.py
    python -m http.server -d site 8000

Then open http://localhost:8000.

## Migrating from the MkDocs repo (one time)

1. Keep your existing `CNAME` file as it is.
2. Move the images, keeping the same folder layout so every existing image URL still works:

        mkdir -p media team
        git mv docs/images images
        git mv docs/media/images media/images
        git mv docs/team/images team/images

3. Copy this project's files over the repo root (`build.py`, `template.html`, `style.css`, `requirements.txt`, `robots.txt`, `content/`, `.github/workflows/main.yml`).
4. Remove what is no longer needed: `docs/`, `overrides/`, `mkdocs.yml`.
5. In the GitHub repo go to Settings > Pages and set the source to "GitHub Actions" (the MkDocs setup most likely published from a `gh-publish` style branch).
6. Push to `main`, then check the Actions tab.

Old addresses keep working: `/media/` and `/team/xs/` forward to the matching part of the page.

## Design

Colors, fonts and spacing are in `style.css` (the `:root` block at the top). Light and dark mode follow the visitor's device. Logo files ending in `#only-light` or `#only-dark` show in one mode only, as on the old site.

## Flags

Flag emoji in the markdown files (for example the Swiss flag) are shown as small icons from `images/flags/`. To use another country, copy its SVG there named by country code, for example `se.svg`. Without a matching file the emoji is shown as is.

## Please check after the first build

- Contact link in `content/partners.md` (currently points to Instagram).
- FIH Level 3 status in the CV (`content/team.md` still says "in progress (2025)").
- Roles marked "present" in the CV.
- The white Swiss Hockey logo sits on a dark tile so it stays visible in light mode. A colored version would look better.

## Document control

Author: Xavier Santolaria. Version history is in `CHANGELOG.md`.
