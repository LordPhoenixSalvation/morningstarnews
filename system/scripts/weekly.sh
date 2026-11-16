#!/bin/bash
rool-llm say /agents/rool/conversations/<conversation-id> "SUNDAY PAPER: Produce this week's Sunday Paper and publish it to the website. This is the weekend edition of Morningstar News - a longer, unhurried read than the daily, not a bigger daily. It is one edition per week.

STAGE 1 - GATHER THE WEEK. Read the last seven daily editions in /home/u10000/repo/morningstarnews/editions/ (the seven most recent YYYY-MM-DD.md files, not the -weekly ones). Those are your record of what actually happened this week - do not invent stories that were not in them, and do not repeat them verbatim either. Then search the web for the week's genuinely significant UK news that the dailies may have missed, and for one or two things that developed after a daily ran (a follow-up, a correction, a consequence), and include any Derbyshire story from the week that mattered beyond the county line or was under-reported locally (from BBC News Derby/Derbyshire, the Derby Telegraph or Derbyshire Live, with a real retrieved link).

STAGE 2 - WRITE IT. Write to /home/u10000/repo/morningstarnews/editions/\$(date -u +%F)-weekly.md with a heredoc. Shape:
- H1: the single biggest story of the week as a headline, no date in it.
- One plain standfirst line saying what kind of week it was.
- '## The week in brief' - six to ten one-line entries, each a real story from the week with a [source](url), in the style of a serious paper's week-in-review column.
- Then three or four '## ' sections of proper length (150-300 words each), on the week's most consequential threads. Choose them from what actually happened - do not force a fixed list of topics. Likely candidates: UK politics and economy, the war or conflict story of the week, science and technology, and whatever dominated tabletop, Trek or Pokémon this week if it genuinely mattered.
- '## From the week's papers' - three or four short interesting items from the dailies that did not lead anywhere, given a second life.
- '## The week ahead' - three or four things actually due next week (votes, launches, releases, matches, TV premieres), each dated.
- A closing observation of two or three sentences, longer and more reflective than the daily's one-liner.
Tone: the same dry British newspaper voice as the daily, but with room to breathe - proper sentences, developed argument, no bullet-point padding. Every factual claim from outside the dailies needs a real retrieved source link. If you have not verified it, leave it out. Put {{xkcd:NUMBER}} on its own line about a third of the way in if a comic genuinely fits.

STAGE 3 - QUOTE, WEATHER, FORAGING. Run python3 /home/u10000/jobs/weather.py and insert its output verbatim after the standfirst if it prints. Run python3 /home/u10000/jobs/forage.py and insert verbatim at the very end if it prints. Never write either yourself.

STAGE 4 - PUBLISH. Run: cd /home/u10000/repo/morningstarnews && python3 /home/u10000/jobs/publish.py \$(date -u +%F)-weekly and confirm it prints the published URL. It will also put a 'Sunday Paper' link at the top of the front page and in the archive. Do not let the weekly replace the front page's daily edition.

STAGE 5 - EMAIL. Send one email to you@example.com with subject 'Morningstar News - The Sunday Paper - <week's headline short>'. Body: three or four lines only - the week's headline, the one detail that matters most, and a link to https://lordphoenixsalvation.github.io/morningstarnews/posts/\$(date -u +%F)-weekly.html . It is a pointer, not a copy. Send one email, then stop."
