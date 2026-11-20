"""Download transcripts for the videos in data/videos.csv.

Run this on YOUR OWN computer: YouTube blocks transcript requests from cloud servers.

    pip install youtube-transcript-api
    python fetch_transcripts.py              # every video, newest first
    python fetch_transcripts.py --limit 50   # just the 50 newest

It is safe to stop (Ctrl+C) and run again: finished videos are skipped.
Each transcript is saved as data/transcripts/<video_id>.json.
Prefers English; if a video only has Hindi captions it asks YouTube for an
English translation, and keeps the Hindi text if that fails.
"""
import argparse
import csv
import json
import random
import sys
import time
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    CouldNotRetrieveTranscript,
    IpBlocked,
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
)

HERE = Path(__file__).parent
VIDEOS = HERE / "data" / "videos.csv"
OUT = HERE / "data" / "transcripts"
MISSING = HERE / "data" / "no_transcript.txt"


def pick(api, video_id):
    tlist = api.list(video_id)
    for langs, generated in ((["en", "en-IN", "en-US", "en-GB"], False),
                             (["en", "en-IN", "en-US", "en-GB"], True)):
        for t in tlist:
            if t.language_code in langs and t.is_generated == generated:
                return t, t.fetch(), t.language_code
    t = next(iter(tlist))  # usually Hindi auto-captions
    if t.is_translatable:
        try:
            return t, t.translate("en").fetch(), f"{t.language_code}->en"
        except CouldNotRetrieveTranscript:
            pass
    return t, t.fetch(), t.language_code


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="only the N newest videos")
    ap.add_argument("--delay", type=float, default=3.0, help="seconds between videos")
    args = ap.parse_args()

    with VIDEOS.open(encoding="utf-8") as f:
        videos = sorted(csv.DictReader(f), key=lambda r: -int(r["order"]))
    if args.limit:
        videos = videos[: args.limit]

    OUT.mkdir(parents=True, exist_ok=True)
    missing = set(MISSING.read_text().split()) if MISSING.exists() else set()
    todo = [v for v in videos
            if not (OUT / f"{v['video_id']}.json").exists() and v["video_id"] not in missing]
    print(f"{len(videos) - len(todo)} done already, {len(todo)} to fetch")

    api = YouTubeTranscriptApi()
    for n, v in enumerate(todo, 1):
        vid = v["video_id"]
        try:
            t, fetched, lang = pick(api, vid)
        except (IpBlocked, RequestBlocked):
            sys.exit("\nYouTube is blocking you for now. Wait an hour or so and run again; "
                     "progress is saved.")
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, StopIteration):
            missing.add(vid)
            MISSING.write_text("\n".join(sorted(missing)) + "\n")
            print(f"[{n}/{len(todo)}] {vid}  no transcript")
            continue
        except CouldNotRetrieveTranscript as e:
            print(f"[{n}/{len(todo)}] {vid}  error: {type(e).__name__} (will retry next run)")
            continue
        text = " ".join(s.text.replace("\n", " ") for s in fetched.snippets)
        record = {
            "video_id": vid,
            "title": v["title"],
            "language": lang,
            "auto_generated": t.is_generated,
            "text": text,
        }
        (OUT / f"{vid}.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        print(f"[{n}/{len(todo)}] {vid}  {lang:8} {len(text):>7} chars  {v['title'][:60]}")
        time.sleep(args.delay + random.uniform(0, 2))
    print("Finished.")


if __name__ == "__main__":
    main()
