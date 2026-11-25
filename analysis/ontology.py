"""Build a Foundry-style ontology of the Figuring Out podcast: one governed record.

Usage:  python ontology.py
Writes: output/sanjaya.db (SQLite), queryable with any SQLite tool, e.g.
        sqlite3 output/sanjaya.db "SELECT * FROM v_episode LIMIT 5"

Objects : episode, guest, topic, entity (people, countries, companies, ideas)
Links   : episode -HAS_GUEST-> guest
          episode -ABOUT-> topic      (score, one row per topic with a score > 0)
          episode -MENTIONS-> entity  (count per 1,000 words)
Every link row carries `source` (title / transcript / youtube) so a fact can
always say where it came from.
"""
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

import analyze

HERE = Path(__file__).parent
DB = HERE / "output" / "sanjaya.db"

# Entity -> aliases (English, plus Devanagari spellings used in Hindi auto-captions).
ENTITIES = {
    # people
    "Donald Trump": ("person", "trump|ट्रंप|ट्रम्प"),
    "Narendra Modi": ("person", "modi|मोदी"),
    "Elon Musk": ("person", "elon|musk|इलॉन|एलन मस्क"),
    "Sam Altman": ("person", "altman|ऑल्टमैन"),
    "Shah Rukh Khan": ("person", "shah rukh|shahrukh|srk|शाहरुख"),
    "Virat Kohli": ("person", "kohli|virat|कोहली|विराट"),
    "MS Dhoni": ("person", "dhoni|धोनी"),
    "Vladimir Putin": ("person", "putin|पुतिन"),
    "Ratan Tata": ("person", "ratan tata|रतन टाटा"),
    # countries and places
    "China": ("country", "china|chinese|चीन|चाइना|चाइनीज"),
    "Pakistan": ("country", "pakistan|पाकिस्तान"),
    "USA": ("country", "america|american|usa|अमेरिका|अमेरिकन"),
    "Russia": ("country", "russia|russian|रशिया|रूस"),
    "Iran": ("country", "iran|ईरान"),
    "Israel": ("country", "israel|इजराइल|इसराइल"),
    "Dubai / UAE": ("country", "dubai|uae|दुबई"),
    "Bangladesh": ("country", "bangladesh|बांग्लादेश"),
    "Europe": ("country", "europe|european|यूरोप"),
    # companies
    "Google": ("company", "google|गूगल"),
    "Amazon": ("company", "amazon|अमेज़न|अमेजन"),
    "Apple": ("company", "apple|iphone|एप्पल|आईफोन"),
    "OpenAI / ChatGPT": ("company", "openai|chatgpt|चैटजीपीटी|ओपनएआई"),
    "Tata": ("company", "tata|टाटा"),
    "Reliance / Ambani": ("company", "reliance|ambani|रिलायंस|अंबानी"),
    # ideas
    "AI": ("idea", "ai|artificial intelligence|एआई"),
    "Crypto": ("idea", "crypto|bitcoin|क्रिप्टो|बिटकॉइन"),
    "Stock market": ("idea", "stock market|share market|nifty|sensex|स्टॉक मार्केट|शेयर मार्केट"),
    "Gold": ("idea", "gold|गोल्ड|सोना"),
    "War": ("idea", "war|wars|वॉर|युद्ध"),
    "Tariffs": ("idea", "tariff|tariffs|टैरिफ"),
    "Nuclear": ("idea", "nuclear|न्यूक्लियर"),
    "Cancer": ("idea", "cancer|कैंसर"),
    "Diabetes / sugar": ("idea", "diabetes|insulin|डायबिटीज|इंसुलिन"),
    "Anxiety / depression": ("idea", "anxiety|depression|एंजायटी|डिप्रेशन"),
    "Dopamine": ("idea", "dopamine|डोपामिन|डोपामाइन"),
    "Marriage": ("idea", "marriage|married|शादी|मैरिज"),
    "Startup funding": ("idea", "funding|valuation|vc|फंडिंग|वैल्यूएशन"),
    "Jobs / layoffs": ("idea", "layoff|layoffs|unemployment|लेऑफ|बेरोजगारी"),
    "Bollywood": ("idea", "bollywood|बॉलीवुड"),
    "Spirituality": ("idea", "spiritual|spirituality|भगवान|स्पिरिचुअल"),
}

ROLES = [
    ("Founder / business leader", r"\b(founder|co-founder|ceo|entrepreneur|chairman|md)\b"),
    ("Doctor / health expert", r"\b(dr\.?|doctor|surgeon|nutritionist|dermatologist|cardiologist|neuro\w*|health expert)\b"),
    ("Military / intelligence", r"\b(col\.?|colonel|major|general|commando|navy seal|marcos|para sf|army|spy|raw|agent|nsg|ex-\w*officer)\b"),
    ("Politician / official / diplomat", r"\b(minister|president|chancellor|mp|mla|ias|ips|diplomat|ambassador|ex-imf|imf|governor|cm)\b"),
    ("Academic / author / scientist", r"\b(prof\.?|professor|author|scientist|historian|nobel|researcher|economist)\b"),
    ("Investor / finance expert", r"\b(investor|trader|ca|fund manager|finance)\b"),
]
TOPIC_ROLE = {
    "Entertainment & Celebrities": "Actor / artist / creator",
    "Sports": "Athlete",
    "Health & Fitness": "Doctor / health expert",
    "Business & Startups": "Founder / business leader",
    "Money & Investing": "Investor / finance expert",
    "Geopolitics & Defence": "Military / intelligence",
    "Spirituality & Mysteries": "Spiritual guide",
}

EP_TAIL = re.compile(r"[\s|\-–]*FO\s?\d+.*$|\|\s*Raj Shamani.*$", re.I)
NAME = re.compile(r"^(?:Dr\.?\s|H\.E\.\s|Prof\.?\s)?[A-Z@][\w.'’@-]*(?:\s(?:&\s)?[A-Z][\w.'’-]*){0,3}$")


def guest_name(title):
    t = EP_TAIL.sub("", title).strip(" |-–")
    parts = [p.strip() for p in re.split(r"\s\|\s|\s[-–]\s", t) if p.strip()]
    # "Title | Guest" or "Title - Guest": the last short, name-shaped segment.
    for p in reversed(parts[1:]):
        p2 = re.sub(r"^(ft\.?|feat\.?|with)\s+", "", p, flags=re.I)
        if len(p2) <= 32 and NAME.match(p2):
            return p2
    m = re.search(r"\b(?:ft\.?|feat\.?|with)\s+(.+?)(?:\s[-|–]|$)", t, re.I)
    if m:
        words = m.group(1).split()
        caps = [w for w in words if w[:1].isupper() or w[:1] == "@"]
        if caps:
            return " ".join(caps[-2:]) if len(caps) > 2 else " ".join(caps)
    m = re.match(r"^([A-Z@][\w.'’@-]*(?:\s[A-Z][\w.'’-]*){0,3})(?:\s[Oo]n\s|\sPodcast\b|:)", t)
    if m:
        return m.group(1)
    return None


def guest_role(title, topic):
    low = title.lower()
    for role, pat in ROLES:
        if re.search(pat, low):
            return role, "title"
    return TOPIC_ROLE.get(topic, "Expert / other"), "inferred from topic"


def entity_patterns():
    pats = {}
    for name, (_, aliases) in ENTITIES.items():
        latin = [a for a in aliases.split("|") if a.isascii()]
        deva = [a for a in aliases.split("|") if not a.isascii()]
        parts = []
        if latin:
            parts.append(r"\b(?:" + "|".join(map(re.escape, latin)) + r")\b")
        if deva:
            parts.append("(?:" + "|".join(map(re.escape, deva)) + ")")
        pats[name] = re.compile("|".join(parts), re.I)
    return pats


def main():
    df = analyze.load_episodes()
    epats = entity_patterns()
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    c = con.cursor()
    c.executescript("""
    CREATE TABLE episode (episode INTEGER PRIMARY KEY, video_id TEXT, title TEXT, views INTEGER,
        minutes REAL, language TEXT, has_transcript INTEGER, primary_topic TEXT, guest_role TEXT,
        guest_role_source TEXT, source TEXT);
    CREATE TABLE guest (guest_id INTEGER PRIMARY KEY, name TEXT UNIQUE, role TEXT, role_source TEXT);
    CREATE TABLE topic (name TEXT PRIMARY KEY);
    CREATE TABLE entity (name TEXT PRIMARY KEY, kind TEXT);
    CREATE TABLE episode_guest (episode INTEGER, guest_id INTEGER, source TEXT);
    CREATE TABLE episode_topic (episode INTEGER, topic TEXT, score REAL, source TEXT);
    CREATE TABLE episode_mentions (episode INTEGER, entity TEXT, per_1000_words REAL, count INTEGER, source TEXT);
    """)
    c.executemany("INSERT INTO topic VALUES (?)", [(t,) for t in list(analyze.TOPICS) + ["Other"]])
    c.executemany("INSERT INTO entity VALUES (?,?)", [(n, k) for n, (k, _) in ENTITIES.items()])

    guests = {}
    named = 0
    for _, r in df.iterrows():
        tx_path = analyze.DATA / "transcripts" / f"{r.video_id}.json"
        text = json.loads(tx_path.read_text(encoding="utf-8"))["text"] if tx_path.exists() else ""
        lang = "" if not r.transcript_lang else ("Hindi" if r.transcript_lang == "hi" else "English")
        views = int(r.views) if str(r.views) not in ("", "nan") else None
        minutes = float(r.duration_s) / 60 if str(r.duration_s) not in ("", "nan") else None
        name = guest_name(r.title)
        role, role_src = guest_role(r.title, r.topic)
        c.execute("INSERT INTO episode VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  (int(r.episode), r.video_id, r.title, views, minutes, lang,
                   int(bool(text)), r.topic, role, role_src, "youtube"))
        if name:
            named += 1
            if name not in guests:
                c.execute("INSERT INTO guest (name, role, role_source) VALUES (?,?,?)", (name, role, role_src))
                guests[name] = c.lastrowid
            c.execute("INSERT INTO episode_guest VALUES (?,?,?)", (int(r.episode), guests[name], "title"))
        for t in analyze.TOPICS:
            if r[t] > 0:
                c.execute("INSERT INTO episode_topic VALUES (?,?,?,?)",
                          (int(r.episode), t, float(r[t]), "title+transcript" if text else "title"))
        if text:
            words = max(len(text.split()), 1)
            for ent, pat in epats.items():
                n = len(pat.findall(text))
                if n:
                    c.execute("INSERT INTO episode_mentions VALUES (?,?,?,?,?)",
                              (int(r.episode), ent, 1000 * n / words, n, "transcript"))
    c.executescript("""
    CREATE VIEW v_episode AS
      SELECT e.episode, e.title, e.primary_topic, e.language, e.views, ROUND(e.minutes) AS minutes,
             g.name AS guest, e.guest_role
      FROM episode e LEFT JOIN episode_guest eg USING (episode) LEFT JOIN guest g USING (guest_id);
    """)
    con.commit()
    n_m = c.execute("SELECT COUNT(*) FROM episode_mentions").fetchone()[0]
    print(f"Ontology: {len(df)} episodes, {len(guests)} guests (named for {named} episodes), "
          f"{len(analyze.TOPICS)} topics, {len(ENTITIES)} entities, {n_m} mention links -> {DB}")
    con.close()


if __name__ == "__main__":
    main()
