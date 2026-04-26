# Code-Summarizer

Lazy to summarize your code? Use this tool!!!

## Requirements

- [x] Single agent, deterministic bottom-up traversal
- [x] One model for everything. Set in .env.
- [x] Summaries stored in .summaries/ folder mirroring repo structure
- [x] Supports code and config files only
- [x] Exclude list for node_modules, .git, dist, etc. -> config.yaml
- [x] Simple sleep(x) rate limiting with incremental backoff on 429
- [ ] Evaluation: you manually grade on a few repos

## Eval

- [ ] Test on simple repo max-depth should be 3 or less.
- [ ] Test on bigger repo max-depth > 6

## Future

- [ ] context_prev carries flat project overview + k layers of parent context
- [ ] No auto-update on commits — manual runs + targeted PR updates later

## Algorithm
```
dfs(directory, parent_context, root_context, config):
    files, folders = list_and_filter(directory, config.exclude)
    docs_context = load_docs_if_exist(files)  # README, etc.

    # One LLM call for all files in this folder
    all_file_contents = read_all_files(files)
    scope_hint = llm.chat(
        "Given this parent context and these file names,
         describe this folder's purpose in 1-2 lines",
        parent_context, file_names(files)
    )

    file_summary = llm.chat(
        "Summarize these files",
        root_context, parent_context, docs_context,
        all_file_contents
    )

    # Recurse into children
    child_summaries = []
    for folder in folders:
        child_context = build_context(parent_context,
                            scope_hint, config.k)
        child_summaries.append({
            "folder": folder,
            "summary": dfs(folder, child_context,
                          root_context, config)
        })

    # Final summary incorporating children
    final_summary = llm.chat(
        "Write final summary for this folder",
        file_summary, child_summaries, docs_context
    )

    write_summary(directory, final_summary)
    return final_summary
```
