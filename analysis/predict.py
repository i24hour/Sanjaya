"""Signals + model + brief: predict Raj Shamani's next episode from the ontology.

Usage:  python ontology.py && python predict.py
Reads:  output/sanjaya.db
Writes: output/next_episode_brief.md, output/next_episode.json

Model: multinomial logistic regression on signals computed only from episodes
before the one being predicted (recent topic mix, what came last, how long since
each topic, which topics are drawing views, language of recent episodes),
blended with the trend model from analyze.py. Tested walk-forward: each test
episode is predicted from the past only, and the blend weight is picked on a
validation window that comes before the test window.
"""
import json
import math
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

import analyze

HERE = Path(__file__).parent
OUT = HERE / "output"
DB = OUT / "sanjaya.db"
TEST_N, VAL_N, MIN_TRAIN = 120, 80, 60
pct = lambda x: f"{100 * x:.0f}%"


def load():
    con = sqlite3.connect(DB)
    ep = pd.read_sql("SELECT * FROM episode ORDER BY episode", con)
    mentions = pd.read_sql("SELECT * FROM episode_mentions", con)
    guests = pd.read_sql("SELECT * FROM v_episode", con)
    con.close()
    ep["logv"] = np.log10(ep["views"].astype(float))
    return ep, mentions, guests


# ---------- signals at a point in time (only uses rows before i) ----------

def features(ep, i, cats):
    past = ep.iloc[:i]
    seq = past["primary_topic"].tolist()
    f = []
    for w in (5, 15, 50):
        c = Counter(seq[-w:])
        f += [c[t] / min(w, len(seq)) for t in cats]
    f += [1.0 if seq[-1] == t else 0.0 for t in cats]
    for t in cats:
        idx = [k for k, s in enumerate(seq) if s == t]
        f.append(math.log1p(len(seq) - idx[-1]) if idx else math.log1p(len(seq)))
    recent = past.tail(40)
    base = recent["logv"].median()
    for t in cats:
        v = recent.loc[recent.primary_topic == t, "logv"].dropna()
        f.append(float(v.median() - base) if len(v) and not math.isnan(base) else 0.0)
    lang = past["language"].tail(10)
    f.append((lang == "English").mean() if len(lang) else 0.0)
    return [0.0 if (x is None or math.isnan(x)) else x for x in f]


def lang_features(ep, i):
    lang = ep["language"].iloc[:i]
    is_en = (lang == "English").astype(float)
    return [is_en.tail(3).mean(), is_en.tail(10).mean(), is_en.tail(30).mean(),
            float(lang.iloc[-1] == "English")]


# ---------- models ----------

def walk_forward(ep, cats, start, end):
    """Predict topics for rows start..end-1. Returns list of (lr_probs, blend_probs, actual)."""
    seq = ep["primary_topic"].tolist()
    X = np.array([features(ep, i, cats) if i >= 10 else np.zeros(1) for i in range(len(ep))],
                 dtype=object)
    out, model, scaler = [], None, None
    for k, i in enumerate(range(start, end)):
        if model is None or k % 10 == 0:
            rows = list(range(MIN_TRAIN, i))
            Xt = np.vstack([X[r] for r in rows])
            yt = [seq[r] for r in rows]
            scaler = StandardScaler().fit(Xt)
            model = LogisticRegression(C=0.05, max_iter=3000).fit(scaler.transform(Xt), yt)
        p = model.predict_proba(scaler.transform(np.array([X[i]], dtype=float)))[0]
        lr = {t: 1e-4 for t in cats}
        for cls, pv in zip(model.classes_, p):
            lr[cls] = pv
        s = sum(lr.values())
        lr = {t: v / s for t, v in lr.items()}
        bl = analyze.forecast(seq[:i], cats, 0.65, 0.0, 40)
        out.append((lr, bl, seq[i]))
    return out


def score(preds, w):
    top1 = top3 = 0
    ll = 0.0
    for lr, bl, y in preds:
        p = {t: w * lr[t] + (1 - w) * bl[t] for t in lr}
        r = sorted(p, key=p.get, reverse=True)
        top1 += r[0] == y
        top3 += y in r[:3]
        ll -= math.log(max(p[y], 1e-9))
    n = len(preds)
    return {"top1": top1 / n, "top3": top3 / n, "logloss": ll / n}


def main():
    ep, mentions, guests = load()
    cats = [t for t in list(analyze.TOPICS) + ["Other"] if (ep.primary_topic == t).any()]
    n = len(ep)
    seq = ep["primary_topic"].tolist()

    # Validation window picks the blend weight; test window reports honestly.
    val = walk_forward(ep, cats, n - TEST_N - VAL_N, n - TEST_N)
    weights = [0.0, 0.25, 0.5, 0.75, 1.0]
    w_best = min(weights, key=lambda w: score(val, w)["logloss"])
    test = walk_forward(ep, cats, n - TEST_N, n)
    results = {
        "Combined model (signals + trend)": score(test, w_best),
        "Signals model alone": score(test, 1.0),
        "Trend model (previous forecast)": score(test, 0.0),
    }
    cnt_base = {"top1": 0, "top3": 0}
    for i in range(n - TEST_N, n):
        c = Counter(seq[:i]).most_common()
        cnt_base["top1"] += c[0][0] == seq[i]
        cnt_base["top3"] += seq[i] in [x for x, _ in c[:3]]
    results["Always the most common topic"] = {k: v / TEST_N for k, v in cnt_base.items()}

    # Final forecast for the next episode: fit on everything.
    X = np.array([features(ep, i, cats) for i in range(MIN_TRAIN, n)], dtype=float)
    y = seq[MIN_TRAIN:n]
    scaler = StandardScaler().fit(X)
    model = LogisticRegression(C=0.05, max_iter=3000).fit(scaler.transform(X), y)
    p = model.predict_proba(scaler.transform(np.array([features(ep, n, cats)])))[0]
    lr = {t: 1e-4 for t in cats}
    lr.update(dict(zip(model.classes_, p)))
    bl = analyze.forecast(seq, cats, 0.65, 0.0, 40)
    topic_p = {t: w_best * lr[t] / sum(lr.values()) + (1 - w_best) * bl[t] for t in cats}
    topic_rank = sorted(topic_p.items(), key=lambda kv: kv[1], reverse=True)

    # Language: logistic model vs "same as last episode".
    lang_rows = [i for i in range(MIN_TRAIN, n) if ep.language.iloc[i]]
    lang_hit = base_hit = 0
    test_rows = [i for i in lang_rows if i >= n - TEST_N]
    for i in test_rows:
        tr = [r for r in lang_rows if r < i]
        m = LogisticRegression(max_iter=1000).fit([lang_features(ep, r) for r in tr],
                                                  [ep.language.iloc[r] for r in tr])
        lang_hit += m.predict([lang_features(ep, i)])[0] == ep.language.iloc[i]
        prev = next(ep.language.iloc[r] for r in range(i - 1, -1, -1) if ep.language.iloc[r])
        base_hit += prev == ep.language.iloc[i]
    lm = LogisticRegression(max_iter=1000).fit([lang_features(ep, r) for r in lang_rows],
                                               [ep.language.iloc[r] for r in lang_rows])
    p_en = dict(zip(lm.classes_, lm.predict_proba([lang_features(ep, n)])[0])).get("English", 0)

    # Guest type given topic (last 150 episodes).
    recent = ep.tail(150)
    role_given_topic = recent.groupby("primary_topic")["guest_role"].value_counts(normalize=True)
    role_p = defaultdict(float)
    for t, pt in topic_p.items():
        if t in role_given_topic.index.get_level_values(0):
            for role, pr in role_given_topic[t].items():
                role_p[role] += pt * pr
    role_rank = sorted(role_p.items(), key=lambda kv: kv[1], reverse=True)

    # Signals ------------------------------------------------------------
    tx = ep[ep.has_transcript == 1]
    last_eps, prior_eps = set(tx.episode.tail(30)), set(tx.episode.iloc[-150:-30])
    m = mentions.pivot_table(index="episode", columns="entity", values="per_1000_words",
                             fill_value=0).reindex(tx.episode, fill_value=0)
    rise = pd.DataFrame({
        "recent": m.loc[m.index.isin(last_eps)].mean(),
        "prior": m.loc[m.index.isin(prior_eps)].mean(),
        "reach": (m.loc[m.index.isin(last_eps)] > 0.2).mean(),
    })
    rise["ratio"] = (rise.recent + 0.05) / (rise.prior + 0.05)
    rising = rise[rise.reach >= 0.1].sort_values("ratio", ascending=False)

    v = ep.tail(60)
    base_v = v["views"].median()
    view_mom = (v.groupby("primary_topic")["views"].agg(["count", "median"])
                .assign(lift=lambda d: d["median"] / base_v).sort_values("lift", ascending=False))

    gaps = {}
    for t in cats:
        idx = [k for k, s in enumerate(seq) if s == t]
        if len(idx) >= 4:
            typical = float(np.median(np.diff(idx[-15:])))
            gaps[t] = (n - 1 - idx[-1], typical)
    due = sorted(((t, g, ty, g / ty) for t, (g, ty) in gaps.items()), key=lambda x: -x[3])

    # Entities linked to each likely topic (co-occurrence in recent episodes of that topic).
    topic_of = ep.set_index("episode")["primary_topic"]
    rec_m = m.loc[m.index.isin(set(tx.episode.tail(120)))]
    def topic_entities(t, k=4):
        rows = rec_m.loc[[e for e in rec_m.index if topic_of.get(e) == t]]
        if rows.empty:
            return []
        score_ = rows.mean() * rise["ratio"].reindex(rows.columns).fillna(1)
        return [e for e in score_.sort_values(ascending=False).index[:k]]

    # Brief ----------------------------------------------------------------
    last = ep.iloc[-1]
    nxt = int(last.episode) + 1
    L = []
    w = L.append
    w(f"# Next-episode brief: FO{nxt}\n")
    w(f"*Prepared from the Sanjaya ontology: {n} episodes, {int(ep.has_transcript.sum())} "
      f"transcripts, {guests.guest.nunique()} guests, {mentions.entity.nunique()} tracked "
      "entities. Every number below can be traced back to episode rows in `output/sanjaya.db`.*\n")
    w("## The call\n")
    t1, t2, t3 = topic_rank[0], topic_rank[1], topic_rank[2]
    lang_call = "English" if p_en >= 0.5 else "Hindi"
    w(f"- **Most likely topic:** {t1[0]} ({pct(t1[1])}), then {t2[0]} ({pct(t2[1])}) "
      f"and {t3[0]} ({pct(t3[1])}).")
    w(f"- **Language:** {lang_call}, {pct(max(p_en, 1 - p_en))} likely.")
    w(f"- **Guest type:** {role_rank[0][0]} ({pct(role_rank[0][1])}), then "
      f"{role_rank[1][0]} ({pct(role_rank[1][1])}).")
    w("\n**Three most likely episode profiles** (likely topic + the guest type and "
      "entities that go with it in recent episodes; these are hypotheses, not leaks):\n")
    for k, (t, pt) in enumerate(topic_rank[:3], 1):
        roles = role_given_topic[t].index[0] if t in role_given_topic.index.get_level_values(0) else "Expert"
        roles = ("outside the usual categories" if roles == "Expert / other"
                 else "a " + roles.lower())
        ents = topic_entities(t)
        w(f"{k}. **{t}** ({pct(pt)}): guest most likely {roles}, {('in English' if p_en >= 0.5 else 'in Hindi')}, "
          f"likely touching on {', '.join(ents) if ents else 'the usual themes'}.")
    w("\n## Confidence: how this model did on past episodes\n")
    w(f"Last {TEST_N} episodes, each predicted only from earlier ones; the blend weight "
      f"({pct(w_best)} signals model) was chosen on the {VAL_N} episodes before that.\n")
    w("| Method | Right first guess | Right in top 3 |\n|---|---|---|")
    for name, r in results.items():
        w(f"| {name} | {pct(r['top1'])} | {pct(r['top3'])} |")
    if w_best == 0:
        w("\n**What this shows:** the extra signals (views, how long since a topic last "
          "appeared, what came last) did not beat the simple recent-trend model when tested on "
          "past episodes, so the validation step gave them no weight. The forecast below is "
          "the trend model's, and the signals are shown as context, not as drivers.")
    w(f"\nLanguage of the next episode: right {pct(lang_hit / len(test_rows))} of the time, "
      f"vs {pct(base_hit / len(test_rows))} for \"same language as last episode\".\n")
    w("## Signals behind the call\n")
    w("**1. Topic momentum** (share of the last 20 episodes vs the last 100)\n")
    w("| Topic | Last 20 | Last 100 |\n|---|---|---|")
    c20, c100 = Counter(seq[-20:]), Counter(seq[-100:])
    for t, _ in sorted(c20.items(), key=lambda kv: -kv[1]):
        w(f"| {t} | {pct(c20[t] / 20)} | {pct(c100[t] / 100)} |")
    w("\n**2. What's drawing views** (last 60 episodes, median views vs the channel's median "
      f"of {base_v / 1e6:.2f}M)\n")
    w("| Topic | Episodes | Median views | vs channel |\n|---|---|---|---|")
    for t, r in view_mom[view_mom["count"] >= 3].iterrows():
        w(f"| {t} | {int(r['count'])} | {r['median'] / 1e6:.2f}M | {r['lift']:.2f}× |")
    w("\nTopics with fewer than 3 recent episodes are left out: one episode is not a trend.")
    w("\n**3. Topics that are \"due\"** (episodes since it last appeared vs its usual gap)\n")
    w("| Topic | Episodes since last | Usual gap | Overdue factor |\n|---|---|---|---|")
    for t, g, ty, r in due[:6]:
        w(f"| {t} | {g} | {ty:.0f} | {r:.1f}× |")
    w("\n**4. Rising in the conversations** (mentions per 1,000 words, last 30 transcribed "
      "episodes vs the 120 before; only entities that come up in at least 10% of recent episodes)\n")
    w("| Entity | Recent | Before | Change |\n|---|---|---|---|")
    for e, r in rising.head(10).iterrows():
        w(f"| {e} | {r.recent:.2f} | {r.prior:.2f} | {r.ratio:.1f}× |")
    w("\n**Fading**\n")
    for e, r in rising.tail(5).iloc[::-1].iterrows():
        w(f"- {e}: {r.prior:.2f} → {r.recent:.2f} per 1,000 words")
    w("\n**5. Guest types, last 30 episodes**\n")
    for role, k in ep.tail(30)["guest_role"].value_counts().items():
        w(f"- {role}: {k}")
    w(f"\n## Last 10 episodes (the most recent context)\n")
    for _, r in ep.tail(10).iloc[::-1].iterrows():
        w(f"- FO{r.episode} · {r.primary_topic} · {r.language or '?'} · "
          f"{'views n/a' if pd.isna(r.views) else f'{r.views / 1e6:.2f}M'} · {analyze.clean_title(r.title).strip(' |')}")
    w("\n## Limits\n")
    w("- Topic choice is mostly the guest's availability, which no public data shows; "
      f"even the best model is right on its first guess only about one time in "
      f"{round(1 / max(results['Combined model (signals + trend)']['top1'], 1e-9))}.")
    w("- Topics and guest types are tagged automatically (about 2 in 3 agree with a "
      "title-only reading); a wrong tag in the history adds noise to the forecast.")
    w("- No upload dates are used (the channel listing doesn't give them from this server), "
      "so seasonality and news events aren't modelled.")
    (OUT / "next_episode_brief.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (OUT / "next_episode.json").write_text(json.dumps({
        "next_episode": nxt,
        "topic_probabilities": {t: round(pv, 4) for t, pv in topic_rank},
        "p_english": round(float(p_en), 3),
        "guest_type_probabilities": {r: round(pv, 4) for r, pv in role_rank},
        "backtest": results, "blend_weight_signals": w_best,
        "rising_entities": rising.head(10)[["recent", "prior", "ratio"]].round(3).to_dict("index"),
    }, indent=2))
    print("\n".join(L))


if __name__ == "__main__":
    main()
