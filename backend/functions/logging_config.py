"""
Centralized logging configuration for SHACL-BI backend.
Provides consistent logging across all modules.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import os


def setup_logging(
    level=logging.INFO,
    log_file=None,
    console_output=True,
    format_string=None,
    include_timestamps=True
):
    """
    Setup logging configuration for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        console_output: Whether to output to console
        format_string: Custom format string (optional)
        include_timestamps: Whether to include timestamps in format
    """

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Default format
    if format_string is None:
        if include_timestamps:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        else:
            format_string = '%(name)s - %(levelname)s - %(message)s'

    formatter = logging.Formatter(format_string)

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name):
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def setup_environment_logging():
    """Setup logging based on environment variables."""
    import config

    # Get configuration
    log_level = getattr(config, 'LOG_LEVEL', 'INFO').upper()
    log_file = getattr(config, 'LOG_FILE', None)

    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level, logging.INFO)

    # Setup logging
    setup_logging(
        level=numeric_level,
        log_file=log_file,
        console_output=True,
        include_timestamps=True
    )


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""

    @property
    def logger(self):
        """Get logger for this class."""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__module__ + '.' + self.__class__.__name__)
        return self._logger


def log_function_call(func):
    """Decorator to log function calls."""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")

        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with error: {e}")
            raise

    return wrapper


def log_performance(func):
    """Decorator to log function performance."""
    import time

    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"{func.__name__} executed in {duration:.4f} seconds")
            return result
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.error(f"{func.__name__} failed after {duration:.4f} seconds: {e}")
            raise

    return wrapper


# Context manager for logging
class LogContext:
    """Context manager for logging operations."""

    def __init__(self, logger_name, operation, level=logging.INFO):
        self.logger = get_logger(logger_name)
        self.operation = operation
        self.level = level
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.log(self.level, f"Starting {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = datetime.now() - self.start_time

        if exc_type is None:
            self.logger.log(self.level, f"Completed {self.operation} in {duration.total_seconds():.4f}s")
        else:
            self.logger.error(f"Failed {self.operation} after {duration.total_seconds():.4f}s: {exc_val}")

        return False  # Don't suppress exceptions


# Configure logging on import
try:
    setup_environment_logging()
except Exception as e:
    # Fallback basic logging if configuration fails
    logging.basicConfig(
        level=logging.INFO,
        format='%(name)s - %(levelname)s - %(message)s'
    )
    logging.error(f"Failed to setup environment logging: {e}")


# Export commonly used items
__all__ = [
    'setup_logging',
    'get_logger',
    'LoggerMixin',
    'log_function_call',
    'log_performance',
    'LogContext'
]