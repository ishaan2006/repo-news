# Repo News

Hacker News style list of GitHub repos. Live at https://ishaan2006.github.io/repo-news/

- **hot** (default): HN's decay formula on daily stars, `stars / (age_hours + 2)^1.8` over the last 14 days,
  so a repo climbing right now beats one that peaked last week.
- **today, 3d, 7d, 14d, 1mo, 3mo, 1y, YTD**: most stars gained in that window.
- **new**: recently created repos. **Topics**: ai/ml, swe, security, finance, apps, fun, learn (labeled by Claude Haiku).

## How it works
`scripts/update.py` runs in GitHub Actions and stores nothing between runs.
1. **Candidates:** GitHub Search (new and active repos) plus GitHub Trending via
   [GitHubTrendingRSS](https://github.com/mshibanami/GitHubTrendingRSS) and
   [github-trending-archive](https://github.com/antonkomarev/github-trending-archive).
2. **Metadata:** one GraphQL query per 25 repos. Forks, archived repos and spam are dropped.
3. **Stars per day:** GitHub's star history endpoint (`/repos/{owner}/{repo}/stargazers/history`), weekly
   buckets with a per-day breakdown. One request covers 30 weeks; 1y/YTD need a second.
   GitHub only reports whole days (since July 2026 the per-star list is owner-only), so there is no sub-day window.
4. **Categories:** Claude Haiku labels repos it hasn't seen before (keyword rules as a fallback).
   Labels and 1y/YTD numbers carry over from the published `data.json`.

## Runs and costs
| Run | Token | Repos | Rankings | Claude |
|---|---|---|---|---|
| Hourly (scheduled) | GitHub's built-in token (free, not yours) | ~800 | hot, today to 3mo | never |
| Manual ("Run workflow") | `GH_STATS_TOKEN` (classic, no scopes) | ~2,400 | + 1y, YTD if ticked | only if "categories" is ticked |

To make everything manual, delete the `schedule:` block in `.github/workflows/update.yml`.
