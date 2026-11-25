# Raj Shamani episode analysis

Predicts the topic of Raj Shamani's next *Figuring Out* podcast episode from his past episodes.

| Step | Script | Where to run |
|---|---|---|
| 1. List all videos | `python fetch_videos.py` → `data/videos.csv` | anywhere (already done) |
| 2. Download transcripts | `python fetch_transcripts.py` → `data/transcripts/` | **your own computer** |
| 3. Tag topics + forecast | `python analyze.py` → `output/` | anywhere |
| 5. Ontology (one record) | `python ontology.py` → `output/sanjaya.db` | anywhere |
| 6. Next-episode brief | `python predict.py` → `output/next_episode_brief.md` | anywhere (needs scikit-learn) |
| 4. Research report | `python research.py` → `output/research.md` | anywhere (needs `pip install scikit-learn`) |

YouTube blocks transcript downloads from cloud servers, so step 2 has to run on a normal home or office connection.

## Step 2 on your computer

```bash
git pull
cd analysis
pip install youtube-transcript-api pandas
python fetch_transcripts.py --limit 20   # try 20 first
python fetch_transcripts.py              # then the rest; pauses by itself if YouTube blocks
git add data/transcripts data/no_transcript.txt
git commit -m "Add transcripts"
git push
```

If YouTube blocks it, the script pauses and retries by itself, so leave it running (e.g. overnight). Ctrl+C is safe; finished videos are skipped next run.

## Output

- `output/next_episode_brief.md`: **the Palantir-style brief**: the call, its track record, and the signals behind it
- `output/sanjaya.db`: the ontology, a SQLite database of episodes, guests, topics and mentioned entities, linked, with the source of every fact. Try `SELECT * FROM v_episode`.

- `output/research.md`: **the main research report**: key findings, topic mix over time, what gets watched, themes found in transcripts, forecast

- `output/report.md`: forecast, backtest accuracy, rising and falling topics, views by topic
- `output/episodes.csv`: every episode with its topic and per-topic scores
- `output/forecast.json`: the same forecast as data, for a dashboard

## How it works

1. Each episode is scored against 13 topics (keywords in `TOPICS` in `analyze.py`), using the title plus the transcript if one exists. Hindi transcripts (Devanagari auto-captions, mostly Hinglish) are matched against Hindi and Hinglish keyword lists (`HINDI` in `analyze.py`). The highest score is the episode's topic.
2. The next topic's probability mixes the recent trend (recent episodes count more), what usually follows the last topic, and the all-time mix. The weights are chosen by testing on earlier episodes.
3. Accuracy is measured on the last 120 episodes, each one predicted only from the episodes before it, and compared with simple baselines.
