#!/usr/bin/env python3
"""The local almanac - all figures pulled from official sources, nothing invented."""
import publish
import json, urllib.request, sys, html, datetime as dt

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

# All three come from config.sh: where the site is built, and where you are.
SITE = config.REPO
LAT, LON = config.LAT, config.LON
PLACE = config.TOWN

def get(url, timeout=25):
    """Fetch a URL and return its text. All the almanac's numbers come from
    official sources, so every call here is to Met Office, Environment Agency
    or astronomy data."""
    req = urllib.request.Request(url, headers={"User-Agent": "morningstar-almanac/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def sun_moon():
    """Sunrise, sunset and moon phase from the machine's own clock and
    your latitude/longitude. No API call — the maths is deterministic."""
    from skyfield.api import load
    from skyfield import almanac
    from skyfield.api import wgs84
    ts = load.timescale()
    eph = load("de421.bsp")
    tz = dt.timezone.utc
    now = dt.datetime.now(tz)
    t0 = ts.utc(now.year, now.month, now.day)
    t1 = ts.utc(now.year, now.month, now.day + 1)
    loc = wgs84.latlon(LAT, LON)
    f = almanac.sunrise_sunset(eph, loc)
    times, events = almanac.find_discrete(t0, t1, f)
    rise = set_ = None
    for t, e in zip(times, events):
        if e == 1: rise = t.utc_datetime()
        else: set_ = t.utc_datetime()
    phase = almanac.moon_phase(eph, ts.now())
    illum = almanac.fraction_illuminated(eph, "moon", ts.now())
    return rise, set_, phase.degrees, illum

def met_office():
    """Weather warnings for the region, from the Met Office feed."""
    try:
        xml = get("https://www.metoffice.gov.uk/public/data/PWSCache/WarningsRSS/Region/em.xml")
        import re
        items = re.findall(r"<item>(.*?)</item>", xml, re.S)
        out = []
        for it in items[:3]:
            t = re.search(r"<title>(.*?)</title>", it, re.S)
            d = re.search(r"<description>(.*?)</description>", it, re.S)
            l = re.search(r"<link>(.*?)</link>", it, re.S)
            if t:
                out.append((html.unescape(t.group(1).strip()),
                            html.unescape((d.group(1) if d else "").strip()),
                            (l.group(1) if l else "").strip()))
        return out
    except Exception as e:
        print("met office failed:", e, file=sys.stderr)
        return []

def river():
    """River level and flow from Environment Agency telemetry. Optional: if the
    station is wrong for your area, change the id and it degrades gracefully."""
    try:
        d = json.loads(get("https://environment.data.gov.uk/flood-monitoring/id/stations/4085"))
        out = {}
        for m in d.get("items", {}).get("measures", []):
            lr = m.get("latestReading", {})
            key = m.get("parameter")
            if key and lr.get("value") is not None:
                out[key] = (lr["value"], m.get("unitName", ""), lr.get("dateTime", ""))
        return out
    except Exception as e:
        print("river failed:", e, file=sys.stderr)
        return {}

def main():
    """Build almanac.html."""
    today = dt.date.today().isoformat()
    rise, set_, deg, illum = sun_moon()
    phases = [(0, "New Moon"), (45, "Waxing Crescent"), (90, "First Quarter"),
              (135, "Waxing Gibbous"), (180, "Full Moon"), (225, "Waning Gibbous"),
              (270, "Last Quarter"), (315, "Waning Crescent"), (361, "New Moon")]
    pname = next(n for a, n in phases if deg < a)
    warnings = met_office()
    riv = river()

    def t(x): return x.strftime("%H:%M") if x else "—"
    rows = []
    rows.append(f"<tr><td>Sunrise</td><td>{t(rise)}</td></tr>")
    rows.append(f"<tr><td>Sunset</td><td>{t(set_)}</td></tr>")
    if rise and set_:
        mins = int((set_ - rise).total_seconds() // 60)
        rows.append(f"<tr><td>Daylight</td><td>{mins//60}h {mins%60:02d}m</td></tr>")
    rows.append(f"<tr><td>Moon</td><td>{pname} &middot; {illum*100:.0f}% lit</td></tr>")
    if "level" in riv:
        v, u, ts = riv["level"]
        rows.append(f"<tr><td>Derwent level</td><td>{v} {u}</td></tr>")
    if "flow" in riv:
        v, u, ts = riv["flow"]
        rows.append(f"<tr><td>Derwent flow</td><td>{v:.0f} {u}</td></tr>")

    warn_html = ""
    if warnings:
        warn_html = "<h2>Weather warnings</h2><ul class='plain'>"
        for ti, de, ln in warnings:
            warn_html += f"<li><a href='{html.escape(ln)}'>{html.escape(ti)}</a></li>"
        warn_html += "</ul>"
    else:
        warn_html = "<h2>Weather warnings</h2><p class='quiet'>No warnings currently issued for the East Midlands.</p>"

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%H:%M UTC, %d %B %Y")
    CSS_PAGE = """.almanac{{max-width:34rem;margin:0 auto;padding:1.5rem 1rem 3rem}}
.almanac table{{width:100%;border-collapse:collapse;margin:1rem 0;font-variant-numeric:tabular-nums}}
.almanac td{{padding:.45rem 0;border-bottom:1px solid rgba(0,0,0,.14)}}
.almanac td:last-child{{text-align:right;font-weight:600}}
.almanac h2{{font-family:var(--serif,Georgia,serif);font-size:1.05rem;letter-spacing:.09em;text-transform:uppercase;margin:2rem 0 .5rem;border-bottom:2px solid #111;padding-bottom:.3rem}}
.almanac ul.plain{{list-style:none;padding:0;margin:0}}
.almanac ul.plain li{{padding:.4rem 0;border-bottom:1px solid rgba(0,0,0,.1)}}
.quiet{{color:#666;font-style:italic}}"""
    _inner = f"""</style></head><body><main class="almanac">
<p style="text-align:center;letter-spacing:.22em;font-size:.7rem;text-transform:uppercase;color:#666;margin-bottom:.2rem">Morningstar News</p>
<h1 style="text-align:center;font-family:var(--serif,Georgia,serif);font-size:1.9rem;margin:.2rem 0 .1rem">{html.escape(PLACE)} Almanac</h1>
<p style="text-align:center;font-size:.85rem;color:#555;margin-top:0">{PLACE} &middot; {today} &middot; updated {stamp}</p>
<h2>Sun &amp; Moon</h2>
<table>{''.join(rows)}</table>
{warn_html}
<h2>River Derwent</h2>
<p>River level and flow from Environment Agency telemetry, updated every 15 minutes. <a href="https://environment.data.gov.uk/flood-monitoring/id/stations/4085">Station 4085</a>.</p>
<p class="src">Sources: sunrise, sunset and lunar phase computed from the JPL DE421 ephemeris; warnings from the Met Office data feed; river data from the Environment Agency flood-monitoring API. Nothing on this page is written by hand &mdash; every figure is pulled at build time.</p>
<p style="text-align:center;margin-top:2rem"><a href="./">&larr; Morningstar News</a> &middot; <a href="radio.html">Radio &amp; Satellites</a> &middot; <a href="foraging.html">Foraging Year</a></p>
</main>"""
    page = publish.frame(f"{PLACE} Almanac", _inner, CSS_PAGE, today)
    with open(f"{SITE}/almanac.html", "w") as f:
        f.write(page)
    print("almanac written", today)

if __name__ == "__main__":
    main()
