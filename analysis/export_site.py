"""Export the research to the website: research/raj-shamani/data.json.

Usage:  python export_site.py      (after analyze.py, ontology.py, predict.py)
"""
import datetime
import json
import sqlite3
from collections import Counter
from pathlib import Path

import pandas as pd

import analyze

HERE = Path(__file__).parent
OUT = HERE / "output"
SITE = HERE.parent / "research" / "raj-shamani" / "data.json"
FOCUS = ["Psychology & Self-Growth", "Business & Startups", "Health & Fitness",
         "Money & Investing", "Geopolitics & Defence"]  # stacking order = colour order
WINDOW = 40


def main():
    con = sqlite3.connect(OUT / "sanjaya.db")
    ep = pd.read_sql("SELECT * FROM v_episode ORDER BY episode", con)
    base = pd.read_sql("SELECT episode, has_transcript, video_id FROM episode", con)
    n_guests = con.execute("SELECT COUNT(*) FROM guest").fetchone()[0]
    n_links = con.execute("SELECT COUNT(*) FROM episode_mentions").fetchone()[0]
    con.close()
    ep = ep.merge(base, on="episode")
    ep["views"] = pd.to_numeric(ep["views"], errors="coerce")
    fc = json.loads((OUT / "next_episode.json").read_text())
    log = pd.read_csv(OUT / "prediction_log.csv") if (OUT / "prediction_log.csv").exists() else None
    clean = lambda t: analyze.clean_title(t).strip(" |")

    # Topic mix over time: rolling share over the previous WINDOW episodes.
    topics = ep["primary_topic"].tolist()
    river = []
    for i in range(WINDOW, len(ep) + 1, 2):
        c = Counter(topics[i - WINDOW:i])
        row = {"episode": int(ep.episode.iloc[i - 1])}
        for t in FOCUS:
            row[t] = round(c[t] / WINDOW, 4)
        row["Other"] = round(1 - sum(row[t] for t in FOCUS), 4)
        river.append(row)

    # Language swing: rolling share of English episodes (transcribed episodes only).
    lang = ep[ep.language.isin(["English", "Hindi"])].reset_index(drop=True)
    langs = []
    for i in range(WINDOW, len(lang) + 1, 2):
        w = lang.iloc[i - WINDOW:i]
        langs.append({"episode": int(w.episode.iloc[-1]),
                      "english": round(float((w.language == "English").mean()), 4)})

    # Made vs watched, last 200 episodes with views.
    rec = ep[ep.views.notna()].tail(200)
    g = rec.groupby("primary_topic")["views"].agg(["count", "median", "sum"])
    made = [{"topic": t, "episodes": int(r["count"]), "median": float(r["median"]),
             "episode_share": round(r["count"] / g["count"].sum(), 4),
             "view_share": round(r["sum"] / g["sum"].sum(), 4)}
            for t, r in g.sort_values("median", ascending=False).iterrows() if r["count"] >= 5]

    length = pd.cut(rec.minutes, [0, 60, 90, 120, 1000],
                    labels=["Under 1 h", "1–1.5 h", "1.5–2 h", "Over 2 h"])
    by_len = [{"length": str(k), "episodes": int(v["count"]), "median": float(v["median"])}
              for k, v in rec.groupby(length, observed=True)["views"].agg(["count", "median"]).iterrows()]

    top = [{"episode": int(r.episode), "title": clean(r.title), "topic": r.primary_topic,
            "views": float(r.views)} for r in ep[ep.views.notna()].nlargest(8, "views").itertuples()]
    recent = [{"episode": int(r.episode), "title": clean(r.title), "topic": r.primary_topic,
               "language": r.language if isinstance(r.language, str) else "",
               "guest": r.guest if isinstance(r.guest, str) else "",
               "views": None if pd.isna(r.views) else float(r.views)}
              for r in ep.tail(40).itertuples()]

    track = []
    if log is not None:
        for r in log.itertuples():
            scored = isinstance(r.actual_topic, str) and r.actual_topic
            track.append({"episode": int(r.episode), "made_on": r.made_on,
                          "predicted": [r.top1, r.top2, r.top3],
                          "actual": r.actual_topic if scored else None,
                          "in_top3": (str(r.hit_top3) == "True") if scored else None})

    shares = Counter(topics)
    data = {
        "updated": datetime.date.today().isoformat(),
        "counts": {"episodes": len(ep), "transcripts": int(ep.has_transcript.sum()),
                   "guests": n_guests, "mention_links": n_links,
                   "first": int(ep.episode.min()), "last": int(ep.episode.max())},
        "focus": FOCUS,
        "forecast": {k: fc[k] for k in ("next_episode", "topic_probabilities", "p_english",
                                        "profiles", "backtest", "language_backtest")},
        "track": track,
        "river": river,
        "language": langs,
        "made_vs_watched": made,
        "by_length": by_len,
        "top": top,
        "recent": recent,
        "signals": {"momentum": fc["momentum"], "overdue": fc["overdue"][:5],
                    "view_momentum": fc["view_momentum"],
                    "entities": [{"entity": k, **v} for k, v in fc["entity_trend"].items()]},
        "mix": [{"topic": t, "episodes": c, "share": round(c / len(topics), 4)}
                for t, c in shares.most_common()],
    }
    SITE.parent.mkdir(parents=True, exist_ok=True)
    SITE.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    print(f"Wrote {SITE} ({SITE.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
