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

def build_frame(days, total, frame_index, frame_count):
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    draw.text((GRID_X, 22), "ASMIT.EXE  /  PAC-MAN CONTRIBUTION RUN",
              font=font(17, True), fill=EMERALD)
    draw.text((GRID_X, 48), "EAT THE DOTS. KEEP THE STREAK ALIVE.",
              font=font(10), fill=MUTED)

    # Real GitHub activity: 53 weeks x 7 days.
    for index, day in enumerate(days):
        col, row = divmod(index, 7)
        x, y = GRID_X + col*STEP, GRID_Y + row*STEP
        draw.rounded_rectangle((x, y, x+CELL, y+CELL), radius=2,
                               fill=heat_color(day["contributionCount"]))

    lane_y = GRID_Y + 3*STEP + CELL//2
    travel = (frame_index / frame_count) * (COLS + 10)
    pac_col = travel % (COLS + 10) - 5
    pac_x = GRID_X + pac_col*STEP + CELL//2

    for col in range(COLS):
        x = GRID_X + col*STEP + CELL//2
        if col > pac_col + 1:
            draw.ellipse((x-1.4, lane_y-1.4, x+1.4, lane_y+1.4), fill=GOLD)

    for offset in (5.5, 10.5, 15.5):
        ghost_col = pac_col - offset
        if -2 <= ghost_col <= COLS+1:
            gx = GRID_X + ghost_col*STEP + CELL//2
            draw_ghost(draw, int(gx), lane_y, 7, frame_index/3 + offset)

    if -2 <= pac_col <= COLS+1:
        draw_pacman(draw, int(pac_x), lane_y, 9, frame_index/2)

    draw.text((GRID_X, 190), f"{total:,} CONTRIBUTIONS",
              font=font(11, True), fill=TEXT)
    draw.text((GRID_X+190, 190), "GHOSTS: EMERALD",
              font=font(10), fill=EMERALD)

    legend_x = 585
    draw.text((legend_x, 190), "LESS", font=font(9), fill=MUTED)
    colors = [(25,31,29), (15,82,54), (20,135,76), (35,195,103), EMERALD]
    for i, color in enumerate(colors):
        x = legend_x + 38 + i*17
        draw.rounded_rectangle((x, 190, x+11, 201), radius=2, fill=color)
    draw.text((legend_x+132, 190), "MORE", font=font(9), fill=MUTED)

    draw.line((GRID_X, 216, WIDTH-GRID_X, 216), fill=(25,55,40), width=1)
    draw.text((GRID_X, 222),
              "CRIMSON PLAYER  /  EMERALD GHOSTS  /  LIVE GITHUB ACTIVITY",
              font=font(8), fill=(91,111,99))
    return image

def main():
    days, total = fetch_calendar()
    frames = [build_frame(days, total, i, 72) for i in range(72)]
    frames[0].save(OUTPUT, save_all=True, append_images=frames[1:],
                   duration=90, loop=0, optimize=True, disposal=2)
    print(f"Generated {OUTPUT} with {len(days)} contribution days and {total} contributions.")

if __name__ == "__main__":
    main()
