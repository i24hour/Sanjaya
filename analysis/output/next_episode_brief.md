# Next-episode brief: FO594

*Prepared from the Sanjaya ontology: 567 episodes, 553 transcripts, 480 guests, 40 tracked entities. Every number below can be traced back to episode rows in `output/sanjaya.db`.*

## The call

- **Most likely topic:** Psychology & Self-Growth (19%), then Business & Startups (13%) and Health & Fitness (12%).
- **Language:** English, 65% likely.
- **Guest type:** Expert / other (35%), then Doctor / health expert (16%).

**Three most likely episode profiles** (likely topic + the guest type and entities that go with it in recent episodes; these are hypotheses, not leaks):

1. **Psychology & Self-Growth** (19%): guest most likely outside the usual categories, in English, likely touching on Marriage, AI, Anxiety / depression, USA.
2. **Business & Startups** (13%): guest most likely a founder / business leader, in English, likely touching on USA, AI, Startup funding, China.
3. **Health & Fitness** (12%): guest most likely a doctor / health expert, in English, likely touching on Dopamine, Anxiety / depression, Diabetes / sugar, AI.

## Live track record

Each forecast is logged in `output/prediction_log.csv` and scored once the episode is out. Language is scored once its transcript is downloaded. FO591's forecast was made after its release, but from data that stopped at FO590 (it never saw FO591); later forecasts are made before release.

| Episode | Predicted top 3 | Actual | In top 3? | Language right? |
|---|---|---|---|---|
| FO591 | Psychology & Self-Growth, Business & Startups, Health & Fitness | Money & Investing | no | not known yet |
| FO593 | Psychology & Self-Growth, Business & Startups, Health & Fitness | Politics & Governance | no | not known yet |


## Confidence: how this model did on past episodes

Last 120 episodes, each predicted only from earlier ones; the blend weight (0% signals model) was chosen on the 80 episodes before that.

| Method | Right first guess | Right in top 3 |
|---|---|---|
| Combined model (signals + trend) | 14% | 38% |
| Signals model alone | 12% | 27% |
| Trend model (previous forecast) | 14% | 38% |
| Always the most common topic | 9% | 41% |

**What this shows:** the extra signals (views, how long since a topic last appeared, what came last) did not beat the simple recent-trend model when tested on past episodes, so the validation step gave them no weight. The forecast below is the trend model's, and the signals are shown as context, not as drivers.

Language of the next episode: right 72% of the time, vs 68% for "same language as last episode".

## Signals behind the call

**1. Topic momentum** (share of the last 20 episodes vs the last 100)

| Topic | Last 20 | Last 100 |
|---|---|---|
| Psychology & Self-Growth | 35% | 22% |
| Geopolitics & Defence | 10% | 14% |
| Politics & Governance | 10% | 9% |
| Tech & AI | 10% | 7% |
| Money & Investing | 10% | 12% |
| Business & Startups | 10% | 11% |
| Education & Career | 5% | 4% |
| Crime & Dark Side | 5% | 2% |
| Health & Fitness | 5% | 11% |

**2. What's drawing views** (last 60 episodes, median views vs the channel's median of 1.00M)

| Topic | Episodes | Median views | vs channel |
|---|---|---|---|
| Geopolitics & Defence | 5 | 1.30M | 1.30× |
| Health & Fitness | 4 | 1.14M | 1.14× |
| Psychology & Self-Growth | 10 | 1.00M | 1.00× |
| Business & Startups | 6 | 0.99M | 0.99× |
| Money & Investing | 7 | 0.98M | 0.98× |
| Tech & AI | 3 | 0.91M | 0.91× |

Topics with fewer than 3 recent episodes are left out: one episode is not a trend.

**3. Topics that are "due"** (episodes since it last appeared vs its usual gap)

| Topic | Episodes since last | Usual gap | Overdue factor |
|---|---|---|---|
| Entertainment & Celebrities | 53 | 8 | 6.2× |
| Geopolitics & Defence | 12 | 4 | 3.0× |
| Sports | 43 | 16 | 2.8× |
| Psychology & Self-Growth | 5 | 3 | 1.7× |
| Crime & Dark Side | 18 | 16 | 1.2× |
| Education & Career | 19 | 19 | 1.0× |

**4. Rising in the conversations** (mentions per 1,000 words, last 30 transcribed episodes vs the 120 before; only entities that come up in at least 10% of recent episodes)

| Entity | Recent | Before | Change |
|---|---|---|---|
| Anxiety / depression | 0.11 | 0.05 | 1.5× |
| Dopamine | 0.09 | 0.05 | 1.5× |
| Startup funding | 0.08 | 0.08 | 1.0× |
| War | 0.26 | 0.27 | 1.0× |
| AI | 0.54 | 0.69 | 0.8× |
| Marriage | 0.12 | 0.17 | 0.8× |
| Europe | 0.12 | 0.21 | 0.7× |
| USA | 0.37 | 0.64 | 0.6× |
| Russia | 0.13 | 0.29 | 0.5× |
| Pakistan | 0.04 | 0.16 | 0.4× |

**Fading**

- China: 0.75 → 0.26 per 1,000 words
- Pakistan: 0.16 → 0.04 per 1,000 words
- Russia: 0.29 → 0.13 per 1,000 words
- USA: 0.64 → 0.37 per 1,000 words
- Europe: 0.21 → 0.12 per 1,000 words

**5. Guest types, last 30 episodes**

- Expert / other: 15
- Founder / business leader: 4
- Military / intelligence: 3
- Academic / author / scientist: 2
- Investor / finance expert: 2
- Doctor / health expert: 2
- Spiritual guide: 1
- Politician / official / diplomat: 1

## Last 10 episodes (the most recent context)

- FO593 · Politics & Governance · ? · views n/a · What's Next For The World: Heatwaves, Water Crisis & Pollution | Sunita Narain
- FO592 · Business & Startups · ? · 1.10M · How To Find Business Ideas, Identify Market Gaps & Make Money | Udit Chawla
- FO591 · Money & Investing · ? · views n/a · How Shadow Economy Shapes Trade, Politics, Money & Power | Mariana Van Zeller
- FO590 · Health & Fitness · English · 1.30M · Top Psychiatrist: What Makes a Criminal Brain Different? | Dr. Daniel Amen
- FO589 · Tech & AI · English · 0.91M · How AI Agents Will Disrupt Jobs, Businesses & The Internet | Sachin Puri
- FO588 · Psychology & Self-Growth · English · views n/a · Why People Ignore You: The Communication Mistakes You Need To Fix | Vinh Giang
- FO587 · Business & Startups · English · 0.81M · How To Market Anything In 2027: Creators, Triggers & Communities | Kent Yoshimura
- FO586 · Psychology & Self-Growth · English · views n/a · Psychology Of Billionaires, Extreme Ambition & Secrets Of Success | Joe Hudson
- FO585 · Money & Investing · English · 2.60M · Ex-IMF Chief: The Truth About US Debt, Pakistan Loans & Inflation | Gita Gopinath
- FO584 · Psychology & Self-Growth · English · views n/a · How To Make The Next 10 Years The Best Years Of Your Life | Mel Robbins

## Limits

- Topic choice is mostly the guest's availability, which no public data shows; even the best model is right on its first guess only about one time in 7.
- Topics and guest types are tagged automatically (about 2 in 3 agree with a title-only reading); a wrong tag in the history adds noise to the forecast.
- No upload dates are used (the channel listing doesn't give them from this server), so seasonality and news events aren't modelled.
