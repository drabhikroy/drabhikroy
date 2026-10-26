
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


        # NES-style bushes for moderately active days.
        if level == "SECOND_QUARTILE":
            svg.append(f"""
            <g class="pixel">
              <rect x="{x+3}" y="{y+5}" width="8"
                    height="6" fill="#153b20"/>
              <rect x="{x+4}" y="{y+3}" width="5"
                    height="6" fill="#389a42"/>
              <rect x="{x+2}" y="{y+6}" width="4"
                    height="3" fill="#66bd4f"/>
              <rect x="{x+6}" y="{y+4}" width="4"
                    height="3" fill="#75ce58"/>
              <rect x="{x+3}" y="{y+10}" width="8"
                    height="2" fill="#102c19"/>
            </g>
            """)

        # Collectible rupees for high-activity days.
        if level in ("THIRD_QUARTILE", "FOURTH_QUARTILE"):
            cx = x + CELL / 2
            cy = y + CELL / 2

            # Match the adventurer's zigzag route.
            position = (
                row * len(weeks)
                + (col if row % 2 == 0
                   else len(weeks) - 1 - col)
            )

            total_positions = len(weeks) * 7
            collect_at = min(
                0.995,
                max(0.001, position / (total_positions - 1))
            )

            rupee_color = (
                "#f5cf4d" if level == "FOURTH_QUARTILE"
                else "#59bbef"
            )

            svg.append(f"""
            <polygon class="pixel"
              points="{cx},{cy-5}
                      {cx+3},{cy}
                      {cx},{cy+5}
                      {cx-3},{cy}"
              fill="{rupee_color}">
              <animate
                attributeName="opacity"
                values="1;0;0;1"
                keyTimes="0;{collect_at:.6f};0.999;1"
                calcMode="discrete"
                dur="95s"
                repeatCount="indefinite"/>
            </polygon>
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


# NES-style adventurer with walking and directional movement.

# Calculate when the hero reaches each new row.
horizontal = (len(weeks) - 1) * STEP
total_distance = 7 * horizontal + 6 * STEP

turn_times = [
    row * (horizontal + STEP) / total_distance
    for row in range(7)
]
turn_times.append(1.0)

flip_times = ";".join(
    f"{t:.6f}" for t in turn_times
)

flip_values = ";".join(
    "1 1" if row % 2 == 0 else "-1 1"
    for row in range(7)
) + ";1 1"

svg.append(f"""
<g id="hero" class="pixel">

  <!-- Face left or right depending on travel direction -->
  <g>
    <animateTransform
      attributeName="transform"
      type="scale"
      values="{flip_values}"
      keyTimes="{flip_times}"
      calcMode="discrete"
      dur="95s"
      repeatCount="indefinite"/>

    <!-- Walking bounce -->
    <g>
      <animateTransform
        attributeName="transform"
        type="translate"
        values="0 0;0 -1;0 0;0 1;0 0"
        dur="0.48s"
        repeatCount="indefinite"/>

      <!-- Green pointed cap -->
      <rect x="-3" y="-10" width="5" height="2"
            fill="#296b35"/>
      <rect x="-5" y="-8" width="9" height="3"
            fill="#4cac52"/>
      <rect x="-6" y="-5" width="11" height="2"
            fill="#276d39"/>
      <rect x="-4" y="-7" width="5" height="2"
            fill="#85cf65"/>

      <!-- Hair and face -->
      <rect x="-5" y="-3" width="9" height="5"
            fill="#a56b39"/>
      <rect x="-3" y="-3" width="8" height="5"
            fill="#f0bd83"/>
      <rect x="3" y="-1" width="2" height="2"
            fill="#15191b"/>
      <rect x="-3" y="1" width="6" height="1"
            fill="#c68b5e"/>

      <!-- Green tunic -->
      <rect x="-5" y="2" width="10" height="6"
            fill="#338c44"/>
      <rect x="-3" y="2" width="5" height="4"
            fill="#67bd57"/>
      <rect x="-5" y="6" width="10" height="2"
            fill="#245d36"/>

      <!-- Belt and buckle -->
      <rect x="-5" y="5" width="10" height="2"
            fill="#83532c"/>
      <rect x="-1" y="5" width="2" height="2"
            fill="#f1d16c"/>

      <!-- Left arm and shield -->
      <rect x="-7" y="2" width="3" height="5"
            fill="#e5ac75"/>
      <rect x="-8" y="3" width="4" height="6"
            fill="#9a6532"/>
      <rect x="-7" y="4" width="2" height="4"
            fill="#d6bc70"/>
      <rect x="-7" y="5" width="2" height="2"
            fill="#d85c48"/>

      <!-- Right arm -->
      <rect x="5" y="2" width="3" height="5"
            fill="#eab57b"/>

      <!-- Sword blade, guard and grip -->
      <rect x="8" y="-7" width="2" height="10"
            fill="#dceaf0"/>
      <rect x="9" y="-7" width="1" height="8"
            fill="#ffffff"/>
      <rect x="6" y="2" width="6" height="2"
            fill="#f0ca63"/>
      <rect x="8" y="4" width="2" height="4"
            fill="#83532c"/>

      <!-- Alternating walking legs -->
      <rect x="-5" y="8" width="4" height="3"
            fill="#8a593b">
        <animate
          attributeName="y"
          values="8;6;8;9;8"
          dur="0.48s"
          repeatCount="indefinite"/>
      </rect>

      <rect x="1" y="8" width="4" height="3"
            fill="#8a593b">
        <animate
          attributeName="y"
          values="8;9;8;6;8"
          dur="0.48s"
          repeatCount="indefinite"/>
      </rect>

    </g>
  </g>

  <!-- Follow the original contribution calendar route -->
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
