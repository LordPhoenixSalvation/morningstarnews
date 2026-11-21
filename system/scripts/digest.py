#!/usr/bin/env python3
"""
digest.py - build the emailed headline digest from a published edition.

The digest is not a copy of the paper. It is a scannable list of that day's
headlines, each linking straight to the section it appears in.

    python3 digest.py [YYYY-MM-DD]

STATUS: not used by the prompt shipped in newsletter.sh. Kept as a working
option for cutting run cost - see "Optional: cheaper runs" in SETUP.md.

Prints a complete email body to stdout, ready to hand to send_email. Building
it from the edition file rather than by retyping it means the links and the
section anchors are always right.

The subject line is printed separately on stderr, so callers can capture it:

    subj=$(python3 digest.py | ...)   # body
"""
import sys
import os
import re
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import PAPER, SITE_URL, REPO  # noqa: E402

# Stationers' names for the weekday, kept here so the script has no locale
# dependency.
# Short inline labels used inside the Tech section. They are bold in the
# edition but they are not headlines, so the digest skips them.
LABELS = {"ai", "linux", "android", "macos", "hardware"}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = ["", "January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def slug(name):
    """Turn a section heading into the anchor the publisher generates."""
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", name.lower())).strip("-")


def parse(md):
    """Return (title, [ (section, [headline, ...]) ]).

    Headlines are the bold run at the start of an item: **Headline** - text.
    A sub-slot such as '### Derbyshire' is folded into the section above it,
    because the digest has no room for a heading of its own."""
    title = ""
    m = re.search(r"^#\s+(.+)$", md, re.M)
    if m:
        title = m.group(1).strip()

    sections = []
    for line in md.split("\n"):
        if line.startswith("## "):
            sections.append((line[3:].strip(), []))
        elif line.startswith("### "):
            continue  # sub-slot heading: its items belong to the parent above
        else:
            h = re.match(r"^\*\*(.+?)\*\*\s*[\u2014-]?\s*(.*)$", line.strip())
            if not h or not sections:
                continue
            head, rest = h.group(1).strip(), h.group(2).strip()
            if head.lower() in LABELS:
                # An inline label: the headline is the sentence after the dash.
                # Cut at the first full stop so the digest stays one line.
                head = re.split(r"(?<=[.!?])\s", rest)[0].strip().rstrip(".") or head
                if len(head) > 95:
                    head = head[:95].rsplit(" ", 1)[0] + "..."
            if head:
                sections[-1][1].append(head)
    return title, [(s, hs) for s, hs in sections if hs]


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    path = f"{REPO}/editions/{date}.md"
    if not os.path.exists(path):
        sys.exit(f"digest: missing {path}")

    title, sections = parse(open(path, encoding="utf-8").read())
    d = datetime.date.fromisoformat(date[:10])
    page = f"{SITE_URL}/posts/{date}.html"

    out = ["Morning.", ""]
    for name, heads in sections:
        out.append(f"**{name.upper()}**")
        for h in heads:
            out.append(f"[{h}]({page}#{slug(name)})")
        out.append("")
    out.append(f"Read the whole paper: {SITE_URL}/")

    print("\n".join(out))
    short = title.split(":")[0].strip()
    print(f"{PAPER} - {DAYS[d.weekday()]} {d.day} {MONTHS[d.month]} - {short}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
