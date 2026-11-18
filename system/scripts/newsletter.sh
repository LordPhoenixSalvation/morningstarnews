#!/bin/bash
# ============================================================================
#  newsletter.sh — the 08:00 daily paper
# ============================================================================
#  This file is mostly one long instruction to an AI agent. Everything the
#  paper gets right is written in that instruction, so read it before you
#  change it. The rules that matter, in order:
#
#   1. Read what yesterday printed before searching (STAGE 0). A model with
#      no memory of yesterday will happily rerun yesterday's story.
#   2. Every item links to an article that was actually opened (STAGE 1).
#      No link, no item. This does more against invented news than anything.
#   3. Omit a section rather than pad it. A short paper is correct.
#   4. Weather and foraging are printed by scripts and reproduced word for
#      word (STAGE 2b). The AI never writes a forecast.
#
#  Settings live in config.sh. Paths appear below as {{JOBS}} and {{REPO}},
#  which are swapped for the real paths at the bottom of this file — you
#  should never need to edit the text in between.
# ============================================================================

set -euo pipefail
cd "$(dirname "$0")"
source ./config.sh

# --- The instruction --------------------------------------------------------
# The lines between <<'PROMPT' and PROMPT are handed to the AI unchanged
# (apart from the {{...}} swaps). The quoting around 'PROMPT' means bash does
# not touch anything inside, so $ and " and ' are all safe here.
read -r -d '' RAW_PROMPT <<'PROMPT' || true
DAILY-NEWSLETTER: Produce today's edition of Morningstar News and publish it to the website, then send a short headline digest by email to {{EMAIL}}.

STAGE 0 - NOTHING REPEATS. Before searching for anything, run: python3 {{JOBS}}/recent.py
That prints every headline and every source URL yesterday's edition already used. Those stories are SPENT. Do not run the same story again with different wording - a reader who has had yesterday's paper must not see the same item reappear. Two rules:
 - An item whose source URL appears in that list is banned, full stop. Find a different story for that slot.
 - A story that is genuinely still developing may return, but only with a NEW development that happened since the last edition, a FRESH source you have not used before, and one clause saying what has actually changed (e.g. 'the review was published this morning'). If you cannot name what is new, it has not moved - drop it.
The only links allowed to repeat are the weather block and the foraging block, which are script output and recur by design. A section coming back empty because its only story already ran is correct behaviour, not a gap to fill.
When in doubt, prefer a story that is one day old and unreported here over a bigger story already in yesterday's paper. The paper should feel new each morning.

STAGE 1 - RESEARCH. Topics, in this order: UK news, UK television, Pokemon, Tabletop games, Sci-fi and fantasy, Tech. UK news means genuinely significant UK stories of the day (politics, economy, legal, science, anything with real consequence) - 2-3 items, the national picture rather than local curiosities, and skip the topic rather than pad on a slow day. AFTER those national items, and inside the same UK news section, add a {{PLACE}} slot: on its own line put '### {{PLACE}}' and follow it with 1 item (2 only if something genuinely big has happened locally) about {{TOWN}} or {{PLACE}}, drawn from a real local source such as BBC News {{TOWN}}/{{PLACE}}, the {{TOWN}} Telegraph or {{PLACE}} Live - transport, council, courts, hospitals, universities, employers, weather warnings that actually affect the county. It must be reported by a named outlet with a link you retrieved, never written from general knowledge, and it must be current (last 24-48 hours), not a local curiosity dressed as news. If there is nothing real in {{PLACE}} that day, OMIT the '### {{PLACE}}' line and its item entirely and let the section stand on its national items alone. Never invent a local story to fill the slot. The Tabletop games section covers tabletop gaming as a whole rather than one franchise: Warhammer 40k (with Orks prioritised - lead with any Ork-specific news such as new Ork kits, codex/supplement news, rules errata, Ork-focused previews, tournament and painting content), Age of Sigmar and Specialist Games only if the week is big, plus Dungeons and Dragons and the wider RPG scene (new rulebooks and supplements, official announcements from Wizards of the Coast, major Actual Play and community news), and other notable wargames, board games and miniatures releases. Lead with 40k and Orks, then D&D, then the rest. Do not give each game its own section - it is one section, 2-3 items, best-first. UK television means what is coming up on British TV worth knowing about in the next week or two - new drama and comedy launches, returning series, major documentaries, specials, big live events, notable casting or scheduling news, and streaming exclusives from the British broadcasters. A few items at most (2-3), each with its date/channel and a link, and skip the topic entirely on a week where nothing notable is due - never list ordinary schedule filler. Sci-fi and fantasy is one section led by Star Trek: give Star Trek news first (series and film developments, casting, production, Paramount announcements, notable anniversary or fandom news), then widen to other sci-fi and fantasy only if there is strong news (Star Wars, Doctor Who, Dune, major genre film and TV, notable game or book releases in genre). 2-3 items, Star Trek first whenever there is any. Tech is one section covering AI, Linux, Android and macOS together in that order: AI model releases and industry news first (major model launches, notable research, policy and regulation, significant company news), then Linux (distribution and kernel news), then Android (major platform and Pixel developments), then macOS and Apple platforms, then Hardware (ESP32 and ESP-IDF projects, Meshtastic and LoRa, amateur and PMR radio mods, and notable maker boards and devices). For Hardware, a significant new release IS an item: check the latest releases from Meshtastic firmware, Meshtastic Android, ESP-IDF and Raspberry Pi Imager, and if one has shipped since the previous edition, report it with what actually changed, not just the version number. Group them under short inline labels (AI, Linux, Android, macOS, Hardware) within the single section - do not make separate sections - and give at most 2 items per label, AI first. For each topic search the web for genuine news from the last 24-48 hours - no filler, no old stories dressed up as new - and give at most 2 short items per topic, each with a one-line take on why it matters. Hard cap of 2 per topic or per subsection label, with one exception: if something genuinely major and breaking has happened in that topic (a resignation, a death, a recall, an outage, a live security emergency), go to 3 or 4 and say so in the item. Never exceed 2 merely to fill space - a cap of 1 is fine on a quiet day. Read articles with the trimmer, not whole pages: python3 {{JOBS}}/fetch.py <url> [max_words] returns the title and the article text with navigation, ads and cookie banners stripped, capped at a word limit (700 is a good default). Use it for every page you open. Reading a full news site raw costs roughly ten times as much for the same sentences.
EVERY item must link to the actual article you found it in: a real URL you retrieved, never a guess or constructed link, never a homepage when a specific article exists. If you cannot supply a link, drop the item. If a topic has nothing real, OMIT THE SECTION ENTIRELY - no heading, no note explaining the absence, no apology. Sections that survive must contain only items with links.

STAGE 2 - WRITE THE PAPER. Write the markdown edition to {{REPO}}/editions/$(date -u +%F).md with a heredoc: an H1 headline line first (the single most interesting story of the day, phrased as a headline, no date in it), then one short plain subheading line that states what kind of day it was in the brief (a factual standfirst, e.g. 'Nvidia's board, two Trek deaths, and a quiet day in the studios' - never a greeting, never reference corrections, the time of day you happen to be running, or the publishing process), then the sections as '## SECTION NAME' headings with items as '**Headline** - text [source](url)' or short paragraphs, then a single wry closing observation tying the day together. Tone: conversational, dry, no corporate newsletter voice. Plain markdown, short paragraphs, no tables. Put the line {{xkcd:NUMBER}} on its own line at roughly the halfway point of the paper (the publisher moves it to the nearest section boundary to the middle, so its exact position does not matter) where NUMBER is the number of an xkcd comic genuinely relevant to one of that day's stories. Find it by searching the web (e.g. 'site:xkcd.com <topic>') and confirm the comic's subject on its own page before using it - never invent a number, never pick a comic that only loosely fits, and if nothing relevant exists omit the line entirely. Do not embed images or write HTML - the publisher pulls one lead image per item automatically.

STAGE 2b - WEATHER AND FORAGING: DO NOTHING. Two pieces of the paper are generated by scripts from official feeds: the weather strip after the standfirst and the foraging note at the end. The publisher adds both automatically when it builds the page. Do not run those scripts, do not write a forecast or a foraging note, and do not put either block in the markdown yourself - a forecast written by a model is the one thing in this paper that must never happen.

STAGE 2c - REFERENCE PAGES: DO NOTHING. The Almanac, Radio & Satellites and Foraging Year pages are rebuilt before this instruction reaches you. They are not your concern.

STAGE 3 - PUBLISH. Run: cd {{REPO}} && python3 {{JOBS}}/publish.py $(date -u +%F) and confirm it prints the published URL. If it prints 'REPEATED SOURCES', that is a failure, not a warning: go back to the edition file, replace each listed item with a fresh unreported story (or drop the item), and publish again. Do not send the email with a repeat in it. The paper page is {{SITE}}/posts/$(date -u +%F).html and the front page is {{SITE}}/

STAGE 4 - EMAIL THE DIGEST. The email is NOT a copy of the paper, and you must not write it by hand. Once the paper is published, run: python3 {{JOBS}}/digest.py $(date -u +%F)
That builds the digest from the edition you just wrote: a list of that day's headlines, each linking to its section, with the subject line on stderr. Send the body it prints with send_email to {{EMAIL}}, using that subject line exactly as printed. Do not add items, summaries, source links or images, and do not restructure what it produced.

After the email is sent, stop. Do not send a second email. Do not modify this schedule or this prompt.
PROMPT

# --- Swap the placeholders for real values ----------------------------------
# This is the only place paths and names get filled in. Add a new {{TOKEN}}
# above and a matching line below if you need another setting.
PROMPT_TEXT="${RAW_PROMPT}"
PROMPT_TEXT="${PROMPT_TEXT//'{{JOBS}}'/$JOBS_DIR}"
PROMPT_TEXT="${PROMPT_TEXT//'{{REPO}}'/$REPO_DIR}"
PROMPT_TEXT="${PROMPT_TEXT//'{{SITE}}'/$SITE_URL}"
PROMPT_TEXT="${PROMPT_TEXT//'{{EMAIL}}'/$EMAIL_TO}"
PROMPT_TEXT="${PROMPT_TEXT//'{{PLACE}}'/$PLACE_NAME}"
PROMPT_TEXT="${PROMPT_TEXT//'{{TOWN}}'/$PLACE_TOWN}"
PROMPT_TEXT="${PROMPT_TEXT//'{{PAPER}}'/$PAPER_NAME}"

# Newsletter pages are addressed in the digest at {{SITE}}/posts/<date>.html
# and the masthead says {{PAPER}}. Neither appears in the instruction above.

# --- Hand it over -----------------------------------------------------------
# run_agent.sh knows how to reach the AI. See that file for the options.
exec "$JOBS_DIR/run_agent.sh" "$PROMPT_TEXT"
