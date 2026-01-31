"""
ETL Pipeline - Extract, Transform, Load
"""

import logging
from datetime import date, datetime
from typing import Optional

from .extractors.events_extractor import EventsExtractor
from .extractors.excel_reader import ExcelReader
from .transformers.production_metrics import MetricsCalculator
from .database import get_db
from .models import (
    ProductionEventDB, ProductionPlanDB, 
    QualityDataDB, UtilityConsumptionDB,
    MachineDB, ProductionEvent, DailySummaryDB
)
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class Pipeline:
    """
    Az ETL folyamat fő vezérlő osztálya.
    Felelős az adatok beolvasásáért (Excel, MES), tisztításáért és mentéséért.
    """
    
    def __init__(self):
        self.events_extractor = EventsExtractor()
        self.excel_reader = ExcelReader()
        self.metrics_calculator = MetricsCalculator()
    
    def run_full_load(self, target_date: date) -> None:
        """
        Lefuttatja a teljes betöltési ciklust egy adott napra:
        Extrakció -> Tisztítás -> Mentés -> KPI kalkuláció.
        
        Args:
            target_date: A feldolgozandó dátum.
        """
        process_date = target_date # The instruction changed the signature to remove Optional and default, so target_date is always provided.
        logger.info(f"ETL folyamat elindítva: {target_date}")
        
        try:
            # 1. Load Master Data & Excel data (planning, lab, utilities)
            self._load_excel_data()

            # 2. Load Production Events from MES (Source DB)
            self._load_production_events(process_date)

            # 3. Calculate Daily Summaries (Transformers)
            self._update_daily_summaries(process_date)
            
            logger.info("ETL pipeline completed successfully")
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise

    def _get_active_machines(self) -> List[str]:
        """Fetch active machine IDs from the database."""
        with get_db() as db:
            machines = db.query(MachineDB.id).all()
            return [m[0] for m in machines]

    def _load_production_events(self, target_date: date) -> None:
        """Extract events from MES and load into production DB."""
        logger.info(f"Loading production events for {target_date}...")
        
        machines = self._get_active_machines()
        if not machines:
            logger.warning("No machines found in database. Please seed master data first.")
            return

        for machine_id in machines:
            events = self.events_extractor.fetch_events(machine_id, target_date)
            if events:
                self._save_events(events)
                logger.info(f"Loaded {len(events)} events for {machine_id}")
            else:
                logger.warning(f"No events found for {machine_id} on {target_date}")

    def _save_events(self, events: List[ProductionEvent]) -> None:
        """Save production events to database with cleanup (Upsert-like behavior)."""
        if not events:
            return
            
        machine_id = events[0].machine_id
        target_date = events[0].timestamp.date()
        start_dt = datetime.combine(target_date, datetime.min.time())
        end_dt = datetime.combine(target_date, datetime.max.time())

        with get_db() as db:
            # Atomic: Delete and Insert in one transaction (if handled by context manager)
            db.query(ProductionEventDB).filter(
                ProductionEventDB.machine_id == machine_id,
                ProductionEventDB.timestamp >= start_dt,
                ProductionEventDB.timestamp <= end_dt
            ).delete()
            
            for event in events:
                event_data = event.model_dump()
                db.add(ProductionEventDB(**event_data))
            
            logger.info(f"Replaced events for {machine_id} on {target_date}")
    
    def _load_excel_data(self) -> None:
        """Load all Excel-based data sources with duplication protection."""
        
        # 1. Planning data
        plans = self.excel_reader.read_planning()
        if plans:
            self._save_plans(plans)
        
        # 2. Lab data
        lab_data = self.excel_reader.read_lab_data()
        if lab_data:
            self._save_quality(lab_data)
        
        # 3. Utilities
        utilities = self.excel_reader.read_utilities()
        if utilities:
            self._save_utilities(utilities)
    
    def _save_plans(self, plans: List[Dict[str, Any]]) -> None:
        """Save production plans to database with cleanup of existing entries."""
        if not plans: return
        
        # Extract unique machine+date combinations to clear
        to_clear = set((p['machine_id'], p['date']) for p in plans)
        
        with get_db() as db:
            for machine_id, plan_date in to_clear:
                db.query(ProductionPlanDB).filter(
                    ProductionPlanDB.machine_id == machine_id,
                    ProductionPlanDB.date == plan_date
                ).delete()
            
            for plan in plans:
                db.add(ProductionPlanDB(**plan))
            logger.info(f"Upserted {len(plans)} plans")
    
    def _save_quality(self, measurements: List[Dict[str, Any]]) -> None:
        """Save quality measurements with cleanup."""
        if not measurements: return
        
        # For quality, we use a broader cleanup or just append? 
        # Better: cleanup by date range found in data
        dates = set(m['timestamp'].date() for m in measurements)
        
        with get_db() as db:
            for d in dates:
                start = datetime.combine(d, datetime.min.time())
                end = datetime.combine(d, datetime.max.time())
                db.query(QualityDataDB).filter(
                    QualityDataDB.timestamp >= start,
                    QualityDataDB.timestamp <= end
                ).delete()
                
            for measurement in measurements:
                db.add(QualityDataDB(**measurement))
            logger.info(f"Upserted {len(measurements)} quality records")
    
    def _save_utilities(self, utilities: List[Dict[str, Any]]) -> None:
        """Save utility consumption with cleanup."""
        if not utilities: return
        
        to_clear = set((u['machine_id'], u['date']) for u in utilities)
        
        with get_db() as db:
            for machine_id, util_date in to_clear:
                db.query(UtilityConsumptionDB).filter(
                    UtilityConsumptionDB.machine_id == machine_id,
                    UtilityConsumptionDB.date == util_date
                ).delete()
                
            for util in utilities:
                db.add(UtilityConsumptionDB(**util))
            logger.info(f"Upserted {len(utilities)} utility records")

    def _update_daily_summaries(self, target_date: date) -> None:
        """Kiszámítja és frissíti a napi OEE és fajlagos mutatókat a választott napra."""
        machines = self._get_active_machines()
        for machine_id in machines:
            summary = self.metrics_calculator.calculate_daily_metrics(machine_id, target_date)
            if summary:
                self.metrics_calculator.save_summary(summary)
