# Repo News

Hacker News style list of GitHub repos ranked by stars gained in the last
12h, 1d, 3d, 7d, 14d, 1mo, 3mo, 1y or since Jan 1. Live at https://ishaan2006.github.io/repo-news/

## How it works
`scripts/update.py` runs in GitHub Actions and stores nothing between runs:
- **12h / 1d / 3d / 7d / 14d:** GitHub GraphQL `stargazers` ordered newest first, paged back to the cutoff. Exact.
- **1mo / 3mo / 1y / YTD:** repos created inside the window count all their stars; older repos up to 40k stars
  are bisected over the REST stargazer list (exact); bigger ones are paged up to a cap and shown as "N+".
- **Candidates:** GitHub Search (new and active repos) plus today's GitHub Trending from
  [GitHubTrendingRSS](https://github.com/mshibanami/GitHubTrendingRSS) and
  [github-trending-archive](https://github.com/antonkomarev/github-trending-archive).
- **Categories:** Claude Haiku labels repos it hasn't seen before (keyword rules as a fallback).
  Labels and long-window numbers are carried over from the published `data.json`.

## Costs
| Run | Token used | Windows | Claude |
|---|---|---|---|
| Scheduled, hourly | GitHub's built-in token (free, not yours) | 12h, 1d, 3d (+ 7d, 14d every 6h) | never |
| Manual ("Run workflow") | `GH_STATS_TOKEN` | everything, long windows if ticked | only if "categories" is ticked |

To make everything manual, delete the `schedule:` block in `.github/workflows/update.yml`.

## Setup
1. Settings, Pages: set **Source** to **GitHub Actions**.
2. Settings, Secrets and variables, Actions: `GH_STATS_TOKEN` (fine-grained PAT, public repos, read-only)
   and `ANTHROPIC_API_KEY`.
3. Actions tab, **Update Repo News**, **Run workflow**.
