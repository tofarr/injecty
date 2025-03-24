"""
Tests for the logging configuration module.
"""

import io
import logging
import sys
from unittest.mock import patch

import pytest

from injecty.logging_config import configure_logging, get_logger


def test_configure_logging():
    """Test that configure_logging sets up the logger correctly."""
    # Use a StringIO to capture log output
    stream = io.StringIO()
    
    # Configure logging with a custom level and stream
    configure_logging(level=logging.DEBUG, stream=stream)
    
    # Get the logger and log a message
    logger = logging.getLogger("injecty")
    logger.debug("Test debug message")
    
    # Check that the message was logged to our stream
    output = stream.getvalue()
    assert "Test debug message" in output
    
    # Check that the logger is configured correctly
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)
    assert not logger.propagate


def test_configure_logging_default_params():
    """Test configure_logging with default parameters."""
    # Patch sys.stdout to avoid actual output during tests
    with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
        # Configure with default parameters
        configure_logging()
        
        # Get the logger and check its configuration
        logger = logging.getLogger("injecty")
        
        # Check that the logger is configured correctly
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert not logger.propagate


def test_configure_logging_custom_format():
    """Test configure_logging with a custom format string."""
    # Use a StringIO to capture log output
    stream = io.StringIO()
    
    # Configure with a custom format
    custom_format = "%(levelname)s - %(message)s"
    configure_logging(format_str=custom_format, stream=stream)
    
    # Get the logger and log a message
    logger = logging.getLogger("injecty")
    logger.info("Test info message")
    
    # Check that the message was formatted correctly
    output = stream.getvalue()
    assert "INFO - Test info message" in output


def test_configure_logging_removes_existing_handlers():
    """Test that configure_logging removes existing handlers."""
    # Reset the logger to ensure a clean state
    logger = logging.getLogger("injecty")
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add a handler
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    
    # Check that the handler was added
    assert len(logger.handlers) == 1
    
    # Configure logging again
    configure_logging()
    
    # Check that there's still only one handler (the old one was removed)
    assert len(logger.handlers) == 1
    assert logger.handlers[0] != handler


def test_get_logger():
    """Test that get_logger returns a logger with the correct name."""
    # Get a logger for a specific module
    logger = get_logger("test_module")
    
    # Check that the logger has the correct name
    assert logger.name == "injecty.test_module"