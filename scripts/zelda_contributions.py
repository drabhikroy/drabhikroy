
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

# --------------------------------------------------
# The Legend of Commits
# NES Zelda-inspired GitHub contribution animation
# --------------------------------------------------

USERNAME = "drabhikroy"
TOKEN = os.environ["GH_TOKEN"]

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

request = Request(
    "https://api.github.com/graphql",
    data=json.dumps({
        "query": QUERY,
        "variables": {"login": USERNAME}
    }).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "legend-of-commits"
    },
    method="POST"
)

with urlopen(request, timeout=30) as response:
    data = json.load(response)

if data.get("errors"):
    raise RuntimeError(data["errors"])

user = data.get("data", {}).get("user")
if user is None:
    raise RuntimeError(f"GitHub user '{USERNAME}' not found")

calendar = user["contributionsCollection"]["contributionCalendar"]
weeks = calendar["weeks"]
total = calendar["totalContributions"]

# NES-inspired palette.
COLORS = {
    "NONE": "#202c22",
    "FIRST_QUARTILE": "#345a35",
    "SECOND_QUARTILE": "#4c8242",
    "THIRD_QUARTILE": "#75ad51",
    "FOURTH_QUARTILE": "#b8d86b",
}

STEP = 15
CELL = 13
LEFT = 29
TOP = 92
WIDTH = LEFT * 2 + (len(weeks) - 1) * STEP + CELL
HEIGHT = 230

svg = [f"""
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {WIDTH} {HEIGHT}"
     role="img"
     aria-label="The Legend of Commits animated contribution graph">
<title>The Legend of Commits - {USERNAME}</title>

<style>
  .pixel {{ shape-rendering: crispEdges; }}
  .text {{
    font-family: monospace;
    font-weight: bold;
    fill: #f3da91;
  }}
</style>

<!-- NES-style frame -->
<rect width="{WIDTH}" height="{HEIGHT}" fill="#10151b"/>
<rect x="5" y="5"
      width="{WIDTH-10}" height="{HEIGHT-10}"
      fill="none" stroke="#b99a53" stroke-width="2"/>
<rect x="10" y="10"
      width="{WIDTH-20}" height="43" fill="#090c13"/>

<text class="text" x="22" y="28" font-size="15">
  THE LEGEND OF COMMITS
</text>
<text class="text" x="22" y="44" font-size="10">
  @{USERNAME} | {total} CONTRIBUTIONS
</text>
"""]

# NES-inspired heart meter.
for i in range(3):
    x = WIDTH - 92 + i * 21
    svg.append(f"""
    <path class="pixel"
      d="M{x} 19 h3 v-3 h4 v3 h3 v5 h-2 v3
         h-2 v3 h-2 v-3 h-2 v-3 h-2 z"
      fill="#ed6256"/>
    """)

# Background tiles.
for col in range(len(weeks)):
    for row in range(7):
        x = LEFT + col * STEP
        y = TOP + row * STEP

        svg.append(
            f'<rect class="pixel" x="{x}" y="{y}" '
            f'width="{CELL}" height="{CELL}" '
            f'fill="#19221c"/>'
        )

# Contribution tiles.
seen_months = set()

for col, week in enumerate(weeks):
    for day in week["contributionDays"]:
        row = day["weekday"]
        x = LEFT + col * STEP
        y = TOP + row * STEP

        count = day["contributionCount"]
        level = day["contributionLevel"]
        color = COLORS.get(level, COLORS["NONE"])

        svg.append(f"""
        <rect class="pixel"
          x="{x}" y="{y}"
          width="{CELL}" height="{CELL}"
          fill="{color}">
          <title>{day["date"]}: {count} contributions</title>
        </rect>
        """)

        # Golden rupees on highly active days.
        if level in ("THIRD_QUARTILE", "FOURTH_QUARTILE"):
            cx = x + CELL / 2
            cy = y + CELL / 2

            svg.append(f"""
            <polygon class="pixel"
              points="{cx},{cy-4}
                      {cx+3},{cy}
                      {cx},{cy+4}
                      {cx-3},{cy}"
              fill="#efd05b"/>
            """)

        # Calendar month labels.
        month = day["date"][:7]
        if month not in seen_months:
            seen_months.add(month)
            from datetime import date
            label = date.fromisoformat(day["date"]).strftime("%b").upper()
            svg.append(
                f'<text class="text" x="{x}" y="78" '
                f'font-size="9">{label}</text>'
            )

# Link's route through the contribution grid.
route = []

for row in range(7):
    columns = list(range(len(weeks)))

    if row % 2:
        columns.reverse()

    for col in columns:
        x = LEFT + col * STEP + CELL / 2
        y = TOP + row * STEP + CELL / 2
        route.append((x, y))

motion_path = "M " + " L ".join(
    f"{x:g} {y:g}" for x, y in route
)

# Original miniature adventurer with NES-style colors.
svg.append(f"""
<g class="pixel" id="hero">
  <!-- Green cap -->
  <rect x="-4" y="-8" width="8" height="3" fill="#5baa51"/>
  <rect x="-5" y="-5" width="10" height="2" fill="#317c35"/>

  <!-- Face -->
  <rect x="-3" y="-3" width="6" height="5" fill="#efbd84"/>
  <rect x="1" y="-2" width="1" height="1" fill="#171b19"/>

  <!-- Green tunic -->
  <rect x="-4" y="2" width="8" height="5" fill="#438f46"/>

  <!-- Shield -->
  <rect x="-6" y="2" width="3" height="5" fill="#bd8743"/>
  <rect x="-5" y="3" width="1" height="3" fill="#e8d78b"/>

  <!-- Sword -->
  <rect x="5" y="-3" width="2" height="8" fill="#d9e4ea"/>
  <rect x="3" y="3" width="6" height="2" fill="#ae8551"/>

  <!-- Boots -->
  <rect x="-4" y="7" width="3" height="3" fill="#83583b"/>
  <rect x="1" y="7" width="3" height="3" fill="#83583b"/>

  <animateMotion
    path="{motion_path}"
    dur="95s"
    calcMode="linear"
    repeatCount="indefinite"/>
</g>
""")

# Triforce appears at the end of the animation.
cx = WIDTH - 48

svg.append(f"""
<g opacity="0">
  <polygon
    points="{cx},201 {cx-7},213 {cx+7},213"
    fill="#f6d45c"/>
  <polygon
    points="{cx-8},214 {cx-15},226 {cx-1},226"
    fill="#f6d45c"/>
  <polygon
    points="{cx+8},214 {cx+1},226 {cx+15},226"
    fill="#f6d45c"/>

  <animate attributeName="opacity"
    values="0;0;1;1;0"
    keyTimes="0;0.90;0.93;0.98;1"
    dur="95s"
    repeatCount="indefinite"/>
</g>

<text class="text" x="25" y="216" font-size="9">
  IT'S DANGEROUS TO CODE ALONE!
</text>
</svg>
""")

# Save the final SVG.
output = Path("img/zelda-contributions.svg")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text("\n".join(svg), encoding="utf-8")

print(f"Created {output}")
print(f"GitHub contributions: {total}")
