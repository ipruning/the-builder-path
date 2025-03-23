"""
## ChangeLog

- [001] - [feat] - Added logging configuration
- [002] - [fix] - Prevented duplicate log handlers
"""

import logging
import sys


def configure_logging():
    """
    Configure the logging system.

    Sets up logging with appropriate format and log level.
    Ensures handlers are not duplicated to prevent multiple log messages.
    """
    # Create a formatter that includes timestamp, level, and message
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Configure the root logger
    root_logger = logging.getLogger()

    # Check if handlers already exist to prevent duplicates
    if not root_logger.handlers:
        # Create a handler that writes to stderr
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(handler)

    return root_logger
