# Changelog

Author: Xavier Santolaria

## 2.2.0 (2026-10-28)

- New logo: X, a green ball carrying the 14 that dissolves into pixels, and S (Black Ops One lettering). Follows light and dark mode.
- Favicon (SVG, ICO), Apple touch icon, and a 1200x630 link preview image (`images/og-image.png`).
- Header logo comes as two fixed-colour files (`x14s-logo-light.svg`, `x14s-logo-dark.svg`) chosen by a `<picture>` element, so phones show the right colours. `x14s-logo.svg` stays as the master.
- Header logo is now an SVG. The old `images/x14s-logo-1.png` is no longer used and can be deleted.
- Hidden author tag now reads "X14S".

## 2.1.0 (2026-10-28)

- Layout: wider page, alternating section bands, uppercase accent section titles, centered Partners section.
- Media: photos always visible, previews shown as italic quotes (collapsed for recent entries, open under "Earlier coverage").
- CV: Experience grouped per club or federation with flags and indented timelines, newest first. Honours, Education and Languages updated, White Star honours dated.
- Flags now display as icons (Twemoji, CC BY 4.0) so they also render on Windows.
- Removed Twitter link and preview tag. Footer reads "X14S".

## 2.0.0 (2026-10-28)

- Replaced MkDocs Material with a one-page site built from markdown by `build.py`.
- Merged Home, Team and Media pages into sections of a single page.
- Media entries now collapse their previews, older coverage is folded away.
- Removed Google Analytics and the cookie banner.
- Affiliate links marked `rel="sponsored"`, with a disclosure line.
- Added social preview tags, sitemap and robots.txt.
- Old `/media/` and `/team/xs/` addresses forward to the new page.
