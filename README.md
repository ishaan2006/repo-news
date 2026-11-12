# Repo News

**Live site: https://ishaan2006.github.io/repo-news/**

A Hacker News style front page for GitHub. It ranks repositories by how fast they are gaining stars,
with presets from today to a year, topic filters, and a language filter. There is no server and no database:
a GitHub Actions job computes the rankings into one JSON file and GitHub Pages serves it with a static page.

## What it ranks
- **hot** (default): Hacker News' decay formula applied to daily star counts,
  `score = sum(stars_that_day / (age_hours + 2)^1.8)` over the last 14 days. A repo climbing right now beats one that peaked last week.
- **today, 3d, 7d, 14d, 1mo, 3mo, 1y, YTD**: most stars gained in that window.
- **new**: recently created repos.
- **Topics**: ai/ml, swe, security, finance, apps, fun, learn. Filters combine and are shareable in the URL hash (for example `#today+ai+lang-rust`).

## Architecture

```
 hourly cron / manual run / push to main
                  │
                  ▼
 ┌───────────────────────────────── GitHub Actions (scripts/update.py) ─────────────────────────────────┐
 │ 1. candidates   GitHub Search + GitHub Trending feeds (new and active repos)                          │
 │ 2. metadata     GraphQL, batched; drops forks, archived repos and spam                                │
 │ 3. star history REST /stargazers/history, weekly buckets with a per-day breakdown, 8 threads          │
 │ 4. score        windows + hot score, anchored to the latest day GitHub has published                 │
 │ 5. labels       keyword rules; Claude Haiku (manual runs only) for repos it has not seen              │
 │ 6. publish      top 150 per ranking + top 25 per topic  ->  site/data.json                            │
 └───────────────────────────────────────────────────┬───────────────────────────────────────────────────┘
                                                      ▼
                             GitHub Pages: static index.html reads data.json in the browser
```

State between runs is the previously published `data.json` itself, which the job downloads at the start.
That is how labels and the expensive 1y / YTD numbers carry over to cheap hourly runs.

## Engineering notes
**GitHub removed the data this was built on.** In July 2026 GitHub made per-star timestamps (the stargazer list)
visible to repo owners only, which would have broken every short window. The updater now reads the star history
endpoint (`/repos/{owner}/{repo}/stargazers/history`, API version `2026-03-10`), which returns weekly buckets with a
per-day array, and rebuilds daily counts from those. GitHub only reports whole days, so there is no sub-day window,
and "today" lags until GitHub publishes the day. The page says so instead of faking precision.

**Spam and star farming.** Fast-growing repos attract fake stars. Candidates are dropped when they have a spam
keyword and almost no forks, zero forks with 40 or more stars, a bot-like owner name, or (for repos under 60 days old)
many stars with a fork-to-star ratio below 0.008. Real breakout repos get forked quickly, so forks are a cheap signal.

**Rate limits as a budget.** The scheduled run uses GitHub's built-in token, which allows roughly 1,000 requests an
hour, so the script tracks `x-ratelimit-remaining`, caps the candidate list (800 hourly, 2,400 on a manual run),
orders candidates most promising first so the cap cuts the least valuable, and stops cleanly with a log line on a
permission error instead of publishing empty data. GraphQL batches that time out are split in half and retried.

**LLM labeling that survives bad output.** Haiku is called with forced tool use and must return `{index, categories}`
items. Answers are matched by index, so a missing or extra item cannot shift labels onto the wrong repo, and
descriptions are flattened to one line first. Keyword rules are the fallback. Only repos without a label are sent.

**Costs.** Scheduled runs never see any secret and never call an LLM. Anything that spends money (Haiku labels,
the larger candidate cap, 1y / YTD) runs only from a manual "Run workflow".

| Run | Token | Repos | Rankings | Claude |
|---|---|---|---|---|
| Hourly (scheduled) | GitHub's built-in token | ~800 | hot, today to 3mo | never |
| Manual, `Update Repo News` | `GH_STATS_TOKEN` (classic, no scopes) | ~2,400 | + 1y, YTD if ticked | only if "categories" is ticked |
| Manual, `Update Today` | GitHub's built-in token | ~800 | short windows only | never |

## Tests
`python3 tests/test_update.py` runs the real updater against a fake GitHub and a fake Anthropic API with known daily
star data, then checks that:
- every window count equals the ground truth computed independently from the daily data,
- the hot score ranks a rising repo above one that peaked last week,
- star-farmed repos are filtered,
- a scheduled run makes zero Claude calls and carries 1y and YTD numbers over.

CI runs it on every push.

## Repository layout
| Path | Purpose |
|---|---|
| `scripts/update.py` | The whole pipeline (standard library only) |
| `site/index.html` | The front end: one static file, no build step |
| `.github/workflows/update.yml` | Hourly, manual and on-push build and deploy |
| `.github/workflows/update-today.yml` | Manual refresh of the short windows only |
| `.github/workflows/test.yml` | Runs the tests |
| `tests/test_update.py` | End-to-end pipeline test with fake GitHub and Anthropic APIs |

## Related
[Repo Translator](https://github.com/ishaan2006/repo-translator) is a companion browser extension that translates
non-English READMEs and commit messages on GitHub, so repos found here are readable regardless of language.
