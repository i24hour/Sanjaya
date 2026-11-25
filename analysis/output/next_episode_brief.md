# Next-episode brief: FO591

*Prepared from the Sanjaya ontology: 564 episodes, 553 transcripts, 477 guests, 40 tracked entities. Every number below can be traced back to episode rows in `output/sanjaya.db`.*

## The call

- **Most likely topic:** Psychology & Self-Growth (20%), then Business & Startups (13%) and Health & Fitness (13%).
- **Language:** English, 87% likely.
- **Guest type:** Expert / other (35%), then Doctor / health expert (17%).

**Three most likely episode profiles** (likely topic + the guest type and entities that go with it in recent episodes; these are hypotheses, not leaks):

1. **Psychology & Self-Growth** (20%): guest most likely outside the usual categories, in English, likely touching on Marriage, AI, Anxiety / depression, USA.
2. **Business & Startups** (13%): guest most likely a founder / business leader, in English, likely touching on USA, AI, Startup funding, China.
3. **Health & Fitness** (13%): guest most likely a doctor / health expert, in English, likely touching on Dopamine, Anxiety / depression, Diabetes / sugar, AI.

## Confidence: how this model did on past episodes

Last 120 episodes, each predicted only from earlier ones; the blend weight (0% signals model) was chosen on the 80 episodes before that.

| Method | Right first guess | Right in top 3 |
|---|---|---|
| Combined model (signals + trend) | 14% | 38% |
| Signals model alone | 12% | 32% |
| Trend model (previous forecast) | 14% | 38% |
| Always the most common topic | 9% | 41% |

**What this shows:** the extra signals (views, how long since a topic last appeared, what came last) did not beat the simple recent-trend model when tested on past episodes, so the validation step gave them no weight. The forecast below is the trend model's, and the signals are shown as context, not as drivers.

Language of the next episode: right 72% of the time, vs 68% for "same language as last episode".

## Signals behind the call

**1. Topic momentum** (share of the last 20 episodes vs the last 100)

| Topic | Last 20 | Last 100 |
|---|---|---|
| Psychology & Self-Growth | 40% | 22% |
| Health & Fitness | 10% | 11% |
| Money & Investing | 10% | 12% |
| Geopolitics & Defence | 10% | 14% |
| Tech & AI | 10% | 7% |
| Education & Career | 5% | 4% |
| Crime & Dark Side | 5% | 3% |
| Politics & Governance | 5% | 8% |
| Business & Startups | 5% | 10% |

**2. What's drawing views** (last 60 episodes, median views vs the channel's median of 0.97M)

| Topic | Episodes | Median views | vs channel |
|---|---|---|---|
| Geopolitics & Defence | 6 | 1.95M | 2.00× |
| Business & Startups | 5 | 0.98M | 1.00× |
| Psychology & Self-Growth | 10 | 0.98M | 1.00× |
| Money & Investing | 8 | 0.89M | 0.91× |
| Tech & AI | 3 | 0.84M | 0.86× |
| Health & Fitness | 4 | 0.74M | 0.76× |

Topics with fewer than 3 recent episodes are left out: one episode is not a trend.

**3. Topics that are "due"** (episodes since it last appeared vs its usual gap)

| Topic | Episodes since last | Usual gap | Overdue factor |
|---|---|---|---|
| Entertainment & Celebrities | 50 | 8 | 5.9× |
| Sports | 40 | 16 | 2.6× |
| Geopolitics & Defence | 9 | 4 | 2.2× |
| Crime & Dark Side | 15 | 16 | 1.0× |
| Education & Career | 16 | 19 | 0.8× |
| Psychology & Self-Growth | 2 | 3 | 0.7× |

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
- Military / intelligence: 4
- Doctor / health expert: 3
- Founder / business leader: 3
- Academic / author / scientist: 2
- Spiritual guide: 1
- Investor / finance expert: 1
- Politician / official / diplomat: 1

## Last 10 episodes (the most recent context)

- FO590 · Health & Fitness · English · 0.53M · How Brain Damage, Trauma & Infections Can Change Human Behaviour | Daniel Amen
- FO589 · Tech & AI · English · 0.77M · Why AI Will Replace These Jobs: The Skills You Need Next | Sachin Puri
- FO588 · Psychology & Self-Growth · English · views n/a · Why Your Communication Makes People Ignore You &  How To Fix It | Vinh Giang
- FO587 · Business & Startups · English · 0.71M · How To Make Your Brand Go Viral & Turn Views Into Sales | Kent Yoshimura
- FO586 · Psychology & Self-Growth · English · views n/a · Psychology Of Billionaires, Extreme Ambition & Secrets Of Success | Joe Hudson
- FO585 · Money & Investing · English · 2.50M · Ex-IMF Chief: The Truth About US Debt, Pakistan Loans & Inflation | Gita Gopinath
- FO584 · Psychology & Self-Growth · English · views n/a · How To Make The Next 10 Years The Best Years Of Your Life | Mel Robbins
- FO583 · Tech & AI · English · 4.60M · Sam Altman On AI Revolution, Superintelligence & Future Of Humanity
- FO582 · Psychology & Self-Growth · English · 0.55M · How To Become Elite At Anything: Bryson DeChambeau’s Framework
- FO581 · Geopolitics & Defence · English · 3.70M · Inside America's Most Secret Base | Aircraft, Testing, Secrecy  | Annie Jacobsen

## Limits

- Topic choice is mostly the guest's availability, which no public data shows; even the best model is right on its first guess only about one time in 7.
- Topics and guest types are tagged automatically (about 2 in 3 agree with a title-only reading); a wrong tag in the history adds noise to the forecast.
- No upload dates are used (the channel listing doesn't give them from this server), so seasonality and news events aren't modelled.
