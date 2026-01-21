"""
Logging configuration for the application.
Call setup_logging() once at application startup.
"""

import logging
import sys
from pathlib import Path

def setup_logging(log_level: str = "INFO"):
    """
    Configure logging for the entire application.
    
    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Define log format
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Root logger configuration
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            # Console handler (WARNING and above)
            logging.StreamHandler(sys.stdout),
            # File handler (INFO and above)
            logging.FileHandler(log_dir / "app.log", encoding="utf-8")
        ]
    )
    
    # Set console handler to WARNING only
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Set file handler to INFO
    file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Clear default handlers and add our custom ones
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    logging.info("Logging system initialized")
