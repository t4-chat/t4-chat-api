import logging
import os
import sys
from typing import Optional

# Default log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def configure_logging(
    level: int = logging.INFO,
    log_format: str = DEFAULT_LOG_FORMAT,
    log_file: Optional[str] = "app.log",
    enable_console: bool = True,
):
    """
    Configure the logging system with a single source of truth.

    Args:
        level: Logging level (default: INFO)
        log_format: Format for log messages
        log_file: Path to log file (set to None to disable file logging)
        enable_console: Whether to log to console
    """
    # Create handlers
    handlers = []

    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)

    # Configure the root logger
    logging.basicConfig(level=level, format=log_format, handlers=handlers)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: Name of the logger

    Returns:
        A logger instance
    """
    return logging.getLogger(name)
