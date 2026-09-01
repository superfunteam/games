#!/usr/bin/env python3
"""
Generate /llms.txt and /llms-full.txt from the Markdown sources.

Usage:  python3 forsale/build-llms.py

llms.txt      a curated map of the site (llmstxt.org convention)
llms-full.txt the complete text of every page, inlined

Both are generated from forsale/content/*.md and forsale/blog/posts/*.md,
so they stay in sync with the pages.
"""
import re, pathlib, datetime

ROOT    = pathlib.Path(__file__).resolve().parents[1]
CONTENT = ROOT / "forsale" / "content"
POSTS   = ROOT / "forsale" / "blog" / "posts"
SITE    = "https://superfun.games"

def parse(path):
    raw = path.read_text()
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', raw, re.S)
    meta, body = {}, raw
    if m:
        for line in m.group(1).split("\n"):
            if ":" in line:
                k, _, v = line.partition(":")
                v = v.strip()
                if len(v) > 1 and v[0] == v[-1] and v[0] in "\"'":
                    v = v[1:-1]
                meta[k.strip()] = v
        body = m.group(2)
    meta["_body"] = body
    meta["_slug"] = path.stem
    return meta

def strip_md(t):
    t = re.sub(r'^:::.*$', '', t, flags=re.M)          # directive fences
    t = re.sub(r'\*\*([^*]+)\*\*', r'\1', t)
    t = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'\1', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (\2)', t)
    return re.sub(r'\n{3,}', '\n\n', t).strip()

games = [parse(p) for p in sorted(CONTENT.glob("*.md"))]
posts  = [p for p in (parse(p) for p in sorted(POSTS.glob("*.md")))
          if p.get("draft","").lower() != "true"]
posts.sort(key=lambda p: p.get("date",""), reverse=True)

# ---------------------------------------------------------------- llms.txt
L = []
L.append("# Superfun Games for News\n")
L.append("> Superfun Games builds complete, whitelabel daily games that newsrooms can "
         "launch under their own brand. Every game ships finished: your logo, your colors, "
         "your domain, no development work required.\n")
L.append("Superfun Games is a family game shop in Austin, Texas, founded by Clark and "
         "Angie Wimberly. Games can be taken off the shelf and rebranded, or designed from "
         "scratch for a specific newsroom. Puzzle production is AI assisted with a human "
         "editor approving everything that ships, which is what makes a daily cadence "
         "practical for a small team.\n")

L.append("## Games for sale\n")
for g in games:
    L.append(f"- [{g['name']}]({SITE}/forsale/{g['_slug']}/): {g.get('description','').strip()}")
L.append("")

L.append("## One-sheets (PDF)\n")
for g in games:
    if g.get("onesheet"):
        L.append(f"- [{g['name']} one-sheet]({SITE}/forsale/{g['_slug']}/{g['onesheet']})")
L.append("")

L.append("## Writing\n")
for p in posts:
    L.append(f"- [{p['title']}]({SITE}/forsale/blog/{p['_slug']}/): {p.get('excerpt','').strip()}")
L.append("")

L.append("## Contact\n")
L.append(f"- [Request a demo]({SITE}/forsale/#demo): opens the demo form, which asks for "
         "newsroom, audience size, and budget.")
L.append("- Superfun Games, Austin, Texas, USA\n")

L.append("## Optional\n")
L.append(f"- [Full site text]({SITE}/llms-full.txt): every page inlined as plain text.")
L.append(f"- [Sitemap]({SITE}/sitemap.xml)")

(ROOT / "llms.txt").write_text("\n".join(L) + "\n")
print("  wrote llms.txt")

# ---------------------------------------------------------------- llms-full.txt
F = ["# Superfun Games for News, full site text",
     f"# Generated from the Markdown sources. Canonical pages live under {SITE}/forsale/.",
     ""]
for g in games:
    F.append(f"\n\n---\n\n# {g['name']}")
    F.append(f"URL: {SITE}/forsale/{g['_slug']}/")
    F.append(f"Tagline: {g.get('tagline','')}")
    for k, v in g.items():
        if k.startswith("meta_"):
            F.append(f"{k[5:].replace('_',' ').title()}: {v}")
    if g.get("onesheet"):
        F.append(f"One-sheet: {SITE}/forsale/{g['_slug']}/{g['onesheet']}")
    F.append("")
    F.append(strip_md(g["_body"]))
for p in posts:
    F.append(f"\n\n---\n\n# {p['title']}")
    F.append(f"URL: {SITE}/forsale/blog/{p['_slug']}/")
    F.append(f"Published: {p.get('date','')}")
    F.append("")
    F.append(strip_md(p["_body"]))
(ROOT / "llms-full.txt").write_text("\n".join(F) + "\n")
print("  wrote llms-full.txt")
