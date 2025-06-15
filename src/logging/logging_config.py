import json
import logging
import os
import sys
from typing import Any, Dict, Optional

import litellm

# Default log formats
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_JSON_FORMAT = True  # Default to JSON format


class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the log record.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        if hasattr(record, "stack_info") and record.stack_info:
            log_data["stack_info"] = self.formatStack(record.stack_info)
            
        # Add any extra attributes
        for key, value in record.__dict__.items():
            if key not in {"args", "asctime", "created", "exc_info", "exc_text", "filename",
                          "funcName", "id", "levelname", "levelno", "lineno", "module",
                          "msecs", "message", "msg", "name", "pathname", "process",
                          "processName", "relativeCreated", "stack_info", "thread", "threadName"}:
                log_data[key] = value
                
        return json.dumps(log_data)


def configure_logging(
    level: int = logging.INFO,
    log_format: str = DEFAULT_LOG_FORMAT,
    log_file: Optional[str] = "app.log",
    enable_console: bool = True,
    json_format: bool = DEFAULT_JSON_FORMAT,
):
    """
    Configure the logging system with a single source of truth.

    Args:
        level: Logging level (default: INFO)
        log_format: Format for log messages (used only when json_format is False)
        log_file: Path to log file (set to None to disable file logging)
        enable_console: Whether to log to console
        json_format: Whether to use JSON formatting for logs
    """
    # Create handlers
    handlers = []

    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        if json_format:
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        if json_format:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)

    # Configure the root logger
    logging.basicConfig(level=level, handlers=handlers)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: Name of the logger

    Returns:
        A logger instance
    """
    return logging.getLogger(name)

# Disable litellm logs
litellm._logging._disable_debugging()
litellm.suppress_debug_info = True

# Disable httpx logs
logging.getLogger("httpx").setLevel(logging.WARNING)