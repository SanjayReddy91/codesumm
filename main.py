import os
import sys
import argparse

from logger import setup_logging, get_logger
from config import load_config
from llm import LLMClient, FatalLLMError
from file_utils import list_contents, filter_supported_files, generate_tree
from summarizer import load_docs_context
from traversal import dfs

log = get_logger(__name__)

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recursively summarize a code repository using an LLM."
    )
    parser.add_argument(
        "repo_root",
        help="Path to the root of the repository to summarize",
    )
    parser.add_argument(
        "--config",
        default=_CONFIG_PATH,
        help="Path to config.yaml (default: config.yaml next to main.py)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    import logging
    setup_logging(level=getattr(logging, args.log_level))

    config = load_config(args.config, args.repo_root)

    log.info("Starting Code Summarizer")
    log.info("Repo: %s", config.repo_root)

    llm = LLMClient(rate_limit=config.rate_limit)

    # Build root context from top-level docs + file tree
    files, folders = list_contents(config.repo_root, config.repo_root, config.exclude)
    _, doc_files = filter_supported_files(files, config.supported_extensions)
    root_context = load_docs_context(doc_files)

    if not root_context:
        log.warning("No README or architecture docs found at root")
        root_context = "No project-level documentation available."

    file_tree = generate_tree(config.repo_root, depth=2, exclude_patterns=config.exclude)
    root_context = root_context + "\n\nProject structure:\n" + file_tree
    log.info("Root context built (%d chars)", len(root_context))

    try:
        dfs(
            config.repo_root,
            parent_context="This is the repository root.",
            root_context=root_context,
            llm=llm,
            config=config,
        )
    except FatalLLMError:
        log.critical("Received 404 from LLM — stopping.")
        sys.exit(1)

    log.info("Done. Summaries written to %s/", config.output_dir)


if __name__ == "__main__":
    main()
