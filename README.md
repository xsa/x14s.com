# x14s.com

One-page site for X14S (field hockey coaching, video and performance analysis).
Content is plain markdown. A small Python script turns it into a single static page.

## Day to day

Edit a file in `content/`, commit, push. GitHub Actions rebuilds and publishes.

| File | Section on the page |
|---|---|
| `content/about.md` | Top of the page (headline, intro, clubs worked with) |
| `content/numbers.md` | "Career in numbers" tiles at the end of the top section |
| `content/services.md` | Services, shown as cards, with the contact line |
| `content/team.md` | Team: profile, links and the full CV in a collapsible block |
| `content/media.md` | Media archive |
| `content/partners.md` | Partner logos |
| `content/recommended.md` | Coach's picks: shop, gear, books, recovery (shown as cards) |
| `content/footer.md` | Footer (`{{year}}` fills in the current year) |

Section order and menu labels are in `build.py` (`SECTIONS`). Do not put a top-level title in these files, the page adds it.

## Cards (Services and Coach's picks)

Every `###` heading in these files becomes a card. A line with `---` ends the cards, and the text after it stays outside (used for the contact line in Services). Which sections show cards is set in `build.py` (`CARD_SECTIONS`).

## Career in numbers

One list item per tile in `content/numbers.md`. The bold number becomes the big figure. Add a tag with `<span class="tag coached">Coached</span>` or `<span class="tag played">Played</span>`, and put a flag emoji after the word for the country.

## CV as a PDF

Every build also creates `Xavier-Santolaria-CV.pdf` from the profile block and the "Full CV" in `content/team.md`, so the PDF always matches the page. Share it as https://www.x14s.com/Xavier-Santolaria-CV.pdf. GitHub Actions has everything needed. To build it on your own computer, run `pip install playwright` and `playwright install chromium` once. Without that the build skips the PDF and says so.

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
- Old MkDocs style entries (`### 2018-06-18: "[TITLE](url)"` and `:flag_ch:` shortcodes) still work.

## Preview on your computer

Create a virtual environment once, outside iCloud Drive:

    python3 -m venv ~/.venvs/x14s
    source ~/.venvs/x14s/bin/activate
    pip install -r requirements.txt

Then, each time:

    source ~/.venvs/x14s/bin/activate
    python build.py
    python -m http.server -d site 8000

Open http://localhost:8000.

## Design

Colors, fonts and spacing are in `style.css` (the `:root` block at the top). Light and dark mode follow the visitor's device.

- Header logo: `images/x14s-logo-light.svg` and `images/x14s-logo-dark.svg`, chosen by a `<picture>` element in `template.html`. `images/x14s-logo.svg` is the master file.
- Favicon and link preview: `images/favicon.svg`, `favicon.ico`, `apple-touch-icon.png`, `og-image.png`.
- Logos ending in `#only-light` or `#only-dark` in markdown show in one mode only. Add `{: .tall }` after an image for near-square logos.

## Flags

Flag emoji in the markdown files are shown as small icons from `images/flags/` (Twemoji, CC BY 4.0), so they also display on Windows. To use another country, copy its SVG there named by country code, for example `se.svg`. Without a matching file the emoji is shown as is.

## Visit counts

GoatCounter (free, open source, no cookies). The account name is set in `build.py` (`GOATCOUNTER`). Stats are at https://x14s.goatcounter.com. Set it to an empty string to switch it off, and the footer note disappears with it.

## Affiliate links

Links to the hosts listed in `SPONSORED_HOSTS` in `build.py` are marked `rel="sponsored"` automatically. Add a host there when you add a new affiliate network.

## Document control

Author: Xavier Santolaria. Version history is in `CHANGELOG.md`.
