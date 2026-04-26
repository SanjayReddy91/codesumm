# All LLM prompt templates live here.
# Functions return fully-formed strings ready to pass to llm.chat().


def file_summary_system() -> str:
    return (
        "You are a senior software engineer reading source code to produce concise, "
        "accurate technical summaries. You understand code structure, design patterns, "
        "and software architecture. You write for an audience of engineers who will use "
        "your summaries to navigate and understand an unfamiliar codebase."
    )


def file_summary_user(
    root_context: str,
    parent_context: str,
    docs_context: str,
    file_blocks: str,
) -> str:
    parts = ["You are summarizing the code files in a single directory.\n"]

    parts.append("## Project Context\n" + root_context.strip())

    parts.append("## Parent Folder Context\n" + parent_context.strip())

    if docs_context.strip():
        parts.append("## Documentation in This Folder\n" + docs_context.strip())

    parts.append("## Files\n" + file_blocks.strip())

    parts.append(
        "## Task\n"
        "Summarize what these files do collectively. Focus on:\n"
        "- The main responsibilities of this code\n"
        "- Key classes, functions, or APIs exposed\n"
        "- How the files relate to each other\n"
        "- Any non-obvious logic or important patterns\n\n"
        "Be concise. Do not repeat the file contents back. "
        "Do not include section headers in your response — plain prose only."
    )

    return "\n\n".join(parts)


def batch_merge_system() -> str:
    return file_summary_system()


def batch_merge_user(partial_summaries: str) -> str:
    return (
        "The files in a directory were too numerous to summarize in one pass. "
        "Below are summaries of batches of those files.\n\n"
        "## Batch Summaries\n"
        + partial_summaries.strip()
        + "\n\n"
        "## Task\n"
        "Merge these into a single coherent summary of all the files in the directory. "
        "Consolidate overlapping points. Do not include section headers — plain prose only."
    )


def scope_hint_system() -> str:
    return (
        "You are a software engineer quickly assessing what a folder in a codebase is for. "
        "You give short, precise answers."
    )


def scope_hint_user(
    parent_context: str,
    folder_name: str,
    file_names: list[str],
    folder_names: list[str],
) -> str:
    file_list = "\n".join(f"  - {n}" for n in file_names) or "  (none)"
    folder_list = "\n".join(f"  - {n}" for n in folder_names) or "  (none)"

    return (
        f"## Parent Context\n{parent_context.strip()}\n\n"
        f"## Folder Being Assessed\n{folder_name}\n\n"
        f"## Files in This Folder\n{file_list}\n\n"
        f"## Subfolders in This Folder\n{folder_list}\n\n"
        "## Task\n"
        "In 1-2 sentences, describe what this folder is responsible for. "
        "Be specific — use the file and folder names as signals. "
        "Do not hedge with 'likely' or 'probably' unless the contents are truly ambiguous."
    )


def final_summary_system() -> str:
    return file_summary_system()


def final_summary_user(
    folder_name: str,
    file_summary: str,
    child_summaries: list[dict],
    docs_context: str,
) -> str:
    parts = [
        f"You are writing the final summary document for the `{folder_name}` directory."
    ]

    if docs_context.strip():
        parts.append("## Documentation\n" + docs_context.strip())

    parts.append("## Code File Summary\n" + file_summary.strip())

    if child_summaries:
        child_block = "\n\n".join(
            f"### {c['folder']}\n{c['summary'].strip()}" for c in child_summaries
        )
        parts.append("## Subdirectory Summaries\n" + child_block)

    parts.append(
        "## Task\n"
        "Write a `summary.md` for this directory using exactly this structure:\n\n"
        "# {folder_name}\n\n"
        "## Purpose\n"
        "What this folder/module is responsible for.\n\n"
        "## Key Components\n"
        "Main files, classes, functions, or APIs — what they do.\n\n"
        "## Internal Dependencies\n"
        "What other parts of the project this module depends on.\n\n"
        "## Notes\n"
        "Anything non-obvious. Omit this section entirely if there is nothing to add.\n\n"
        "Rules:\n"
        "- Use the exact section headers above (h1 for folder name, h2 for sections)\n"
        f"- Replace {{folder_name}} with `{folder_name}`\n"
        "- For simple or shallow folders, keep Purpose and Key Components to 2-3 lines each\n"
        "- Do not invent details not present in the summaries above"
    )

    return "\n\n".join(parts)
