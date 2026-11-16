#!/usr/bin/env python3
"""Availability watcher. Silent unless something changes.

Compares current public release/stock state against the last run. Prints a
plain-text summary and exits 0 if anything changed, exits 1 (printing nothing)
when everything is as it was - so the cron wrapper only wakes the agent on a
real change.
"""
import json, os, sys, urllib.request, datetime as dt, re

STATE = "/home/u10000/jobs/watch_state.json"
UA = {"User-Agent": "morningstar-watch/1.0"}

def get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def check():
    out = {}
    # Meshtastic firmware
    try:
        j = json.loads(get("https://api.github.com/repos/meshtastic/firmware/releases/latest"))
        out["meshtastic_firmware"] = {"v": j.get("tag_name"), "name": j.get("name"),
                                      "url": j.get("html_url"),
                                      "at": (j.get("published_at") or "")[:10]}
    except Exception as e:
        print(f"watch: meshtastic_firmware failed ({e})", file=sys.stderr)
    # Meshtastic Android
    try:
        j = json.loads(get("https://api.github.com/repos/meshtastic/Meshtastic-Android/releases/latest"))
        out["meshtastic_android"] = {"v": j.get("tag_name"), "name": j.get("name"),
                                     "url": j.get("html_url"),
                                     "at": (j.get("published_at") or "")[:10]}
    except Exception as e:
        print(f"watch: meshtastic_android failed ({e})", file=sys.stderr)
    # ESP-IDF
    try:
        j = json.loads(get("https://api.github.com/repos/espressif/esp-idf/releases?per_page=5"))
        rel = [r for r in j if not r.get("prerelease") and not r.get("draft")]
        if rel:
            out["esp_idf"] = {"v": rel[0].get("tag_name"), "name": rel[0].get("name"),
                              "url": rel[0].get("html_url"),
                              "at": (rel[0].get("published_at") or "")[:10]}
    except Exception as e:
        print(f"watch: esp_idf failed ({e})", file=sys.stderr)
    # Raspberry Pi Imager
    try:
        j = json.loads(get("https://downloads.raspberrypi.org/os_list_imagingutility_v3.json"))
        v = j.get("imager", {}).get("latest_version")
        if v:
            out["rpi_imager"] = {"v": v, "name": f"Raspberry Pi Imager {v}",
                                 "url": "https://www.raspberrypi.com/software/", "at": ""}
    except Exception as e:
        print(f"watch: rpi_imager failed ({e})", file=sys.stderr)
    return out

LABELS = {"meshtastic_firmware": "Meshtastic firmware",
          "meshtastic_android": "Meshtastic Android",
          "esp_idf": "ESP-IDF",
          "rpi_imager": "Raspberry Pi Imager"}

def main():
    cur = check()
    if not cur:
        print("watch: every source failed, nothing to compare", file=sys.stderr)
        return 1
    try:
        old = json.load(open(STATE))
    except Exception:
        old = {}
    changes = []
    for k, v in cur.items():
        prev = old.get(k, {})
        if prev.get("v") != v.get("v"):
            if prev:
                changes.append((LABELS.get(k, k), prev.get("v"), v))
            else:
                changes.append((LABELS.get(k, k), None, v))
    json.dump(cur, open(STATE, "w"), indent=1)
    if not changes:
        return 1
    lines = ["WATCH: change detected - send this to Neil by email now, subject "
             "'Morningstar Watch: <short summary>', body as below, no paper, no extra commentary."]
    for label, was, v in changes:
        if was:
            lines.append(f"- {label}: {was} -> {v.get('v')} ({v.get('at') or 'no date'})")
        else:
            # first run: record silently rather than report the whole world as new
            lines.append(f"- {label}: {v.get('v')} (first run, baseline)")
        lines.append(f"  {v.get('url')}")
    first_run = all(w is None for _, w, _ in changes)
    if first_run:
        return 1
    print("\n".join(lines))
    return 0

if __name__ == "__main__":
    sys.exit(main())
