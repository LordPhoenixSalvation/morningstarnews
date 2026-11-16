#!/usr/bin/env python3
"""Pull the BBC's own forecast feed for Derby and print it as markdown.
Nothing is generated: every word of the forecast comes from the BBC feed."""
import re, sys, requests
from xml.etree import ElementTree as ET

LOCATION = "2651347"            # BBC Weather location id for Derby
PAGE = f"https://www.bbc.co.uk/weather/{LOCATION}"
FEED = f"https://weather-broker-cdn.api.bbci.co.uk/en/forecast/rss/3day/{LOCATION}"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"}

def safe(s):
    return (s or "").strip()

def main():
    try:
        r = requests.get(FEED, headers=UA, timeout=30)
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except Exception as e:
        print(f"weather.py: feed unavailable ({e})", file=sys.stderr)
        return 1

    days = []
    for item in root.iter("item"):
        title = safe(item.findtext("title"))
        m = re.match(r"([^:]+):\s*(.*?),\s*Minimum Temperature:\s*(-?\d+)°C.*?Maximum Temperature:\s*(-?\d+)°C", title)
        if not m:
            continue
        when, sky, lo, hi = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
        days.append((when, sky, lo, hi))
    if not days:
        print("weather.py: unparseable feed", file=sys.stderr)
        return 1

    label = {"Today": "Today", "Monday": "Monday", "Tuesday": "Tuesday",
             "Wednesday": "Wednesday", "Thursday": "Thursday",
             "Friday": "Friday", "Saturday": "Saturday", "Sunday": "Sunday"}
    parts = []
    for when, sky, lo, hi in days[:3]:
        parts.append(f"{label.get(when, when)} {sky.lower()} ({lo}–{hi}°C)")

    print("## UK weather")
    print()
    print(f"Derbyshire: {'; '.join(parts)}. "
          f"[BBC Weather, Derby]({PAGE})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
