# Security

- Scheduled runs use only GitHub's built-in `GITHUB_TOKEN` and never receive any secret.
- `GH_STATS_TOKEN` and `ANTHROPIC_API_KEY` are repository secrets exposed only to manual "Run workflow" runs.
  Workflows never print them and they are never committed.
- The published site is static and makes no requests except for its own `data.json`.

To report a vulnerability, use the repository's Security tab ("Report a vulnerability") instead of a public issue.
