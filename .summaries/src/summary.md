# src

## Purpose
The root source directory containing the core logic and distribution metadata for the `codesumm` AI-powered codebase summarization tool.

## Key Components
- `codesumm`: The primary module responsible for the bottom-up DFS traversal and generation of hierarchical technical summaries.
- `codesumm.egg-info`: Contains setuptools metadata used for package distribution and installation.

## Internal Dependencies
- `codesumm` relies on `pathspec` and OpenAI-compatible APIs for file exclusion and summarization logic.