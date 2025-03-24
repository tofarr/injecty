"""
Logging configuration for injecty.

This module provides functions to configure logging for the injecty package.
"""

import logging
import sys
from typing import Optional


def configure_logging(
    level: int = logging.INFO,
    format_str: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream: Optional[object] = sys.stdout,
) -> None:
    """
    Configure logging for the injecty package.

    Args:
        level: The logging level (default: logging.INFO)
        format_str: The log format string
        stream: The stream to log to (default: sys.stdout)
    """
    # Create a handler
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter(format_str))

    # Configure the injecty logger
    logger = logging.getLogger("injecty")
    logger.setLevel(level)
    
    # Remove any existing handlers to avoid duplicate logs
    for hdlr in logger.handlers:
        logger.removeHandler(hdlr)
    
    logger.addHandler(handler)
    logger.propagate = False  # Don't propagate to the root logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module within injecty.

    Args:
        name: The name of the module (without the 'injecty.' prefix)

    Returns:
        A configured logger
    """
    return logging.getLogger(f"injecty.{name}")