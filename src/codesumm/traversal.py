import os
from codesumm.llm import LLMClient
from codesumm.config import Config
from codesumm.file_utils import list_contents, filter_supported_files, read_all_files
from codesumm.summarizer import load_docs_context, summarize_files, generate_scope_hint, generate_final_summary
from codesumm.writer import write_summary
from codesumm.logger import get_logger

log = get_logger(__name__)


def dfs(
    directory: str,
    parent_context: str,
    root_context: str,
    llm: LLMClient,
    config: Config,
) -> str:
    log.info("Entering: %s", directory)

    files, folders = list_contents(directory, config.repo_root, config.exclude)
    code_files, doc_files = filter_supported_files(files, config.supported_extensions)

    log.info(
        "Found %d code files, %d doc files, %d subfolders in %s",
        len(code_files),
        len(doc_files),
        len(folders),
        directory,
    )

    # Step 1: Load documentation context for this folder
    docs_context = load_docs_context(doc_files)

    # Step 2: Summarize all code files in this folder
    if code_files:
        file_contents = read_all_files(code_files)
        if file_contents:
            file_summary = summarize_files(
                llm,
                root_context,
                parent_context,
                docs_context,
                file_contents,
                config.context_reserve_ratio,
            )
            log.info("File summary generated for %s", directory)
        else:
            file_summary = "No readable code files in this folder."
            log.warning("All code files in %s failed to read", directory)
    else:
        file_summary = "No code files in this folder."
        log.info("No code files found in %s", directory)

    # Step 3: Generate scope hint for children
    scope_hint = generate_scope_hint(
        llm,
        parent_context,
        os.path.basename(directory),
        [os.path.basename(f) for f in code_files],
        [os.path.basename(f) for f in folders],
    )

    # Step 4: Recurse into subfolders
    child_summaries = []
    for folder in folders:
        log.info("Recursing into: %s", folder)
        child_summary = dfs(
            folder,
            parent_context=scope_hint,
            root_context=root_context,
            llm=llm,
            config=config,
        )
        child_summaries.append({
            "folder": os.path.basename(folder),
            "summary": child_summary,
        })

    # Step 5: Generate final summary
    final_summary = generate_final_summary(
        llm,
        os.path.basename(directory),
        file_summary,
        child_summaries,
        docs_context,
    )
    log.info("Final summary generated for %s", directory)

    # Step 6: Write to .summaries/
    write_summary(config.repo_root, directory, config.output_dir, final_summary)
    log.info("Summary written for %s", directory)

    return final_summary
