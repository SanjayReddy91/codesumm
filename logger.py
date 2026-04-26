import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger for the given module name.
    All loggers share the same handler/format configured on the root logger.
    Call setup_logging() once at startup before calling get_logger().
    """
    return logging.getLogger(name)


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configures the root logger with a consistent format.
    Should be called once in main.py before anything else.

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
