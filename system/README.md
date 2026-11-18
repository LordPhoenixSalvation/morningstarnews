# How the paper works

**Building your own? Read [SETUP.md](SETUP.md) instead** — it walks through it
from an empty GitHub account, in plain English, with nothing assumed.

This page is the shorter description for someone who wants to know how the pieces
fit before reading code.

---

## The shape of it

```
cron ──► newsletter.sh ──► run_agent.sh ──► the AI
             │                                │
             │   (before the AI is called)    │
             ├─ almanac.py, radio.py, forage_guide.py   reference pages
             └─ run_agent.sh opens a fresh conversation
                                              │
                              the AI researches, writes editions/<date>.md,
                              then runs the publisher and sends the email
                                              │
                                              ▼
                                        publish.py <date>
                                              │
             weather.py + forage.py ──────────┤  injected at build time
             digest.py ───────────────────────┤  builds the email body
                                              │
                              editions/*.md ──► HTML + stylesheet + RSS
                                              │
                                       git push ──► GitHub Pages
```

Two cron jobs:

| When | Script | What |
|---|---|---|
| 08:00 daily | `newsletter.sh` | Researches and publishes the daily paper, emails a digest |
| 09:00 Sunday | `weekly.sh` | The Sunday Paper — longer, weekly, kept out of the daily archive |

## What the AI does, and what it doesn't

The AI is only used for the part that needs judgement: searching, choosing
stories, and writing them up. Everything mechanical is a script, because scripts
are cheaper, predictable, and cannot invent a forecast.

| Done by | What |
|---|---|
| Scripts, before the AI is called | Reference pages, a fresh conversation |
| The AI | Research, selection, writing the edition |
| The publisher, at build time | Weather block, foraging note, images, the xkcd comic, HTML, RSS, git push |
| `digest.py` | The email body |

One edition is around nine model calls, most of them searches. The weather, the
foraging note and the reference pages used to cost five turns a day between them
and now cost none.

## Every setting lives in one file

`config.sh` holds the paper's name, its public address, the email address, the
paths, and your location. Every script reads from it, and `config.py` is how the
Python scripts read it. There is no path, address or place name hardcoded
anywhere else.

That matters most when you copy this: change `config.sh` and the whole system
follows, including the masthead, the email links and the almanac.

## The scripts

| File | Language | Job |
|---|---|---|
| `config.sh` | bash | Every setting. The only file you edit |
| `config.py` | Python | Reads `config.sh` for the Python scripts |
| `newsletter.sh` | bash | The daily prompt. Fills in the settings and hands it to the AI |
| `weekly.sh` | bash | The Sunday prompt. Same pattern, longer brief |
| `run_agent.sh` | bash | Calls the AI. Swap the block inside to change provider |
| `publish.py` | Python | Markdown → HTML, CSS, front page, archive, RSS, git push |
| `recent.py` | Python | Prints the previous edition's headlines and sources |
| `fetch.py` | Python | Fetches a page and returns only its article text, capped |
| `digest.py` | Python | Builds the morning email from the finished edition |
| `weather.py` | Python | The forecast, from the BBC feed |
| `forage.py` | Python | Today's seasonal note |
| `forage_guide.py` | Python | The Foraging Year — twelve monthly pages, 30-day cache |
| `almanac.py` | Python | Sun and moon, warnings, river levels |
| `radio.py` | Python | Satellite passes and space weather |
| `quotes.json` | JSON | The quote pool the closing line is drawn from |

Every function in the Python files has a docstring saying what it is for. The
two shell scripts that carry the prompts explain at the top what each stage does
and why.

## The publisher

`publish.py <date>` reads `editions/<date>.md` and does the rest:

- **Repeat check.** Compares every source URL against the previous edition and
  prints a blocking `REPEATED SOURCES` failure. This exists because a model with
  no memory of yesterday will rerun yesterday's story and it will look fine to
  the model.
- **Pulled blocks.** `{{xkcd:2451}}` and the weather/foraging output are
  substituted at build time. Those are script output, reproduced verbatim.
- **Page furniture.** Front page, `history.html`, `feed.xml`, the reference pages
  and the dropdown menu bar are regenerated on every publish.
- **The push.** `git add -A && git commit && git push origin main`. If the push
  fails, the edition is built but not live and the script exits non-zero.

## Dependencies

```
pandoc            markdown → HTML
python3           + requests, beautifulsoup4, Pillow, matplotlib
skyfield          satellite passes (radio.py)
de421.bsp         JPL ephemeris, 17 MB, downloaded once, not in this repo
```

```bash
python3 -c "from skyfield.api import load; load('de421.bsp')"
```

## Credentials

None in this repo, deliberately.

- **Push access.** This machine uses a token in the git remote URL, stored in
  `.git/config` and never committed. A fine-grained token with Contents:
  read-and-write, or an SSH deploy key, is better practice.
- **Email.** Sent through the agent's own mail tool. No SMTP credentials here.
- **The AI.** `run_agent.sh` calls `rool-llm say` on a Rool Machine. Any agent
  that can take a long instruction, search the web, write files and run commands
  will do; the prompt is portable, the invocation is not.

Published copies have the personal email and conversation id replaced with
placeholders.

## The rules that actually matter

The code is the easy half. What keeps the paper honest is the instruction text in
`newsletter.sh`:

1. **Every item links to a page opened during that run.** No link, no item.
2. **Read yesterday's list before searching.** A story may return only with a
   fresh source and a clause naming what changed.
3. **Omit a section rather than pad it.** A short paper is correct.
4. **Pulled data is never rewritten.** Weather and foraging are script output,
   reproduced verbatim, with the source named.

## Keeping this current

The live scripts are in the jobs folder (`JOBS_DIR` in `config.sh`). After
changing any of them:

```bash
"$JOBS_DIR/sync_system.sh"
cd "$REPO_DIR"
git add system && git commit -m "Sync system scripts" && git push
```

`sync_system.sh` copies the scripts, publishes `config.sh` as
`config.sh.example`, and replaces personal details. Never copy them here by hand.
