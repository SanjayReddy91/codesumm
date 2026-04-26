# Code-Summarizer

Lazy to summarize your code? Use this tool!!!

## Requirements

- [] Single agent, deterministic bottom-up traversal
- [] One model for everything (via OpenRouter)
- [] Summaries stored in .summaries/ folder mirroring repo structure
- [] Supports code and config files only
- [] Exclude list for node_modules, .git, dist, etc.
- [] Simple sleep(x) rate limiting with incremental backoff on 429
- [] Evaluation: you manually grade on a few repos

## Future

- [] context_prev carries flat project overview + k layers of parent context
- [] No auto-update on commits — manual runs + targeted PR updates later

## Algorithm

dfs(directory: str, parent_summary: str) -> str:
files = list_files(directory) #folders and file names
start_context = load_documentation_context(files)

    file_summaries = []
    #only files other than documentation files
    for file in files:
        file_summaries.append(f"{file} summary: llm.chat(parent_summary + get_file(file))")

    folder_summary_init = llm.chat(start_context, files, parent_summary, file_summaries) #takes context of parent summary, current file summaries, file and folder names, documentation context.

    child_summaries = []
    #only folders
    for folder in files:
        child_summary.append(f"{folder} summary: {dfs(folder, folder_summary_init)}")

    folder_summary_final = llm.chat(folder_summary_init, child_summaries)

    return folder_summary_final

main():
files = list_files()
start_context = load_documentation_context(files) #Get context from architecture.md/readme.md/documentation.md for root node.

    root_summary = llm.chat(start_context)
    #load root_summary into system prompt.

    llm.system_prompt(root_summary)

    dfs(/root, root_summary)

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
