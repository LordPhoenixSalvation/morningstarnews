# Morningstar News

A daily newspaper, researched and written by a Rool Machine, published to GitHub Pages.

**Read it:** https://lordphoenixsalvation.github.io/morningstarnews/

Six sections — UK news (with a Derbyshire slot), UK television, Pokémon, tabletop
games, sci-fi and fantasy, and tech. Plus the [Derbyshire
Almanac](https://lordphoenixsalvation.github.io/morningstarnews/almanac.html),
[Radio & Satellites](https://lordphoenixsalvation.github.io/morningstarnews/radio.html)
and [The Foraging Year](https://lordphoenixsalvation.github.io/morningstarnews/foraging.html).
A longer Sunday Paper runs weekly.

Every item carries a link to a source that was retrieved during that morning's run.
Nothing is written from memory. Weather, foraging, river levels and satellite passes
are pulled from official feeds and reproduced verbatim rather than generated.

## How it works

The machinery — cron schedule, every Python script, the publisher, and the full
instruction prompts — is in [`system/`](system/README.md). That's the part worth
reading if you want to build your own.

## Layout

```
editions/     the source of each paper, in markdown
posts/        the built HTML
assets/       images, nameplate, favicons
system/       the scripts and prompts that make it
```
