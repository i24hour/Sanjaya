"""What gets @ixtremeai more impressions? Analysis of the X Premium analytics export.

Usage:  python analyze_x.py
Reads:  every .csv in data/ (the Content export: one row per post; the Overview
        export: one row per day). Column names are matched loosely, because X
        renames them now and then.
Writes: output/report.md, output/posts.csv (each post with its derived features)
"""
import math
import re
from collections import Counter
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "output"
IST = "Asia/Kolkata"
# Times in the export without a timezone are treated as UTC. If the hours in the
# report look shifted by 5.5 h, set this to IST.
EXPORT_TZ = "UTC"

# canonical name -> substrings that identify the column (lowercase, no spaces)
COLS = {
    "id": ["postid", "tweetid", "id"],
    "date": ["date", "time", "createdat"],
    "text": ["posttext", "tweettext", "text"],
    "link": ["postlink", "permalink", "link"],
    "impressions": ["impressions"],
    "engagements": ["engagements"],
    "likes": ["likes"],
    "replies": ["replies"],
    "reposts": ["reposts", "retweets"],
    "bookmarks": ["bookmarks"],
    "shares": ["shares"],
    "follows": ["newfollows", "follows"],
    "unfollows": ["unfollows"],
    "profile_visits": ["profilevisits", "userprofileclicks"],
    "url_clicks": ["urlclicks"],
    "expands": ["detailexpands"],
    "media_views": ["mediaviews", "videoviews"],
}
METRICS = ["impressions", "engagements", "likes", "replies", "reposts", "bookmarks",
           "shares", "follows", "profile_visits", "url_clicks", "expands", "media_views"]


def canon(df):
    keyed = {re.sub(r"[^a-z0-9]", "", c.lower()): c for c in df.columns}
    out = {}
    for name, keys in COLS.items():
        for k in keys:
            hit = next((orig for kk, orig in keyed.items() if kk == k), None) or \
                  next((orig for kk, orig in keyed.items() if k in kk and orig not in out.values()), None)
            if hit and hit not in out.values():
                out[name] = hit
                break
    d = df.rename(columns={v: k for k, v in out.items()})[list(out)]
    for m in METRICS + ["unfollows"]:
        if m in d:
            d[m] = pd.to_numeric(d[m].astype(str).str.replace(",", ""), errors="coerce").fillna(0)
    return d


def load():
    posts, days = [], []
    for f in sorted(DATA.glob("*.csv")):
        d = canon(pd.read_csv(f))
        (posts if "text" in d else days).append(d)
        print(f"{f.name}: {len(d)} rows, {'posts' if 'text' in d else 'daily'}; columns {list(d.columns)}")
    p = pd.concat(posts, ignore_index=True) if posts else pd.DataFrame()
    dy = pd.concat(days, ignore_index=True) if days else pd.DataFrame()
    if len(p):
        key = "id" if "id" in p else "text"
        p = p.drop_duplicates(key, keep="last")
    return p, dy


def parse_dates(s):
    t = pd.to_datetime(s, errors="coerce", format="mixed")
    if t.dt.tz is None:
        t = t.dt.tz_localize(EXPORT_TZ, ambiguous="NaT", nonexistent="NaT")
    has_time = bool((t.dt.hour + t.dt.minute).fillna(0).astype(bool).any())
    return t.dt.tz_convert(IST), has_time


EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


def features(p):
    p = p.copy()
    p["text"] = p["text"].fillna("").astype(str)
    t = p["text"]
    p["kind"] = "Original post"
    p.loc[t.str.match(r"^\s*@\w+"), "kind"] = "Reply"
    p.loc[t.str.match(r"^\s*RT @"), "kind"] = "Repost"
    p["chars"] = t.str.replace(r"https?://\S+", "", regex=True).str.len()
    p["has_link"] = t.str.contains(r"https?://(?!t\.co/\w+$)\S+", regex=True)
    p["has_media"] = (p["media_views"] > 0) if "media_views" in p else t.str.contains(r"pic\.x\.com|pic\.twitter\.com|t\.co/\w+\s*$", regex=True)
    p["lines"] = t.str.count("\n") + 1
    p["has_question"] = t.str.contains(r"\?")
    p["has_number"] = t.str.contains(r"\d")
    p["has_emoji"] = t.apply(lambda x: bool(EMOJI.search(x)))
    p["hashtags"] = t.str.count(r"#\w+")
    p["mentions"] = t.str.count(r"@\w+") - (p["kind"] == "Reply").astype(int)
    p["hindi"] = t.str.contains(r"[ऀ-ॿ]")
    p["is_thread"] = t.str.contains(r"(?:^|\s)(?:🧵|thread|1/\d*|\(1/)", case=False, regex=True)
    p["first_line"] = t.str.split("\n").str[0].str.strip()
    p["eng_rate"] = (p["engagements"] / p["impressions"]).where(p["impressions"] > 0) if "engagements" in p else float("nan")
    if "follows" in p:
        p["follows_per_1k"] = (1000 * p["follows"] / p["impressions"]).where(p["impressions"] > 0)
    return p


def bucket_table(p, col, order=None, min_n=3):
    g = p.groupby(col)["impressions"].agg(["count", "median", "mean"])
    if "eng_rate" in p:
        g["eng"] = p.groupby(col)["eng_rate"].median()
    g = g[g["count"] >= min_n]
    if order:
        g = g.reindex([o for o in order if o in g.index])
    return g


def fmt(n):
    return f"{n / 1e6:.1f}M" if n >= 1e6 else f"{n / 1e3:.1f}K" if n >= 1e3 else f"{n:.0f}"


def words(text):
    text = re.sub(r"https?://\S+|@\w+", " ", text.lower())
    return set(w for w in re.findall(r"[a-z][a-z0-9']{2,}|[ऀ-ॿ]{2,}", text)) - STOP


STOP = set("""the and for you your are that this with have has was were but not just its it's
from they them what when how why who all can will would about into out more most than then
there their our get got one also very like been being here only some any which while each
over such these those because should could did does doing let i'm i've don't can't amp""".split())


def main():
    OUT.mkdir(exist_ok=True)
    posts, days = load()
    if posts.empty:
        raise SystemExit("No post-level CSV found in data/. Export the Content tab from X Analytics.")
    p = features(posts)
    p["when"], has_time = parse_dates(p["date"])
    p = p[p["impressions"].notna()]
    orig = p[p.kind == "Original post"]
    L = []
    w = L.append
    span = f"{p['when'].min():%d %b %Y} to {p['when'].max():%d %b %Y}" if p["when"].notna().any() else "unknown dates"
    w("# @ixtremeai: what gets impressions\n")
    w(f"{len(p)} posts ({span}): {len(orig)} original posts, {(p.kind == 'Reply').sum()} replies. "
      f"Total impressions {fmt(p.impressions.sum())}; median per post {fmt(p.impressions.median())}.\n")

    # --- concentration
    s = p.impressions.sort_values(ascending=False)
    top10 = s.head(max(1, len(s) // 10)).sum() / max(s.sum(), 1)
    w("## 1. How concentrated is reach?\n")
    w(f"The top 10% of posts brought **{100 * top10:.0f}%** of all impressions. "
      + ("Reach comes from a few breakout posts, so the goal is more shots at a breakout, "
         "and learning what the breakouts share." if top10 > 0.5 else
         "Reach is fairly even across posts, so consistency matters more than breakouts.") + "\n")

    def table(title, g, label):
        w(f"### {title}\n")
        cols = "| " + label + " | Posts | Median impressions | Average |" + (" Engagement rate |" if "eng" in g else "")
        w(cols + "\n|---|---|---|---|" + ("---|" if "eng" in g else ""))
        for k, r in g.iterrows():
            w(f"| {k} | {int(r['count'])} | {fmt(r['median'])} | {fmt(r['mean'])} |"
              + (f" {100 * r['eng']:.1f}% |" if "eng" in g and not math.isnan(r["eng"]) else (" – |" if "eng" in g else "")))
        w("")

    w("## 2. What kind of post works\n")
    table("Post type", bucket_table(p, "kind"), "Type")
    o = orig.copy()
    o["Format"] = o.apply(lambda r: "Thread" if r.is_thread else "With media" if r.has_media
                          else "With link" if r.has_link else "Text only", axis=1)
    table("Format (original posts)", bucket_table(o, "Format"), "Format")
    o["Length"] = pd.cut(o.chars, [-1, 70, 140, 280, 100000],
                         labels=["Under 70 chars", "70–140", "140–280", "Long (280+)"])
    table("Length (original posts)", bucket_table(o, "Length", order=list(o["Length"].cat.categories)), "Length")
    flags = []
    for col, name in [("has_question", "Asks a question"), ("has_number", "Has a number"),
                      ("has_emoji", "Has an emoji"), ("hindi", "Has Hindi"),
                      ("has_link", "Has a link"), ("has_media", "Has media")]:
        a, b = o[o[col]], o[~o[col]]
        if len(a) >= 3 and len(b) >= 3:
            flags.append((name, len(a), a.impressions.median(), b.impressions.median()))
    if (o.hashtags > 0).sum() >= 3:
        flags.append(("Uses hashtags", int((o.hashtags > 0).sum()),
                      o[o.hashtags > 0].impressions.median(), o[o.hashtags == 0].impressions.median()))
    if flags:
        w("### Features (original posts: median impressions with vs without)\n")
        w("| Feature | Posts with it | With | Without | Lift |\n|---|---|---|---|---|")
        for name, n, a, b in sorted(flags, key=lambda x: -(x[2] / max(x[3], 1))):
            w(f"| {name} | {n} | {fmt(a)} | {fmt(b)} | {a / max(b, 1):.2f}× |")
        w("")

    if has_time:
        w("## 3. When to post (IST)\n")
        w(f"*Export times read as {EXPORT_TZ} and shown in IST.*\n")
        o["Hour"] = o["when"].dt.hour
        o["Slot"] = pd.cut(o["Hour"], [-1, 5, 9, 12, 15, 18, 21, 24],
                           labels=["Night (0–6)", "Early (6–10)", "Morning (10–13)", "Afternoon (13–16)",
                                   "Evening (16–19)", "Prime (19–22)", "Late (22–24)"])
        table("Time of day", bucket_table(o, "Slot", order=list(o["Slot"].cat.categories)), "Slot")
        o["Day"] = o["when"].dt.day_name()
        table("Day of week", bucket_table(o, "Day", order=["Monday", "Tuesday", "Wednesday", "Thursday",
                                                          "Friday", "Saturday", "Sunday"]), "Day")
    else:
        w("## 3. When to post\n\nThe export has dates but no times, so time of day can't be analysed.\n")

    # --- winners vs the rest
    w("## 4. Your winners vs the rest\n")
    q90, q50 = o.impressions.quantile(0.9), o.impressions.quantile(0.5)
    win, rest = o[o.impressions >= q90], o[o.impressions <= q50]
    if len(win) >= 3 and len(rest) >= 3:
        def share(df, col):
            return df[col].mean()
        rows = [("Median length (chars)", f"{win.chars.median():.0f}", f"{rest.chars.median():.0f}"),
                ("Lines", f"{win.lines.median():.0f}", f"{rest.lines.median():.0f}")]
        for col, name in [("has_media", "With media"), ("has_link", "With a link"), ("has_question", "Asks a question"),
                          ("has_number", "Has a number"), ("is_thread", "Thread"), ("hindi", "Has Hindi")]:
            rows.append((name, f"{100 * share(win, col):.0f}%", f"{100 * share(rest, col):.0f}%"))
        w(f"Top 10% of original posts ({len(win)} posts, {fmt(q90)}+ impressions) vs bottom half ({len(rest)} posts).\n")
        w("| | Winners | Bottom half |\n|---|---|---|")
        for r in rows:
            w(f"| {r[0]} | {r[1]} | {r[2]} |")
        cw, cr = Counter(), Counter()
        for t in win.text:
            cw.update(words(t))
        for t in rest.text:
            cr.update(words(t))
        score = {k: (cw[k] + 0.5) / (len(win) + 1) / ((cr[k] + 0.5) / (len(rest) + 1)) for k in cw if cw[k] >= 2}
        top_words = sorted(score, key=score.get, reverse=True)[:15]
        if top_words:
            w(f"\n**Words that show up far more in winners:** {', '.join(top_words)}\n")
    w("\n**Your 10 best posts**\n")
    for _, r in p.nlargest(10, "impressions").iterrows():
        extra = f", {int(r['follows'])} follows" if "follows" in r and r["follows"] else ""
        w(f"- **{fmt(r.impressions)}**{extra} · {r.kind.lower()} · {r.first_line[:140]}")

    # --- replies
    reps = p[p.kind == "Reply"]
    if len(reps) >= 5 and len(orig) >= 5:
        w("\n## 5. Replies vs original posts\n")
        w(f"- Replies: {len(reps)}, median {fmt(reps.impressions.median())} impressions, "
          f"{fmt(reps.impressions.sum())} in total ({100 * reps.impressions.sum() / p.impressions.sum():.0f}% of all).")
        w(f"- Original posts: {len(orig)}, median {fmt(orig.impressions.median())}, "
          f"{fmt(orig.impressions.sum())} in total.")
        if "follows" in p:
            w(f"- New follows per 1,000 impressions: replies {reps.follows.sum() * 1000 / max(reps.impressions.sum(), 1):.2f}, "
              f"originals {orig.follows.sum() * 1000 / max(orig.impressions.sum(), 1):.2f}.")
        w("")

    # --- daily
    if not days.empty and "date" in days:
        d = days.copy()
        d["day"] = pd.to_datetime(d["date"], errors="coerce", format="mixed")
        d = d.dropna(subset=["day"]).sort_values("day")
        if len(d) >= 14 and "impressions" in d:
            d["month"] = d.day.dt.to_period("M")
            g = d.groupby("month").agg(impressions=("impressions", "sum"),
                                       **({"follows": ("follows", "sum")} if "follows" in d else {}))
            w("## 6. Month by month\n")
            w("| Month | Impressions |" + (" New follows |" if "follows" in g else "") + "\n|---|---|" + ("---|" if "follows" in g else ""))
            for m, r in g.iterrows():
                w(f"| {m} | {fmt(r.impressions)} |" + (f" {int(r.follows)} |" if "follows" in g else ""))
            w("")
    (OUT / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    p.drop(columns=["when"]).assign(when=p["when"].astype(str)).to_csv(OUT / "posts.csv", index=False)
    print("\n".join(L))


if __name__ == "__main__":
    main()
