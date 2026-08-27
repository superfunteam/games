#!/usr/bin/env python3
"""
Superfun Games for News - blog generator.

Usage:  python3 forsale/blog/build.py

Drop a Markdown file in forsale/blog/posts/ and re-run. It writes:
  forsale/blog/index.html            (post list)
  forsale/blog/<slug>/index.html     (each post)
  and refreshes the "latest post" block on forsale/index.html

Frontmatter (between --- lines):
  title:   Post title
  date:    2026-08-25          (ISO; controls ordering)
  excerpt: One-line summary used in listings and meta
  draft:   true                (optional, skips the post)

Markdown supported: ## / ###, paragraphs, - and 1. lists, > quotes,
---, **bold**, *italic*, [links](url), `code`.

Custom blocks:

  ::: quote cite="Who said it"
  The line worth pulling out.
  :::

  ::: figure src="/path.webp" alt="..." caption="..."
  :::

  ::: examples caption="Optional caption"
  /path-one.webp | Label one
  /path-two.webp | Label two
  :::

  ::: game flipwords
  :::
"""
import os, re, html, datetime, pathlib, hashlib

ROOT   = pathlib.Path(__file__).resolve().parents[2]      # repo root
BLOG   = ROOT / "forsale" / "blog"
POSTS  = BLOG / "posts"
SITE   = "https://superfun.games"

GAMES = {
  "flipwords": dict(name="FlipWords", url="/forsale/flipwords/", icon="/forsale/flipwords/assets/icon.png",
                    accent="#25988F", pitch="Flip, flop, and swap your tiles to solve clues from all sides."),
  "links":     dict(name="Links", url="/forsale/links/", icon="/forsale/links/assets/icon.png",
                    accent="#17845A", pitch="Each clue connects to the last, in this word puzzle with golf scoring."),
  "texas-two-step": dict(name="Texas Two Step", url="/forsale/texas-two-step/", icon="/forsale/texas-two-step/assets/icon.png",
                    accent="#FA6B16", pitch="Twist your tiles to match the clues in this word game with Texas twang."),
}

# ---------------------------------------------------------------- inline md
def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', t)
    return t

def attrs(s):
    return dict(re.findall(r'(\w+)="([^"]*)"', s))

# ---------------------------------------------------------------- blocks
def render_directive(kind, arg, body):
    a = attrs(arg)
    if kind == "quote":
        cite = a.get("cite", "")
        out = f'<blockquote class="pull"><p>{inline(" ".join(body).strip())}</p>'
        if cite: out += f'<cite>{inline(cite)}</cite>'
        return out + '</blockquote>'

    if kind == "figure":
        cap = a.get("caption", "")
        out  = ('<figure class="shot">'
                f'<button class="zoomable" type="button" aria-label="Expand image">'
                f'<img src="{a.get("src","")}" alt="{html.escape(a.get("alt",""))}" loading="lazy">'
                '<span class="zoom-hint" aria-hidden="true">'
                '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">'
                '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5M11 8v6M8 11h6"/></svg></span>'
                '</button>')
        if cap: out += f'<figcaption>{inline(cap)}</figcaption>'
        return out + '</figure>'

    if kind == "examples":
        cap = a.get("caption", "")
        items = []
        for line in body:
            if not line.strip(): continue
            src, _, label = line.partition("|")
            items.append(
              '<figure><button class="zoomable" type="button" aria-label="Expand image">'
              f'<img src="{src.strip()}" alt="{html.escape(label.strip())}" loading="lazy"></button>'
              + (f'<figcaption>{inline(label.strip())}</figcaption>' if label.strip() else '')
              + '</figure>')
        out = f'<div class="examples" data-count="{len(items)}">' + "".join(items) + '</div>'
        if cap: out = f'<div class="examples-wrap">{out}<p class="examples-cap">{inline(cap)}</p></div>'
        return out

    if kind == "game":
        g = GAMES.get(arg.strip())
        if not g: return ""
        return (f'<a class="game-feature" href="{g["url"]}" style="--accent:{g["accent"]}">'
                f'<img src="{g["icon"]}" alt="">'
                f'<span class="gf-copy"><span class="gf-kicker">Featured game</span>'
                f'<span class="gf-name">{g["name"]}</span>'
                f'<span class="gf-pitch">{html.escape(g["pitch"])}</span></span>'
                f'<span class="gf-go" aria-hidden="true">'
                '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" '
                'stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></svg>'
                '</span></a>')
    return ""

def render_body(md):
    out, lines, i = [], md.split("\n"), 0
    while i < len(lines):
        line = lines[i]
        if line.startswith(":::"):
            m = re.match(r':::\s*(\w+)\s*(.*)', line)
            kind, arg, body = m.group(1), m.group(2), []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(":::"):
                body.append(lines[i]); i += 1
            i += 1
            out.append(render_directive(kind, arg, body)); continue
        if not line.strip():
            i += 1; continue
        if line.startswith("### "):
            out.append(f"<h3>{inline(line[4:])}</h3>"); i += 1; continue
        if line.startswith("## "):
            out.append(f"<h2>{inline(line[3:])}</h2>"); i += 1; continue
        if line.strip() == "---":
            out.append("<hr>"); i += 1; continue
        if re.match(r'^\s*[-*] ', line):
            items = []
            while i < len(lines) and re.match(r'^\s*[-*] ', lines[i]):
                items.append(f"<li>{inline(re.sub(r'^\s*[-*] ', '', lines[i]))}</li>"); i += 1
            out.append("<ul>" + "".join(items) + "</ul>"); continue
        if re.match(r'^\s*\d+\. ', line):
            items = []
            while i < len(lines) and re.match(r'^\s*\d+\. ', lines[i]):
                items.append(f"<li>{inline(re.sub(r'^\s*\d+\. ', '', lines[i]))}</li>"); i += 1
            out.append("<ol>" + "".join(items) + "</ol>"); continue
        if line.startswith("> "):
            buf = []
            while i < len(lines) and lines[i].startswith("> "):
                buf.append(lines[i][2:]); i += 1
            out.append(f"<blockquote><p>{inline(' '.join(buf))}</p></blockquote>"); continue
        buf = []
        while i < len(lines) and lines[i].strip() and not lines[i].startswith((":::","#",">","---")) \
              and not re.match(r'^\s*([-*]|\d+\.) ', lines[i]):
            buf.append(lines[i]); i += 1
        out.append(f"<p>{inline(' '.join(buf))}</p>")
    return "\n      ".join(out)

# ---------------------------------------------------------------- parse
def parse(path):
    raw = path.read_text()
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', raw, re.S)
    meta, body = {}, raw
    if m:
        for l in m.group(1).split("\n"):
            if ":" in l:
                k, _, v = l.partition(":")
                v = v.strip()
                if len(v) > 1 and v[0] == v[-1] and v[0] in "\"'":
                    v = v[1:-1]
                meta[k.strip()] = v
        body = m.group(2)
    meta.setdefault("title", path.stem)
    meta.setdefault("date", "1970-01-01")
    meta.setdefault("excerpt", "")
    meta["slug"] = path.stem
    meta["body"] = body
    return meta

def pretty(d):
    try:
        return datetime.date.fromisoformat(d).strftime("%B %-d, %Y")
    except ValueError:
        return d


# ---------------------------------------------------------------- pixel cover
def _rng(seed_bytes):
    """Tiny deterministic PRNG so a slug always yields the same artwork."""
    state = int.from_bytes(hashlib.sha256(seed_bytes).digest()[:8], "big") or 1
    def nxt():
        nonlocal state
        state ^= (state << 13) & 0xFFFFFFFFFFFFFFFF
        state ^= state >> 7
        state ^= (state << 17) & 0xFFFFFFFFFFFFFFFF
        return state / 0xFFFFFFFFFFFFFFFF
    return nxt

def _hsl(h, s, l):
    h = h % 360; s = max(0, min(1, s)); l = max(0, min(1, l))
    c = (1 - abs(2*l - 1)) * s
    x = c * (1 - abs((h/60) % 2 - 1))
    m = l - c/2
    r, g, b = [(c,x,0),(x,c,0),(0,c,x),(0,x,c),(x,0,c),(c,0,x)][int(h//60) % 6]
    return "#%02X%02X%02X" % (round((r+m)*255), round((g+m)*255), round((b+m)*255))

def cover_svg(slug, cols=32, rows=24):
    """Hash-seeded pixel burst on a 4:3 grid. Every cell is the same size."""
    rnd = _rng(slug.encode())
    base = rnd() * 360
    tri  = rnd() < 0.45                      # duotone or tritone
    hues = [base, base + (150 + rnd()*60 if tri else 22 + rnd()*26)]
    if tri: hues.append(base + 22 + rnd()*26)

    bg    = _hsl(hues[0], 0.62 + rnd()*0.2, 0.44 + rnd()*0.1)
    mid   = _hsl(hues[1 % len(hues)], 0.60 + rnd()*0.22, 0.62 + rnd()*0.08)
    accent= _hsl(hues[-1], 0.58 + rnd()*0.24, 0.72 + rnd()*0.08)
    core  = "#FFFFFF"

    cx, cy = (cols-1)/2, (rows-1)/2
    maxd = (cx**2 + cy**2) ** 0.5
    cells = []
    for y in range(rows):
        for x in range(cols):
            d = ((x-cx)**2 + (y-cy)**2) ** 0.5 / maxd
            # dense in the middle, scattering toward the edges
            p = max(0.0, 1.0 - d*1.18)
            if rnd() > p ** 1.55:
                continue
            if   d < 0.20: fill = core
            elif d < 0.34: fill = core if rnd() < 0.72 else accent
            elif d < 0.52: fill = accent if rnd() < 0.68 else mid
            else:          fill = mid
            cells.append(f'<rect x="{x}" y="{y}" width="1" height="1" fill="{fill}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cols} {rows}" '
            f'preserveAspectRatio="xMidYMid slice" shape-rendering="crispEdges" role="img" '
            f'aria-label="Abstract pixel artwork">'
            f'<rect width="{cols}" height="{rows}" fill="{bg}"/>' + "".join(cells) + '</svg>')

# ---------------------------------------------------------------- template
FONTS = "".join(
  f'    @font-face{{font-family:"SF Pro Display";src:url("/forsale/fonts/SF-Pro-Display-{w}.woff2") '
  f'format("woff2");font-weight:{n};font-style:normal;font-display:swap}}\n'
  for w, n in [("Light",300),("Regular",400),("Medium",500),("Semibold",600),("Bold",700)])

BASE_CSS = FONTS + """    @view-transition{navigation:auto}
    ::view-transition-old(root){animation:vt-out .18s ease both}
    ::view-transition-new(root){animation:vt-in .26s ease both}
    @keyframes vt-out{to{opacity:0}}
    @keyframes vt-in{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
    @media(prefers-reduced-motion:reduce){::view-transition-old(root),::view-transition-new(root){animation:none}}
    :root{--ink:#14161A;--muted:#6B7280;--line:#E7E9ED;--paper:#FFFFFF;--panel:#F7F8FA;
      --surface:#FFFFFF;--strip:#F4F4F1;--green:#00E07A;--green-ink:#04351F;--maxw:1180px}
    :root.dark{--ink:#F3F4F6;--muted:#9AA1AC;--line:#23262B;--paper:#0B0C0E;--panel:#131519;
      --surface:#171B21;--strip:#101215;--green:#00FF85}
    *{box-sizing:border-box}
    html{scroll-behavior:smooth}
    body{margin:0;font-family:"SF Pro Display",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      color:var(--ink);background:var(--paper);-webkit-font-smoothing:antialiased;line-height:1.55}
    h1,h2,h3{font-family:"SF Pro Display",sans-serif}
    a{color:inherit;text-decoration:none}
    img{max-width:100%;display:block}
    .wrap{max-width:var(--maxw);margin:0 auto;padding:0 24px}
    header.site{position:sticky;top:0;z-index:50;background:color-mix(in srgb,var(--paper) 88%,transparent);
      backdrop-filter:saturate(1.2) blur(8px);border-bottom:1px solid var(--line)}
    .site-inner{display:flex;align-items:center;justify-content:space-between;height:64px}
    .brand{display:flex;align-items:center;gap:10px;font-family:"SF Pro Display";font-weight:700;font-size:18px}
    .brand img{width:34px;height:34px} .brand-suffix{font-weight:500}
    @media(max-width:640px){.brand-name{display:none}}
    .brand .dark-logo{display:none}
    :root.dark .brand .light-logo{display:none}
    :root.dark .brand .dark-logo{display:block}
    .head-actions{display:flex;align-items:center;gap:12px}
    .icon-btn{display:inline-flex;align-items:center;justify-content:center;width:38px;height:38px;
      border-radius:10px;border:1px solid var(--line);background:transparent;color:var(--ink);cursor:pointer;opacity:.7}
    .icon-btn:hover{opacity:1}
    .btn-demo{display:inline-flex;align-items:center;gap:8px;font-family:"SF Pro Display";font-weight:700;
      font-size:15px;padding:10px 18px;border-radius:12px;background:#00E07A;color:#04351F;
      border:1px solid transparent;cursor:pointer;transition:filter .15s ease,transform .1s ease}
    :root.dark .btn-demo{background:#00FF85}
    .btn-demo:hover{filter:brightness(.95)}
    footer.site{border-top:1px solid var(--line);padding:26px 0;margin-top:8px}
    .foot-inner{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;
      color:var(--muted);font-size:14px}
    .foot-inner a:hover{color:var(--ink)}
"""

POST_CSS = """    .post{padding:56px 0 20px}
    .post-head{max-width:760px}
    .eyebrow{font-family:"SF Pro Display";font-weight:600;font-size:13px;letter-spacing:2px;
      text-transform:uppercase;color:var(--muted);margin:0 0 12px}
    .post h1{font-size:clamp(32px,5vw,50px);line-height:1.06;letter-spacing:-1.4px;margin:0 0 14px;font-weight:700}
    .post-meta{color:var(--muted);font-size:15px;margin:0}
    .post-cover{margin:26px 0 6px;border-radius:18px;overflow:hidden;aspect-ratio:4/3;max-width:520px}
    .post-cover svg{width:100%;height:100%;display:block}
    .post-body{max-width:760px;padding:8px 0 40px;font-size:18px;line-height:1.65}
    .post-body h2{font-size:clamp(23px,2.6vw,29px);letter-spacing:-.5px;margin:44px 0 12px}
    .post-body h3{font-size:20px;margin:32px 0 8px}
    .post-body p{margin:0 0 20px}
    .post-body ul,.post-body ol{margin:0 0 22px;padding-left:22px}
    .post-body li{margin:0 0 10px}
    .post-body hr{border:0;border-top:1px solid var(--line);margin:38px 0}
    .post-body a{color:var(--ink);text-decoration:underline;text-decoration-thickness:1.5px;text-underline-offset:3px}
    .post-body a:hover{color:var(--muted)}
    .post-body code{background:var(--strip);padding:2px 6px;border-radius:5px;font-size:.9em}
    /* pull quote */
    .pull{margin:40px 0;padding:0}
    .pull p{font-size:clamp(22px,2.6vw,28px);line-height:1.35;letter-spacing:-.4px;font-weight:600;margin:0}
    .pull cite{display:block;margin-top:12px;font-style:normal;font-size:15px;color:var(--muted)}
    /* figure + zoom */
    .shot{margin:34px 0}
    .shot figcaption,.examples figcaption,.examples-cap{color:var(--muted);font-size:14px;margin-top:10px;text-align:center}
    .zoomable{display:block;width:100%;padding:0;border:0;background:var(--strip);border-radius:16px;
      overflow:hidden;cursor:zoom-in;position:relative;line-height:0}
    .zoomable img{width:100%;height:auto}
    .zoom-hint{position:absolute;right:12px;bottom:12px;width:34px;height:34px;border-radius:50%;
      background:rgba(0,0,0,.55);color:#fff;display:flex;align-items:center;justify-content:center;opacity:0;
      transition:opacity .2s ease}
    .zoom-hint svg{width:17px;height:17px}
    .zoomable:hover .zoom-hint,.zoomable:focus-visible .zoom-hint{opacity:1}
    /* examples row */
    .examples{display:grid;gap:14px;margin:34px 0 0;grid-template-columns:repeat(auto-fit,minmax(0,1fr))}
    .examples figure{margin:0}
    .examples .zoomable{background:var(--strip)}
    .examples-wrap{margin:34px 0}
    .examples-wrap .examples{margin:0}
    @media(max-width:600px){.examples{grid-template-columns:1fr 1fr}}
    /* featured game */
    .game-feature{display:flex;align-items:center;gap:16px;margin:36px 0;padding:18px 20px;border-radius:18px;
      background:var(--strip);transition:transform .18s ease,box-shadow .22s ease}
    .game-feature:hover{transform:translateY(-3px);box-shadow:0 20px 40px -26px rgba(0,0,0,.45)}
    .game-feature img{width:60px;height:60px;border-radius:15px;flex:0 0 auto}
    .gf-copy{display:flex;flex-direction:column;gap:2px;min-width:0}
    .gf-kicker{font-size:11.5px;letter-spacing:1.6px;text-transform:uppercase;color:var(--accent);font-weight:700}
    .gf-name{font-size:20px;font-weight:700;letter-spacing:-.3px}
    .gf-pitch{font-size:14.5px;color:var(--muted);line-height:1.4}
    .gf-go{margin-left:auto;color:var(--accent);flex:0 0 auto}
    .gf-go svg{width:22px;height:22px}
    @media(max-width:560px){.game-feature{gap:13px;padding:16px}.game-feature img{width:48px;height:48px}.gf-go{display:none}}
    /* lightbox */
    .lb{position:fixed;inset:0;z-index:120;background:rgba(8,10,14,.94);display:flex;align-items:center;
      justify-content:center;opacity:0;visibility:hidden;transition:opacity .22s ease,visibility 0s linear .22s;
      touch-action:none;overscroll-behavior:contain}
    .lb.open{opacity:1;visibility:visible;transition:opacity .22s ease}
    .lb img{max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain;
      transform-origin:0 0;cursor:zoom-in;user-select:none;-webkit-user-drag:none}
    .lb.zoomed img{cursor:grab}
    .lb-close{position:absolute;top:14px;right:14px;width:44px;height:44px;border-radius:50%;border:0;
      background:rgba(255,255,255,.14);color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center}
    .lb-close:hover{background:rgba(255,255,255,.24)}
    .lb-tip{position:absolute;bottom:18px;left:50%;transform:translateX(-50%);color:rgba(255,255,255,.7);
      font-size:13px;pointer-events:none}
    /* post nav */
    .post-nav{border-top:1px solid var(--line);padding:26px 0 60px;display:flex;justify-content:space-between;
      gap:16px;flex-wrap:wrap;font-weight:600}
    .post-nav a{color:var(--muted)} .post-nav a:hover{color:var(--ink)}
"""

INDEX_CSS = """    .blog-hero{padding:60px 0 26px}
    .blog-hero .eyebrow{font-family:"SF Pro Display";font-weight:600;font-size:13px;letter-spacing:2px;
      text-transform:uppercase;color:var(--muted);margin:0 0 10px}
    .blog-hero h1{font-size:clamp(34px,5.5vw,52px);line-height:1.04;letter-spacing:-1.5px;margin:0 0 12px;font-weight:700}
    .blog-hero p{color:var(--muted);font-size:clamp(17px,1.7vw,20px);margin:0;max-width:62ch}
    .posts{padding:14px 0 70px;display:grid;gap:2px}
    .post-row{display:flex;gap:22px;align-items:center;padding:24px 0;border-top:1px solid var(--line)}
    .row-thumb{flex:0 0 150px;aspect-ratio:4/3;border-radius:12px;overflow:hidden}
    .row-thumb svg{width:100%;height:100%;display:block}
    .row-copy{min-width:0}
    @media(max-width:640px){.post-row{gap:14px}.row-thumb{flex-basis:96px}}
    .post-row:last-child{border-bottom:1px solid var(--line)}
    .post-row .d{font-size:13.5px;letter-spacing:1.4px;text-transform:uppercase;color:var(--muted);font-weight:600}
    .post-row h2{font-size:clamp(22px,2.6vw,30px);letter-spacing:-.5px;margin:6px 0 8px;line-height:1.18}
    .post-row p{color:var(--muted);font-size:16.5px;margin:0;max-width:70ch}
    .post-row:hover h2{color:var(--muted)}
"""

def head(title, desc, canon, extra_css, og_img=f"{SITE}/forsale/ogimage.png"):
    return f"""<!DOCTYPE html>
<html lang="en-US">
<head>
  <meta charset="UTF-8">
  <title>{html.escape(title)}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#FFFFFF">
  <link rel="icon" href="/wp-content/themes/superfun-games/images/logo-superfun.svg">
  <link rel="canonical" href="{canon}">
  <meta name="description" content="{html.escape(desc)}">
  <meta property="og:url" content="{canon}">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(desc)}">
  <meta property="og:image" content="{og_img}">
  <meta property="og:site_name" content="Superfun Games">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:locale" content="en_US">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{html.escape(title)}">
  <meta name="twitter:description" content="{html.escape(desc)}">
  <meta name="twitter:image" content="{og_img}">
  <style>
{BASE_CSS}{extra_css}  </style>
</head>
<body>
  <header class="site">
    <div class="wrap site-inner">
      <a class="brand" href="/forsale/">
        <img class="light-logo" src="/wp-content/themes/superfun-games/images/logo-superfun.svg" alt="Superfun Games">
        <img class="dark-logo" src="/wp-content/themes/superfun-games/images/logo-superfun-dark.svg" alt="Superfun Games">
        <span><span class="brand-name">Superfun&nbsp;Games </span><span class="brand-suffix">for&nbsp;News</span></span>
      </a>
      <div class="head-actions">
        <button id="theme-toggle" class="icon-btn" aria-label="Toggle dark mode"></button>
        <a class="btn-demo js-mailto" data-u="clark" data-d="superfun.team">Contact</a>
      </div>
    </div>
  </header>
"""

FOOT = """  <footer class="site">
    <div class="wrap foot-inner">
      <span>&copy; Superfun Games &middot; Austin, TX</span>
      <span><a href="/forsale/">Games for sale</a> &middot; <a href="/forsale/blog/">Blog</a> &middot;
        <a class="js-email" data-u="clark" data-d="superfun.team">email us</a></span>
    </div>
  </footer>
  <script>
    (function(){var r=document.documentElement;
      function apply(d){r.classList.toggle('dark',d);
        var m=document.querySelector('meta[name="theme-color"]');if(m)m.setAttribute('content',d?'#0B0C0E':'#FFFFFF');
        var b=document.getElementById('theme-toggle');
        b.innerHTML=d?'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" width="18" height="18"><path d="M14.438 10.148c.19-.425-.321-.787-.748-.601A5.5 5.5 0 0 1 6.453 2.31c.186-.427-.176-.938-.6-.748a6.501 6.501 0 1 0 8.585 8.586Z"/></svg>':'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" width="18" height="18"><path d="M8 1a.75.75 0 0 1 .75.75v1.5a.75.75 0 0 1-1.5 0v-1.5A.75.75 0 0 1 8 1ZM10.5 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0ZM12.95 4.11a.75.75 0 1 0-1.06-1.06l-1.062 1.06a.75.75 0 0 0 1.061 1.062l1.06-1.061ZM15 8a.75.75 0 0 1-.75.75h-1.5a.75.75 0 0 1 0-1.5h1.5A.75.75 0 0 1 15 8ZM11.89 12.95a.75.75 0 0 0 1.06-1.06l-1.06-1.062a.75.75 0 0 0-1.062 1.061l1.061 1.06ZM8 12a.75.75 0 0 1 .75.75v1.5a.75.75 0 0 1-1.5 0v-1.5A.75.75 0 0 1 8 12ZM5.172 11.89a.75.75 0 0 0-1.061-1.062L3.05 11.89a.75.75 0 1 0 1.06 1.06l1.06-1.06ZM4 8a.75.75 0 0 1-.75.75h-1.5a.75.75 0 0 1 0-1.5h1.5A.75.75 0 0 1 4 8ZM4.11 5.172A.75.75 0 0 0 5.173 4.11L4.11 3.05a.75.75 0 1 0-1.06 1.06l1.06 1.06Z"/></svg>';}
      var d=localStorage.theme==='dark'||(!localStorage.theme&&matchMedia('(prefers-color-scheme: dark)').matches);
      apply(d);document.getElementById('theme-toggle').addEventListener('click',function(){
        d=!r.classList.contains('dark');localStorage.theme=d?'dark':'light';apply(d);});})();
    (function(){['.js-email','.js-mailto'].forEach(function(sel){
      [].forEach.call(document.querySelectorAll(sel),function(el){
        var e=(el.dataset.u||'')+'@'+(el.dataset.d||'');
        el.setAttribute('href','mailto:'+e+'?subject=Superfun%20Games%20for%20News');
        if(sel==='.js-email') el.textContent=e;});});})();
  </script>
</body>
</html>
"""

LIGHTBOX_JS = """  <div class="lb" id="lb" role="dialog" aria-modal="true" aria-label="Expanded image" hidden>
    <button class="lb-close" id="lbClose" aria-label="Close">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"
        stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg></button>
    <img id="lbImg" alt="">
    <span class="lb-tip" id="lbTip">Tap image to zoom</span>
  </div>
  <script>
  (function(){
    var lb=document.getElementById('lb'),img=document.getElementById('lbImg'),tip=document.getElementById('lbTip');
    if(!lb) return;
    var scale=1,tx=0,ty=0,last=null,opener=null,hide;
    function apply(){img.style.transform='translate('+tx+'px,'+ty+'px) scale('+scale+')';
      lb.classList.toggle('zoomed',scale>1);}
    function reset(){scale=1;tx=0;ty=0;apply();}
    function open(src,alt,btn){
      opener=btn;clearTimeout(hide);lb.hidden=false;img.src=src;img.alt=alt||'';
      document.body.style.overflow='hidden';reset();
      requestAnimationFrame(function(){lb.classList.add('open');});
      tip.textContent = matchMedia('(pointer:coarse)').matches ? 'Pinch or double-tap to zoom' : 'Click image to zoom';
    }
    function close(){lb.classList.remove('open');document.body.style.overflow='';
      hide=setTimeout(function(){lb.hidden=true;img.src='';reset();},240);
      if(opener&&opener.focus)opener.focus();}
    [].forEach.call(document.querySelectorAll('.zoomable'),function(b){
      b.addEventListener('click',function(){var i=b.querySelector('img');open(i.currentSrc||i.src,i.alt,b);});});
    document.getElementById('lbClose').addEventListener('click',close);
    lb.addEventListener('click',function(e){if(e.target===lb)close();});
    document.addEventListener('keydown',function(e){if(!lb.hidden&&e.key==='Escape')close();});
    // click / double-tap to toggle zoom around the pointer
    img.addEventListener('click',function(e){
      e.stopPropagation();
      var r=img.getBoundingClientRect();
      if(scale>1){reset();return;}
      scale=2.4;
      tx=(r.width/2-(e.clientX-r.left))*(scale-1)/scale*1.0;
      ty=(r.height/2-(e.clientY-r.top))*(scale-1)/scale*1.0;
      apply();
    });
    // drag to pan when zoomed (mouse + touch)
    function start(x,y){last={x:x,y:y};}
    function move(x,y){if(!last||scale===1)return;tx+=x-last.x;ty+=y-last.y;last={x:x,y:y};apply();}
    function end(){last=null;}
    img.addEventListener('mousedown',function(e){if(scale>1){e.preventDefault();start(e.clientX,e.clientY);}});
    window.addEventListener('mousemove',function(e){move(e.clientX,e.clientY);});
    window.addEventListener('mouseup',end);
    img.addEventListener('touchstart',function(e){if(e.touches.length===1&&scale>1)start(e.touches[0].clientX,e.touches[0].clientY);},{passive:true});
    img.addEventListener('touchmove',function(e){if(e.touches.length===1&&scale>1){e.preventDefault();move(e.touches[0].clientX,e.touches[0].clientY);}},{passive:false});
    img.addEventListener('touchend',end);
    var lastTap=0;
    img.addEventListener('touchend',function(e){
      var now=Date.now();
      if(now-lastTap<300){ if(scale>1){reset();} else {scale=2.4;apply();} }
      lastTap=now;
    });
  })();
  </script>
"""

# ---------------------------------------------------------------- write
def build():
    posts = [parse(p) for p in sorted(POSTS.glob("*.md"))]
    posts = [p for p in posts if p.get("draft","").lower() != "true"]
    posts.sort(key=lambda p: p["date"], reverse=True)
    if not posts:
        print("no posts found"); return

    for i, p in enumerate(posts):
        canon = f"{SITE}/forsale/blog/{p['slug']}/"
        newer = posts[i-1] if i > 0 else None
        older = posts[i+1] if i+1 < len(posts) else None
        nav = '<div class="wrap post-nav">'
        nav += f'<a href="/forsale/blog/{older["slug"]}/">&larr; {html.escape(older["title"])}</a>' if older else '<span></span>'
        nav += f'<a href="/forsale/blog/{newer["slug"]}/">{html.escape(newer["title"])} &rarr;</a>' if newer else '<span></span>'
        nav += '</div>'
        page = (head(f"{p['title']} | Superfun Games for News", p["excerpt"], canon, POST_CSS)
          + f"""  <article class="post">
    <div class="wrap post-head">
      <p class="eyebrow"><a href="/forsale/blog/">Blog</a></p>
      <h1>{html.escape(p['title'])}</h1>
      <p class="post-meta">{pretty(p['date'])}</p>
    </div>
    <div class="wrap post-head"><div class="post-cover">{cover_svg(p['slug'])}</div></div>
    <div class="wrap post-body">
      {render_body(p['body'])}
    </div>
  </article>
{nav}
{LIGHTBOX_JS}""" + FOOT)
        out = BLOG / p["slug"]
        out.mkdir(parents=True, exist_ok=True)
        (out / "cover.svg").write_text(cover_svg(p["slug"]))
        (out / "index.html").write_text(page)
        print(f"  wrote blog/{p['slug']}/index.html")

    rows = "".join(
      f'''        <a class="post-row" href="/forsale/blog/{p["slug"]}/">
          <span class="row-thumb">{cover_svg(p["slug"], 20, 15)}</span>
          <span class="row-copy">
            <span class="d">{pretty(p["date"])}</span>
            <h2>{html.escape(p["title"])}</h2>
            <p>{html.escape(p["excerpt"])}</p>
          </span>
        </a>\n''' for p in posts)
    idx = (head("Blog | Superfun Games for News",
                "Notes on daily games, newsrooms, and what makes a puzzle worth sharing.",
                f"{SITE}/forsale/blog/", INDEX_CSS)
      + f"""  <section class="blog-hero">
    <div class="wrap">
      <p class="eyebrow">Blog</p>
      <h1>Notes from the game shop.</h1>
      <p>What we are learning about daily games, newsrooms, and the habits that keep readers coming back.</p>
    </div>
  </section>
  <section class="posts">
    <div class="wrap">
{rows}    </div>
  </section>
""" + FOOT)
    (BLOG / "index.html").write_text(idx)
    print("  wrote blog/index.html")

    # refresh the latest-post block on the /forsale homepage
    latest = posts[0]
    home = ROOT / "forsale" / "index.html"
    s = home.read_text()
    recent = posts[1:5] if len(posts) > 1 else []
    L = latest
    rows = "".join(
      f'''          <a class="c-row" href="/forsale/blog/{r["slug"]}/">
            <span class="c-num">{i+1:02d}</span>
            <span class="c-copy"><span class="c-title">{html.escape(r["title"])}</span>
              <span class="j-date">{pretty(r["date"])}</span></span>
          </a>\n''' for i, r in enumerate(recent))
    block = f'''<!-- BLOG:LATEST -->
  <section class="journal jC">
    <div class="wrap">
      <div class="c-grid">
        <a class="c-feature" href="/forsale/blog/{L["slug"]}/">
          <span class="c-cover">{cover_svg(L["slug"], 20, 15)}</span>
          <span class="c-kicker">Latest post</span>
          <span class="c-ftitle">{html.escape(L["title"])}</span>
          <span class="c-fex">{html.escape(L["excerpt"])}</span>
          <span class="j-more">Read the post
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"
              stroke-linejoin="round"><path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></svg></span>
        </a>
        <div class="c-left">
          <div class="j-head"><h2>From the journal</h2><a class="j-all" href="/forsale/blog/">All posts</a></div>
{rows}        </div>
      </div>
    </div>
  </section>
  <!-- /BLOG:LATEST -->'''
    if "<!-- BLOG:LATEST -->" in s:
        s = re.sub(r'<!-- BLOG:LATEST -->.*?<!-- /BLOG:LATEST -->', block, s, flags=re.S)
        home.write_text(s)
        print("  refreshed latest-post block on forsale/index.html")
    else:
        print("  ! marker <!-- BLOG:LATEST --> not found on forsale/index.html")

if __name__ == "__main__":
    print("building blog...")
    build()
    print("done.")
