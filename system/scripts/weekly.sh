#!/bin/bash
# ============================================================================
#  weekly.sh — the Sunday Paper, 09:00 on Sundays
# ============================================================================
#  Same pattern as newsletter.sh: one long instruction to the AI, settings
#  from config.sh, placeholders swapped at the bottom.
#
#  Two differences from the daily, both deliberate:
#   - It reads the week's seven daily editions first and builds from them,
#     so the Sunday paper is a record of what actually happened, not a fresh
#     guess at the news.
#   - No repeat check when publishing. A weekly is expected to revisit the
#     week's stories; the publisher's check is for the dailies.
# ============================================================================

set -euo pipefail
cd "$(dirname "$0")"
source ./config.sh

read -r -d '' RAW_PROMPT <<'PROMPT' || true
SUNDAY PAPER: Produce this week's Sunday Paper and publish it to the website. This is the weekend edition of {{PAPER}} - a longer, unhurried read than the daily, not a bigger daily. It is one edition per week.

STAGE 1 - GATHER THE WEEK. Read the last seven daily editions in {{REPO}}/editions/ (the seven most recent YYYY-MM-DD.md files, not the -weekly ones). Those are your record of what actually happened this week - do not invent stories that were not in them, and do not repeat them verbatim either. Then search the web for the week's genuinely significant UK news that the dailies may have missed, and for one or two things that developed after a daily ran (a follow-up, a correction, a consequence), and include any {{PLACE}} story from the week that mattered beyond the county line or was under-reported locally (from BBC News {{TOWN}}/{{PLACE}}, the {{TOWN}} Telegraph or {{PLACE}} Live, with a real retrieved link).

STAGE 2 - WRITE IT. Write to {{REPO}}/editions/$(date -u +%F)-weekly.md with a heredoc. Shape:
- H1: the single biggest story of the week as a headline, no date in it.
- One plain standfirst line saying what kind of week it was.
- '## The week in brief' - six to ten one-line entries, each a real story from the week with a [source](url), in the style of a serious paper's week-in-review column.
- Then three or four '## ' sections of proper length (150-300 words each), on the week's most consequential threads. Choose them from what actually happened - do not force a fixed list of topics. Likely candidates: UK politics and economy, the war or conflict story of the week, science and technology, and whatever dominated tabletop, Trek or Pokémon this week if it genuinely mattered.
- '## From the week's papers' - three or four short interesting items from the dailies that did not lead anywhere, given a second life.
- '## The week ahead' - three or four things actually due next week (votes, launches, releases, matches, TV premieres), each dated.
- A closing observation of two or three sentences, longer and more reflective than the daily's one-liner.
Tone: the same dry British newspaper voice as the daily, but with room to breathe - proper sentences, developed argument, no bullet-point padding. Every factual claim from outside the dailies needs a real retrieved source link. If you have not verified it, leave it out. Put {{xkcd:NUMBER}} on its own line about a third of the way in if a comic genuinely fits.

STAGE 3 - NO QUOTE, BUT PULL WEATHER AND FORAGING. Do NOT write a closing quotation, epigraph or attribution, and do not start any line with '>': the publisher appends the curated quote from quotes.json automatically, so a quote written here appears twice at the foot of the page. Two pieces of the paper ARE script output and you must reproduce them exactly, character for character - do not paraphrase, summarise, tidy, "improve" or invent any of it, and never write a forecast or a foraging note yourself. The foraging block is the ONLY blockquote anywhere in the edition.
  Run: python3 {{JOBS}}/weather.py
  If it prints, insert that output in full immediately after the standfirst line, before the first section heading. If it prints nothing (it exits non-zero when the BBC feed is down), OMIT the weather block entirely rather than writing your own.
  Run: python3 {{JOBS}}/forage.py
  If it prints, insert that output in full as the very last thing in the file, after the closing observation. If it prints nothing, omit it.
Do not edit the scripts, their output, or the links they contain.

STAGE 4 - PUBLISH. Run: cd {{REPO}} && python3 {{JOBS}}/publish.py $(date -u +%F)-weekly and confirm it prints the published URL. It will also put a 'Sunday Paper' link at the top of the front page and in the archive. Do not let the weekly replace the front page's daily edition.

STAGE 5 - EMAIL. Send one email to {{EMAIL}} with subject '{{PAPER}} - The Sunday Paper - <week's headline short>'. Body: three or four lines only - the week's headline, the one detail that matters most, and a link to {{SITE}}/posts/$(date -u +%F)-weekly.html . It is a pointer, not a copy. Send one email, then stop.
PROMPT

PROMPT_TEXT="${RAW_PROMPT}"
PROMPT_TEXT="${PROMPT_TEXT//'{{JOBS}}'/$JOBS_DIR}"
PROMPT_TEXT="${PROMPT_TEXT//'{{REPO}}'/$REPO_DIR}"
PROMPT_TEXT="${PROMPT_TEXT//'{{SITE}}'/$SITE_URL}"
PROMPT_TEXT="${PROMPT_TEXT//'{{EMAIL}}'/$EMAIL_TO}"
PROMPT_TEXT="${PROMPT_TEXT//'{{PLACE}}'/$PLACE_NAME}"
PROMPT_TEXT="${PROMPT_TEXT//'{{TOWN}}'/$PLACE_TOWN}"
PROMPT_TEXT="${PROMPT_TEXT//'{{PAPER}}'/$PAPER_NAME}"

exec "$JOBS_DIR/run_agent.sh" "$PROMPT_TEXT"
