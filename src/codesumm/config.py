import os
import sys
import yaml
from dataclasses import dataclass
from codesumm.logger import get_logger

log = get_logger(__name__)

DEFAULTS = {
    "exclude": [
        "node_modules/",
        ".git/",
        "dist/",
        "build/",
        "__pycache__/",
        "*.pyc",
        "*.lock",
        "*.min.js",
        ".env",
        ".summaries/",
        "*.egg-info/",
        "venv/",
        ".venv/",
    ],
    "supported_extensions": [
        ".py", ".js", ".ts", ".go", ".java", ".rs",
        ".cpp", ".c", ".h", ".rb", ".php",
        ".yaml", ".yml", ".toml", ".json",
        ".dockerfile", ".tf", ".sh", ".sql", ".md",
    ],
    "output_dir": ".summaries",
    "rate_limit": {
        "base_delay_seconds": 1.0,
        "max_retries": 5,
    },
    "context_reserve_ratio": 0.3,
}


@dataclass
class RateLimitConfig:
    base_delay_seconds: float = 1.0
    max_retries: int = 5


@dataclass
class Config:
    exclude: list[str]
    supported_extensions: list[str]
    output_dir: str
    rate_limit: RateLimitConfig
    context_reserve_ratio: float
    repo_root: str = ""


def load_config(config_path: str | None, repo_root: str) -> Config:
    """
    Loads config from file if provided, otherwise uses built-in defaults.
    Raises Exception on invalid YAML so cli.py can catch and print.
    """
    if config_path is not None:
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if not isinstance(raw, dict):
            raise ValueError(f"Config file is empty or not a valid YAML mapping: {config_path}")

        log.info("Config loaded from %s", config_path)
    else:
        raw = {}
        log.info("No config file provided, using built-in defaults")

    # Merge: file values override defaults
    merged = {**DEFAULTS, **raw}

    # rate_limit is nested, merge separately
    default_rl = DEFAULTS["rate_limit"]
    file_rl = raw.get("rate_limit", {})
    if not isinstance(file_rl, dict):
        file_rl = {}
    merged["rate_limit"] = {**default_rl, **file_rl}

    errors = _validate(merged)
    if errors:
        for err in errors:
            log.error("Config error: %s", err)
        raise ValueError("Invalid config: " + "; ".join(errors))

    if not os.path.isdir(repo_root):
        raise ValueError(f"repo_root is not a valid directory: {repo_root}")

    rate_limit = RateLimitConfig(
        base_delay_seconds=merged["rate_limit"]["base_delay_seconds"],
        max_retries=merged["rate_limit"]["max_retries"],
    )

    config = Config(
        exclude=merged["exclude"],
        supported_extensions=merged["supported_extensions"],
        output_dir=merged["output_dir"],
        rate_limit=rate_limit,
        context_reserve_ratio=merged["context_reserve_ratio"],
        repo_root=os.path.abspath(repo_root),
    )

    log.info("Output dir: %s", config.output_dir)
    log.info("Excluded patterns: %d", len(config.exclude))
    log.info("Supported extensions: %d", len(config.supported_extensions))
    log.info("Context reserve ratio: %.0f%%", config.context_reserve_ratio * 100)

    return config


def _validate(raw: dict) -> list[str]:
    errors = []

    if not isinstance(raw.get("exclude", []), list):
        errors.append("'exclude' must be a list")

    if not isinstance(raw.get("supported_extensions", []), list):
        errors.append("'supported_extensions' must be a list")
    elif not raw.get("supported_extensions"):
        errors.append("'supported_extensions' is empty — nothing would be processed")

    ratio = raw.get("context_reserve_ratio")
    if ratio is not None:
        if not isinstance(ratio, (int, float)) or not (0.0 < ratio < 1.0):
            errors.append("'context_reserve_ratio' must be a float between 0 and 1 (exclusive)")

    rl = raw.get("rate_limit")
    if rl is not None:
        if not isinstance(rl, dict):
            errors.append("'rate_limit' must be a mapping")
        else:
            if "base_delay_seconds" in rl and not isinstance(rl["base_delay_seconds"], (int, float)):
                errors.append("'rate_limit.base_delay_seconds' must be a number")
            if "max_retries" in rl and not isinstance(rl["max_retries"], int):
                errors.append("'rate_limit.max_retries' must be an integer")

    return errors