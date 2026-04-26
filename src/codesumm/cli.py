import argparse
import os
import sys

from dotenv import load_dotenv

from codesumm import __version__
from codesumm.config import load_config
from codesumm.logger import get_logger, set_log_level, setup_logging
from codesumm.main import run

log = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        prog="codesumm",
        description="AI-powered code summarizer that generates summary.md for every folder in your repo",
    )

    parser.add_argument(
        "repo_path",
        type=str,
        help="Path to the repository to summarize",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        dest="config_path",
        help="Path to config.yaml",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Override output directory name (default: .summaries)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override LLM model name",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="Override LLM API base URL",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"codesumm {__version__}",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Additional exclude patterns (gitignore format). Can be repeated.",
    )

    args = parser.parse_args()

    setup_logging()
    if args.verbose:
        set_log_level("DEBUG")

    # --- Validate repo_path ---
    repo_path = os.path.abspath(args.repo_path)

    if not os.path.exists(repo_path):
        print(f"Error: '{args.repo_path}' does not exist", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(repo_path):
        print(f"Error: '{args.repo_path}' is not a directory", file=sys.stderr)
        sys.exit(1)

    # --- Load .env from repo root if it exists ---
    env_path = os.path.join(repo_path, ".env")
    if os.path.isfile(env_path):
        load_dotenv(env_path, override=False)
        log.info("Loaded .env from %s", env_path)
    else:
        load_dotenv(override=False)
        log.debug("No .env found in repo root, using environment")

    # --- Apply CLI overrides to environment before LLMClient reads them ---
    if args.model is not None:
        os.environ["LLM_MODEL"] = args.model

    if args.base_url is not None:
        os.environ["LLM_BASE_URL"] = args.base_url

    if args.exclude:
        config.exclude.extend(args.exclude)

    # --- Validate LLM_API_KEY ---
    if not os.environ.get("LLM_API_KEY"):
        print(
            "Error: LLM_API_KEY environment variable is required. "
            "Set it in .env or export it.",
            file=sys.stderr,
        )
        sys.exit(1)

    # --- Resolve config file ---
    config_path = _resolve_config_path(args.config_path, repo_path)

    if config_path:
        log.info("Using config: %s", config_path)
    else:
        log.info("No config file found, using built-in defaults")

    # --- Load config ---
    try:
        config = load_config(config_path, repo_path)
    except Exception as e:
        print(f"Error: Failed to parse config file: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Apply CLI overrides to config ---
    if args.output_dir is not None:
        config.output_dir = args.output_dir

    # --- Run ---
    log.info("Starting codesumm v%s", __version__)
    log.info("Repo: %s", repo_path)
    log.info("Output: %s", config.output_dir)

    run(repo_path, config)


def _resolve_config_path(cli_config: str | None, repo_path: str) -> str | None:
    """
    Resolves config file path using fallback chain:
    1. CLI --config flag (error if provided but doesn't exist)
    2. config.yaml in repo root
    3. ~/.codesumm/config.yaml
    4. None (use built-in defaults)
    """
    if cli_config is not None:
        path = os.path.abspath(cli_config)
        if not os.path.isfile(path):
            print(f"Error: Config file '{cli_config}' not found", file=sys.stderr)
            sys.exit(1)
        return path

    repo_config = os.path.join(repo_path, "config.yaml")
    if os.path.isfile(repo_config):
        return repo_config

    home_config = os.path.join(os.path.expanduser("~"), ".codesumm", "config.yaml")
    if os.path.isfile(home_config):
        return home_config

    return None