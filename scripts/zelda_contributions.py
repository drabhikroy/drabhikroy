"""The Legend of Commits: NES-inspired animated GitHub contribution calendar.

GitHub Actions supplies GH_TOKEN. No third-party packages are required.
All images are original SVG pixel art; the script reads GitHub's real daily counts.
"""

import json
import os
from datetime import date
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

USERNAME = "drabhikroy"
CYCLE = 86                 # seconds per loop
START = 0.04              # walking starts after the title appears
END = 0.90                # walking stops before the finale
PITCH = 15
CELL = 13
LEFT = 28
TOP = 111

# A small, coordinated NES-inspired palette, drawn without external artwork.
PAL = {
    "night": "#10151b",
    "frame": "#b99a53",
    "gold": "#f1d071",
    "cream": "#f2e5b5",
    "red": "#d45243",
    "water": "#5aa5aa",
    "shadow": "#1a271d",
    "NONE": "#243426",
    "FIRST_QUARTILE": "#355c37",
    "SECOND_QUARTILE": "#508341",
    "THIRD_QUARTILE": "#7eab53",
    "FOURTH_QUARTILE": "#c1d67a",
}

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            weekday
            contributionCount
            contributionLevel
          }
        }
      }
    }
  }
}
"""


def get_calendar():
    token = os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("GH_TOKEN is required (GitHub Actions sets it automatically).")

    request = Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USERNAME}}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "legend-of-commits",
        },
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    user = (payload.get("data") or {}).get("user")
    if user is None:
        raise RuntimeError(f"GitHub account '{USERNAME}' not found")
    return user["contributionsCollection"]["contributionCalendar"]


def rect(x, y, w, h, color, extra=""):
    return (f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
            f'fill="{color}" {extra}/>')


def text(x, y, label, size=10, color=None, extra=""):
    return (f'<text x="{x:g}" y="{y:g}" font-size="{size}" '
            f'fill="{color or PAL["cream"]}" {extra}>{escape(str(label))}</text>')


def timed_visibility(time_fraction, initially_visible=True):
    """Hold visibility until an event, then toggle for the rest of the loop."""
