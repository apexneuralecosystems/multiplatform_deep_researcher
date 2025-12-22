"""
Logging configuration for the application.
Provides structured logging with different levels for development and production.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from backend.core.config import settings


def setup_logging() -> logging.Logger:
    """
    Configure application logging.
    
    Returns:
        The root application logger.
    """
    # Determine log level based on DEBUG setting
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    simple_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    
    # File handler (rotates daily)
    log_filename = log_dir / f"app_{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # Always log everything to file
    file_handler.setFormatter(detailed_formatter)
    
    # Error file handler (errors only)
    error_filename = log_dir / f"errors_{datetime.now().strftime('%Y-%m-%d')}.log"
    error_handler = logging.FileHandler(error_filename, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # Create application logger
    app_logger = logging.getLogger("deep_researcher")
    app_logger.setLevel(log_level)
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    app_logger.info(f"Logging initialized | Level: {logging.getLevelName(log_level)} | Log file: {log_filename}")
    
    return app_logger


# Create logger instance
logger = setup_logging()
