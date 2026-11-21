import os
import requests
from PIL import Image, ImageDraw
from datetime import datetime, timedelta

USERNAME = "asmit6109-droid"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_GIF = os.path.join(BASE_DIR, "void-wyrm.gif")
OUTPUT_GIF = os.path.join(BASE_DIR, "void-wyrm-live.gif")

TOKEN = os.environ["GH_TOKEN"]

QUERY = """
query($username: String!) {
  user(login: $username) {
    contributionsCollection {
      contributionCalendar {
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

def get_contributions():
    response = requests.post(
        "https://api.github.com/graphql",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "query": QUERY,
            "variables": {"username": USERNAME}
        },
        timeout=30
    )
    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        raise RuntimeError(data["errors"])

    weeks = data["data"]["user"]["contributionsCollection"][
        "contributionCalendar"
    ]["weeks"]

    return [
        day
        for week in weeks
        for day in week["contributionDays"]
    ]


def contribution_color(count, maximum=None):
    if count == 0:
        return (35, 30, 34, 255)
    elif count <= 9:
        return (121, 11, 22, 255)
    elif count <= 19:
        return (215, 25, 50, 255)
    elif count <= 29:
        return (255, 100, 28, 255)
    else:
        return (255, 203, 104, 255)


def create_grid(image, contributions):
    image = image.convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")

    width, height = image.size

    cell = max(5, min(width // 65, 12))
    gap = max(2, cell // 4)

    columns = 53
    rows = 7

    grid_width = columns * (cell + gap)
    grid_height = rows * (cell + gap)

    start_x = (width - grid_width) // 2
    start_y = height - grid_height - 55

    maximum = max(
        (day["contributionCount"] for day in contributions),
        default=1
    )

    draw.rounded_rectangle(
        (
            start_x - 14,
            start_y - 24,
            start_x + grid_width + 14,
            start_y + grid_height + 14
        ),
        radius=12,
        fill=(8, 9, 11, 225),
        outline=(121, 11, 22, 220),
        width=2
    )

    draw.text(
        (start_x, start_y - 17),
        "VOID WYRM  //  CONTRIBUTION HUNT",
        fill=(255, 203, 104, 255)
    )

    for index, day in enumerate(contributions[-371:]):
        column = index // 7
        row = index % 7

        x = start_x + column * (cell + gap)
        y = start_y + row * (cell + gap)

        color = contribution_color(
            day["contributionCount"],
            maximum
        )

        draw.rounded_rectangle(
            (x, y, x + cell, y + cell),
            radius=2,
            fill=color
        )
          # Cover the old static artwork legend
    legend_y = height - 42

    draw.rectangle(
        (0, legend_y, width, height),
        fill=(8, 9, 11, 255)
    )

    # Draw the live contribution legend
    legend = [
        ("0", (35, 30, 34, 255)),
        ("1-9", (121, 11, 22, 255)),
        ("10-19", (215, 25, 50, 255)),
        ("20-29", (255, 100, 28, 255)),
        ("30+", (255, 203, 104, 255))
    ]

    x = 110

    for label, color in legend:
        draw.rounded_rectangle(
            (x, legend_y + 12, x + 15, legend_y + 27),
            radius=3,
            fill=color
        )

        draw.text(
            (x + 21, legend_y + 12),
            label,
            fill=(230, 220, 210, 255)
        )

        x += 105

    return image


def main():
    if not os.path.exists(INPUT_GIF):
        raise FileNotFoundError(INPUT_GIF)

    contributions = get_contributions()

    dragon = Image.open(INPUT_GIF)
    frames = []

    try:
        while True:
            frame = dragon.convert("RGBA")
            frame = create_grid(frame, contributions)
            frames.append(frame)
            dragon.seek(dragon.tell() + 1)

    except EOFError:
        pass

    if not frames:
        raise RuntimeError("No GIF frames found.")

    frames[0].save(
        OUTPUT_GIF,
        save_all=True,
        append_images=frames[1:],
        duration=dragon.info.get("duration", 100),
        loop=0,
        optimize=True,
        disposal=2
    )

    print(f"Created: {OUTPUT_GIF}")
    print(f"Frames: {len(frames)}")
    print(f"Contributions loaded: {len(contributions)}")


if __name__ == "__main__":
    main()
