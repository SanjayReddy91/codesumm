import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """Returns a logger under the codesumm namespace."""
    return logging.getLogger(f"codesumm.{name}" if not name.startswith("codesumm") else name)


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configures the root logger with a consistent format.
    Must be called once at startup before any logging happens.

    Format: [TIMESTAMP] [LEVEL    ] [MODULE         ] message
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)-8s] [%(name)-20s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers if setup_logging is called more than once
    if not root.handlers:
        root.addHandler(handler)


def set_log_level(level: str) -> None:
    """Sets the log level for all loggers. Accepts a string like 'DEBUG', 'INFO', etc."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(numeric_level)
    for handler in root.handlers:
        handler.setLevel(numeric_level)