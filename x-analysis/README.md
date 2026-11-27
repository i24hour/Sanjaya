# @ixtremeai X analysis (project 2)

Finds what gets the account more impressions, from the X Premium analytics export.

1. On x.com open **Premium → Analytics** (`x.com/i/account_analytics`).
2. **Content** tab → longest date range → **Export data**. Do the same on the **Overview** tab.
3. Put both CSVs in `x-analysis/data/`, then run `python analyze_x.py` (needs pandas).

Output: `output/report.md` (post types, formats, features, time of day, winners vs the rest,
replies vs originals, month by month) and `output/posts.csv` (each post with its features).
