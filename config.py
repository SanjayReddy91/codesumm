import os
import sys
import yaml
from dataclasses import dataclass, field
from logger import get_logger

log = get_logger(__name__)


@dataclass
class RateLimitConfig:
    base_delay_seconds: float = 1.0
    max_retries: int = 5


@dataclass
class Config:
    # From config.yaml
    exclude: list[str]
    supported_extensions: list[str]
    output_dir: str
    rate_limit: RateLimitConfig
    context_reserve_ratio: float

    # Set at runtime from CLI arg
    repo_root: str = ""


def load_config(config_path: str, repo_root: str) -> Config:
    """
    Loads and validates config.yaml, then attaches repo_root from CLI.
    Exits the process if config is missing or invalid.
    """
    if not os.path.isfile(config_path):
        log.error("Config file not found: %s", config_path)
        sys.exit(1)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        log.error("Failed to parse config file: %s", e)
        sys.exit(1)

    if not isinstance(raw, dict):
        log.error("Config file is empty or not a valid YAML mapping: %s", config_path)
        sys.exit(1)

    errors = _validate(raw)
    if errors:
        for err in errors:
            log.error("Config error: %s", err)
        sys.exit(1)

    if not os.path.isdir(repo_root):
        log.error("repo_root is not a valid directory: %s", repo_root)
        sys.exit(1)

    rate_limit_raw = raw.get("rate_limit", {})
    rate_limit = RateLimitConfig(
        base_delay_seconds=rate_limit_raw.get("base_delay_seconds", 1.0),
        max_retries=rate_limit_raw.get("max_retries", 5),
    )

    config = Config(
        exclude=raw.get("exclude", []),
        supported_extensions=raw.get("supported_extensions", []),
        output_dir=raw.get("output_dir", ".summaries"),
        rate_limit=rate_limit,
        context_reserve_ratio=raw.get("context_reserve_ratio", 0.3),
        repo_root=os.path.abspath(repo_root),
    )

    log.info("Config loaded from %s", config_path)
    log.info("Output dir: %s", config.output_dir)
    log.info("Excluded patterns: %d", len(config.exclude))
    log.info("Supported extensions: %d", len(config.supported_extensions))
    log.info("Context reserve ratio: %.0f%%", config.context_reserve_ratio * 100)

    return config


def _validate(raw: dict) -> list[str]:
    errors = []

    if "exclude" in raw and not isinstance(raw["exclude"], list):
        errors.append("'exclude' must be a list")

    if "supported_extensions" not in raw or not isinstance(raw["supported_extensions"], list):
        errors.append("'supported_extensions' must be a non-empty list")
    elif not raw["supported_extensions"]:
        errors.append("'supported_extensions' is empty — nothing would be processed")

    if "context_reserve_ratio" in raw:
        ratio = raw["context_reserve_ratio"]
        if not isinstance(ratio, (int, float)) or not (0.0 < ratio < 1.0):
            errors.append("'context_reserve_ratio' must be a float between 0 and 1 (exclusive)")

    if "rate_limit" in raw:
        rl = raw["rate_limit"]
        if not isinstance(rl, dict):
            errors.append("'rate_limit' must be a mapping")
        else:
            if "base_delay_seconds" in rl and not isinstance(rl["base_delay_seconds"], (int, float)):
                errors.append("'rate_limit.base_delay_seconds' must be a number")
            if "max_retries" in rl and not isinstance(rl["max_retries"], int):
                errors.append("'rate_limit.max_retries' must be an integer")

    return errors
