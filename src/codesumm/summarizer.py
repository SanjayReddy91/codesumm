import os
from codesumm.llm import LLMClient
from codesumm.file_utils import read_file
from codesumm.prompts import (
    file_summary_system,
    file_summary_user,
    batch_merge_system,
    batch_merge_user,
    scope_hint_system,
    scope_hint_user,
    final_summary_system,
    final_summary_user,
)
from codesumm.logger import get_logger

log = get_logger(__name__)


def load_docs_context(doc_files: list[str]) -> str:
    """
    Reads all documentation files and concatenates them with clear delimiters.
    Returns an empty string if no docs exist or none can be read.
    """
    parts = []
    for path in doc_files:
        content = read_file(path)
        if content:
            parts.append(f"<!-- {os.path.basename(path)} -->\n{content.strip()}")

    if not parts:
        return ""

    return "\n\n---\n\n".join(parts)


def _format_file_blocks(file_contents: list[dict]) -> str:
    """
    Formats a list of {"path": str, "content": str} into a single string
    with fenced code blocks, ready to include in a prompt.
    """
    blocks = []
    for fc in file_contents:
        path = fc["path"]
        content = fc["content"].strip()
        ext = os.path.splitext(path)[1].lstrip(".")
        blocks.append(f"### {path}\n```{ext}\n{content}\n```")
    return "\n\n".join(blocks)


def _make_batches(
    llm: LLMClient,
    file_contents: list[dict],
    static_texts: list[str],
    reserve_ratio: float,
) -> list[list[dict]]:
    """
    Splits file_contents into batches where each batch + static_texts fits
    within the context window.
    """
    batches: list[list[dict]] = []
    current_batch: list[dict] = []

    for fc in file_contents:
        candidate = current_batch + [fc]
        candidate_block = _format_file_blocks(candidate)
        if not llm.fits_in_context(static_texts + [candidate_block], reserve_ratio):
            if not current_batch:
                # Single file already too large — include it alone and warn
                log.warning("File exceeds context limit on its own, including anyway: %s", fc["path"])
                batches.append([fc])
            else:
                batches.append(current_batch)
                current_batch = [fc]
        else:
            current_batch = candidate

    if current_batch:
        batches.append(current_batch)

    return batches


def summarize_files(
    llm: LLMClient,
    root_context: str,
    parent_context: str,
    docs_context: str,
    file_contents: list[dict],
    reserve_ratio: float,
) -> str:
    """
    Summarizes all code files in a directory.

    If all files fit in one context window: single LLM call.
    If not: splits into batches, summarizes each, then merges.
    """
    static_texts = [root_context, parent_context, docs_context]
    file_blocks = _format_file_blocks(file_contents)

    if llm.fits_in_context(static_texts + [file_blocks], reserve_ratio):
        log.info("Summarizing %d files in a single call", len(file_contents))
        system = file_summary_system()
        user = file_summary_user(root_context, parent_context, docs_context, file_blocks)
        return llm.chat(system, user)

    # Batched path
    batches = _make_batches(llm, file_contents, static_texts, reserve_ratio)
    log.info(
        "Files too large for single call — batching %d files into %d batches",
        len(file_contents),
        len(batches),
    )

    batch_summaries = []
    for i, batch in enumerate(batches):
        log.info("Summarizing batch %d/%d (%d files)", i + 1, len(batches), len(batch))
        system = file_summary_system()
        user = file_summary_user(
            root_context, parent_context, docs_context, _format_file_blocks(batch)
        )
        batch_summaries.append(llm.chat(system, user))

    # Merge batch summaries
    partial = "\n\n---\n\n".join(
        f"**Batch {i + 1}:**\n{s}" for i, s in enumerate(batch_summaries)
    )

    if not llm.fits_in_context([partial], reserve_ratio):
        log.warning(
            "Merged batch summaries exceed context limit (%d estimated tokens) — "
            "truncation may occur",
            llm.estimate_tokens(partial),
        )

    log.info("Merging %d batch summaries", len(batch_summaries))
    return llm.chat(batch_merge_system(), batch_merge_user(partial))


def generate_scope_hint(
    llm: LLMClient,
    parent_context: str,
    folder_name: str,
    file_names: list[str],
    folder_names: list[str],
) -> str:
    """
    Produces a 1-2 sentence description of a folder's purpose.
    Used as parent_context when recursing into child folders.
    """
    log.info("Generating scope hint for folder: %s", folder_name)
    system = scope_hint_system()
    user = scope_hint_user(parent_context, folder_name, file_names, folder_names)
    return llm.chat(system, user)


def generate_final_summary(
    llm: LLMClient,
    folder_name: str,
    file_summary: str,
    child_summaries: list[dict],
    docs_context: str,
) -> str:
    """
    Produces the final summary.md content in the standard format.
    """
    log.info(
        "Generating final summary for: %s (%d child summaries)",
        folder_name,
        len(child_summaries),
    )
    system = final_summary_system()
    user = final_summary_user(folder_name, file_summary, child_summaries, docs_context)
    return llm.chat(system, user)
