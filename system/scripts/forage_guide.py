#!/usr/bin/env python3
"""Build the Foraging Year reference page. Species names are lifted verbatim
from reputable UK sources and each month links to the page they came from.
Nothing on this page is identified or invented by us."""
import publish
import json, os, sys, datetime, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forage import sources, harvest

import config
SITE = config.REPO                                  # where the site is built
CACHE = os.path.join(config.JOBS, "forage_cache.json")  # 30-day cache
MONTHS = ["January","February","March","April","May","June","July",
          "August","September","October","November","December"]

def load_cache():
    """Read the 30-day cache of species pages. Fetching twelve months of pages
    on every run would be rude to the source, so results are reused."""
    try:
        d = json.load(open(CACHE))
        if (datetime.date.today() - datetime.date.fromisoformat(d["_built"])).days < 30:
            return d
    except Exception:
        pass
    return {"_built": datetime.date.today().isoformat()}

def main():
    """Build foraging.html."""
    cache = load_cache()
    for m in MONTHS:
        if m in cache and cache[m].get("species"):
            continue
        got = None
        for url in sources(m):
            try:
                picks = harvest(url)
            except Exception as e:
                print(f"guide {m}: {url} failed ({e})", file=sys.stderr)
                continue
            if not picks:
                continue
            names = [n for n, _ in picks]
            latins = [l for _, l in picks]
            if got and len(got["species"]) < 2:
                for n, l in picks:
                    if len(got["species"]) >= 3:
                        break
                    if all(n.lower() != x.lower() for x in got["species"]):
                        got["species"].append(n); got["latin"].append(l)
                continue
            got = {"species": names, "latin": latins, "url": url}
            if len(names) >= 2:
                break
        cache[m] = got or {"species": [], "latin": [], "url": ""}
        print(f"  {m}: {'ok' if got else 'no source'}", file=sys.stderr)
    cache["_built"] = datetime.date.today().isoformat()
    json.dump(cache, open(CACHE, "w"), indent=1)

    cur = datetime.date.today().strftime("%B")
    rows = []
    for m in MONTHS:
        d = cache.get(m, {})
        sp = d.get("species", [])
        if sp:
            body = ", ".join(html.escape(x) for x in sp)
            if d.get("url"):
                body += f" <a class='src-link' href='{html.escape(d['url'])}'>&rarr;</a>"
        else:
            body = "<span class='quiet'>no source available</span>"
        cls = " class='now'" if m == cur else ""
        rows.append(f"<tr{cls}><th scope='row'>{m}</th><td>{body}</td></tr>")

    stamp = datetime.date.today().isoformat()
    CSS_PAGE = """.guide{{max-width:36rem;margin:0 auto;padding:1.5rem 1rem 3rem}}
.guide table{{width:100%;border-collapse:collapse;margin:1.2rem 0;font-size:.9rem}}
.guide th[scope=row]{{text-align:left;font-weight:600;width:8.2rem;padding:.55rem .5rem .55rem 0;border-bottom:1px solid rgba(0,0,0,.12);vertical-align:top;font-family:var(--serif,Georgia,serif);font-size:.95rem}}
.guide td{{padding:.55rem 0;border-bottom:1px solid rgba(0,0,0,.12);line-height:1.45}}
.guide tr.now th[scope=row]{{color:#8a2b1f}}
.guide tr.now{{background:rgba(138,43,31,.055)}}
.src-link{{text-decoration:none;color:#666;font-size:.8rem}}
.quiet{{color:#888;font-style:italic}}
.warn{{border-left:3px solid #8a2b1f;background:rgba(138,43,31,.06);padding:.8rem .9rem;font-size:.87rem;line-height:1.5;margin:1.2rem 0}}
.legend{{font-size:.8rem;color:#666;margin:.2rem 0 1rem}}"""
    _inner = f"""</style></head><body><main class="guide">
<p style="text-align:center;letter-spacing:.22em;font-size:.7rem;text-transform:uppercase;color:#666;margin-bottom:.2rem">Morningstar News</p>
<h1 style="text-align:center;font-family:var(--serif,Georgia,serif);font-size:1.9rem;margin:.2rem 0 .1rem">The Foraging Year</h1>
<p style="text-align:center;font-size:.85rem;color:#555;margin-top:0">What is in season in Britain, month by month</p>

<div class="warn"><strong>A calendar, not an identification guide.</strong> These names are copied from the sources linked beside them, not from our own identification. Several edible species have dangerously similar-looking relatives. Check a proper field guide, and never eat anything you are not certain of.</div>

<p class="legend">The current month is highlighted. The arrow links to the page the names came from.</p>
<table>{''.join(rows)}</table>

<p class="src">Sources: the National Allotment Society, Countryfile and Foragers Log, whichever answered for that month; names are reproduced verbatim and each month links to its source. Refreshed every 30 days, last built {stamp}. Nothing here is written by hand.</p>
<p style="text-align:center;margin-top:2rem"><a href="./">&larr; {html.escape(config.PAPER)}</a> &middot; <a href="almanac.html">{html.escape(config.PLACE)} Almanac</a> &middot; <a href="radio.html">Radio &amp; Satellites</a></p>
</main>"""
    page = publish.frame("The Foraging Year", _inner, CSS_PAGE, "%d %s %d" % (datetime.date.today().day, datetime.date.today().strftime("%B"), datetime.date.today().year))
    open(f"{SITE}/foraging.html", "w").write(page)
    print("foraging page written")

if __name__ == "__main__":
    main()
