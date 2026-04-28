# codesumm

## Purpose
An AI-powered tool that generates structured, hierarchical technical summaries of a codebase using a bottom-up Depth-First Search (DFS) traversal to propagate implementation details from leaf directories to the root.

## Key Components
- `main.py` & `traversal.py`: Orchestrate the DFS process, manage scope hints, and aggregate file and folder summaries.
- `summarizer.py`: Handles the batching and merging of files that exceed the model's context window.
- `llm.py`: Manages API integration, token estimation, context window validation, and rate limiting via `LLMClient`.
- `cli.py` & `config.py`: Handle the command-line interface, environment loading, and YAML configuration validation.
- `file_utils.py`: Manages filesystem interactions, project tree generation, and `.gitignore` exclusions.
- `prompts.py`: Contains the specialized prompt templates used for summarization.
- `writer.py`: Persists the generated summaries as markdown files, mirroring the original project structure.

## Internal Dependencies
- `pathspec`: Used by `file_utils.py` for handling file exclusions.
- OpenAI-compatible APIs: Integrated via `llm.py` for the core summarization logic.