"""
ETL Pipeline - Extract, Transform, Load
"""

import logging
from datetime import date
from typing import Optional

from .extractors.api_client import APIClient
from .extractors.excel_reader import ExcelReader
from .database import get_db
from .models import (
    ProductionEventDB, ProductionPlanDB, 
    QualityDataDB, UtilityConsumptionDB
)

logger = logging.getLogger(__name__)

class Pipeline:
    """Main ETL pipeline orchestrator."""
    
    def __init__(self):
        self.api_client = APIClient()
        self.excel_reader = ExcelReader()
    
    def run_full_load(self, target_date: Optional[date] = None):
        """
        Run full ETL process for a specific date.
        
        Args:
            target_date: Date to process (defaults to today)
        """
        if not target_date:
            target_date = date.today()
        
        logger.info(f"Starting ETL pipeline for {target_date}")
        
        # 1. Load Excel data (planning, lab, utilities)
        self._load_excel_data()
        
        logger.info("ETL pipeline completed successfully")
    
    def _load_excel_data(self):
        """Load all Excel-based data sources."""
        
        # Planning data
        logger.info("Loading production plans...")
        plans = self.excel_reader.read_planning()
        if plans:
            self._save_plans(plans)
            logger.info(f"Loaded {len(plans)} production plans")
        
        # Lab data
        logger.info("Loading lab quality data...")
        lab_data = self.excel_reader.read_lab_data()
        if lab_data:
            self._save_quality(lab_data)
            logger.info(f"Loaded {len(lab_data)} quality measurements")
        
        # Utilities
        logger.info("Loading utilities data...")
        utilities = self.excel_reader.read_utilities()
        if utilities:
            self._save_utilities(utilities)
            logger.info(f"Loaded {len(utilities)} utility records")
    
    def _save_plans(self, plans: list):
        """Save production plans to database."""
        with get_db() as db:
            for plan in plans:
                db.add(ProductionPlanDB(**plan))
            logger.info(f"Saved {len(plans)} plans to database")
    
    def _save_quality(self, measurements: list):
        """Save quality measurements to database."""
        with get_db() as db:
            for measurement in measurements:
                db.add(QualityDataDB(**measurement))
            logger.info(f"Saved {len(measurements)} quality measurements")
    
    def _save_utilities(self, utilities: list):
        """Save utility consumption to database."""
        with get_db() as db:
            for util in utilities:
                db.add(UtilityConsumptionDB(**util))
            logger.info(f"Saved {len(utilities)} utility records")
