import sys

from codesumm.logger import get_logger
from codesumm.config import Config
from codesumm.llm import LLMClient, FatalLLMError
from codesumm.file_utils import list_contents, filter_supported_files, generate_tree
from codesumm.summarizer import load_docs_context
from codesumm.traversal import dfs

log = get_logger(__name__)


def run(repo_path: str, config: Config) -> None:
    """Entry point called by cli.py after config is resolved."""

    llm = LLMClient(rate_limit=config.rate_limit)

    # Build root context from top-level docs + file tree
    files, folders = list_contents(repo_path, config.repo_root, config.exclude)
    _, doc_files = filter_supported_files(files, config.supported_extensions)
    root_context = load_docs_context(doc_files)

    if not root_context:
        log.warning("No README or architecture docs found at root")
        root_context = "No project-level documentation available."

    file_tree = generate_tree(repo_path, depth=2, exclude_patterns=config.exclude)
    root_context = root_context + "\n\nProject structure:\n" + file_tree
    log.info("Root context built (%d chars)", len(root_context))

    try:
        dfs(
            repo_path,
            parent_context="This is the repository root.",
            root_context=root_context,
            llm=llm,
            config=config,
        )
    except FatalLLMError:
        log.critical("Received 404 from LLM — stopping.")
        sys.exit(1)

    log.info("Done. Summaries written to %s/", config.output_dir)