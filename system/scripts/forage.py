#!/usr/bin/env python3
"""Pull this month's in-season foraging notes from a reputable UK source and
print them as a one-line markdown footer. Species names are lifted verbatim
from the source page - nothing here is generated or identified by us."""
import datetime, re, sys, requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"}
SKIP = re.compile(r"what not to forage|safety|sustainab|recipe|instruction|method|"
                  r"about us|newsletter|join|follow|share|related|comments", re.I)
NUM = re.compile(r"^\s*\d+\s*[.)]\s*")
PAIR_PAREN = re.compile(r"^([A-Z][A-Za-z'\- ]{2,28}?)\s*\(([A-Z][a-z]+ [a-z\-]+)\)")
PAIR_BARE = re.compile(r"^([A-Z][A-Za-z'\- ]{2,28}?)\s+([A-Z][a-z]+ [a-z\-]+)\b")
LIMIT = 3
STOP = {"the", "our", "your", "where", "how", "what", "why", "when", "this", "that",
        "these", "those", "creamy", "recipe", "instructions", "method", "ingredients",
        "and", "with", "from", "for", "how to", "find", "top", "best"}

def sources(month):
    m = month.capitalize()
    return [f"https://thenas.org.uk/{m}-Foraging",
            f"https://www.countryfile.com/how-to/foraging/foraging-in-{month.lower()}",
            f"https://foragerslog.co.uk/what-to-forage/{month.lower()}"]

def species_of(text):
    text = NUM.sub("", text).strip()
    m = PAIR_PAREN.match(text) or PAIR_BARE.match(text)
    if not m:
        return None
    name, latin = m.group(1).strip(" ,-"), m.group(2)
    words = name.split()
    if len(words) > 3 or any(w.lower().strip(".,") in STOP for w in words):
        return None
    if not all(w[0].isupper() for w in words):
        return None
    genus, _, epithet = latin.partition(" ")
    NOT_LATIN = {"Good", "Great", "Best", "Wild", "Edible", "Common", "Black",
                 "White", "Red", "Green", "Sweet", "Fresh", "Young", "Large",
                 "Small", "Early", "Late", "Field", "Wood", "Garden", "Hedge"}
    if genus in NOT_LATIN:
        return None
    if not (genus[:1].isupper() and genus[1:].islower() and len(genus) > 3):
        return None
    if not (epithet.islower() and len(epithet) > 3):
        return None
    # a misparse shows up as the genus leaking into the English name
    if any(w.lower() == genus.lower() for w in words):
        return None
    # reject if the English name contains the Latin epithet or a capitalised
    # fourth+ word that looks like taxonomy leaking through
    if any(w.lower() == epithet.lower() for w in words):
        return None
    if any(len(w) > 5 and w[0].isupper() and w.lower() in latin.lower() for w in words):
        return None
    return name, latin

def harvest(url):
    r = requests.get(url, headers=UA, timeout=30)
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    for t in soup(["script", "style", "nav", "footer", "header", "form"]):
        t.decompose()
    sections, cur = [], None
    for el in soup.find_all(["h2", "h3", "li"]):
        if el.name in ("h2", "h3"):
            heading = el.get_text(" ", strip=True)
            cur = None if SKIP.search(heading) else []
            if cur is not None:
                sections.append(cur)
            continue
        if cur is None:
            continue
        got = species_of(el.get_text(" ", strip=True))
        if got and all(got[0].lower() != n.lower() for n, _ in cur):
            cur.append(got)
    sections = [x for x in sections if x]
    if not sections:
        return None
    picks = [x[0] for x in sections[:LIMIT]]
    if len(picks) < LIMIT:
        for sec in sections:
            for item in sec[1:]:
                if all(item[0].lower() != p[0].lower() for p in picks):
                    picks.append(item)
                if len(picks) >= LIMIT:
                    break
            if len(picks) >= LIMIT:
                break
    return picks[:LIMIT] or None

def main():
    month = datetime.date.today().strftime("%B")
    for url in sources(month):
        try:
            picks = harvest(url)
        except Exception as e:
            print(f"forage.py: {url} failed ({e})", file=sys.stderr)
            continue
        if picks:
            items = ", ".join(n for n, _ in picks[:LIMIT])
            print("> **In season — " + month + ":** " + items + ".")
            print(">")
            print("> A calendar nudge, not identification — check a proper field guide "
                  f"before eating anything. [Source]({url})")
            return 0
    print("forage.py: no source available today", file=sys.stderr)
    return 1

if __name__ == "__main__":
    sys.exit(main())
