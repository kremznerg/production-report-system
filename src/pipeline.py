"""
ETL Pipeline - Extract, Transform, Load
"""

import logging
from datetime import date, datetime
from typing import Optional

from .extractors.events_extractor import EventsExtractor
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
        self.events_extractor = EventsExtractor()
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

        # 2. Load Production Events from MES (Source DB)
        self._load_production_events(target_date)
        
        logger.info("ETL pipeline completed successfully")

    def _load_production_events(self, target_date: date):
        """Extract events from MES and load into production DB."""
        logger.info(f"Loading production events for {target_date}...")
        
        # A gépek listája (PM1, PM2)
        machines = ["PM1", "PM2"]
        
        for machine_id in machines:
            events = self.events_extractor.fetch_events(machine_id, target_date)
            if events:
                self._save_events(events)
                logger.info(f"Loaded {len(events)} events for {machine_id}")
            else:
                logger.warning(f"No events found for {machine_id} on {target_date}")

    def _save_events(self, events: list):
        """Save production events to database with cleanup."""
        if not events:
            return
            
        machine_id = events[0].machine_id
        # Kiszámoljuk a napot az első eseményből
        target_date = events[0].timestamp.date()
        start_dt = datetime.combine(target_date, datetime.min.time())
        end_dt = datetime.combine(target_date, datetime.max.time())

        with get_db() as db:
            # ELŐSZÖR TÖRÖLJÜK A RÉGI ADATOKAT ERRE A NAPRA/GÉPRE
            db.query(ProductionEventDB).filter(
                ProductionEventDB.machine_id == machine_id,
                ProductionEventDB.timestamp >= start_dt,
                ProductionEventDB.timestamp <= end_dt
            ).delete()
            
            # AZUTÁN MENTJÜK AZ ÚJAKAT
            for event in events:
                event_data = event.model_dump()
                db.add(ProductionEventDB(**event_data))
            
            logger.info(f"Cleaned up and saved {len(events)} events for {machine_id}")
    
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
