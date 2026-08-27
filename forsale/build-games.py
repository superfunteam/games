#!/usr/bin/env python3
"""
Superfun Games for News - game page text builder.

Usage:  python3 forsale/build-games.py

Edit the copy in forsale/content/<game>.md and re-run. This injects the text
into the existing forsale/<game>/index.html, leaving layout, CSS, imagery, and
scripts untouched.

Sections in the .md:
  frontmatter  name, eyebrow, tagline, meta_*, description
  ## about     one or more paragraphs (first is the lead)
  ## included  one "Title | description" per line
  ## superfun  a single paragraph
  ## cta       line 1 = heading, line 2 = body
"""
import re, html, pathlib

ROOT    = pathlib.Path(__file__).resolve().parent
CONTENT = ROOT / "content"

def esc(t):
    """Markdown-ish inline -> HTML, with entity-safe ampersands and curly quotes."""
    t = t.replace("&", "&amp;")
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', t)
    t = t.replace("'", "&rsquo;")
    return t

def parse(path):
    raw = path.read_text()
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', raw, re.S)
    meta, body = {}, raw
    if m:
        for line in m.group(1).split("\n"):
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()
        body = m.group(2)
    secs = {}
    for sm in re.finditer(r'^## (\w+)\n(.*?)(?=^## |\Z)', body, re.S | re.M):
        secs[sm.group(1)] = sm.group(2).strip()
    return meta, secs

def build(slug):
    md = CONTENT / f"{slug}.md"
    page = ROOT / slug / "index.html"
    if not md.exists() or not page.exists():
        print(f"  ! skipping {slug} (missing md or page)"); return
    meta, secs = parse(md)
    s = page.read_text()
    name = meta["name"]

    # --- hero -------------------------------------------------------------
    s = re.sub(r'(<p class="eyebrow">)[^<]*(</p>)', rf'\g<1>{esc(meta["eyebrow"])}\g<2>', s, count=1)
    s = re.sub(r'(<h1>)[^<]*(</h1>)', rf'\g<1>{esc(name)}\g<2>', s, count=1)
    s = re.sub(r'(<p class="tagline">)[^<]*(</p>)', rf'\g<1>{esc(meta["tagline"])}\g<2>', s, count=1)

    # --- meta strip (any meta_* key, in the order written in the .md) ------
    cells = []
    for k, v in meta.items():
        if not k.startswith("meta_"):
            continue
        label = k[5:].replace("_", " ").title()
        cells.append(f'<div class="meta"><div class="k">{esc(label)}</div>'
                     f'<div class="v">{esc(v)}</div></div>')
    if cells:
        s = re.sub(r'<div class="meta-row">.*?\n      </div>',
                   lambda m: '<div class="meta-row">\n        '
                             + "\n        ".join(cells) + "\n      </div>",
                   s, count=1, flags=re.S)

    # --- about ------------------------------------------------------------
    if "about" in secs:
        paras = [p.strip() for p in secs["about"].split("\n\n") if p.strip()]
        blocks = [f'<p class="lead">{esc(para)}</p>' for para in paras]
        s = re.sub(r'(<p class="kicker">About [^<]*</p>\s*)(?:<p class="lead".*?</p>\s*)+',
                   lambda m: m.group(1) + "\n        ".join(blocks) + "\n      ", s, count=1, flags=re.S)
        s = re.sub(r'(<p class="kicker">About )[^<]*(</p>)', rf'\g<1>{esc(name)}\g<2>', s, count=1)

    # --- what's included --------------------------------------------------
    if "included" in secs:
        items = []
        for line in secs["included"].split("\n"):
            if "|" not in line: continue
            t, _, d = line.partition("|")
            items.append('<li><span class="tick">&#10003;</span><span>'
                         f'<span class="ft">{esc(t.strip())}</span><br>'
                         f'<span class="fd">{esc(d.strip())}</span></span></li>')
        s = re.sub(r'(<ul class="features">).*?(</ul>)',
                   lambda m: m.group(1) + "\n          " + "\n          ".join(items) + "\n        " + m.group(2),
                   s, count=1, flags=re.S)

    # --- about superfun ---------------------------------------------------
    if "superfun" in secs:
        s = re.sub(r'(About Superfun Games</p>\s*)<p class="lead"[^>]*>.*?</p>',
                   lambda m: m.group(1) + f'<p class="lead" style="max-width:760px">{esc(secs["superfun"])}</p>',
                   s, count=1, flags=re.S)

    # --- closing CTA ------------------------------------------------------
    if "cta" in secs:
        lines = [l for l in secs["cta"].split("\n") if l.strip()]
        if len(lines) >= 2:
            s = re.sub(r'(<div class="pitch">\s*<h2>)[^<]*(</h2>\s*<p>)[^<]*(</p>)',
                       rf'\g<1>{esc(lines[0])}\g<2>{esc(lines[1])}\g<3>', s, count=1, flags=re.S)

    # --- JSON-LD description follows the .md too ---------------------------
    if "description" in meta:
        s = re.sub(r'("@type":"SoftwareApplication".*?"description":)"[^"]*"',
                   lambda m: m.group(1) + '"' + meta["description"].replace('"', "'") + '"',
                   s, count=1, flags=re.S)

    # --- one-sheet download links -----------------------------------------
    if "onesheet" in meta:
        s = re.sub(r'href="[^"]*\.pdf"', f'href="{meta["onesheet"]}"', s)

    # --- head meta --------------------------------------------------------
    if "description" in meta:
        d = esc(meta["description"])
        for pat in [r'(<meta name="description" content=")[^"]*(")',
                    r'(<meta property="og:description" content=")[^"]*(")',
                    r'(<meta name="twitter:description" content=")[^"]*(")']:
            s = re.sub(pat, rf'\g<1>{d}\g<2>', s, count=1)

    page.write_text(s)
    print(f"  built forsale/{slug}/index.html from content/{slug}.md")

if __name__ == "__main__":
    print("building game pages...")
    for md in sorted(CONTENT.glob("*.md")):
        build(md.stem)
    print("done.")
