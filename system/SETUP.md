# Build your own daily paper

This is the whole thing, from an empty GitHub account to a newspaper that writes
itself at 8am. No programming experience needed. If you can copy and paste a
command, you can do this.

It takes about an hour, most of which is waiting for software to install.

If you get stuck, the most likely cause is written down in
[Troubleshooting](#troubleshooting) at the bottom.

---

## What you are actually building

Every morning at 8am, your computer wakes up on a timer and does this:

1. Runs a small program that prints yesterday's headlines, so today's paper knows
   what not to repeat.
2. Runs a small program that prints the weather and what's in season.
3. Hands a long instruction to an AI, and that AI searches the web for today's
   news, writes today's paper as a text file, and saves it.
4. Runs the publisher, which turns that text file into a web page, puts it on
   your site, and adds it to the archive.
5. Emails you a list of the headlines.

You are not writing a news website. You are writing **one long instruction** and
setting a timer for it. Everything else is plumbing.

### What it is not

It is not a program that invents news. The AI can only report a story it has
opened on the web, and every item in the paper carries a link to prove it. If it
cannot find a link, it drops the item. That rule does more to stop nonsense than
any amount of code.

---

## What you need

| Thing | Why | Cost |
|---|---|---|
| A computer that stays switched on | It has to be awake at 8am | A spare laptop, a Raspberry Pi, or a rented server |
| A GitHub account | Free hosting and version history | Free |
| An AI you can send a long instruction to, which can search the web and write files | It is the reporter | Free tier to ~£5-15/month |
| An email address | For the digest (optional) | Free |

**The computer.** This runs on Linux or macOS. Windows is fine if you install
WSL (Windows Subsystem for Linux) — one command, Microsoft's instructions are
good. A Raspberry Pi 4 or 5 is ideal: it uses almost no electricity, sits in a
cupboard, and never overheats doing this.

You do not need a powerful machine. The hard work happens on the AI company's
servers, not yours.

**The AI.** This is the one part that decides how good the paper is, and the one
part with no single answer. You need something that can:

- take an instruction several pages long,
- search the web and read the pages it finds,
- write a file to your computer,
- run a command (to publish the paper),
- send an email.

Three ways to get that, in order of ease:

1. **A Rool Machine** ([rool.dev](https://rool.dev)) — a hosted AI computer that
   already has all five. This paper runs on one. Easiest by a wide margin.
2. **An agent app on your own computer** — Claude Code, OpenAI's Codex CLI, or
   aider. These run on your machine and can read, write and search. You install
   one with a single command and log in.
3. **An API plus your own tool loop** — only if the first two are impossible. It
   means writing code to handle the AI's requests. Not covered in detail here.

You will be asked to pick one when you get to
[Step 5](#step-5--tell-it-how-to-reach-the-ai).

---

## Step 1 — Make the repo

GitHub hosts the finished paper for free, and "Pages" turns a folder into a
website.

1. Sign in at [github.com](https://github.com).
2. Click **New repository**. Name it something like `my-daily-paper`. Set it
   **Public** (Pages is free on public repos). Do not add a README — you already
   have one.
3. On the new repo page, go to **Settings → Pages**.
4. Under **Source**, choose **Deploy from a branch**, branch `main`, folder
   `/ (root)`. Save.
5. Your site will live at `https://YOURNAME.github.io/YOUR-REPO/`. Nothing will
   be there yet. That's fine.

Write that address down. You will type it into `config.sh` later, with **no
trailing slash**.

### Getting the starting files

The easiest route is to copy this repository's layout. You need:

```
YOUR-REPO/
  editions/      <- today's paper lands here as a text file
  posts/         <- the built web pages
  assets/        <- the masthead image and item photos
  system/        <- the scripts and this guide
  style.css
  index.html
  .nojekyll      <- a single empty file; stops GitHub reprocessing the site
```

On GitHub, the simplest version: open this repo, click **Fork**, then rename it.
Or download it as a ZIP (**Code → Download ZIP**), unzip it, and push it to your
own repo.

### Getting the files onto your computer

On your computer, install git if it isn't there:

```bash
sudo apt install git        # Debian, Ubuntu, Raspberry Pi OS
```

Then copy your own repo down (change the name):

```bash
cd ~
mkdir -p repo && cd repo
git clone https://github.com/YOURNAME/YOUR-REPO.git
```

That creates `~/repo/YOUR-REPO`. Everything below assumes that address. If you
put it somewhere else, remember where — you'll type it into `config.sh`.

### Let it push without a password

The publisher ends by uploading the finished page. It needs permission.

The tidy way is a **fine-grained token**:

1. GitHub → your picture → **Settings → Developer settings → Personal access
   tokens → Fine-grained tokens → Generate new token**.
2. Repository access: **only your repo**. Permissions: **Contents: Read and
   write**.
3. Copy the token. It starts `github_pat_...` and you will not see it again.

Then tell git to remember it:

```bash
cd ~/repo/YOUR-REPO
git config credential.helper store
git push        # paste the token as the PASSWORD when asked
```

It's saved in `~/.git-credentials` on your own machine and never in the repo.
Treat it like a password. If it leaks, delete it on GitHub and make a new one.

---

## Step 2 — Install the software

Two programs and a handful of Python packages. One block of commands.

```bash
# The page builder and the maths for the sun and satellites
sudo apt update
sudo apt install -y pandoc python3 python3-pip python3-venv

# Python packages the scripts need
pip3 install requests beautifulsoup4 pillow matplotlib skyfield
```

Check it worked:

```bash
pandoc --version | head -1
python3 -c "import requests, bs4, PIL, matplotlib, skyfield; print('all good')"
```

You should see a pandoc version and `all good`.

One more file, needed only by the satellite page. It's 17 MB and downloads
once:

```bash
python3 -c "from skyfield.api import load; load('de421.bsp')"
```

That leaves `de421.bsp` in whatever folder you ran it from. Move it next to the
scripts in the next step.

### Put the scripts in place

```bash
mkdir -p ~/jobs
cp YOUR-REPO/system/scripts/* ~/jobs/
chmod +x ~/jobs/*.sh
mv de421.bsp ~/jobs/
cp ~/jobs/config.sh.example ~/jobs/config.sh
```

You now have a `jobs` folder with the machinery in it, and a `config.sh` with
example settings. Next step is to fill it in.

---

## Step 3 — Edit config.sh

Open it in any text editor:

```bash
nano ~/jobs/config.sh      # Ctrl-O to save, Ctrl-X to leave
```

Change these six things. Leave the rest alone for now.

```bash
JOBS_DIR="/home/YOURNAME/jobs"                  # the folder you just made
REPO_DIR="/home/YOURNAME/repo/YOUR-REPO"        # where you cloned your repo

PAPER_NAME="The Fenland Herald"                 # whatever you want on the masthead
SITE_URL="https://YOURNAME.github.io/YOUR-REPO" # no trailing slash

EMAIL_TO="you@example.com"                      # "" to skip email entirely

PLACE_NAME="Cambridgeshire"                     # appears in the paper
PLACE_TOWN="Cambridge"
PLACE_LAT="52.2053"                             # decimal degrees, north positive
PLACE_LON="0.1218"                              # decimal degrees, east positive
BBC_WEATHER_ID="2655603"                        # see below
```

**Finding your BBC Weather id.** Go to [bbc.co.uk/weather](https://www.bbc.co.uk/weather),
search your town, and look at the number at the end of the address. For Cambridge
that's `/weather/2655603`, so the id is `2655603`.

**Finding your latitude and longitude.** Search "latitude longitude of
YOUR-TOWN". If you're unsure, Google Maps: right-click your house, and the two
numbers at the top of the menu are what you want. North and east are positive,
so the UK is positive, negative — for example `52.2` and `0.1`.

**RADIO_GRID** is only used by the satellite page. If you're not a radio
amateur, put your nearest town's Maidenhead locator (search "Maidenhead locator
converter") or leave it as it is.

---

## Step 4 — Test the small programs

These are the parts that need no AI. Run each one and look at the output.

```bash
cd ~/jobs
python3 weather.py     # should print a forecast line and a BBC link
python3 forage.py      # should print what's in season
python3 almanac.py     # should print "almanac written"
python3 radio.py       # should print "radio written" and a number of passes
```

If all four print something sensible, the hardest half is done. The page
`almanac.html` and `radio.html` should now exist in your repo folder.

If one fails, that's usually the internet, a source changing its page layout, or
a missing Python package. See [Troubleshooting](#troubleshooting).

---

## Step 5 — Tell it how to reach the AI

Open `~/jobs/run_agent.sh`. It contains three options as comments. Uncomment the
one that applies to you and comment out the others.

### If you are on a Rool Machine

Change `AGENT_CMD` in `config.sh` to your own conversation path:

```bash
AGENT_CMD="rool-llm say /agents/YOURNAME/conversations/YOUR-ID"
```

Nothing else to do. The machine already has web search, file access and email.

### If you are using a local agent app

Install one, log in, and change `AGENT_CMD` to that app's one-shot command. For
Claude Code it looks like:

```bash
AGENT_CMD="claude -p --allowedTools Bash,WebSearch,Read,Write"
```

Check your app's help for the exact flag that means "run this prompt once and
exit" — it is usually `-p` or `exec`. The prompt has to arrive as a single
argument, which is what `run_agent.sh` does.

**Email is the one thing a local agent may not be able to do.** If your setup has
no email tool, set `EMAIL_TO=""` in `config.sh` and skip the digest. The paper
still publishes; you just won't be notified.

---

## Step 6 — The first paper, by hand

Never schedule something you haven't run once manually. Run the daily job now:

```bash
cd ~/jobs
./newsletter.sh
```

You'll see it think for a few minutes. Then:

```bash
ls -la ~/repo/YOUR-REPO/editions/
```

You want today's date there as a `.md` file, and `posts/<date>.html` beside it.

**To see the instruction without running it**, and to check your edits are sane:

```bash
DRY_RUN=1 ./newsletter.sh | less
```

That prints exactly what would be sent, with your paths and name already filled
in. Use it whenever you change the prompt.

**Then look at your site.** GitHub takes a minute or two to publish. Reload
`https://YOURNAME.github.io/YOUR-REPO/`.

If the page appears but looks unstyled, your `style.css` didn't upload. If you
get a 404, check Settings → Pages is set to `main` and `/ (root)`, and that the
file `.nojekyll` exists in your repo root (create an empty one if not).

---

## Step 7 — Put it on a timer

Cron is the timer. One line, run once:

```bash
crontab -e
```

Choose nano if it asks. Add these two lines, with your own paths:

```
0 8 * * 1-6 /home/YOURNAME/jobs/newsletter.sh  # DAILY-NEWSLETTER
0 9 * * 0   /home/YOURNAME/jobs/weekly.sh      # WEEKLY-PAPER
```

Read `0 8 * * 1-6` as "minute 0, hour 8, Monday to Saturday, every month". The
`1-6` matters: it is Monday to Saturday, so Sunday has no daily and the Sunday
Paper is the only paper that day. The second line is 9am on Sundays only.

If you keep the daily on Sunday as well (`0 8 * * *`) you get two papers and two
emails, and the weekly reads Monday-to-Sunday rather than the week just gone.

**Cron uses the machine's clock**, so if your computer is set to local time, 8
means 8am local. Check with `date`.

Test it without waiting a day:

```bash
# run the daily job at the next minute, purely as a test
crontab -e     # temporarily change 0 8 to the next minute, e.g. 42 15
# watch for it
tail -f /home/YOURNAME/jobs/news.log
```

Cron's output goes nowhere by default, which makes failures invisible. Wrap the
job so it writes a log:

```
0 8 * * 1-6 /home/YOURNAME/jobs/newsletter.sh >> /home/YOURNAME/jobs/news.log 2>&1  # DAILY-NEWSLETTER
```

Now `news.log` is your record of every run. When something breaks at 8am while
you're asleep, that file tells you why.

**If your computer sleeps, cron does not fire.** On a laptop, either stop it
sleeping or use a Raspberry Pi. This is the single most common reason a paper
"stops working".

---

## Step 8 — Make it yours

The paper's character lives in one place: the long instruction inside
`newsletter.sh`. Everything between `<<'PROMPT'` and `PROMPT` is that
instruction. It is written in plain English, so edit it like English.

The parts worth changing first:

**The sections.** Find `STAGE 1 - RESEARCH. Topics, in this order:` and change
the list to what you actually care about. The instruction deliberately explains
*what counts as news* for each section — keep that habit. "Pokemon" is vague;
"Pokemon: game releases, official announcements, competitive scene, notable
community news, 2 items at most" gets you a better paper.

**The local slot.** The instruction has a placeholder slot for your county,
inside the news section, with instructions to omit it when nothing real has
happened. Keep the omit rule. It is what stops a slow Tuesday producing a story
about a reopened roundabout.

**The tone.** There's a line about tone near the start of STAGE 2. "Conversational,
dry, no corporate newsletter voice" is what this paper uses. Write your own.

**Your name and place** are already handled by `config.sh` — you don't edit them
in the prompt.

### Rules worth keeping

These are not decoration. Each one exists because of a specific failure:

| Rule | The failure it prevents |
|---|---|
| Every item links to a page that was fetched | An AI writing plausible news from memory |
| Omit the section rather than pad it | A quiet news day filled with old stories |
| Read yesterday's list before searching | The same story running twice — it looks fine to the AI, which has no memory of yesterday |
| Never write the weather, only print the script's output | A confidently invented forecast |
| The publisher refuses repeated sources | Everything above, caught mechanically when the AI forgets |
| The AI never writes weather or foraging; the publisher injects them | A confidently invented forecast, and two wasted turns per edition |

The repeat check is in `publish.py`. When it prints `REPEATED SOURCES`, that is a
failure, not a warning: the paper did not go out. The fix is to replace those
items with fresh ones.

### What the scripts do on their own

Worth knowing, because it is what keeps a paper cheap:

- **The weather and the foraging note are collected by the AI, not written by it.**
  The instruction tells it to run `weather.py` and `forage.py` and paste the
  output in verbatim. It never invents a forecast — a model-written forecast is
  the one thing this system must never produce.
- **The reference pages** (Almanac, Radio, Foraging Year) are rebuilt before the
  AI is even called.
- **The closing quote is added by the publisher** from `quotes.json`. The
  instruction tells the AI to stop at its closing observation and write no
  quotation of its own, so an edition has exactly one epigraph.

That leaves the AI doing only what needs judgement: searching, choosing, and
writing.

### One conversation per edition

`config.sh` ships with `AGENT_ROTATE=0`, so every run reuses one conversation. Set
it to `1` and each run gets a brand-new conversation instead.
That matters more than it sounds. Append eighty editions to one conversation and
every morning's run sits on top of an archive it will never read. Rotating keeps
each run to that morning's work; old conversations stay on disk if you want to
look back, and each new one is logged to `~/jobs/conversations.log`.

The paper's real memory is `editions/` and `recent.py` — the files, not the chat.
That is why rotating costs nothing.

Leave `AGENT_ROTATE=0` to reuse one conversation, which is what this paper does;
set it to `1` to start a fresh one each morning.

### The Sunday paper

`weekly.sh` reads the week's seven daily editions and writes a longer piece. It
skips the repeat check on purpose — a weekly is meant to revisit the week. Either
keep it, change it, or delete the cron line and have a daily only.

With the daily running Monday to Saturday, those seven editions are exactly the
week just gone: last Sunday's paper is not a daily, so the weekly starts clean on
Monday and covers the seven days up to Saturday. Give the daily all seven days
and the weekly would instead read Monday-to-Sunday, with Sunday's own daily half
an hour old and duplicated in it.

### Optional: cheaper runs

Two scripts ship in a working state that the prompt does not call. Neither is
broken and neither is needed to get a paper out; they are here because they are
the two obvious ways to spend fewer credits, and they are worth a try once your
paper is running.

**`fetch.py` — read pages more cheaply.** The AI can read a web page directly,
but a raw page carries menus, adverts and cookie banners, and you pay for all of
it. `fetch.py` returns the title and the article text, cut at a word limit, and
takes several URLs in one call:

```bash
python3 fetch.py https://www.bbc.co.uk/news --words 300
python3 fetch.py https://www.bbc.co.uk/news https://www.bbc.co.uk/sport --words 200
```

To use it, add a line to the instruction in `newsletter.sh` telling the AI to
read pages with `fetch.py` rather than directly, and to pass several URLs per
call.

**`digest.py` — build the email from the finished edition.** The shipped prompt
has the AI write the digest itself, which is one more model call. `digest.py`
takes a published edition and returns the subject and body, so the email can be
sent by shell afterwards with no AI involved:

```bash
python3 digest.py 2026-01-01
```

Either change is small, but **change one thing at a time and measure it.** The
number that matters is not how many calls a run makes, it is the total size of
the conversation, because every turn re-sends everything before it. A run that
makes half as many calls but carries twice the text per call costs more, not
less. This paper's own history is the warning: a round of changes cut the turns
from 34 to 11 and made the edition ten times more expensive, because each turn
was carrying eight fat search results instead of two. It was reverted. Fewer,
smaller turns is the goal; fewer turns alone is not.

Set `AGENT_ROTATE=1` too if you expect to run for months — see above.

---

## Troubleshooting

**Nothing happens at 8am.**
Your computer was asleep, or cron isn't running. Check `news.log` first — if it's
empty, cron never fired. If the machine is a laptop, stop it sleeping.

**`pandoc: command not found`.**
Step 2 didn't finish. Re-run the `apt install` line.

**The paper publishes but the page is 404.**
Settings → Pages must be `main` and `/ (root)`. The `.nojekyll` file must exist in
the repo root. Wait two minutes after a push.

**The page publishes but has no styling.**
`style.css` isn't in the repo root. Copy it in and push.

**`REPEATED SOURCES`.**
Working as intended. Replace the listed items with unreported stories, or drop
them, and publish again.

**A section is empty or missing.**
Also working as intended. The instruction says omit rather than pad.

**An edition file has no weather block.** The AI runs `weather.py` during the job
and pastes its output in, so a missing strip means the script printed nothing or the
step was skipped. If `weather.py` fails, the paper goes out without the strip, which
is correct behaviour — better no forecast than an invented one. Check the edition
file: a standfirst followed straight by a `## ` heading is the tell.

**The closing quote appears twice.** The publisher appends it from `quotes.json`, so
the instruction must never ask for one too. Both `newsletter.sh` and `weekly.sh` say
so explicitly, and any blockquote that isn't real forage output renders unstyled as
`stray-quote` so you can see it. Delete the quote from the edition file and publish
again.

**`weather.py` prints nothing.**
The BBC feed changed or is down. The paper will run without a weather block —
that's the designed behaviour. Fix the parser when you have time.

**The push fails with `403` or asks for a password.**
Your token expired or lacks **Contents: Read and write**. Make a new one and
`git push` again with it.

**`skyfield` can't find `de421.bsp`.**
It looks in the current folder. `cd ~/jobs` before running `radio.py`, or move
the file next to the script.

**The AI writes a story with no link.**
Strengthen the line in the prompt that says an item without a link is dropped.
It's already there; an AI under pressure to fill a section will drift from it.
The fix is usually to make the prompt more explicit that an empty section is
correct.

---

## What this costs

The scripts cost nothing to run: a few web requests a day.

The AI is the only real cost. This one runs at roughly 50 credits an edition on
Rool, which is about €0.07. On a metered provider expect 8-10 model calls with
web search per edition — pennies rather than pounds, but search-heavy work costs
more than chat because every fetched page goes into the conversation. Check your provider's pricing before
committing — search-heavy work uses more tokens than chat because every fetched
page goes into the context.

GitHub Pages is free for public repositories.

---

## Where to go next

- `system/README.md` — how the pieces fit together, for when you want to read
  the code
- `system/scripts/newsletter.sh` — the instruction. Read this before you change
  anything
- `system/scripts/publish.py` — the publisher. Long, but it's the only file that
  has to be correct
- `system/crontab.txt` — the schedule

This guide describes a system built by one person for one county. Change the
county, change the sections, change the voice. The shape holds.
