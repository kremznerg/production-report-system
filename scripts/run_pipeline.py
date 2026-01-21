#!/usr/bin/env python3
"""
Run the ETL pipeline to load data into the database.
"""

from datetime import date
from src.logging_config import setup_logging
from src.config import settings
from src.pipeline import Pipeline

if __name__ == "__main__":
    # Initialize logging
    setup_logging(settings.LOG_LEVEL)
    
    # Create pipeline instance
    pipeline = Pipeline()
    
    # Run full ETL for today
    pipeline.run_full_load(target_date=date.today())
    
    print("\n✅ Pipeline completed! Check logs/app.log for details.")
