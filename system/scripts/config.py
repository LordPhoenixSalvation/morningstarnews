"""Read settings from config.sh so every script uses the same values.

Order of precedence, highest first:
  1. an environment variable of the same name  (handy for testing)
  2. the KEY="${KEY:-default}" line in config.sh
  3. the fallback written in DEFAULTS below

config.sh stays the single place a person edits. This module only reads it,
it never writes to it.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_SH = os.path.join(HERE, "config.sh")

DEFAULTS = {
    "JOBS_DIR": HERE,
    "REPO_DIR": os.path.join(os.path.expanduser("~"), "repo", "morningstarnews"),
    "PAPER_NAME": "Morningstar News",
    "SITE_URL": "https://example.github.io/morningstarnews",
    "EMAIL_TO": "",
    "PLACE_NAME": "Derbyshire",
    "PLACE_TOWN": "Derby",
    "PLACE_LAT": "52.9219",
    "PLACE_LON": "-1.4756",
    "BBC_WEATHER_ID": "2651347",
    "RADIO_GRID": "IO92",
}


def _from_config_sh():
    """Pull the default out of lines like:  SITE_URL="${SITE_URL:-https://x}"  """
    found = {}
    try:
        text = open(CONFIG_SH, encoding="utf-8").read()
    except OSError:
        return found
    for m in re.finditer(r'^([A-Z_]+)="\$\{\1:-([^}]*)\}"', text, re.M):
        found[m.group(1)] = m.group(2)
    return found


_sh = _from_config_sh()


def get(key):
    """Return one setting as a string."""
    if key in os.environ and os.environ[key] != "":
        return os.environ[key]
    return _sh.get(key, DEFAULTS.get(key, ""))


def getf(key):
    """Return one setting as a float (for latitude and longitude)."""
    return float(get(key))


def geti(key):
    """Return one setting as an integer."""
    return int(get(key))


# Convenient names, so scripts can write `config.REPO` instead of `config.get()`.
REPO = get("REPO_DIR")
JOBS = get("JOBS_DIR")
SITE_URL = get("SITE_URL")
PAPER = get("PAPER_NAME")
EMAIL = get("EMAIL_TO")
PLACE = get("PLACE_NAME")
TOWN = get("PLACE_TOWN")
LAT = getf("PLACE_LAT")
LON = getf("PLACE_LON")
BBC_ID = get("BBC_WEATHER_ID")
GRID = get("RADIO_GRID")
