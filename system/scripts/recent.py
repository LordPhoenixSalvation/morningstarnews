#!/usr/bin/env python3
"""Print what the last N editions already covered, so the daily run does not repeat itself.

Usage: recent.py [n]   (default 1 = just the previous edition)
Output: for each edition, the headline of every item and the source URL it used.
"""
import re, sys, glob, os
from datetime import date, timedelta

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
REPO = config.REPO   # folder holding editions/, set in config.sh
# Links that legitimately recur every day - never treat as repeats.
RECURRING = ("bbc.co.uk/weather", "thenas.org.uk/", "foragers")

def norm(u):
    return u.rstrip("/").split("?")[0].lower()

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    today = date.today()
    cands = sorted((f for f in glob.glob(os.path.join(REPO, "editions/*.md"))
                    if not f.endswith("-weekly.md")
                    and os.path.basename(f)[:10] < today.isoformat()),
                   reverse=True)
    files = cands[:n]
    if not files:
        print("No previous edition found - nothing to avoid.")
        return
    seen_urls, out = set(), []
    for f in sorted(files, reverse=True):
        t = open(f).read()
        stamp = os.path.basename(f)[:10]
        lines = []
        section = ""
        for line in t.splitlines():
            m = re.match(r"^##\s+(.+)$", line)
            if m:
                section = m.group(1).strip()
                continue
            for head in re.findall(r"\*\*(.+?)\*\*", line):
                if head.lower().startswith("in season"):
                    continue  # foraging block, recurs daily
                head = re.sub(r"^(AI|Linux|Android|macOS|Hardware)\s*[-\u2014]\s*", "", head)
                links = [u for u in re.findall(r"\]\((https?://[^)\s]+)\)", line)
                         if not any(r in u for r in RECURRING)]
                lines.append((section, head, links))
                seen_urls.update(norm(u) for u in links)
        if lines:
            out.append("### %s" % stamp)
            for section, head, links in lines:
                out.append("- [%s] %s%s" % (section or "-", head,
                                            ("  <- " + links[0]) if links else ""))
    print("ALREADY COVERED IN THE PREVIOUS EDITION - do not run these again unless there is a\n"
          "genuinely new development (say what is new in the item, and prefer a fresh source):\n")
    print("\n".join(out))
    print("\nSources already used (%d). Do not reuse unless the story has moved on:" % len(seen_urls))
    for u in sorted(seen_urls):
        print("  " + u)

main()
