
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


# Three NES-inspired Octorok encounters.
# Each enemy disappears when the hero reaches its tile.

enemy_locations = [
    (1, len(weeks) // 4),
    (3, len(weeks) // 2),
    (5, 3 * len(weeks) // 4),
]

total_steps = 7 * len(weeks) - 1

for row, col in enemy_locations:
    # The hero travels in alternating directions.
    position = (
        row * len(weeks)
        + (col if row % 2 == 0
           else len(weeks) - 1 - col)
    )

    hit_time = position / total_steps

    x = LEFT + col * STEP + CELL / 2
    y = TOP + row * STEP + CELL / 2

    svg.append(f"""
    <g class="pixel" transform="translate({x},{y})">

      <!-- Red Octorok-style enemy -->
      <g opacity="1">
        <animate
          attributeName="opacity"
          values="1;0;0;1"
          keyTimes="0;{hit_time:.6f};0.999;1"
          calcMode="discrete"
          dur="95s"
          repeatCount="indefinite"/>

        <g>
          <animateTransform
            attributeName="transform"
            type="translate"
            values="0 0;0 -1;0 0"
            dur="0.65s"
            repeatCount="indefinite"/>

          <!-- Body and head -->
          <rect x="-3" y="-6" width="6" height="3"
                fill="#a73530"/>
          <rect x="-5" y="-4" width="10" height="7"
                fill="#ca5040"/>
          <rect x="-6" y="-1" width="12" height="3"
                fill="#e36b51"/>

          <!-- Eyes -->
          <rect x="-3" y="-2" width="2" height="2"
                fill="#ffffff"/>
          <rect x="1" y="-2" width="2" height="2"
                fill="#ffffff"/>
          <rect x="-2" y="-1" width="1" height="1"
                fill="#17181a"/>
          <rect x="2" y="-1" width="1" height="1"
                fill="#17181a"/>

          <!-- Snout -->
          <rect x="-2" y="2" width="4" height="3"
                fill="#8b2928"/>

          <!-- Feet -->
          <rect x="-5" y="5" width="3" height="2"
                fill="#a73530"/>
          <rect x="2" y="5" width="3" height="2"
                fill="#a73530"/>
        </g>
      </g>

      <!-- Golden impact effect -->
      <g opacity="0">
        <animate
          attributeName="opacity"
          values="0;0;1;0;0"
          keyTimes="0;{hit_time-0.002:.6f};{hit_time:.6f};{hit_time+0.012:.6f};1"
          dur="95s"
          repeatCount="indefinite"/>

        <rect x="-1" y="-8" width="2" height="16"
              fill="#ffe58b"/>
        <rect x="-8" y="-1" width="16" height="2"
              fill="#ffe58b"/>
        <rect x="-5" y="-5" width="2" height="2"
              fill="#fff2c2"/>
        <rect x="3" y="3" width="2" height="2"
              fill="#fff2c2"/>
      </g>
    </g>
    """)

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


# --------------------------------------------------
# QUEST UPGRADE: Combat, pickups, HUD and finale
# --------------------------------------------------

DURATION = 95
WEEK_COUNT = len(weeks)
TOTAL_VISITS = 7 * WEEK_COUNT - 1


def visit_time(row, col):
    """Fraction of the animation when Link visits a tile."""
    position = (
        row * WEEK_COUNT
        + (col if row % 2 == 0 else WEEK_COUNT - 1 - col)
    )
    return position / TOTAL_VISITS


# 1. NES-style exploration progress bar.
bar_x = LEFT + 78
bar_y = 61
bar_width = WIDTH - LEFT - bar_x

svg.append(f"""
<text class="text" x="{LEFT}" y="67" font-size="9">
  QUEST
</text>
<rect class="pixel" x="{bar_x}" y="{bar_y}"
  width="{bar_width}" height="7" fill="#394133"/>
<rect class="pixel" x="{bar_x}" y="{bar_y}"
  width="0" height="7" fill="#d7b553">
  <animate attributeName="width"
    from="0" to="{bar_width}"
    dur="{DURATION}s" repeatCount="indefinite"/>
</rect>
""")

# 2. Sword slashes synchronized with Octorok encounters.
enemy_times = []

for row, col in enemy_locations:
    t = visit_time(row, col)
    enemy_times.append(t)

    x = LEFT + col * STEP + CELL / 2
    y = TOP + row * STEP + CELL / 2

    start = max(0, t - 0.008)
    finish = min(0.999, t + 0.012)

    svg.append(f"""
    <g class="pixel" transform="translate({x},{y})">
      <g opacity="0">
        <animate attributeName="opacity"
          values="0;0;1;0;0"
          keyTimes="0;{start:.6f};{t:.6f};{finish:.6f};1"
          dur="{DURATION}s"
          repeatCount="indefinite"/>

        <g>
          <animateTransform
            attributeName="transform"
            type="rotate"
            values="-40;-40;40;40;-40"
            keyTimes="0;{start:.6f};{t:.6f};{finish:.6f};1"
            dur="{DURATION}s"
            repeatCount="indefinite"/>

          <path d="M -8 5 L -3 -5 L 6 -8"
            fill="none" stroke="#fff2b1"
            stroke-width="3"
            stroke-linecap="square"/>
          <path d="M -6 7 L 0 8"
            fill="none" stroke="#e4b94d"
            stroke-width="2"/>
        </g>
      </g>
    </g>
    """)

# 3. Enemy counter in the top status bar.
enemy_times.sort()
enemy_count = len(enemy_times)

for defeated in range(enemy_count + 1):
    if defeated == 0:
        values = "1;0;0"
        times = f"0;{enemy_times[0]:.6f};1"
    elif defeated == enemy_count:
        values = "0;1;1"
        times = f"0;{enemy_times[-1]:.6f};1"
    else:
        values = "0;1;0;0"
        times = (
            f"0;{enemy_times[defeated-1]:.6f};"
            f"{enemy_times[defeated]:.6f};1"
        )

    svg.append(f"""
    <text class="text" x="{WIDTH-235}" y="43"
      font-size="10" opacity="0">
      FOES {defeated}/{enemy_count}
      <animate attributeName="opacity"
        values="{values}"
        keyTimes="{times}"
        calcMode="discrete"
        dur="{DURATION}s"
        repeatCount="indefinite"/>
    </text>
    """)

# 4. Sparkles when rupees are collected.
for col, week in enumerate(weeks):
    for day in week["contributionDays"]:
        if day["contributionLevel"] not in (
            "THIRD_QUARTILE", "FOURTH_QUARTILE"
        ):
            continue

        row = day["weekday"]
        t = visit_time(row, col)

        # Skip the very beginning and end of the loop.
        if not 0.004 < t < 0.99:
            continue

        x = LEFT + col * STEP + CELL / 2
        y = TOP + row * STEP + CELL / 2

        start = t - 0.003
        finish = t + 0.008

        svg.append(f"""
        <g class="pixel" transform="translate({x},{y})"
          opacity="0">
          <animate attributeName="opacity"
            values="0;0;1;0;0"
            keyTimes="0;{start:.6f};{t:.6f};{finish:.6f};1"
            dur="{DURATION}s"
            repeatCount="indefinite"/>

          <rect x="-1" y="-6" width="2" height="4"
            fill="#ffeb83"/>
          <rect x="-1" y="2" width="2" height="4"
            fill="#ffeb83"/>
          <rect x="-6" y="-1" width="4" height="2"
            fill="#ffeb83"/>
          <rect x="2" y="-1" width="4" height="2"
            fill="#ffeb83"/>
        </g>
        """)

# 5. Golden Triforce finale sparkles.
finale_x = WIDTH - 48

svg.append(f"""
<g class="pixel" opacity="0">
  <animate attributeName="opacity"
    values="0;0;1;0;0"
    keyTimes="0;0.90;0.94;0.985;1"
    dur="{DURATION}s"
    repeatCount="indefinite"/>

  <rect x="{finale_x-25}" y="202"
    width="4" height="4" fill="#fff2a5"/>
  <rect x="{finale_x+21}" y="202"
    width="4" height="4" fill="#fff2a5"/>
  <rect x="{finale_x-17}" y="192"
    width="3" height="3" fill="#efc75c"/>
  <rect x="{finale_x+14}" y="192"
    width="3" height="3" fill="#efc75c"/>
  <rect x="{finale_x-22}" y="217"
    width="3" height="3" fill="#fff2a5"/>
  <rect x="{finale_x+19}" y="217"
    width="3" height="3" fill="#fff2a5"/>
</g>
""")


# --------------------------------------------------
# OVERWORLD UPGRADE
# Terrain, projectiles, chests, introduction, finale
# --------------------------------------------------

# 1. Small terrain details.
# Keep the original contribution colors visible.
for col, week in enumerate(weeks):
    for day in week["contributionDays"]:
        row = day["weekday"]
        level = day["contributionLevel"]
        x = LEFT + col * STEP
        y = TOP + row * STEP

        if level == "NONE" and (col * 7 + row * 11) % 31 == 0:
            # A small gray rock.
            svg.append(f"""
            <g class="pixel">
              <rect x="{x+3}" y="{y+7}" width="7"
                    height="4" fill="#626c63"/>
              <rect x="{x+5}" y="{y+5}" width="4"
                    height="3" fill="#a0a99a"/>
              <rect x="{x+3}" y="{y+10}" width="7"
                    height="2" fill="#343d37"/>
            </g>
            """)

        elif (
            level == "FIRST_QUARTILE"
            and (col + 2 * row) % 9 == 0
        ):
            # Two blades of grass.
            svg.append(f"""
            <g class="pixel" fill="#80bd59">
              <rect x="{x+3}" y="{y+7}"
                    width="2" height="4"/>
              <rect x="{x+8}" y="{y+5}"
                    width="2" height="5"/>
              <rect x="{x+2}" y="{y+9}"
                    width="2" height="2"/>
            </g>
            """)


# 2. Octorok projectiles.
# Each enemy fires shortly before Link arrives.
for row, col in enemy_locations:
    t = visit_time(row, col)

    start = t - 0.032
    visible = t - 0.029
    end = t - 0.004

    x = LEFT + col * STEP + CELL / 2
    y = TOP + row * STEP + CELL / 2

    # Projectiles move toward Link's approach direction.
    direction = 1 if row % 2 else -1
    distance = direction * 29

    svg.append(f"""
    <g class="pixel" transform="translate({x},{y})">
      <g opacity="0">
        <animate
          attributeName="opacity"
          values="0;0;1;0;0"
          keyTimes="0;{start:.6f};{visible:.6f};{end:.6f};1"
          dur="{DURATION}s"
          repeatCount="indefinite"/>

        <animateTransform
          attributeName="transform"
          type="translate"
          values="0 0;0 0;{distance} 0;{distance} 0"
          keyTimes="0;{start:.6f};{end:.6f};1"
          dur="{DURATION}s"
          repeatCount="indefinite"/>

        <rect x="-3" y="-2" width="6" height="4"
              fill="#d6a45b"/>
        <rect x="-1" y="-1" width="3" height="2"
              fill="#ffe6a1"/>
      </g>
    </g>
    """)


# 3. Two treasure chests along Link's route.
chest_locations = [
    (2, WEEK_COUNT // 3),
    (4, (WEEK_COUNT * 2) // 3),
]

for row, col in chest_locations:
    t = visit_time(row, col)

    x = LEFT + col * STEP + CELL / 2
    y = TOP + row * STEP + CELL / 2

    svg.append(f"""
    <g class="pixel" transform="translate({x},{y})">

      <!-- Closed chest -->
      <g opacity="1">
        <animate
          attributeName="opacity"
          values="1;0;0"
          keyTimes="0;{t:.6f};1"
          calcMode="discrete"
          dur="{DURATION}s"
          repeatCount="indefinite"/>

        <rect x="-5" y="-4" width="10" height="9"
              fill="#83512c"/>
        <rect x="-5" y="-4" width="10" height="3"
              fill="#d69a4e"/>
        <rect x="-1" y="-3" width="2" height="6"
              fill="#f2d16c"/>
        <rect x="-4" y="3" width="8" height="2"
              fill="#59351e"/>
      </g>

      <!-- Open chest -->
      <g opacity="0">
        <animate
          attributeName="opacity"
          values="0;1;1"
          keyTimes="0;{t:.6f};1"
          calcMode="discrete"
          dur="{DURATION}s"
          repeatCount="indefinite"/>

        <rect x="-5" y="0" width="10" height="5"
              fill="#83512c"/>
        <rect x="-4" y="1" width="8" height="2"
              fill="#f2d16c"/>
        <rect x="-5" y="-6" width="10" height="3"
              fill="#d69a4e"/>
        <rect x="-4" y="-3" width="8" height="3"
              fill="#342519"/>
      </g>

      <!-- Treasure sparkle -->
      <g opacity="0">
        <animate
          attributeName="opacity"
          values="0;0;1;0;0"
          keyTimes="0;{t-0.003:.6f};{t:.6f};{t+0.015:.6f};1"
          dur="{DURATION}s"
          repeatCount="indefinite"/>

        <path d="M 0 -12 V -5 M -4 -9 H 4"
              fill="none"
              stroke="#ffec85"
              stroke-width="2"/>
      </g>
    </g>
    """)


# 4. Classic introductory message.
intro_x = WIDTH / 2
svg.append(f"""
<text class="text"
  x="{intro_x}" y="215"
  font-size="12" text-anchor="middle"
  opacity="1">
  THE QUEST BEGINS
  <animate
    attributeName="opacity"
    values="1;1;0;0"
    keyTimes="0;0.025;0.035;1"
    dur="{DURATION}s"
    repeatCount="indefinite"/>
</text>
""")


# 5. Victory message after completing the quest.
svg.append(f"""
<text class="text"
  x="{intro_x}" y="215"
  font-size="12" text-anchor="middle"
  fill="#f7d567"
  opacity="0">
  QUEST COMPLETE!
  <animate
    attributeName="opacity"
    values="0;0;1;1;0"
    keyTimes="0;0.91;0.94;0.98;1"
    dur="{DURATION}s"
    repeatCount="indefinite"/>
</text>
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
