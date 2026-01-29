#!/usr/bin/env python3
"""
Run the ETL pipeline to load data into the database.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from datetime import date
from src.logging_config import setup_logging
from src.config import settings
from src.pipeline import Pipeline

if __name__ == "__main__":
    # Initialize logging
    setup_logging(settings.LOG_LEVEL)
    
    # Create pipeline instance
    pipeline = Pipeline()
    
    # Run full ETL for the last 30 days (standard demo period)
    import datetime
    end_date = date.today()
    start_date = end_date - datetime.timedelta(days=30)
    
    current_date = start_date
    while current_date <= end_date:
        pipeline.run_full_load(target_date=current_date)
        current_date += datetime.timedelta(days=1)
    
    print(f"\n✅ Pipeline completed for period {start_date} to {end_date}!")
