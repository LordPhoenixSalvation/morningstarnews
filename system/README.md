# How Morningstar News works

This directory holds the machinery behind the paper: the scripts that gather data,
the prompts that drive each edition, the publisher, and the cron schedule. It is a
copy of what actually runs, synced from the live machine — see **Keeping this
current** at the bottom.

Nothing here is clever. Two cron jobs, a handful of Python scripts, and a job
prompt that says what to do. The interesting part is the rules, not the code.

---

## The shape of it

```
cron ──► newsletter.sh ──► rool-llm say "<the whole prompt>"
                                   │
                                   ├─ python3 weather.py       (BBC, Derby)
                                   ├─ python3 forage.py        (what's in season)
                                   ├─ python3 recent.py        (what already ran)
                                   │
                                   └─ agent researches, writes editions/<date>.md
                                              │
                                              ▼
                                        publish.py <date>
                                              │
                                    edits/*.md ─► HTML + stylesheet
                                              │
                                       git commit && git push
                                              │
                                              ▼
                                    GitHub Pages serves the site
```

Three jobs:

| When | Script | What |
|---|---|---|
| 08:00 daily | `newsletter.sh` | Researches and publishes the daily paper, emails a digest |
| 09:00 Sunday | `weekly.sh` | The Sunday Paper — longer, weekly, kept out of the daily archive |

## The crontab

```
0 8 * * * /home/u10000/jobs/newsletter.sh # DAILY-NEWSLETTER
0 9 * * 0 /home/u10000/jobs/weekly.sh    # WEEKLY-PAPER
```

The daily runs at 08:00 **UTC**. The comments at the end of each line are there so
`crontab -l | grep DAILY-NEWSLETTER` can find and replace a single job without
disturbing the others.

## The scripts

| File | Language | Job |
|---|---|---|
| `newsletter.sh` | bash | The daily prompt. Sets the vars, calls the four data scripts, hands everything to the agent |
| `weekly.sh` | bash | The Sunday prompt. Same pattern, longer brief, no repeat check by design |
| `publish.py` | Python | Markdown → HTML, CSS, front page, archive, RSS, git push. ~750 lines |
| `recent.py` | Python | Prints the previous edition's headlines and source URLs — what has already run |
| `weather.py` | Python | BBC 3-day forecast for Derby (location 2651347) |
| `forage.py` | Python | Today's seasonal note from the National Allotment Society |
| `forage_guide.py` | Python | The Foraging Year — twelve monthly pages, 30-day cache |
| `almanac.py` | Python | Sun and moon, Met Office warnings, Environment Agency river levels |
| `radio.py` | Python | Satellite passes over Derby (IO92) via CelesTrak TLEs and Skyfield |
| `quotes.json` | JSON | The 30-quote pool the closing quote is drawn from |

## The publisher

`publish.py <date>` reads `editions/<date>.md` and does the rest. Worth knowing:

- **Repeat check.** It compares every source URL in the edition against the
  previous edition and prints a blocking `!! REPEATED SOURCES` failure if any
  match. This exists because a model with no memory of yesterday will rerun
  yesterday's story, and it will look perfectly fine to the model.
- **Pulled blocks.** Lines like `{{weather}}`, `{{forage}}`, `{{xkcd:2451}}` are
  substituted at build time. Weather and foraging come from script output and are
  reproduced verbatim — never written by the agent.
- **Page furniture.** Front page, `history.html`, `feed.xml`, and the dropdown
  menu bar are all regenerated on every publish. Nothing is hand-maintained.
- **The push.** `git add -A && git commit && git push origin main`. If the push
  fails the edition is built but not live, and the script exits non-zero.

## Dependencies

```
pandoc            markdown → HTML
python3           + Pillow, requests, beautifulsoup4
skyfield          satellite passes (radio.py)
matplotlib        moon and sun graphics
```

Also `de421.bsp`, the JPL ephemeris Skyfield needs — 17 MB, downloaded once, not
in this repo:

```
python3 -c "from skyfield.api import load; load('de421.bsp')"
```

## Credentials

None in this repo, deliberately. The scripts assume:

- **A git remote with push access.** This machine uses a token embedded in the
  remote URL (`x-access-token:<PAT>@github.com/...`), which lives in `.git/config`
  and is never committed. Better practice is an SSH deploy key or `gh auth login`.
- **Email.** Sending goes through the agent's own mail tool, which uses the
  machine's configured address — no SMTP credentials here.
- **The agent.** `newsletter.sh` calls `rool-llm say <conversation> "<prompt>"`,
  a Rool command. On another platform the equivalent is whatever lets you invoke
  a model with a long instruction and tool access — the prompt itself is portable,
  the invocation is not.

The copies here have the personal email address and conversation ID replaced with
placeholders. They are safe to read; they will not run as-is.

## The rules that actually matter

The code is the easy half. What keeps the paper honest is the instruction text in
`newsletter.sh`, and it comes down to four things:

1. **Every item needs a link the agent opened during that run.** No link, no item.
   This single rule does more against invented news than everything else combined.
2. **Omit a section rather than pad it.** A short paper is correct; a padded one
   is a lie about the day.
3. **Read yesterday's list first.** `recent.py` runs before any searching, so the
   agent knows what has already been printed. A developing story may return only
   with a fresh source and a clause naming what changed.
4. **Pulled data is never rewritten.** Weather, foraging, river levels and
   satellite passes are script output, reproduced verbatim, with the source named.

## Keeping this current

The live scripts are in `/home/u10000/jobs`. After changing any of them:

```
/home/u10000/jobs/sync_system.sh
cd /home/u10000/repo/morningstarnews
git add system && git commit -m "Sync system scripts" && git push
```

`sync_system.sh` copies the scripts and scrubs the personal details. Never copy
the files here by hand — you will leak an email address eventually.
