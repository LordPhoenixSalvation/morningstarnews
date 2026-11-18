#!/usr/bin/env python3
"""
fetch.py - fetch a web page and return only the useful part of it.

Why this exists: an agent that reads a whole news article can spend 10,000
tokens on menus, cookie banners and "related stories" it will never use. This
script strips all of that and prints a title line plus the article text, capped
at a word limit, so the same information costs a few hundred tokens.

    python3 fetch.py <url> [max_words]

Prints:
    Title: <page title>
    URL Source: <url>
    Markdown Content:
    <trimmed text>

Exits non-zero and prints nothing useful if the page cannot be read, so a
caller can fall back to another source.
"""
import sys
import re
import requests
from bs4 import BeautifulSoup

# Tags that never contain article text. Dropping them first is what does most
# of the saving.
JUNK = ("script", "style", "nav", "header", "footer", "aside", "form",
        "noscript", "iframe", "svg", "figure", "button")

# Class/id fragments that mark navigation, sharing bars and promos. Matched
# case-insensitively against every element's class and id.
JUNK_HINT = re.compile(
    r"(nav|menu|share|social|cookie|consent|newsletter|subscribe|promo|"
    r"advert|ad-|related|recommend|comment|sidebar|footer|header|breadcrumb|"
    r"paywall|banner|popup|modal)", re.I)


def clean(soup):
    """Remove the tags that never hold article prose.

    Deliberately conservative: an earlier version also deleted anything whose
    class or id looked like navigation or a sidebar, which wiped entire BBC
    articles because their real article container was called
    'ContainerWithSidebarWrapper'. Tags are only dropped by name now, and the
    paragraph filter in text_of does the rest of the work.
    """
    for tag in soup(list(JUNK)):
        tag.decompose()
    return soup


def text_of(soup):
    """Prefer <p> paragraphs, which is where article prose lives. Fall back to
    the whole body if a page has no paragraphs at all."""
    paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    paras = [p for p in paras if len(p.split()) > 6]
    if paras:
        return "\n\n".join(paras)
    body = soup.find("article") or soup.find("main") or soup.body or soup
    return re.sub(r"\n{3,}", "\n\n", body.get_text("\n", strip=True))


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    url = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 700
    try:
        r = requests.get(url, timeout=20, headers={
            "User-Agent": "Mozilla/5.0 (compatible; MorningstarNews/1.0)"})
        r.raise_for_status()
        # Many sites send no charset, and requests then guesses Latin-1, which
        # turns "£" into "Â£". Assume UTF-8 unless the header says otherwise.
        if "charset" not in r.headers.get("content-type", "").lower():
            r.encoding = "utf-8"
    except Exception as e:
        sys.exit(f"fetch failed: {e}")

    soup = BeautifulSoup(r.text, "html.parser")
    title = (soup.title.get_text(strip=True) if soup.title else url)
    body = text_of(clean(soup))

    words = body.split()
    if len(words) > limit:
        body = " ".join(words[:limit]) + " [...]"

    print(f"Title: {title}")
    print(f"URL Source: {url}")
    print("Markdown Content:")
    print(body)


if __name__ == "__main__":
    main()
