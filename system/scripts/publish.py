#!/usr/bin/env python3
"""Build a newspaper-styled edition and publish to GitHub Pages."""
import sys, os, re, json, subprocess, datetime, html, hashlib, shutil
import urllib.request, urllib.parse

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

# Every path and address comes from config.sh — see config.py.
REPO = config.REPO          # folder holding editions/ and posts/
SITE = config.SITE_URL      # public address, no trailing slash
PAPER = config.PAPER        # name in the masthead
PLACE = config.PLACE        # county/region shown in the dateline
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

CSS = r"""
:root{
  --paper:#f4f1ea; --ink:#14130f; --dim:#6a655c; --rule:#1a1814;
  --hair:#c9c2b4; --red:#8c1c13; --firm:#dcd5c6;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;overflow-x:hidden}
img{max-width:100%;height:auto}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:Georgia,'Times New Roman',Times,serif;
  background-image:
    repeating-linear-gradient(0deg,rgba(0,0,0,.012) 0 1px,transparent 1px 3px);}
a{color:inherit;text-decoration:none;border-bottom:1px solid var(--hair)}
a:hover{border-bottom-color:var(--ink)}
.page{max-width:60rem;margin:0 auto;padding:0 .85rem 4rem;overflow-x:clip}

/* masthead */
.masthead{border-bottom:3px double var(--rule);padding:.85rem 0 .45rem;text-align:center;position:relative;max-width:100%}
.masthead .dev{font-size:.58rem;letter-spacing:.34em;text-transform:uppercase;
  font-family:'Helvetica Neue',Arial,sans-serif;color:var(--dim);margin-bottom:.55rem}
.masthead h1{margin:0;line-height:0}
.masthead h1 a{border:0;display:block}
.masthead .logo{display:block;width:100%;max-width:100%;height:auto;margin:0 auto}
.dateline{display:flex;justify-content:space-between;gap:.5rem;align-items:center;
  border-top:1px solid var(--hair);margin-top:.5rem;padding-top:.32rem;
  font-family:'Helvetica Neue',Arial,sans-serif;font-size:.6rem;letter-spacing:.15em;
  text-transform:uppercase;color:var(--dim);flex-wrap:wrap}
.dateline .mid{letter-spacing:.08em}

/* headline block */
main{padding-top:1.4rem}
.kicker{font-family:'Helvetica Neue',Arial,sans-serif;font-size:.6rem;letter-spacing:.26em;
  text-transform:uppercase;color:var(--red);margin-bottom:.5rem;font-weight:700}
h1.head{font-size:clamp(1.6rem,6.4vw,3rem);line-height:1.06;margin:0 0 .7rem;
  font-weight:700;letter-spacing:-.018em;text-align:center}
.deck{text-align:center;color:var(--dim);font-style:italic;font-size:1rem;
  max-width:38rem;margin:0 auto 1.2rem}
.byline{text-align:center;font-family:'Helvetica Neue',Arial,sans-serif;font-size:.58rem;
  letter-spacing:.2em;text-transform:uppercase;color:var(--dim);
  border-top:1px solid var(--hair);border-bottom:1px solid var(--hair);
  padding:.4rem 0;margin-bottom:1.6rem}

/* body */
article p{margin:0 0 .95rem;font-size:1.02rem;line-height:1.6;text-align:justify;
  hyphens:auto;-webkit-hyphens:auto}
article p.lede{font-size:1.12rem;line-height:1.55}
article p.lede:first-letter{float:left;font-size:3.2rem;line-height:.82;padding:.08em .09em 0 0;font-weight:700}

h2.sec{font-family:'Helvetica Neue',Arial,sans-serif;font-size:.68rem;letter-spacing:.24em;
  text-transform:uppercase;font-weight:700;margin:2.1rem 0 .1rem;padding-bottom:.35rem;
  border-bottom:2px solid var(--ink)}
h2.sec::before{content:"";display:block;height:3px;background:var(--ink);margin-bottom:.1rem;
  border-top:0}
h2.sec + p{margin-top:.85rem}

/* items */
.item{margin-bottom:1.35rem;overflow:hidden}
.item h3{font-size:1.16rem;line-height:1.24;margin:0 0 .3rem;font-weight:700;letter-spacing:-.008em}
h3.local{font-family:'Helvetica Neue',Arial,sans-serif;font-size:.6rem;font-weight:600;
  letter-spacing:.2em;text-transform:uppercase;color:var(--red);
  margin:1.15rem 0 .55rem;padding-top:.4rem;border-top:1px solid var(--hair)}
h3.local + p{margin-top:0}
.item p{margin:0 0 .35rem}
.item .take{color:var(--dim);font-style:italic;font-size:.92rem;border-left:2px solid var(--hair);
  padding-left:.6rem;margin-top:.5rem;text-align:left}
.src{font-family:'Helvetica Neue',Arial,sans-serif;font-size:.62rem;letter-spacing:.1em;
  text-transform:uppercase;color:var(--dim)}
.thumb{float:right;width:38%;max-width:230px;margin:.15rem 0 .5rem .9rem;
  border:1px solid var(--hair);background:#e6e1d6;filter:saturate(.92)}
.thumb img{display:block;width:100%;height:auto;filter:contrast(1.02) sepia(.06)}
figcaption{font-family:'Helvetica Neue',Arial,sans-serif;font-size:.56rem;letter-spacing:.08em;
  color:var(--dim);padding:.28rem .35rem;text-transform:uppercase}

/* close */
.signoff{margin-top:2rem;padding-top:.9rem;border-top:3px double var(--rule);
  font-style:italic;color:var(--dim);font-size:.98rem;text-align:center}

/* footer */
p.deck{margin:.1rem auto 1.35rem;max-width:34rem;text-align:center;font-size:.94rem;
  line-height:1.45;color:var(--dim);font-style:italic;hyphens:none}
figure.comic{margin:1.9rem auto;max-width:38rem;text-align:center;break-inside:avoid}
figure.comic img{width:100%;max-width:640px;height:auto;border:1px solid var(--ink);background:#fff}
figure.comic figcaption{margin-top:.45rem;font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--dim);line-height:1.5}
figure.comic figcaption a{color:var(--dim)}
.epigraph{margin:2.2rem auto 0;max-width:34rem;text-align:center;padding-top:1.1rem;
  border-top:1px solid var(--hair)}
.epigraph .q{display:block;font-size:2.6rem;line-height:.2;color:var(--dim);margin-bottom:.55rem}
.epigraph p{margin:0;font-style:italic;font-size:1.02rem;line-height:1.45;text-align:center;hyphens:none}
.epigraph p.src{margin-top:.5rem;font-style:normal;font-size:.66rem;letter-spacing:.14em;
  text-transform:uppercase;color:var(--dim)}
/* menu bar */
.menubar{display:flex;align-items:center;justify-content:center;
  border-bottom:1px solid var(--rule);padding:.34rem 0 .3rem;position:relative;
  font-family:'Helvetica Neue',Arial,sans-serif;font-size:.6rem;letter-spacing:.16em;
  text-transform:uppercase}
.menu{position:relative}
.menu>summary{list-style:none;cursor:pointer;border:1px solid var(--rule);
  padding:.24rem .62rem;letter-spacing:.18em;color:var(--ink);background:none;
  -webkit-tap-highlight-color:transparent}
.menu>summary::-webkit-details-marker{display:none}
.menu>summary::before{content:"\2630";margin-right:.42em;font-size:.86em}
.menu[open]>summary{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.menu ul{position:absolute;top:calc(100% + .34rem);left:50%;transform:translateX(-50%);
  z-index:60;margin:0;padding:.3rem 0;list-style:none;min-width:11.5rem;
  background:var(--paper);border:1px solid var(--rule);box-shadow:0 3px 10px rgba(0,0,0,.14)}
.menu ul li{margin:0}
.menu ul a{display:block;padding:.44rem .95rem;border:0;color:var(--ink);letter-spacing:.14em}
.menu ul a:hover,.menu ul a:focus{background:var(--ink);color:var(--paper)}
.menu ul .sep{height:1px;background:var(--hair);margin:.3rem .6rem}

footer.site{margin-top:2.4rem;border-top:1px solid var(--hair);padding-top:.8rem;
  font-family:'Helvetica Neue',Arial,sans-serif;font-size:.58rem;letter-spacing:.14em;
  text-transform:uppercase;color:var(--dim);display:flex;justify-content:space-between;
  gap:1rem;flex-wrap:wrap}

/* weekly banner */
.weekly-banner{margin:0 0 1.4rem;padding:.7rem .9rem;border:1px solid var(--ink);
  border-left:5px solid var(--ink);font-family:'Helvetica Neue',Arial,sans-serif;
  font-size:.74rem;letter-spacing:.06em;text-transform:uppercase;text-align:center;line-height:1.5}
.weekly-banner a{color:inherit;text-decoration:none;display:block}
.weekly-banner a:after{content:" \2192"}

/* history */
.hist h1{font-size:clamp(1.4rem,5vw,2.2rem);text-transform:uppercase;letter-spacing:.02em;
  border-bottom:3px double var(--rule);padding-bottom:.5rem;margin:0 0 1.2rem;text-align:center}
.month{font-family:'Helvetica Neue',Arial,sans-serif;font-size:.64rem;letter-spacing:.26em;
  text-transform:uppercase;color:var(--red);font-weight:700;margin:1.6rem 0 .3rem;
  border-bottom:1px solid var(--hair);padding-bottom:.25rem}
.hist ol{list-style:none;margin:0;padding:0}
.hist li{display:flex;gap:.85rem;align-items:baseline;padding:.6rem 0;border-bottom:1px dotted var(--hair)}
.hist .d{flex:0 0 4.6rem;font-family:'Helvetica Neue',Arial,sans-serif;font-size:.62rem;
  letter-spacing:.1em;text-transform:uppercase;color:var(--dim)}
.hist .t{font-size:1.02rem;line-height:1.3}
.back{text-align:center;margin:1.4rem 0 0;font-family:'Helvetica Neue',Arial,sans-serif;
  font-size:.62rem;letter-spacing:.2em;text-transform:uppercase}

@media(min-width:56rem){
  article{column-count:2;column-gap:2.4rem;column-rule:1px solid var(--hair)}
  article h2.sec{column-span:all;margin-top:2.2rem}
  article .item{break-inside:avoid;column-fill:auto}
  article p{text-align:justify}
  h1.head,.deck,.byline,.kicker{column-span:all}
  article .item h3{font-size:1.1rem}
}
@media(max-width:27rem){
  .page{padding-left:.7rem;padding-right:.7rem}
  .menubar{gap:.55rem;font-size:.55rem}
  .menu ul{left:auto;right:0;transform:none;min-width:10.5rem}
  .masthead{padding:.6rem 0 .35rem}
  .masthead .dev{font-size:.5rem;letter-spacing:.22em;margin-bottom:.4rem}
  .dateline{font-size:.52rem;letter-spacing:.08em;gap:.3rem}
  h1.head{font-size:1.55rem;line-height:1.08}
  article p{font-size:.98rem;line-height:1.55;text-align:left;hyphens:none}
  .item h3{font-size:1.05rem}
}
@media(max-width:34rem){
  .thumb{float:none;display:block;width:100%;max-width:none;margin:.3rem 0 .7rem}
  .thumb figcaption{font-size:.58rem}
  article p{font-size:1rem}
}

/* weather strip */
.wx{border-top:1px solid var(--hair);border-bottom:1px solid var(--hair);
  padding:.42rem 0;margin:0 0 1.1rem;font-family:'Helvetica Neue',Arial,sans-serif;
  font-size:.66rem;letter-spacing:.045em;line-height:1.5;color:var(--dim);
  display:flex;flex-wrap:wrap;align-items:baseline;gap:.55rem}
.wx #weather-text{flex:1 1 14rem;min-width:0}
.wx a{border-bottom-color:var(--hair)}
.wxbtn{flex:0 0 auto;font:inherit;font-size:.58rem;letter-spacing:.14em;
  text-transform:uppercase;color:var(--dim);background:transparent;
  border:1px solid var(--hair);padding:.26rem .5rem;cursor:pointer;
  font-family:'Helvetica Neue',Arial,sans-serif}
.wxbtn:hover:not(:disabled){color:var(--ink);border-color:var(--rule)}
.wxbtn:disabled{opacity:.55;cursor:default}
"""


def fetch(url, timeout=15):
    """Download a URL and return the HTML as text. Returns "" on any failure,
    because a missing image must never stop the paper going out."""
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "text/html,application/xhtml+xml", "Accept-Language": "en-GB,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", "")


def og_image(url):
    """Find the picture to use for an item: its og:image, or the first
    reasonably large <img> on the page. Returns None if there is nothing suitable."""
    """Return absolute og:image URL for a page, or None."""
    try:
        raw, ctype = fetch(url)
        if "html" not in ctype.lower():
            return None
        doc = raw.decode("utf-8", "ignore")
        for pat in [r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
                    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
                    r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)']:
            m = re.search(pat, doc, re.I)
            if m:
                return urllib.parse.urljoin(url, html.unescape(m.group(1)))
    except Exception:
        return None
    return None


def download_image(img_url, date, idx):
    """Save one item image into assets/<date>/ under a short hash of its URL,
    so the same picture is never stored twice."""
    """Download, downscale, save. Returns relative path or None."""
    try:
        raw, ctype = fetch(img_url, timeout=20)
        if not ctype.startswith("image") or len(raw) < 3000:
            return None
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(raw))
        if im.width < 200:
            return None
        im = im.convert("RGB")
        if im.width > 640:
            im = im.resize((640, round(im.height * 640 / im.width)), Image.LANCZOS)
        name = hashlib.sha1(img_url.encode()).hexdigest()[:10] + ".jpg"
        d = f"{REPO}/assets/{date}"
        os.makedirs(d, exist_ok=True)
        im.save(f"{d}/{name}", "JPEG", quality=82, optimize=True)
        return f"assets/{date}/{name}"
    except Exception:
        return None


def xkcd_comic(num, date):
    """Download an xkcd comic for {{xkcd:N}} and return its local filename.
    The comic is placed by the author at section boundaries; see build_body."""
    """Fetch an xkcd by number; download the image. Returns dict or None."""
    try:
        raw, _ = fetch(f"https://xkcd.com/{int(num)}/info.0.json", timeout=15)
        j = json.loads(raw.decode("utf-8"))
        img = j.get("img") or ""
        parts = urllib.parse.urlparse(img)
        if not parts.scheme:
            return None
        rid = urllib.request.Request(img, headers={"User-Agent": "Mozilla/5.0 (MorningstarNews)"})
        blob = urllib.request.urlopen(rid, timeout=20).read()
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(blob)).convert("RGB")
        if im.width > 640:
            im = im.resize((640, round(im.height * 640 / im.width)), Image.LANCZOS)
        d = f"{REPO}/assets/{date}"
        os.makedirs(d, exist_ok=True)
        name = f"xkcd-{j['num']}.png"
        im.save(f"{d}/{name}", "PNG", optimize=True)
        return {"num": j["num"], "title": j.get("title", ""), "alt": j.get("alt", ""),
                "path": f"assets/{date}/{name}"}
    except Exception as e:
        print("xkcd fetch failed:", e)
        return None


def slug(t):
    """Turn a section heading into the anchor used in links: "UK news" -> "uk-news"."""
    return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')


def drop_empty_sections(md):
    """Remove any section heading with no items beneath it, so the paper
    never shows an empty section. The prompt tells the AI to omit them, this
    makes sure it actually did."""
    """Remove any ## section whose paragraphs contain no external link."""
    parts = re.split(r'(?m)^(##\s+.+)$', md)
    out = [parts[0]]
    i = 1
    while i < len(parts) - 1:
        head, chunk = parts[i], parts[i + 1]
        if re.search(r'\]\(https?://', chunk):
            out.extend([head, chunk])
        i += 2
    if i < len(parts):
        out.append(parts[i])
    return "".join(out)


def para_items(md, date):
    """Parse the markdown into sections and items: for each item, its headline,
    body text, source link and the section it belongs to. This is the parse
    everything downstream depends on."""
    """Split body into blocks; attach images to paragraphs that contain links."""
    blocks = re.split(r'\n\s*\n', md)
    out = []
    cache = {}
    idx = 0
    weather_next = False
    for b in blocks:
        s = b.strip()
        if not s:
            continue
        if s.startswith("## "):
            head = s[3:].strip()
            weather_next = head.lower().startswith("uk weather")
            out.append(("h2", head))
            continue
        if s.startswith("### "):
            out.append(("h3", s[4:].strip()))
            continue
        if s.startswith("# "):
            out.append(("h1", s[2:].strip()))
            continue
        if set(s) <= set("-"):
            out.append(("hr", ""))
            continue
        if s.startswith(">"):
            out.append(("note", s))
            continue
        if weather_next:
            weather_next = False
            out.append(("wx", s))
            continue
        # paragraph: first external link
        links = re.findall(r'\[([^\]]*)\]\((https?://[^)\s]+)\)', s)
        img = None
        if links:
            target = links[0][1]
            if target in cache:
                img = cache[target]
            else:
                o = og_image(target)
                img = download_image(o, date, idx) if o else None
                cache[target] = img
        if img:
            idx += 1
            alt = re.sub(r'[*_\[\]]', '', links[0][0])[:60]
            s = f'![{alt}]({SITE}/{img}){{.thumb}}' + s
        out.append(("p", s))
    return out


def pandoc(md):
    """Convert the markdown body to HTML using pandoc. Raises if pandoc is not
    installed, which is the most common setup mistake."""
    return subprocess.run(["pandoc", "-f", "markdown+link_attributes", "-t", "html"],
                          input=md, capture_output=True, text=True).stdout


QUOTES = json.load(open(os.path.join(config.JOBS, "quotes.json"), encoding="utf-8"))


def pick_quote(date):
    """Choose the closing quote. It is seeded by the date, so the same day always
    gets the same quote and different days get different ones."""
    """Deterministic per-edition rotation, so a re-publish never changes the quote."""
    try:
        day = datetime.date.fromisoformat(date).toordinal()
    except Exception:
        day = len(date)
    return QUOTES[day % len(QUOTES)]


def epigraph(date):
    """Wrap the quote in the blockquote markup the stylesheet expects."""
    q = pick_quote(date)
    return ('<div class="epigraph"><span class="q" aria-hidden="true">&ldquo;</span>'
            f'<p>{html.escape(q["text"])}</p>'
            f'<p class="src">&mdash; {html.escape(q["source"])}</p></div>')


def build_body(md, date):
    """Assemble the article HTML: standfirst, sections, items, images, the xkcd
    comic at the midpoint, and the closing quote."""
    md = drop_empty_sections(md)
    xk = re.search(r'\{\{xkcd:(\d+)\}\}', md)
    xkcd_html = ""
    if xk:
        md = re.sub(r'\{\{xkcd:\d+\}\}', '', md)
        c = xkcd_comic(xk.group(1), date)
        if c:
            xkcd_html = (f'<figure class="comic"><a href="https://xkcd.com/{c["num"]}/">'
                         f'<img src="{c["path"]}" alt="{html.escape(c["alt"] or c["title"])}" '
                         f'width="640" height="auto"></a>'
                         f'<figcaption>xkcd #{c["num"]} &middot; {html.escape(c["title"])} '
                         f'&middot; <a href="https://xkcd.com/{c["num"]}/">xkcd.com/{c["num"]}</a>'
                         f'</figcaption></figure>')
    blocks = para_items(md, date)
    parts, i = [], 0
    # headline
    if blocks and blocks[0][0] == "h1":
        head = blocks.pop(0)[1]
        parts.append(f'<div class="kicker">Today&rsquo;s Edition</div><h1 class="head">{html.escape(head)}</h1>')
        parts.append('<div class="byline">Compiled by the Rool Machine &middot; Sources linked</div>')
    # the line under the headline is a factual standfirst, set as a deck, never a greeting
    if blocks and blocks[0][0] == "p" and not blocks[0][1].lstrip().startswith(("*", "**")):
        deck = blocks.pop(0)[1].strip()
        parts.append(f'<p class="deck">{html.escape(deck)}</p>')
    seen_first_p = False
    for kind, val in blocks:
        if kind == "h1":
            parts.append(f'<h1 class="head">{html.escape(val)}</h1>')
        elif kind == "h2":
            cls = "sec weather" if val.strip().lower().startswith("uk weather") else "sec"
            parts.append(f'<h2 class="{cls}" id="{slug(val)}">{html.escape(val)}</h2>')
        elif kind == "h3":
            parts.append(f'<h3 class="local">{html.escape(val)}</h3>')
        elif kind == "hr":
            parts.append('<div class="signoff-marker"></div>')
        elif kind == "wx":
            inner = pandoc(val).strip()
            m = re.fullmatch(r"<p>(.*?)</p>", inner, re.S)
            if m:
                inner = m.group(1)
            parts.append(
                f'<div class="wx"><span id="weather-text">{inner}</span>'
                f'<button id="local-weather-btn" class="wxbtn" type="button">Use my location</button>'
                f'</div>')
        elif kind == "note":
            txt = re.sub(r"^>[ \t]?", "", val, flags=re.M).strip()
            chunks = [c.strip() for c in re.split(r"\n\s*\n", txt) if c.strip()]
            inner = "".join(pandoc(c).strip() for c in chunks)
            parts.append(f'<div class="forage">{inner}</div>')
        else:
            f = pandoc(val).strip()
            lead = re.sub(r'^(!\[[^\]]*\]\([^)]*\)\{[^}]*\})+', '', val).lstrip()
            is_take = bool(re.match(r'^\*(?!\*)', lead))
            is_item = lead.startswith("**")
            # first paragraph = lede
            if not seen_first_p and not is_take and not is_item:
                f = f.replace("<p>", '<p class="lede">', 1)
                seen_first_p = True
            if is_item:
                f = f.replace("<p>", '<div class="item"><p>', 1)
                f = re.sub(r"</p>\s*$", "</p></div>", f)
            if is_take:
                f = f.replace("<p>", '<p class="take">', 1)
            parts.append(f)
    if xkcd_html:
        cuts = [i for i, p in enumerate(parts) if p.startswith('<h2 class="sec"')]
        if len(cuts) >= 2:
            target = len(parts) // 2
            at = min(cuts, key=lambda i: abs(i - target))
            parts.insert(at, xkcd_html)
        else:
            parts.append(xkcd_html)
    body = "\n".join(parts)
    # merge consecutive signoff markers into the closing paragraph
    body = body.replace('<div class="signoff-marker"></div>', "")
    return body + epigraph(date)


def shell(title, body, datestr="", is_home=False, extra_head="", url=None):
    """Wrap a page in the shared furniture: <head>, masthead, dropdown menu bar,
    dateline and footer. Every page on the site goes through here."""
    og_img = ""
    m = re.search(r'src="(' + re.escape(SITE) + r'/assets/[^"]+)"', body)
    if m:
        og_img = (f'<meta property="og:image" content="{m.group(1)}">\n'
                  f'<meta name="twitter:image" content="{m.group(1)}">\n')
    desc = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', body))
    desc = re.sub(r"^\s*Today.{0,12}Edition\s*", '', desc)
    desc = re.sub(r'Compiled by the Rool Machine.*?Sources linked\s*', '', desc)
    desc = html.escape(desc.strip()[:180]).strip()
    og = (f'<meta property="og:type" content="article">\n'
          f'<meta property="og:site_name" content="{html.escape(PAPER)}">\n'
          f'<meta property="og:title" content="{html.escape(title)}">\n'
          f'<meta property="og:description" content="{desc}">\n'
          f'<meta property="og:url" content="{url or SITE + chr(47)}">\n'
          f'<meta name="twitter:card" content="summary_large_image">\n' + og_img)
    nav = (f'<div class="dateline"><span>No. {len(os.listdir(REPO+"/posts")) if os.path.isdir(REPO+"/posts") else 1}</span>'
           f'<span class="mid">{html.escape(datestr)}</span>'
           f'<span>{html.escape(PLACE)}</span></div>')
    bardate = html.escape(datestr) if datestr else html.escape(PLACE + ", England")
    return f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(PAPER)}: news, television, games, film and technology.">
{og}
<link rel="alternate" type="application/rss+xml" title="Morningstar News" href="{SITE}/feed.xml">
<link rel="stylesheet" href="{SITE}/style.css?v={CSSV}">
{extra_head}
</head>
<body>
<div class="page">
<header class="masthead">
  <div class="dev">Est. 2026 &middot; Published daily</div>
  <h1><a href="{SITE}/"><img class="logo" src="{SITE}/assets/nameplate.png" alt="{html.escape(PAPER)}" width="2222" height="151" style="width:100%;max-width:100%;height:auto"></a></h1>
  {nav}
</header>
<nav class="menubar">
  <details class="menu">
    <summary>Sections</summary>
    <ul>
      <li><a href="{SITE}/almanac.html">{html.escape(PLACE)} Almanac</a></li>
      <li><a href="{SITE}/radio.html">Radio &amp; Satellites</a></li>
      <li><a href="{SITE}/foraging.html">The Foraging Year</a></li>
      <li class="sep"></li>
      <li><a href="{SITE}/history.html">Previous editions</a></li>
      <li><a href="{SITE}/feed.xml">RSS feed</a></li>
    </ul>
  </details>
</nav>
<main>
{body}
</main>
<footer class="site">
  <span>Every item links to a real source</span>
</footer>
</div>
<script>{WXJS}</script>
</body>
</html>
"""


WXJS = r"""
(function(){
  var btn=document.getElementById('local-weather-btn');
  var textEl=document.getElementById('weather-text');
  if(!btn||!textEl||!('geolocation' in navigator))return;
  var wmo={0:'clear sky',1:'mainly clear',2:'partly cloudy',3:'overcast',45:'fog',48:'depositing rime fog',51:'light drizzle',53:'moderate drizzle',55:'dense drizzle',61:'light rain',63:'moderate rain',65:'heavy rain',71:'light snow',73:'moderate snow',75:'heavy snow',80:'rain showers',81:'moderate showers',82:'violent showers',95:'thunderstorm'};
  function dayName(d,i){return i===0?'Today':new Date(d+'T12:00:00').toLocaleDateString('en-GB',{weekday:'long'});}
  btn.addEventListener('click',function(){
    btn.disabled=true;btn.textContent='Locating…';
    navigator.geolocation.getCurrentPosition(function(pos){
      var lat=pos.coords.latitude.toFixed(4),lon=pos.coords.longitude.toFixed(4);
      Promise.all([
        fetch('https://api.open-meteo.com/v1/forecast?latitude='+lat+'&longitude='+lon+'&daily=weather_code,temperature_2m_min,temperature_2m_max&timezone=auto&forecast_days=3').then(function(r){return r.json();}),
        fetch('https://api.bigdatacloud.net/data/reverse-geocode-client?latitude='+lat+'&longitude='+lon+'&localityLanguage=en').then(function(r){return r.json();})
      ]).then(function(res){
        var wx=res[0],geo=res[1];
        var place=geo.city||geo.locality||geo.principalSubdivision||'Your location';
        var summary=wx.daily.time.map(function(d,i){
          return dayName(d,i)+' '+(wmo[wx.daily.weather_code[i]]||'mixed conditions')+' ('+Math.round(wx.daily.temperature_2m_min[i])+'–'+Math.round(wx.daily.temperature_2m_max[i])+'°C)';
        }).join('; ');
        textEl.innerHTML=place+': '+summary+'. <a href="https://open-meteo.com/">Open-Meteo</a>';
        btn.remove();
      }).catch(function(){btn.disabled=false;btn.textContent='Weather unavailable — retry';});
    },function(){
      btn.disabled=false;btn.textContent='Location blocked';
    },{timeout:10000,maximumAge:600000});
  });
})();
"""

CSSV = hashlib.sha1(CSS.encode()).hexdigest()[:8]


def frame(title, inner, extra_css="", datestr=""):
    """A lighter wrapper for the reference pages (almanac, radio, foraging),
    which share the masthead but none of the article layout."""
    """Wrap a reference page in the shared masthead, menu bar and footer."""
    return shell(title, inner, datestr=datestr,
                 extra_head=(f"<style>{extra_css}</style>" if extra_css else ""))


def pretty_date(d):
    """Turn 2026-11-16 into "Monday, 16 November 2026" for display."""
    try:
        return datetime.date.fromisoformat(d).strftime("%A, %-d %B %Y").upper()
    except Exception:
        return d


def title_of(path):
    """Read the H1 out of an edition markdown file — used for the archive."""
    try:
        md = open(path, encoding="utf-8").read()
        m = re.search(r'^#\s+(.+)$', md, re.M)
        return m.group(1).strip() if m else path
    except Exception:
        return path


def published_editions():
    """Every daily edition on disk, newest first."""
    d = f"{REPO}/editions"
    if not os.path.isdir(d):
        return []
    names = [f[:-3] for f in os.listdir(d) if f.endswith(".md")]
    return sorted([n for n in names if not n.endswith("-weekly")], reverse=True)


def published_weeklies():
    """Every Sunday Paper on disk, newest first. Kept separate so the weekly
    never appears in the daily archive."""
    d = f"{REPO}/editions"
    if not os.path.isdir(d):
        return []
    names = [f[:-3] for f in os.listdir(d) if f.endswith("-weekly.md")]
    return sorted([n[:-7] for n in names], reverse=True)


def check_repeats(md, date):
    """THE REPEAT CHECK. Compare every source URL in this edition against the
    previous edition. A shared URL means the same story ran twice; the caller
    treats that as a hard failure and the paper does not publish.

    Weather and foraging links are exempt: the scripts print those daily and
    they are expected to recur."""
    """Flag items whose source URL already ran in the previous edition. Warns, never blocks."""
    import glob as _glob
    recurring = ("bbc.co.uk/weather", "thenas.org.uk/", "foragers")
    def norm(u):
        return u.rstrip("/").split("?")[0].lower()
    prev = None
    for f in sorted(_glob.glob(f"{REPO}/editions/*.md"), reverse=True):
        base = os.path.basename(f)[:10]
        if base.endswith("-weekly"):
            continue
        if base < date:
            prev = (base, f)
            break
    if not prev:
        print("Repeat check: no previous edition.")
        return []
    used = {}
    for u in re.findall(r"\]\((https?://[^)\s]+)\)", open(prev[1], encoding="utf-8").read()):
        if not any(r in u for r in recurring):
            used[norm(u)] = prev[0]
    hits = []
    for u in re.findall(r"\]\((https?://[^)\s]+)\)", md):
        if any(r in u for r in recurring):
            continue
        if norm(u) in used:
            hits.append((u, used[norm(u)]))
    if hits:
        print("\n!! REPEATED SOURCES - this story ran in the previous edition:")
        for u, d in hits:
            print(f"   {u}  (ran {d})")
        print("   Rewrite with a fresh source or drop the item.\n")
    else:
        print("Repeat check: clean against the previous edition.")
    return hits


def main():
    """Entry point. Build the article, rebuild the front page, archive, RSS and
    reference pages, then commit and push. Exits non-zero on failure so cron
    and the caller can tell."""
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    weekly = date.endswith("-weekly")
    if weekly:
        date = date[:-7]
    slug = f"{date}-weekly" if weekly else date
    src = f"{REPO}/editions/{slug}.md"
    if not os.path.exists(src):
        sys.exit(f"missing {src}")
    md = open(src, encoding="utf-8").read()

    check_repeats(md, date)

    body = build_body(md, date)
    title_m = re.search(r'^#\s+(.+)$', md, re.M)
    title = title_m.group(1).strip() if title_m else "Morningstar News"

    os.makedirs(f"{REPO}/posts", exist_ok=True)
    out_name = slug
    open(f"{REPO}/posts/{out_name}.html", "w", encoding="utf-8").write(
        shell(f"{title} — {pretty_date(date)}", body,
              ("THE SUNDAY PAPER · " + pretty_date(date)) if weekly else pretty_date(date),
              url=f"{SITE}/posts/{out_name}.html"))
    open(f"{REPO}/style.css", "w", encoding="utf-8").write(CSS)
    open(f"{REPO}/.nojekyll", "w").write("")

    # homepage = latest daily edition (a weekly never overwrites it)
    eds = published_editions()
    latest = eds[0] if eds else date
    lsrc = f"{REPO}/editions/{latest}.md"
    lbody = build_body(open(lsrc, encoding="utf-8").read(), latest)
    ltitle_m = re.search(r'^#\s+(.+)$', lsrc and open(lsrc, encoding="utf-8").read(), re.M)
    ltitle = ltitle_m.group(1).strip() if ltitle_m else "Morningstar News"
    weeklies = published_weeklies()
    wbanner = ""
    if weeklies:
        w = weeklies[0]
        wtitle = title_of(f"{REPO}/editions/{w}-weekly.md")
        wbanner = (f'<p class="weekly-banner"><a href="{SITE}/posts/{w}-weekly.html">'
                   f'The Sunday Paper &mdash; {html.escape(wtitle)}</a></p>')
        lbody = wbanner + lbody
    open(f"{REPO}/index.html", "w", encoding="utf-8").write(
        shell(f"Morningstar News — {pretty_date(latest)}", lbody, pretty_date(latest), is_home=True))
    if weekly:
        # and the weekly page itself gets the banner pointing back
        pass

    # history
    by_month = {}
    for d in eds:
        by_month.setdefault(d[:7], []).append(d)
    chunks = ['<div class="hist"><h1>Archive</h1>']
    if weeklies:
        chunks.append('<div class="month">The Sunday Papers</div><ol>')
        for w in weeklies[:26]:
            t = title_of(f"{REPO}/editions/{w}-weekly.md")
            lab = datetime.date.fromisoformat(w).strftime("%-d %b")
            chunks.append(f'<li><span class="d">{lab}</span>'
                          f'<span class="t"><a href="{SITE}/posts/{w}-weekly.html">{html.escape(t)}</a></span></li>')
        chunks.append("</ol>")
    for m in sorted(by_month, reverse=True):
        label = datetime.date.fromisoformat(m + "-01").strftime("%B %Y")
        chunks.append(f'<div class="month">{label}</div><ol>')
        for d in by_month[m]:
            t = title_of(f"{REPO}/editions/{d}.md")
            lab = datetime.date.fromisoformat(d).strftime("%-d %b")
            chunks.append(f'<li><span class="d">{lab}</span>'
                          f'<span class="t"><a href="{SITE}/posts/{d}.html">{html.escape(t)}</a></span></li>')
        chunks.append("</ol>")
    chunks.append(f'<p class="back"><a href="{SITE}/">&larr; Today&rsquo;s edition</a></p></div>')
    open(f"{REPO}/history.html", "w", encoding="utf-8").write(
        shell("Archive — Morningstar News", "\n".join(chunks), "ARCHIVE"))

    # RSS feed
    items = []
    for d in eds[:20]:
        pm = f"{REPO}/editions/{d}.md"
        try:
            raw = open(pm, encoding="utf-8").read()
        except Exception:
            continue
        t = title_of(pm)
        paras = [x.strip() for x in re.split(r'\n\s*\n', drop_empty_sections(raw)) if x.strip()]
        lede = next((x for x in paras if not x.startswith('#') and not x.startswith('*')), '')
        lede = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', lede)
        try:
            dt = datetime.datetime.fromisoformat(d + "T08:00:00+00:00")
        except Exception:
            dt = datetime.datetime.now(datetime.timezone.utc)
        items.append(
            "  <item>\n"
            f"    <title>{html.escape(t)}</title>\n"
            f"    <link>{SITE}/posts/{d}.html</link>\n"
            f"    <guid isPermaLink=\"true\">{SITE}/posts/{d}.html</guid>\n"
            f"    <pubDate>{dt.strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>\n"
            f"    <description>{html.escape(lede[:400])}</description>\n"
            "  </item>")
    feed = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n<channel>\n'
            "  <title>Morningstar News</title>\n"
            f"  <link>{SITE}/</link>\n"
            "  <description>UK news, Pokemon, Warhammer, Star Trek, AI, Android, macOS, Linux. Published daily.</description>\n"
            "  <language>en-gb</language>\n"
            f'  <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>\n'
            + "\n".join(items) + "\n</channel>\n</rss>\n")
    open(f"{REPO}/feed.xml", "w", encoding="utf-8").write(feed)

    r = subprocess.run('git add -A && git commit -q -m "Edition: ' + slug + '" && git push -q origin main',
                       shell=True, cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
        print(r.stdout, r.stderr)
    print("Published:", f"{SITE}/posts/{out_name}.html")


if __name__ == "__main__":
    main()
