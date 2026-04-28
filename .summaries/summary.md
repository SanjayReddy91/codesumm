# codesumm

## Purpose
An AI-powered tool that generates hierarchical, human-readable technical summaries (`summary.md`) for every folder in a repository using a bottom-up DFS traversal.

## Key Components
- `src/codesumm`: The core engine responsible for directory traversal, context management, and LLM-driven summarization.
- `pyproject.toml`: Handles project packaging, dependency management (e.g., `openai`, `pyyaml`), and CLI entry point configuration.
- `config.yaml`: Defines default operational parameters, including supported file extensions, exclusion patterns, and rate-limiting settings.

## Internal Dependencies
- Relies on `pathspec` for `.gitignore`-style file exclusions.
- Integrates with any OpenAI-compatible API via the `/v1/chat/completions` endpoint.