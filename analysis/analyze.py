"""Tag every Raj Shamani podcast episode with a topic and predict the next one.

Usage:  python analyze.py
Reads:  data/videos.csv and, when present, data/transcripts/<video_id>.json
Writes: output/episodes.csv   (one row per episode with its topic scores)
        output/report.md      (trends, backtest accuracy, next-episode forecast)
        output/forecast.json  (the forecast, for a dashboard)

Only numbered "Figuring Out" episodes (FO###) are used: the older videos are a
different format. Topic tagging uses the title, and the transcript as well when
one has been downloaded (the title counts more: it is what Raj chose to lead with).
"""
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "output"

# Topic -> keywords. Matched on word starts, case-insensitive, so "invest"
# also catches "investing" and "investor".
TOPICS = {
    "Business & Startups": [
        "business", "startup", "founder", "entrepreneur", "unicorn", "brand", "company",
        "companies", "ceo", "shark tank", "marketing", "sales", "banking", "bharatpe", "car selling", "d2c", "ecommerce",
        "e-commerce", "funding", "vc", "industry", "franchise", "restaurant", "cr company",
        "billion dollar", "empire", "market", "zomato", "zepto", "swiggy", "ola", "boat",
    ],
    "Money & Investing": [
        "money", "wealth", "invest", "stock", "share market", "mutual fund", "crypto",
        "bitcoin", "real estate", "property", "gold", "tax", "salary", "rich", "poor",
        "finance", "financial", "loan", "debt", "insurance", "retire", "sip", "trading",
        "trader", "income", "budget", "economy", "inflation", "billionaire", "millionaire",
    ],
    "Health & Fitness": [
        "health", "doctor", "dr ", "diet", "weight", "fat", "gut", "sleep", "hormone",
        "protein", "supplement", "fitness", "gym", "workout", "disease", "cancer", "heart",
        "diabetes", "liver", "kidney", "skin", "hair", "brain", "longevity", "ageing",
        "aging", "nutrition", "food", "rice", "wheat", "focus", "sugar", "detox", "fasting", "pcos", "sex",
        "fertility", "pregnan", "baby", "yoga", "ayurved", "addiction", "alcohol",
        "infection", "immun", "testosterone", "cholesterol", "eye", "teeth", "dental",
    ],
    "Psychology & Self-Growth": [
        "psycholog", "mindset", "confidence", "habit", "discipline", "motivation",
        "success", "relationship", "love", "marriage", "dating", "breakup", "heartbreak",
        "trauma", "anxiety", "depression", "stress", "mental", "therap", "emotion",
        "communication", "speaking", "productiv", "manifest", "happiness", "loneliness",
        "parenting", "parents", "behaviour", "behavior", "ambition", "life lesson",
        "self", "personality", "mind", "elite", "read people", "trust", "friends",
        "best years", "limits", "unbreakable", "reading", "books", "leadership", "status", "body language", "charisma", "persuasion",
    ],
    "Spirituality & Mysteries": [
        "spiritual", "god", "temple", "mandir", "religion", "hindu", "mahabharat",
        "ramayan", "krishna", "shiva", "karma", "astrolog", "kundli", "vastu", "tantra",
        "aghori", "ghost", "paranormal", "black magic", "kumbh", "sanatan", "meditation",
        "rebirth", "reincarnation", "afterlife", "death", "occult", "mystery", "mysteries",
        "puran", "veda", "upanishad", "bhagavad", "gita", "monk", "sadhguru", "naga",
        "devi", "chakra", "energy", "universe", "aliens", "ufo",
    ],
    "Geopolitics & Defence": [
        "geopolitic", "china", "pakistan", "usa", "america", "russia", "ukraine",
        "israel", "iran", "war", "army", "military", "navy", "air force", "soldier",
        "commando", "marcos", "para sf", "spy", "raw", "intelligence", "isi", "cia",
        "mossad", "terror", "border", "kashmir", "foreign affairs", "foreign policy",
        "diplomat", "defence", "defense", "missile", "nuclear", "bangladesh", "trump",
        "tariff", "operation sindoor", "26/11", "kargil", "ind vs china", "world order",
    ],
    "Politics & Governance": [
        "politic", "election", "bjp", "congress", "aap", "modi", "rahul gandhi",
        "minister", "chief minister", "cm ", "mp ", "mla", "parliament", "government",
        "governance", "policy", "upsc", "ias", "ips", "bureaucra", "corruption",
        "constitution", "president", "world leader", "city", "bmc", "metro", "floods",
        "climate", "pollution", "heat", "unliveable", "supreme court", "judge", "law", "lawyer", "legal", "caste",
        "reservation", "democracy", "vote", "state", "ambedkar",
    ],
    "Entertainment & Celebrities": [
        "bollywood", "film", "movie", "cinema", "actor", "actress", "stardom", "director",
        "song", "singer", "music", "rapper", "comedy", "comedian", "ott", "netflix",
        "web series", "tv", "serial", "fame", "celebrity", "box office", "south indian",
        "k-pop", "influencer", "content creat", "ranveer", "beerbiceps", "youtuber", "content creator", "creator", "podcast",
        "kiara", "suniel", "arshad", "vishal mishra", "falguni",
    ],
    "Sports": [
        "cricket", "cricketer", "ipl", "team india", "dhoni", "kohli", "virat", "rohit",
        "world cup", "asia cup", "olympic", "athlete", "football", "chess", "boxing",
        "wrestl", "kabaddi", "medal", "sport", "titles", "golf", "squash", "ganguly", "rinku", "jaiswal",
    ],
    "Tech & AI": [
        "ai", "a.i", "artificial intelligence", "chatgpt", "openai", "agent", "tech",
        "technology", "software", "coding", "programm", "internet", "robot", "automation",
        "data", "cyber", "hacker", "hacking", "app", "smartphone", "semiconductor",
        "space", "isro", "metaverse", "web 3", "nft", "otp", "gmail", "nasa", "future of", "jobs", "quantum", "cto",
    ],
    "Crime & Dark Side": [
        "crime", "criminal", "murder", "serial killer", "police", "scam", "fraud",
        "mafia", "gangster", "underworld", "drug", "dr*gs", "prison", "jail", "cbi",
        "ed ", "investigation", "dark web", "cult", "kidnap", "exposed", "exposing",
        "illegal", "smuggl", "gang", "bishnoi", "dawood", "safe", "safety",
        "violence", "danger", "risk", "security", "interrogat", "reveal", "trafficking", "secret service",
    ],
    "Education & Career": [
        "education", "school", "teacher", "textbook", "exam", "mba", "iim", "iit", "college",
        "student", "career", "job", "skills", "neet", "jee", "study", "abroad",
    ],
    "History & Culture": [
        "history", "historian", "ancient", "mughal", "british", "empire", "king",
        "civilization", "civilisation", "harappa", "archaeolog", "culture", "tradition",
        "festival", "navratri", "diwali", "language", "india's past", "freedom fighter",
        "partition", "independence", "travel", "country", "jungle", "snake",
        "wildlife", "adventure", "west", "untold",
    ],
}


# Hindi transcripts are YouTube auto-captions in Devanagari, full of English words
# written phonetically ("बिज़नेस", "इन्वेस्टमेंट"). These lists cover both Hindi words
# and those loanwords. A transcript word counts if it starts with a keyword
# (keywords of 2 letters or fewer must match the whole word).
HINDI = {
    "Business & Startups": "बिजनेस स्टार्टअप कंपनी कंपनीज ब्रांड फाउंडर कस्टमर मार्केटिंग सेल्स प्रोडक्ट रेवेन्यू प्रॉफिट फंडिंग इन्वेस्टर दुकान एंटरप्रेन्योर मार्जिन फ्रेंचाइजी रिटेल वैल्यूएशन यूनिकॉर्न",
    "Money & Investing": "पैसा पैसे पैसों इन्वेस्ट स्टॉक म्यूचुअल म्यूच्यूअल क्रिप्टो बिटकॉइन गोल्ड टैक्स सैलरी लोन रुपए रुपये करोड़ डॉलर इनकम ट्रेडिंग ट्रेडर इकोनॉमी इन्फ्लेशन प्रॉपर्टी रियल बैंक फाइनेंस फाइनेंशियल अमीर गरीब वेल्थ मार्केट",
    "Health & Fitness": "हेल्थ डॉक्टर बीमारी डाइट वेट फैट ब्लड हार्ट शुगर डायबिटीज कैंसर स्लीप नींद प्रोटीन एक्सरसाइज जिम वर्कआउट स्किन हेयर ब्रेन हॉस्पिटल मेडिकल मेडिसिन लिवर किडनी हार्मोन हेल्दी योगा प्रेगनेंसी सेक्स न्यूट्रिशन विटामिन इंफेक्शन पेशेंट",
    "Psychology & Self-Growth": "माइंडसेट कॉन्फिडेंस हैबिट डिसिप्लिन मोटिवेशन सक्सेस रिलेशनशिप प्यार लव शादी मैरिज ब्रेकअप ट्रॉमा एंजायटी डिप्रेशन स्ट्रेस मेंटल इमोशन थेरेपी पर्सनालिटी बिहेवियर फियर गुस्सा हैप्पी पेरेंट्स पेरेंटिंग दोस्त कम्युनिकेशन साइकोलॉजी ईगो",
    "Spirituality & Mysteries": "भगवान गॉड मंदिर धर्म हिंदू महाभारत रामायण कृष्ण शिव कर्म ज्योतिष कुंडली वास्तु तंत्र अघोरी भूत आत्मा कुंभ सनातन मेडिटेशन पूजा गीता वेद पुराण देवी देवता साधु मोक्ष पुनर्जन्म ब्रह्मांड यूनिवर्स चक्र स्पिरिचुअल",
    "Geopolitics & Defence": "चाइना चीन पाकिस्तान अमेरिका रशिया यूक्रेन इजराइल ईरान वॉर युद्ध आर्मी मिलिट्री नेवी एयरफोर्स सोल्जर कमांडो स्पाई इंटेलिजेंस आईएसआई टेररिस्ट टेरर बॉर्डर कश्मीर डिफेंस मिसाइल न्यूक्लियर बांग्लादेश ट्रंप टैरिफ जियोपॉलिटिक्स",
    "Politics & Governance": "पॉलिटिक्स पॉलिटिकल पॉलिटिशियन इलेक्शन बीजेपी कांग्रेस मोदी मिनिस्टर गवर्नमेंट सरकार पार्लियामेंट पॉलिसी यूपीएससी आईएएस आईपीएस करप्शन कॉन्स्टिट्यूशन कोर्ट जज कानून वकील लॉयर वोट नेता डेमोक्रेसी ब्यूरोक्रेसी",
    "Entertainment & Celebrities": "बॉलीवुड फिल्म मूवी एक्टर एक्ट्रेस डायरेक्टर गाना सॉन्ग सिंगर म्यूजिक कॉमेडी कॉमेडियन ओटीटी नेटफ्लिक्स सीरीज टीवी हीरो स्टारडम सेलिब्रिटी इन्फ्लुएंसर यूट्यूबर कंटेंट क्रिएटर शूटिंग एक्टिंग",
    "Sports": "क्रिकेट क्रिकेटर आईपीएल धोनी कोहली विराट रोहित ओलंपिक एथलीट फुटबॉल चेस बॉक्सिंग रेसलिंग कबड्डी मेडल स्पोर्ट्स कोच बैटिंग बॉलिंग",
    "Tech & AI": "एआई टेक्नोलॉजी सॉफ्टवेयर कोडिंग इंटरनेट रोबोट ऑटोमेशन डाटा डेटा साइबर हैकर हैकिंग ऐप स्मार्टफोन सेमीकंडक्टर इसरो नासा चैटजीपीटी एल्गोरिदम कंप्यूटर डिजिटल",
    "Crime & Dark Side": "क्राइम क्रिमिनल मर्डर पुलिस स्कैम फ्रॉड माफिया गैंगस्टर अंडरवर्ल्ड ड्रग्स जेल सीबीआई इन्वेस्टिगेशन किडनैप गैंग गोली हत्या चोरी",
    "Education & Career": "एजुकेशन स्कूल टीचर एग्जाम कॉलेज स्टूडेंट करियर जॉब नौकरी स्किल पढ़ाई डिग्री यूनिवर्सिटी आईआईटी नीट जेईई कोचिंग एमबीए",
    "History & Culture": "हिस्ट्री इतिहास एंशिएंट मुगल ब्रिटिश अंग्रेज राजा सभ्यता कल्चर संस्कृति परंपरा ट्रेडिशन त्योहार ट्रेवल आजादी पार्टीशन",
}
NUKTA = "\u093c"
HINDI = {t: [w.replace(NUKTA, "") for w in ws.split()] for t, ws in HINDI.items()}
DEVA = re.compile(r"[\u0900-\u097F]+")


def hindi_counts(text):
    """Count topic keywords among the Devanagari words of a transcript."""
    words = Counter(w.replace(NUKTA, "") for w in DEVA.findall(text))
    out = {}
    for topic, keys in HINDI.items():
        n = 0
        for w, c in words.items():
            if any(w == k if len(k) <= 2 else w.startswith(k) for k in keys):
                n += c
        out[topic] = n
    return out


TITLE_WEIGHT = 1.0
TRANSCRIPT_WEIGHT = 0.15  # per match per 1,000 words, so long episodes don't swamp the title
EP = re.compile(r"\|\s*FO\s?\d+.*$", re.I)


def compile_patterns():
    pats = {}
    for topic, words in TOPICS.items():
        alts = sorted({re.escape(w.strip()) for w in words}, key=len, reverse=True)
        # Short words (ai, raw, cm) must match whole; longer ones match as word prefixes.
        whole = [a for a in alts if len(a.replace("\\", "")) <= 3]
        prefix = [a for a in alts if a not in whole]
        parts = []
        if prefix:
            parts.append(r"\b(?:" + "|".join(prefix) + r")")
        if whole:
            parts.append(r"\b(?:" + "|".join(whole) + r")\b")
        pats[topic] = re.compile("|".join(parts), re.I)
    return pats


PATTERNS = compile_patterns()


def clean_title(title):
    # Drop the "| FO123 Raj Shamani" suffix and the guest's name segment noise stays.
    return EP.sub("", title).replace("Raj Shamani", "")


def score(title, transcript):
    t = clean_title(title)
    words = max(len(transcript.split()), 1) if transcript else 0
    hi = hindi_counts(transcript) if transcript else {}
    scores = {}
    for topic, pat in PATTERNS.items():
        s = TITLE_WEIGHT * len(pat.findall(t))
        if transcript:
            hits = len(pat.findall(transcript)) + hi.get(topic, 0)
            s += TRANSCRIPT_WEIGHT * hits * 1000 / words
        scores[topic] = s
    return scores


def load_episodes():
    df = pd.read_csv(DATA / "videos.csv")
    df = df[df["episode"].notna()].copy()
    df["episode"] = df["episode"].astype(int)
    df = df.sort_values(["episode", "order"]).drop_duplicates("episode", keep="last")
    texts, langs = [], []
    for vid in df["video_id"]:
        p = DATA / "transcripts" / f"{vid}.json"
        if p.exists():
            rec = json.loads(p.read_text(encoding="utf-8"))
            texts.append(rec.get("text", ""))
            langs.append(rec.get("language", ""))
        else:
            texts.append("")
            langs.append("")
    df["has_transcript"] = [bool(t) for t in texts]
    df["transcript_lang"] = langs
    rows = [score(ti, tx) for ti, tx in zip(df["title"], texts)]
    sc = pd.DataFrame(rows, index=df.index)
    df = pd.concat([df, sc], axis=1)
    df["topic"] = [
        max(r, key=r.get) if max(r.values()) > 0 else "Other" for r in rows
    ]
    return df.reset_index(drop=True)


# ---------- Forecasting ----------
# P(next topic) = w_recent * recency-weighted share
#               + w_markov * share of topics that followed the last episode's topic
#               + w_base   * all-time share
# Each piece is smoothed so no topic ever gets probability zero.

def recent_dist(seq, cats, half_life):
    w = defaultdict(float)
    for age, c in enumerate(reversed(seq)):
        w[c] += 0.5 ** (age / half_life)
    tot = sum(w.values()) + 0.5 * len(cats)
    return {c: (w[c] + 0.5) / tot for c in cats}


def markov_dist(seq, cats):
    trans = defaultdict(Counter)
    for a, b in zip(seq, seq[1:]):
        trans[a][b] += 1
    row = trans[seq[-1]]
    tot = sum(row.values()) + len(cats)
    return {c: (row[c] + 1) / tot for c in cats}


def base_dist(seq, cats):
    cnt = Counter(seq)
    tot = len(seq) + len(cats)
    return {c: (cnt[c] + 1) / tot for c in cats}


def forecast(seq, cats, w_recent, w_markov, half_life):
    w_base = max(0.0, 1 - w_recent - w_markov)
    r, m, b = recent_dist(seq, cats, half_life), markov_dist(seq, cats), base_dist(seq, cats)
    p = {c: w_recent * r[c] + w_markov * m[c] + w_base * b[c] for c in cats}
    s = sum(p.values())
    return {c: v / s for c, v in p.items()}


def backtest(seq, cats, predict, test_n):
    top1 = top3 = 0
    logloss = 0.0
    start = len(seq) - test_n
    for i in range(start, len(seq)):
        p = predict(seq[:i])
        ranked = sorted(p, key=p.get, reverse=True)
        top1 += ranked[0] == seq[i]
        top3 += seq[i] in ranked[:3]
        logloss -= math.log(max(p.get(seq[i], 1e-9), 1e-9))
    return {"top1": top1 / test_n, "top3": top3 / test_n, "logloss": logloss / test_n}


def main():
    OUT.mkdir(exist_ok=True)
    df = load_episodes()
    cats = list(TOPICS) + ["Other"]
    seq = df["topic"].tolist()
    test_n = min(120, len(seq) // 4)
    tune_seq = seq[:-test_n]  # tune on earlier episodes only, so the test is honest
    tune_n = min(120, len(tune_seq) // 3)

    best = None
    for w_r in [0.2, 0.35, 0.5, 0.65, 0.8]:
        for w_m in [0.0, 0.1, 0.2, 0.3]:
            if w_r + w_m > 1:
                continue
            for hl in [5, 10, 20, 40]:
                res = backtest(tune_seq, cats,
                               lambda s: forecast(s, cats, w_r, w_m, hl), tune_n)
                if best is None or res["logloss"] < best[0]["logloss"]:
                    best = (res, w_r, w_m, hl)
    _, w_r, w_m, hl = best

    model = backtest(seq, cats, lambda s: forecast(s, cats, w_r, w_m, hl), test_n)
    baselines = {
        "Always the most common topic so far": backtest(seq, cats, lambda s: base_dist(s, cats), test_n),
        "Same topic as last episode": backtest(
            seq, cats, lambda s: {c: (0.9 if c == s[-1] else 0.1 / (len(cats) - 1)) for c in cats}, test_n),
        "Random guess": {"top1": 1 / len(cats), "top3": 3 / len(cats), "logloss": math.log(len(cats))},
    }

    nxt = forecast(seq, cats, w_r, w_m, hl)
    ranked = sorted(nxt.items(), key=lambda kv: kv[1], reverse=True)

    recent, prior = seq[-50:], seq[-150:-50]
    trend = []
    for c in cats:
        a, b = recent.count(c) / len(recent), (prior.count(c) / len(prior)) if prior else 0
        trend.append((c, a, b, a - b))
    trend.sort(key=lambda t: t[3], reverse=True)

    views = df[pd.to_numeric(df["views"], errors="coerce").notna()].copy()
    views["views"] = views["views"].astype(float)
    last200 = views.tail(200)
    perf = last200.groupby("topic")["views"].agg(["count", "median"]).sort_values("median", ascending=False)

    out_cols = ["episode", "video_id", "title", "topic", "views", "duration_s",
                "has_transcript", "transcript_lang"] + list(TOPICS)
    df[out_cols].to_csv(OUT / "episodes.csv", index=False)

    last = df.iloc[-1]
    forecast_obj = {
        "next_episode": int(last["episode"]) + 1,
        "based_on_episodes": len(seq),
        "episodes_with_transcript": int(df["has_transcript"].sum()),
        "model": {"recent_weight": w_r, "markov_weight": w_m, "half_life_episodes": hl},
        "backtest": {"test_episodes": test_n, "model": model, "baselines": baselines},
        "probabilities": [{"topic": c, "p": round(p, 4)} for c, p in ranked],
        "trend_last50_vs_prior100": [
            {"topic": c, "recent_share": round(a, 3), "prior_share": round(b, 3)} for c, a, b, _ in trend
        ],
    }
    (OUT / "forecast.json").write_text(json.dumps(forecast_obj, indent=2))

    pct = lambda x: f"{100 * x:.0f}%"
    L = []
    L.append("# Raj Shamani: what's the next episode about?\n")
    L.append(f"Based on {len(seq)} *Figuring Out* episodes (FO{df['episode'].min()} to "
             f"FO{last['episode']}). Transcripts used for {int(df['has_transcript'].sum())} of them; "
             "the rest are tagged from the title alone.\n")
    L.append(f"## Forecast for FO{int(last['episode']) + 1}\n")
    L.append("| Topic | Probability |\n|---|---|")
    for c, p in ranked[:6]:
        L.append(f"| {c} | {pct(p)} |")
    L.append(f"\nLast episode: FO{last['episode']}, *{clean_title(last['title']).strip(' |')}*, "
             f"tagged **{last['topic']}**.\n")
    L.append(f"## How good is this? (tested on the last {test_n} episodes)\n")
    L.append("Each of those episodes was predicted using only the episodes before it. "
             "Settings were chosen on earlier episodes, never on the test set.\n")
    L.append("| Method | Right first guess | Right in top 3 |\n|---|---|---|")
    L.append(f"| **This model** | **{pct(model['top1'])}** | **{pct(model['top3'])}** |")
    for name, r in baselines.items():
        L.append(f"| {name} | {pct(r['top1'])} | {pct(r['top3'])} |")
    L.append(f"\nModel settings: {pct(w_r)} recent trend (half-life {hl} episodes), "
             f"{pct(w_m)} what usually follows the last topic, rest all-time mix.\n")
    L.append("## Rising and falling topics (last 50 episodes vs the 100 before)\n")
    L.append("| Topic | Last 50 | 100 before | Change |\n|---|---|---|---|")
    for c, a, b, d in trend:
        if a or b:
            L.append(f"| {c} | {pct(a)} | {pct(b)} | {'+' if d >= 0 else ''}{100 * d:.0f} pts |")
    L.append("\n## Which topics get watched (last 200 episodes, median views)\n")
    L.append("| Topic | Episodes | Median views |\n|---|---|---|")
    for c, r in perf.iterrows():
        L.append(f"| {c} | {int(r['count'])} | {r['median'] / 1e6:.2f}M |")
    L.append("\n## Topic mix of the last 15 episodes\n")
    for _, r in df.tail(15).iloc[::-1].iterrows():
        L.append(f"- FO{r['episode']} · **{r['topic']}** · {clean_title(r['title']).strip(' |')}")
    (OUT / "report.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
