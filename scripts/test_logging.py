#!/usr/bin/env python3
"""
Demo script to test the logging system.
"""

from src.logging_config import setup_logging
from src.config import settings
import logging

# Initialize logging
setup_logging(settings.LOG_LEVEL)

# Get a logger
logger = logging.getLogger(__name__)

# Test different log levels
logger.debug("This is a DEBUG message (won't show in console)")
logger.info("This is an INFO message (will be in file)")
logger.warning("This is a WARNING message (will show in console AND file)")
logger.error("This is an ERROR message (will show everywhere)")

print("\n✅ Check logs/app.log to see all messages!")
