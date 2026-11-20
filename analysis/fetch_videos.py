"""List every long-form video on Raj Shamani's channel and save it to data/videos.csv.

Usage:  python fetch_videos.py
Needs:  pip install yt-dlp
"""
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

CHANNEL = "https://www.youtube.com/@rajshamani/videos"
OUT = Path(__file__).parent / "data" / "videos.csv"
EP = re.compile(r"\bFO\s?(\d{1,4})\b", re.I)


def main():
    raw = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "--flat-playlist", "-J", CHANNEL],
        check=True, capture_output=True, text=True,
    ).stdout
    entries = json.loads(raw)["entries"]
    # The channel tab lists newest first; "order" counts from the oldest video (1).
    rows = []
    for i, e in enumerate(reversed(entries), start=1):
        m = EP.search(e.get("title") or "")
        rows.append({
            "order": i,
            "video_id": e["id"],
            "title": e.get("title") or "",
            "episode": int(m.group(1)) if m else "",
            "duration_s": e.get("duration") or "",
            "views": e.get("view_count") or "",
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"Saved {len(rows)} videos to {OUT}")


if __name__ == "__main__":
    main()
