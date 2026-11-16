#!/bin/bash
# Hourly availability watcher. Wakes the agent only when something changed.
cd /home/u10000/jobs || exit 1
out=$(python3 watch.py 2>/dev/null) || exit 0
[ -z "$out" ] && exit 0
rool-llm say /agents/rool/conversations/<conversation-id> "AVAILABILITY WATCH - something Neil has been waiting for has changed. The watcher printed this:

$out

Turn it into one short email to you@example.com. Subject: 'Morningstar Watch: <what changed>'. Body: a single line saying what changed from what to what, with the link. Nothing else - no greeting beyond one word, no commentary, no paper. Send exactly one email, then stop."
