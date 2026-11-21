#!/usr/bin/env python3
"""
fetch.py - fetch a web page and return only the useful part of it.

Why this exists: an agent that reads a whole news article can spend 10,000
tokens on menus, cookie banners and "related stories" it will never use. This
script strips all of that and prints a title line plus the article text, capped
at a word limit, so the same information costs a few hundred tokens.

    python3 fetch.py <url> [<url> ...] [--words N]

STATUS: not used by the prompt shipped in newsletter.sh. Kept as a working
option for cutting run cost - see "Optional: cheaper runs" in SETUP.md.

Fetch several pages in ONE call and separate them with a line of dashes. That
matters more than it looks: every separate call re-sends the whole conversation
to the model, so six URLs in one call can be a fifth of the cost of six calls.

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


def one(url, limit, total_cap):
    """Fetch a single URL and return the printable block, or an error line."""
    try:
        r = requests.get(url, timeout=20, headers={
            "User-Agent": "Mozilla/5.0 (compatible; MorningstarNews/1.0)"})
        r.raise_for_status()
        # Many sites send no charset, and requests then guesses Latin-1, which
        # turns "£" into "Â£". Assume UTF-8 unless the header says otherwise.
        if "charset" not in r.headers.get("content-type", "").lower():
            r.encoding = "utf-8"
    except Exception as e:
        return f"Title: (fetch failed)\nURL Source: {url}\nMarkdown Content:\nfetch failed: {e}"

    soup = BeautifulSoup(r.text, "html.parser")
    title = (soup.title.get_text(strip=True) if soup.title else url)
    body = text_of(clean(soup))

    words = body.split()
    if len(words) > limit:
        body = " ".join(words[:limit]) + " [...]"

    return f"Title: {title}\nURL Source: {url}\nMarkdown Content:\n{body}"


def main():
    args = sys.argv[1:]
    limit = 700
    # --words N sets the per-page cap; everything else is a URL.
    if "--words" in args:
        i = args.index("--words")
        limit = int(args[i + 1])
        del args[i:i + 2]
    if not args:
        sys.exit(__doc__)

    # A hard ceiling on the whole call, so a long list of URLs cannot flood the
    # conversation. Roughly 900 words of body text per page is plenty.
    total_cap = 1400 * len(args)
    out, used = [], 0
    for u in args:
        block = one(u, limit, total_cap)
        out.append(block)
        used += len(block.split())
        if used > total_cap:
            out.append("(stopped: output cap reached, fetch the rest separately)")
            break
    print("\n\n" + "-" * 70 + "\n\n".join(out))

    # Exit non-zero only if nothing at all could be read.
    if all("fetch failed" in b for b in out):
        sys.exit(1)


if __name__ == "__main__":
    main()
