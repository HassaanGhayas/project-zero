#!/usr/bin/env python3
"""
Unit tests for logger configuration.

Tests cover:
- Logger initialization
- File handler creation
- Console handler creation
- Log format validation
- Log level configuration
"""

import logging
import tempfile
from pathlib import Path

import pytest

from src.watchers.logger_config import setup_logging, get_logger


@pytest.fixture
def temp_vault(tmp_path):
    """Create a temporary vault directory for logging tests."""
    vault = tmp_path / "test_vault"
    vault.mkdir()
    (vault / "Logs").mkdir()
    return vault


class TestLoggerConfiguration:
    """Test suite for logger configuration."""

    def test_setup_logging_creates_logger(self, temp_vault):
        """Test that setup_logging creates a logger instance."""
        logger = setup_logging(
            "test_logger",
            vault_path=temp_vault,
            level=logging.INFO,
            console_output=False,
            file_output=False
        )

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_logger_level_configuration(self, temp_vault):
        """Test that logger level is set correctly."""
        logger = setup_logging(
            "test_logger",
            vault_path=temp_vault,
            level=logging.DEBUG,
            console_output=False,
            file_output=False
        )

        assert logger.level == logging.DEBUG

    def test_console_handler_enabled(self, temp_vault):
        """Test that console handler is added when enabled."""
        logger = setup_logging(
            "test_logger",
            vault_path=temp_vault,
            level=logging.INFO,
            console_output=True,
            file_output=False
        )

        # Check for StreamHandler
        has_console = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
        assert has_console

    def test_file_handler_enabled(self, temp_vault):
        """Test that file handler is added when enabled."""
        logger = setup_logging(
            "test_logger",
            vault_path=temp_vault,
            level=logging.INFO,
            console_output=False,
            file_output=True
        )

        # Check for FileHandler
        has_file = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        assert has_file

    def test_log_file_creation(self, temp_vault):
        """Test that log file is created in correct location."""
        logger = setup_logging(
            "test_logger",
            vault_path=temp_vault,
            level=logging.INFO,
            console_output=False,
            file_output=True
        )

        # Log a message
        logger.info("Test message")

        # Check that log file exists
        from datetime import datetime
        log_file = temp_vault / "Logs" / f"watcher-{datetime.now().strftime('%Y-%m-%d')}.log"
        assert log_file.exists()

    def test_log_message_format(self, temp_vault):
        """Test that log messages are formatted correctly."""
        logger = setup_logging(
            "test_logger",
            vault_path=temp_vault,
            level=logging.INFO,
            console_output=False,
            file_output=True
        )

        # Log a test message
        test_message = "Test log entry"
        logger.info(test_message)

        # Read log file
        from datetime import datetime
        log_file = temp_vault / "Logs" / f"watcher-{datetime.now().strftime('%Y-%m-%d')}.log"
        log_content = log_file.read_text()

        # Verify format: [YYYY-MM-DD HH:MM:SS] LEVEL: message
        assert test_message in log_content
        assert "INFO:" in log_content
        assert "[" in log_content  # Timestamp bracket

    def test_multiple_log_levels(self, temp_vault):
        """Test that different log levels are handled correctly."""
        logger = setup_logging(
            "test_logger",
            vault_path=temp_vault,
            level=logging.DEBUG,
            console_output=False,
            file_output=True
        )

        # Log messages at different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # Read log file
        from datetime import datetime
        log_file = temp_vault / "Logs" / f"watcher-{datetime.now().strftime('%Y-%m-%d')}.log"
        log_content = log_file.read_text()

        # Verify all levels are logged
        assert "DEBUG:" in log_content
        assert "INFO:" in log_content
        assert "WARNING:" in log_content
        assert "ERROR:" in log_content

    def test_get_logger_returns_existing(self, temp_vault):
        """Test that get_logger returns existing logger if already configured."""
        # Create logger first
        logger1 = setup_logging(
            "test_logger",
            vault_path=temp_vault,
            level=logging.INFO,
            console_output=False,
            file_output=False
        )

        # Get same logger
        logger2 = get_logger("test_logger")

        assert logger1 is logger2

    def test_log_directory_creation(self, tmp_path):
        """Test that Logs directory is created if missing."""
        vault = tmp_path / "new_vault"
        vault.mkdir()

        logger = setup_logging(
            "test_logger",
            vault_path=vault,
            level=logging.INFO,
            console_output=False,
            file_output=True
        )

        # Log a message to trigger file handler
        logger.info("Test")

        # Verify Logs directory was created
        assert (vault / "Logs").exists()

    def test_logger_isolation(self, temp_vault):
        """Test that different loggers don't interfere."""
        logger1 = setup_logging(
            "logger1",
            vault_path=temp_vault,
            level=logging.INFO,
            console_output=False,
            file_output=False
        )

        logger2 = setup_logging(
            "logger2",
            vault_path=temp_vault,
            level=logging.DEBUG,
            console_output=False,
            file_output=False
        )

        assert logger1.name == "logger1"
        assert logger2.name == "logger2"
        assert logger1.level == logging.INFO
        assert logger2.level == logging.DEBUG


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
