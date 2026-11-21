import os
import math
import requests
from PIL import Image, ImageDraw, ImageFont

USERNAME = "asmit6109-droid"
TOKEN = os.environ["GH_TOKEN"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(BASE_DIR, "pacman-contributions.gif")

QUERY = """
query($username: String!) {
  user(login: $username) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

WIDTH, HEIGHT = 900, 238
CELL, GAP = 9, 4
STEP = CELL + GAP
COLS, GRID_X, GRID_Y = 53, 105, 82
BG = (8, 9, 11)
TEXT = (220, 232, 225)
MUTED = (112, 130, 119)
CRIMSON = (215, 25, 50)
GOLD = (255, 203, 104)
EMERALD = (57, 255, 136)

def font(size, bold=False):
    path = ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()

def fetch_calendar():
    response = requests.post(
        "https://api.github.com/graphql",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"query": QUERY, "variables": {"username": USERNAME}},
        timeout=30
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    calendar = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [day for week in calendar["weeks"] for day in week["contributionDays"]]
    return days[-371:], calendar["totalContributions"]

def heat_color(count):
    if count == 0:
        return (25, 31, 29)
    if count <= 2:
        return (15, 82, 54)
    if count <= 5:
        return (20, 135, 76)
    if count <= 9:
        return (35, 195, 103)
    return EMERALD

def draw_pacman(draw, cx, cy, radius, phase):
    mouth = 0.18 + 0.25 * (0.5 + 0.5 * math.sin(phase))
    angle = mouth * 180
    box = (cx-radius, cy-radius, cx+radius, cy+radius)
    draw.pieslice(box, start=angle, end=360-angle, fill=CRIMSON)
    draw.ellipse((cx-radius+3, cy-radius+3, cx+radius-3, cy+radius-3),
                 outline=(255, 91, 105), width=2)
    draw.ellipse((cx+1, cy-radius+5, cx+5, cy-radius+9), fill=GOLD)

def draw_ghost(draw, cx, cy, radius, phase):
    left, top = cx-radius, cy-radius
    right, bottom = cx+radius, cy+radius
    draw.ellipse((left, top, right, top+radius*1.55), fill=EMERALD)
    draw.rectangle((left, top+radius, right, bottom-3), fill=EMERALD)
    points = []
    for i in range(9):
        x = left + i * (2*radius/8)
        y = bottom-3 + (3 if (i + int(phase)) % 2 else -2)
        points.append((x, y))
    points.extend([(right, bottom), (left, bottom)])
    draw.polygon(points, fill=EMERALD)
    eye_y = cy-2
    draw.ellipse((cx-radius*.55, eye_y-radius*.42, cx-radius*.05, eye_y+radius*.35), fill=(245,255,249))
    draw.ellipse((cx+radius*.05, eye_y-radius*.42, cx+radius*.55, eye_y+radius*.35), fill=(245,255,249))
    draw.ellipse((cx-radius*.38, eye_y-radius*.12, cx-radius*.17, eye_y+radius*.2), fill=(8,35,23))
    draw.ellipse((cx+radius*.22, eye_y-radius*.12, cx+radius*.43, eye_y+radius*.2), fill=(8,35,23))

```python
def random_pacman_path(length=72):
    import random

    rng = random.Random(42)
    path = [(2, 3)]

    for _ in range(length - 1):
        col, row = path[-1]
        previous = path[-2] if len(path) > 1 else None

        moves = [
            (col + 1, row),
            (col - 1, row),
            (col, row + 1),
            (col, row - 1)
        ]

        valid = [
            p for p in moves
            if 0 <= p[0] < 53
            and 0 <= p[1] < 7
            and p != previous
        ]

        if not valid:
            valid = [
                p for p in moves
                if 0 <= p[0] < 53
                and 0 <= p[1] < 7
            ]

        path.append(rng.choice(valid))

    return path


def ghost_intercept_step(current, target, rng):
    col, row = current

    moves = [
        (col + 1, row),
        (col - 1, row),
        (col, row + 1),
        (col, row - 1)
    ]

    valid = [
        p for p in moves
        if 0 <= p[0] < 53 and 0 <= p[1] < 7
    ]

    valid.sort(
        key=lambda p: abs(p[0] - target[0]) +
                      abs(p[1] - target[1])
    )

    best_distance = (
        abs(valid[0][0] - target[0]) +
        abs(valid[0][1] - target[1])
    )

    best_moves = [
        p for p in valid
        if abs(p[0] - target[0]) +
           abs(p[1] - target[1]) == best_distance
    ]

    return rng.choice(best_moves)


def build_frame(days, total, frame_index, frame_count):
    import random

    rng = random.Random(17)

    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    pacman_path = random_pacman_path(frame_count)

    # Pac-Man's current position
    pacman_pos = pacman_path[frame_index]

    # Ghost 1 follows Pac-Man's exact route with a delay
    delay = 10
    ghost1_index = max(0, frame_index - delay)
    ghost1_pos = pacman_path[ghost1_index]

    # Ghost 2 starts elsewhere and tries to intercept Pac-Man
    ghost2_pos = (52, 6)

    for i in range(frame_index + 1):
        target_index = min(i + 6, frame_count - 1)
        target = pacman_path[target_index]
        ghost2_pos = ghost_intercept_step(
            ghost2_pos, target, rng
        )

    draw.text(
        (GRID_X, 22),
        "ASMIT.EXE / PAC-MAN CONTRIBUTION RUN",
        font=font(17, True),
        fill=EMERALD
    )

    draw.text(
        (GRID_X, 48),
        "EAT THE DOTS. KEEP THE STREAK ALIVE.",
        font=font(10),
        fill=MUTED
    )

    # Draw real GitHub contribution activity
    for index, day in enumerate(days):
        col, row = divmod(index, 7)
        x = GRID_X + col * STEP
        y = GRID_Y + row * STEP

        draw.rounded_rectangle(
            (x, y, x + CELL, y + CELL),
            radius=2,
            fill=heat_color(day["contributionCount"])
        )

    # Draw gold dots and remove dots already eaten
    eaten = set(pacman_path[:frame_index + 1])

    for col in range(53):
        for row in range(7):
            if (col, row) not in eaten:
                cx = GRID_X + col * STEP + CELL // 2
                cy = GRID_Y + row * STEP + CELL // 2

                draw.ellipse(
                    (cx - 1, cy - 1, cx + 1, cy + 1),
                    fill=GOLD
                )

    # Convert grid coordinates into image coordinates
    def position(point):
        col, row = point
        return (
            GRID_X + col * STEP + CELL // 2,
            GRID_Y + row * STEP + CELL // 2
        )

    # Ghost 2: independent interception route
    gx2, gy2 = position(ghost2_pos)
    draw_ghost(draw, gx2, gy2, 6, frame_index / 3)

    # Ghost 1: delayed Pac-Man follower
    gx1, gy1 = position(ghost1_pos)
    draw_ghost(draw, gx1, gy1, 6, frame_index / 3 + 2)

    # Pac-Man
    px, py = position(pacman_pos)
    draw_pacman(draw, px, py, 8, frame_index / 2)

    draw.text(
        (GRID_X, 190),
        f"{total:,} CONTRIBUTIONS",
        font=font(11, True),
        fill=TEXT
    )

    draw.text(
        (GRID_X + 190, 190),
        "2 GHOSTS / 1 TARGET",
        font=font(10),
        fill=EMERALD
    )

    legend_x = 585
    draw.text((legend_x, 190), "LESS", font=font(9), fill=MUTED)

    colors = [
        (25, 31, 29),
        (15, 82, 54),
        (20, 135, 76),
        (35, 195, 103),
        EMERALD
    ]

    for i, color in enumerate(colors):
        x = legend_x + 38 + i * 17
        draw.rounded_rectangle(
            (x, 190, x + 11, 201),
            radius=2,
            fill=color
        )

    draw.text(
        (legend_x + 132, 190),
        "MORE",
        font=font(9),
        fill=MUTED
    )

    draw.line(
        (GRID_X, 216, WIDTH - GRID_X, 216),
        fill=(25, 55, 40),
        width=1
    )

    draw.text(
        (GRID_X, 222),
        "CRIMSON PLAYER / EMERALD HUNTERS / LIVE GITHUB ACTIVITY",
        font=font(8),
        fill=(91, 111, 99)
    )

    return image
```
def main():
    days, total = fetch_calendar()
    frames = [build_frame(days, total, i, 72) for i in range(72)]
    frames[0].save(OUTPUT, save_all=True, append_images=frames[1:],
                   duration=90, loop=0, optimize=True, disposal=2)
    print(f"Generated {OUTPUT} with {len(days)} contribution days and {total} contributions.")

if __name__ == "__main__":
    main()
