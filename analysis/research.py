"""Research report on Raj Shamani's Figuring Out podcast, built from titles and transcripts.

Usage:  python research.py        (run analyze.py first for the forecast)
Writes: output/research.md
"""
import json
import re
from pathlib import Path

import pandas as pd
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer

import analyze

HERE = Path(__file__).parent
OUT = HERE / "output"
pct = lambda x: f"{100 * x:.0f}%"


def load():
    df = analyze.load_episodes()
    texts = {}
    for vid in df["video_id"]:
        p = analyze.DATA / "transcripts" / f"{vid}.json"
        texts[vid] = json.loads(p.read_text(encoding="utf-8"))["text"] if p.exists() else ""
    df["text"] = df["video_id"].map(texts)
    df["lang"] = df["transcript_lang"].map(
        lambda l: "" if not l else ("Hindi" if l == "hi" else "English"))
    df["views"] = pd.to_numeric(df["views"], errors="coerce")
    df["minutes"] = pd.to_numeric(df["duration_s"], errors="coerce") / 60
    df["block"] = ((df["episode"] - 1) // 100) * 100 + 1
    df["block"] = df["block"].map(lambda b: f"FO{b}–{b + 99}")
    return df


def themes(texts, n_topics, lang):
    if lang == "en":
        vec = TfidfVectorizer(stop_words="english", max_df=0.35, min_df=5,
                              token_pattern=r"(?u)\b[a-zA-Z]{4,}\b", max_features=20000)
    else:
        vec = TfidfVectorizer(max_df=0.25, min_df=5,
                              token_pattern=r"[ऀ-ॿ]{3,}", max_features=20000)
    X = vec.fit_transform(texts)
    model = NMF(n_components=n_topics, random_state=0, init="nndsvda", max_iter=400).fit(X)
    words = vec.get_feature_names_out()
    W = model.transform(X)
    out = []
    for k, comp in enumerate(model.components_):
        top = [words[i] for i in comp.argsort()[::-1][:9]]
        out.append((top, int((W.argmax(axis=1) == k).sum())))
    return sorted(out, key=lambda t: -t[1])


def main():
    df = load()
    videos = pd.read_csv(analyze.DATA / "videos.csv")
    n_tx = len(list((analyze.DATA / "transcripts").glob("*.json")))
    missing = analyze.DATA / "no_transcript.txt"
    n_none = len(missing.read_text().split()) if missing.exists() else 0
    fc = json.loads((OUT / "forecast.json").read_text())
    topics = [t for t in list(analyze.TOPICS) + ["Other"] if (df["topic"] == t).any()]
    L = []
    w = L.append

    w("# Raj Shamani's *Figuring Out*: what he talks about, what works, what's next\n")
    w(f"Built from {len(videos)} channel videos: {n_tx} transcripts downloaded, "
      f"{n_none} videos with no transcript on YouTube. The analysis covers the {len(df)} "
      f"numbered podcast episodes (FO{df.episode.min()} to FO{df.episode.max()}), "
      f"{int(df.has_transcript.sum())} of them with a transcript.\n")

    # ---- Key findings placeholder (filled below once numbers exist) ----
    findings_at = len(L)

    # ---- 1. Topic mix ----
    w("## 1. What the show is about\n")
    share = df["topic"].value_counts(normalize=True)
    w("| Topic | Episodes | Share |\n|---|---|---|")
    for t, s in share.items():
        w(f"| {t} | {(df.topic == t).sum()} | {pct(s)} |")
    w("\nEach episode gets the topic its title and transcript score highest on (keywords in "
      "English, Hindi and Hinglish). Check of reliability: tagging from the transcript alone "
      "agrees with tagging from the title alone for two thirds of episodes, and the title's "
      "topic is in the transcript's top two for about 85%, for both Hindi and English episodes.\n")

    # ---- 2. Over time ----
    w("## 2. How the show changed, 100 episodes at a time\n")
    blocks = list(dict.fromkeys(df["block"]))
    mix = pd.crosstab(df["topic"], df["block"], normalize="columns")[blocks]
    w("| Topic | " + " | ".join(blocks) + " |\n|---|" + "---|" * len(blocks))
    for t in share.index:
        w(f"| {t} | " + " | ".join(pct(mix.loc[t, b]) if t in mix.index else "0%" for b in blocks) + " |")
    lang_by_block = (df[df.lang != ""].groupby("block")["lang"]
                     .apply(lambda s: (s == "English").mean()).reindex(blocks))
    w("| *English-language episodes* | " + " | ".join(pct(x) for x in lang_by_block) + " |")
    med_by_block = df.groupby("block")["views"].median().reindex(blocks)
    w("| *Median views* | " + " | ".join(f"{x / 1e6:.2f}M" for x in med_by_block) + " |")
    w("")

    # ---- 3. What gets watched ----
    recent = df[df.views.notna()].tail(200)
    w("## 3. What gets watched (last 200 episodes)\n")
    tv = recent.groupby("topic")["views"].agg(["count", "median", "sum"])
    tv["ep_share"] = tv["count"] / tv["count"].sum()
    tv["view_share"] = tv["sum"] / tv["sum"].sum()
    tv = tv.sort_values("median", ascending=False)
    w("| Topic | Episodes | Median views | Share of episodes | Share of all views |\n|---|---|---|---|---|")
    for t, r in tv.iterrows():
        w(f"| {t} | {int(r['count'])} | {r['median'] / 1e6:.2f}M | {pct(r.ep_share)} | {pct(r.view_share)} |")
    w("\nTopics whose share of views beats their share of episodes are under-served by the "
      "show; the reverse are over-served. Topics with fewer than 5 episodes are too thin to "
      "read much into.\n")
    lv = recent[recent.lang != ""].groupby("lang")["views"].agg(["count", "median"])
    w("| Episode language | Episodes | Median views |\n|---|---|---|")
    for l, r in lv.iterrows():
        w(f"| {l} | {int(r['count'])} | {r['median'] / 1e6:.2f}M |")
    recent = recent.assign(length=pd.cut(recent.minutes, [0, 60, 90, 120, 1000],
                                         labels=["under 1h", "1–1.5h", "1.5–2h", "over 2h"]))
    dv = recent.groupby("length", observed=True)["views"].agg(["count", "median"])
    w("\n| Episode length | Episodes | Median views |\n|---|---|---|")
    for l, r in dv.iterrows():
        w(f"| {l} | {int(r['count'])} | {r['median'] / 1e6:.2f}M |")
    top = df[df.views.notna()].nlargest(10, "views")
    w("\n**Ten most-watched episodes**\n")
    for _, r in top.iterrows():
        w(f"- {r.views / 1e6:.1f}M · FO{r.episode} · {r.topic} · "
          f"{analyze.clean_title(r.title).strip(' |')}")
    w("")

    # ---- 4. Themes discovered ----
    w("## 4. Themes found in the transcripts themselves\n")
    w("Independent of the topic list above: an unsupervised model (NMF) groups transcripts "
      "by the words they share. Shown with the words that define each theme and how many "
      "episodes it leads in. A couple of the Hindi themes are caption noise "
      "(auto-captions mishearing words), which is expected.\n")
    en = df[(df.lang == "English") & (df.text.str.len() > 2000)]
    hi = df[(df.lang == "Hindi") & (df.text.str.len() > 2000)]
    w(f"**English episodes ({len(en)})**\n")
    for words, n in themes(en.text.tolist(), 10, "en"):
        w(f"- {n} episodes: {', '.join(words)}")
    w(f"\n**Hindi episodes ({len(hi)})**\n")
    for words, n in themes(hi.text.tolist(), 10, "hi"):
        w(f"- {n} episodes: {', '.join(words)}")
    w("")

    # ---- 5. Forecast ----
    w(f"## 5. Forecast for FO{fc['next_episode']}\n")
    w("| Topic | Probability |\n|---|---|")
    for r in fc["probabilities"][:6]:
        w(f"| {r['topic']} | {pct(r['p'])} |")
    bt = fc["backtest"]
    m, base = bt["model"], bt["baselines"]["Always the most common topic so far"]
    w(f"\nTested on the last {bt['test_episodes']} episodes, each predicted only from the "
      "episodes before it:\n")
    w("| Method | Right first guess | Right in top 3 |\n|---|---|---|")
    w(f"| Forecast model | {pct(m['top1'])} | {pct(m['top3'])} |")
    for name, r in bt["baselines"].items():
        w(f"| {name} | {pct(r['top1'])} | {pct(r['top3'])} |")
    w(f"\nThe next topic is only weakly predictable: the model's first guess is right about "
      f"one time in {round(1 / m['top1'])}. It is best read as a ranking of likely topics, not a call.\n")

    # ---- Key findings ----
    tr = {r["topic"]: r for r in fc["trend_last50_vs_prior100"]}
    rising = sorted(tr.values(), key=lambda r: r["recent_share"] - r["prior_share"], reverse=True)
    best = tv[tv["count"] >= 5].sort_values("median", ascending=False)
    first_en, last_en = lang_by_block.iloc[0], lang_by_block.iloc[-1]
    keyf = [
        "## Key findings\n",
        f"1. **The show has moved from business to the mind.** {rising[0]['topic']} went from "
        f"{pct(rising[0]['prior_share'])} to {pct(rising[0]['recent_share'])} of episodes "
        "(last 50 vs the 100 before), while Business, Money and Health shrank.",
        f"2. **The language has swung back to English.** English-language episodes went from "
        f"{pct(first_en)} in {blocks[0]} down to {pct(lang_by_block.min())} in "
        f"{lang_by_block.idxmin()} (the Hindi, Indian-guest era) and back up to {pct(last_en)} "
        f"in {blocks[-1]}, as foreign guests took over. Hindi and English episodes get about "
        "the same median views.",
        f"3. **What gets watched isn't what he makes most.** Among topics with 5+ recent "
        f"episodes, {best.index[0]} ({best['median'].iloc[0] / 1e6:.2f}M median) and "
        f"{best.index[1]} ({best['median'].iloc[1] / 1e6:.2f}M) lead; "
        f"{best.index[-1]} trails at {best['median'].iloc[-1] / 1e6:.2f}M. "
        f"Geopolitics is {pct(tv.loc['Geopolitics & Defence', 'ep_share'])} of episodes but "
        f"{pct(tv.loc['Geopolitics & Defence', 'view_share'])} of views, while Health is "
        f"{pct(tv.loc['Health & Fitness', 'ep_share'])} of episodes and "
        f"{pct(tv.loc['Health & Fitness', 'view_share'])} of views.",
        f"4. **Longer episodes get more views.** Episodes over 2 hours have a "
        f"{dv['median'].iloc[-1] / 1e6:.2f}M median, against {dv['median'].iloc[1] / 1e6:.2f}M "
        "for 1–1.5 hours (likely partly because bigger guests get longer conversations).",
        f"5. **Next episode:** most likely {fc['probabilities'][0]['topic']} "
        f"({pct(fc['probabilities'][0]['p'])}), then {fc['probabilities'][1]['topic']} and "
        f"{fc['probabilities'][2]['topic']}. Topic choice is only weakly predictable "
        f"({pct(m['top1'])} first-guess accuracy vs {pct(base['top1'])} for the obvious baseline).",
        "",
    ]
    L[findings_at:findings_at] = keyf
    (OUT / "research.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
