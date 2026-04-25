# Code-Summarizer

Lazy to summarize your code? Use this tool!!!

## Requirements

- [] Single agent, deterministic bottom-up traversal
- [] One model for everything (via OpenRouter)
- [] Summaries stored in .summaries/ folder mirroring repo structure
- [] Supports code and config files only
- [] Exclude list for node_modules, .git, dist, etc.
- [] context_prev carries flat project overview + k layers of parent context
- [] Simple sleep(x) rate limiting with incremental backoff on 429
- [] No auto-update on commits — manual runs + targeted PR updates later
- [] Evaluation: you manually grade on a few repos
