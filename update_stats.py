import os
import re
import json
import urllib.request
from datetime import date, datetime, timedelta, timezone

USERNAME = "asmit6109-droid"
TOKEN = os.environ["GH_TOKEN"]

today = datetime.now(timezone.utc).date()
start = today - timedelta(days=364)
year_start = date(today.year, 1, 1)

query = """
query($login: String!, $from: DateTime!, $to: DateTime!,
      $yearStart: DateTime!) {
  user(login: $login) {
    recent: contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
    yearly: contributionsCollection(from: $yearStart, to: $to) {
      contributionCalendar {
        totalContributions
      }
    }
  }
}
"""

def iso(d):
    return datetime.combine(
        d, datetime.min.time(), timezone.utc
    ).isoformat().replace("+00:00", "Z")

payload = {
    "query": query,
    "variables": {
        "login": USERNAME,
        "from": iso(start),
        "to": iso(today),
        "yearStart": iso(year_start)
    }
}

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps(payload).encode(),
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
)

with urllib.request.urlopen(request) as response:
    result = json.loads(response.read())

if "errors" in result:
    raise RuntimeError(result["errors"])

user = result["data"]["user"]

counts = {}

for week in user["recent"]["contributionCalendar"]["weeks"]:
    for day in week["contributionDays"]:
        counts[date.fromisoformat(day["date"])] = day["contributionCount"]

# Current streak
current = 0
cursor = today

if counts.get(cursor, 0) == 0:
    cursor -= timedelta(days=1)

while counts.get(cursor, 0) > 0:
    current += 1
    cursor -= timedelta(days=1)

# Longest streak
longest = 0
streak = 0

for day in sorted(counts):
    if counts[day] > 0:
        streak += 1
        longest = max(longest, streak)
    else:
        streak = 0

# Yearly contributions
total = user["yearly"]["contributionCalendar"]["totalContributions"]

# Update SVG
path = "assets/consistency-engine.svg"

with open(path, encoding="utf-8") as file:
    svg = file.read()

values = {
    "current-streak": current,
    "longest-streak": longest,
    "total-contributions": total
}

for element_id, value in values.items():
    pattern = (
        r'(<text\b[^>]*\bid="' +
        re.escape(element_id) +
        r'"[^>]*>).*?(</text>)'
    )

    svg, count = re.subn(
        pattern,
        lambda m: m.group(1) + str(value) + m.group(2),
        svg,
        count=1,
        flags=re.DOTALL
    )

    if count != 1:
        raise ValueError(f"Missing SVG element: {element_id}")

with open(path, "w", encoding="utf-8") as file:
    file.write(svg)

print("ASMIT.EXE Consistency Engine updated!")
print("Current streak:", current)
print("Longest streak:", longest)
print("Yearly contributions:", total)
