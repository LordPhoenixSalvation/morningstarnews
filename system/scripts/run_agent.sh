#!/bin/bash
# ============================================================================
#  run_agent.sh — send a long instruction to an AI and let it use tools
# ============================================================================
#  The paper is not built by a program that writes news. It is built by an
#  AI agent that is handed a long instruction (the prompt in newsletter.sh),
#  which then searches the web, writes a markdown file, runs the publisher
#  and sends the email itself.
#
#  So the only thing this script does is hand the prompt over. Which service
#  does the handing over depends on where you are running this. Pick ONE of
#  the three blocks below and comment out the others.
#
#  Usage:  ./run_agent.sh "the whole prompt, as one argument"
# ============================================================================

set -euo pipefail
source "$(dirname "$0")/config.sh"

PROMPT="$1"

# Dry run: DRY_RUN=1 ./newsletter.sh prints the prompt instead of sending it.
# Use this to check your edits before letting anything loose.
if [ "${DRY_RUN:-0}" = "1" ]; then
  printf '%s\n' "$PROMPT"
  exit 0
fi

# ---------------------------------------------------------------------------
# OPTION 1 — Rool Machine  (what this paper uses; easiest if you are on Rool)
# ---------------------------------------------------------------------------
# A Rool Machine already has a model, web search, a filesystem and an email
# tool. `rool-llm say` posts the prompt into a conversation and the machine
# does the rest. Set AGENT_CMD in config.sh to your conversation path.
#
#   rool-llm say /agents/<you>/conversations/<id> "$PROMPT"

# ---------------------------------------------------------------------------
# OPTION 2 — a local agent CLI (Claude Code, OpenAI Codex CLI, aider, etc.)
# ---------------------------------------------------------------------------
# These run on your own computer, can read and write files, run commands and
# search the web, which is everything the prompt asks for. Example:
#
#   claude -p "$PROMPT" --allowedTools "Bash,WebSearch,Read,Write"
#
# or:
#
#   codex exec "$PROMPT"

# ---------------------------------------------------------------------------
# OPTION 3 — the OpenAI-compatible API with tool use
# ---------------------------------------------------------------------------
# Hardest of the three: you must implement the tool loop yourself (the model
# asks to search, you search, you hand back results). Do not start here.
# Use it only if options 1 and 2 are unavailable.

# ---------------------------------------------------------------------------
# The default: use whatever AGENT_CMD says. Edit AGENT_CMD in config.sh to
# switch between the options above.
# ---------------------------------------------------------------------------
$AGENT_CMD "$PROMPT"
