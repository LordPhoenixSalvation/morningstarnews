#!/usr/bin/env python3
"""Radio & Satellites - pass predictions and space weather, all from published data."""
import publish
import urllib.request, sys, html, datetime as dt, json

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

SITE = config.REPO            # where the site is built
LAT, LON = config.LAT, config.LON
ALT = 60.0                    # your height above sea level, metres
GRID = config.GRID            # Maidenhead locator, config.sh
SATS = [
    ("ISS (ZARYA)", "25544"),
    ("SO-50 (SaudiSat 1C)", "27607"),
    ("AO-91 (Fox-1B)", "43017"),
    ("PO-101 (Diwata-2)", "43678"),
    ("RS-44 (DOSAAF-85)", "44909"),
]

def get(url, timeout=25):
    """Fetch a URL and return its text."""
    req = urllib.request.Request(url, headers={"User-Agent": "morningstar-radio/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def tles():
    """Download the current orbital elements (TLEs) for the satellites in SATS
    from CelesTrak. These change slowly, so one fetch covers the day."""
    out = {}
    for name, catnr in SATS:
        try:
            txt = get(f"https://celestrak.org/NORAD/elements/gp.php?CATNR={catnr}&FORMAT=TLE").strip().splitlines()
            if len(txt) >= 3 and txt[1].startswith("1 "):
                out[name] = (txt[1].strip(), txt[2].strip())
        except Exception as e:
            print(f"tle {name}: {e}", file=sys.stderr)
    return out

def passes(tle_map):
    """Work out when each satellite rises above the horizon for your latitude
    and longitude, how high it gets, and in which direction. This is the maths
    behind the pass table."""
    from skyfield.api import load, wgs84, EarthSatellite
    ts = load.timescale()
    obs = wgs84.latlon(LAT, LON, elevation_m=ALT)
    now = dt.datetime.now(dt.timezone.utc)
    t0 = ts.utc(now)
    t1 = ts.utc(now + dt.timedelta(hours=36))
    rows = []
    for name, (l1, l2) in tle_map.items():
        try:
            sat = EarthSatellite(l1, l2, name, ts)
            times, events = sat.find_events(obs, t0, t1, altitude_degrees=10.0)
            cur = None
            for t, e in zip(times, events):
                if e == 0:
                    cur = {"name": name, "rise": t, "max": None, "set": None, "sat": sat}
                elif e == 1 and cur:
                    cur["max"] = t
                elif e == 2 and cur:
                    cur["set"] = t
                    rows.append(cur); cur = None
        except Exception as e:
            print(f"passes {name}: {e}", file=sys.stderr)
    rows.sort(key=lambda r: r["rise"].utc_datetime())
    out = []
    for r in rows[:14]:
        alt = 0
        if r["max"] is not None:
            try:
                alt = (r["sat"].at(r["max"]) - obs.at(r["max"])).altaz()[0].degrees
            except Exception:
                alt = 0
        dur = (r["set"].utc_datetime() - r["rise"].utc_datetime()).total_seconds() / 60 if r["set"] is not None else 0
        out.append((r["name"], r["rise"].utc_datetime(), alt, dur))
    return out

def spacewx():
    """Space weather: the planetary K index and solar flux from NOAA. High Kp
    means the aurora may be visible and HF radio gets difficult."""
    d = {}
    try:
        kp = json.loads(get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"))
        series = kp[1:] if isinstance(kp[0], list) else kp
        if series and isinstance(series[0], dict):
            cur = [x for x in series if x.get("Kp") is not None][-1]
            d["kp"] = float(cur["Kp"]); d["kp_time"] = cur["time_tag"]
        else:
            cur = [x for x in series if x[1] is not None][-1]
            d["kp"] = float(cur[1]); d["kp_time"] = cur[0]
    except Exception as e:
        print("kp failed:", e, file=sys.stderr)
    try:
        txt = get("https://services.swpc.noaa.gov/json/solar-cycle/observed-solar-cycle-indices.json")
        j = json.loads(txt)
        last = [x for x in j if x.get("f10.7") is not None][-1]
        d["flux"] = last["f10.7"]
    except Exception as e:
        print("flux failed:", e, file=sys.stderr)
    return d

def band_from_kp(kp):
    """Translate the K index into a plain statement about HF conditions."""
    if kp < 3: return "Quiet &mdash; good HF conditions, especially 20m and below."
    if kp < 4: return "Unsettled &mdash; some fading on the higher bands, lower bands steadier."
    if kp < 5: return "Active &mdash; expect fading and flutter, better on 40m and 80m."
    if kp < 6: return "Minor storm &mdash; HF paths degraded, auroral paths may open on VHF."
    return "Storm &mdash; widespread HF blackouts likely, watch for aurora on 6m and 2m."

def main():
    """Build radio.html."""
    today = dt.date.today().isoformat()
    tle_map = tles()
    pl = passes(tle_map) if tle_map else []
    wx = spacewx()

    prow = ""
    for name, rise, alt, dur in pl:
        local = rise.replace(tzinfo=dt.timezone.utc) + dt.timedelta(hours=0)
        prow += (f"<tr><td>{html.escape(name)}</td><td>{local.strftime('%a %H:%M')}</td>"
                 f"<td>{alt:.0f}&deg;</td><td>{dur:.0f} min</td></tr>")
    if not prow:
        prow = "<tr><td colspan='4' class='quiet'>No passes above 10&deg; in the next 36 hours.</td></tr>"

    kp = wx.get("kp"); flux = wx.get("flux")
    wxrow = ""
    if kp is not None:
        wxrow += f"<tr><td>Planetary K index</td><td>Kp {kp:.2f}</td></tr>"
    if flux is not None:
        wxb = "poor" if flux < 100 else ("fair" if flux < 150 else "good")
        wxrow += f"<tr><td>Solar flux (F10.7)</td><td>{flux} &middot; {wxb}</td></tr>"
    band = band_from_kp(kp) if kp is not None else ""

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%H:%M UTC, %d %B %Y")
    CSS_PAGE = """.radio{{max-width:36rem;margin:0 auto;padding:1.5rem 1rem 3rem}}
.radio table{{width:100%;border-collapse:collapse;margin:1rem 0;font-size:.9rem;font-variant-numeric:tabular-nums}}
.radio th{{text-align:left;font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;border-bottom:2px solid #111;padding:.3rem .2rem;color:#444}}
.radio td{{padding:.42rem .2rem;border-bottom:1px solid rgba(0,0,0,.12)}}
.radio td:nth-child(n+2),.radio th:nth-child(n+2){{text-align:right}}
.radio h2{{font-family:var(--serif,Georgia,serif);font-size:1.05rem;letter-spacing:.09em;text-transform:uppercase;margin:2rem 0 .5rem;border-bottom:2px solid #111;padding-bottom:.3rem}}
.note{{background:rgba(0,0,0,.045);padding:.7rem .9rem;font-size:.88rem;line-height:1.5;border-left:3px solid #111}}
.src{{font-size:.78rem;color:#666;margin-top:2.5rem;border-top:1px solid #ccc;padding-top:.8rem}}"""
    _inner = f"""</style></head><body><main class="radio">
<p style="text-align:center;letter-spacing:.22em;font-size:.7rem;text-transform:uppercase;color:#666;margin-bottom:.2rem">The Fenland Herald</p>
<h1 style="text-align:center;font-family:var(--serif,Georgia,serif);font-size:1.9rem;margin:.2rem 0 .1rem">Radio &amp; Satellites</h1>
<p style="text-align:center;font-size:.85rem;color:#555;margin-top:0">Grid {GRID} &middot; {html.escape(config.TOWN)} &middot; next 36 hours &middot; updated {stamp}</p>

<h2>Space weather</h2>
<table>{wxrow}</table>
<p class="note">{band}</p>

<h2>Satellite passes above 10&deg;</h2>
<table><thead><tr><th>Satellite</th><th>Rise (UTC)</th><th>Max alt</th><th>Pass</th></tr></thead><tbody>{prow}</tbody></table>

<h2>Working the birds</h2>
<p class="note"><strong>FM birds</strong> (SO-50, AO-91, AO-92, PO-101): 2m up, 70cm down. SO-50 needs a 74.4&nbsp;Hz CTCSS tone to open. Full-duplex or two radios beats one &mdash; you need to hear yourself coming back. Doppler shifts about &plusmn;3&nbsp;kHz on 70cm through a pass, so tune as it moves.<br>
<strong>Linear birds</strong> (RS-44): invert the transponder &mdash; LSB on the uplink becomes USB on the downlink. Best from 5&deg; elevation upward.<br>
<strong>ISS</strong>: voice on 145.800&nbsp;FM during school contacts, APRS on 145.825. Listen before you transmit.</p>

<p class="src">Sources: orbital elements from CelesTrak, refreshed at build time; passes computed with Skyfield from the published TLEs (accuracy degrades over days as elements age); geomagnetic and solar indices from the NOAA Space Weather Prediction Center. Times are UTC &mdash; subtract nothing, the UK is on GMT in winter. Everything here is calculated or pulled, not written.</p>
<p style="text-align:center;margin-top:2rem"><a href="./">&larr; The Fenland Herald</a> &middot; <a href="almanac.html">{html.escape(config.PLACE)} Almanac</a> &middot; <a href="foraging.html">Foraging Year</a></p>
</main>"""
    page = publish.frame("Radio & Satellites", _inner, CSS_PAGE, today)
    with open(f"{SITE}/radio.html", "w") as f:
        f.write(page)
    print("radio written", today, f"{len(pl)} passes")

if __name__ == "__main__":
    main()
