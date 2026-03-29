"""
ETL FOLYAMAT VEZÉRLŐ (ORCHESTRATOR)
===================================
Ez a modul a rendszer "karmestere". 
Összehangolja az adatkinyerést (Extract), az adatok transzformálását (Transform) 
és az eredmények adatbázisba töltését (Load).
"""

import logging
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from .extractors.events_extractor import EventsExtractor
from .extractors.excel_reader import ExcelReader
from .transformers.production_metrics import MetricsCalculator
from .database import get_db
from .models import (
    ProductionEventDB, ProductionPlanDB, 
    QualityDataDB, UtilityConsumptionDB,
    MachineDB, ProductionEvent, DailySummaryDB
)

logger = logging.getLogger(__name__)

class Pipeline:
    """
    Az ETL folyamat fő vezérlő osztálya.
    Gondoskodik az adatok konzisztenciájáról és a folyamatok sorrendiségéről.
    """
    
    def __init__(self) -> None:
        """Komponensek (Extractorok és Calculator) példányosítása."""
        self.events_extractor = EventsExtractor()
        self.excel_reader = ExcelReader()
        self.metrics_calculator = MetricsCalculator()
    
    def run_full_load(self, target_date: date, target_machine_id: Optional[str] = None) -> None:
        """
        Lefuttatja a teljes betöltési ciklust egy adott napra és (opcionálisan) gépre.
        Ez a folyamat törli a korábbi adatokat az adott napra (Upsert), 
        így bármikor újraindítható hiba nélkül.
        
        A futás sorrendje:
        1. Excel adatok beolvasása (Terv, Labor, Közmű).
        2. MES események lekérése a forrás adatbázisból.
        3. KPI mutatók újraszámolása és az összesítő tábla frissítése.
        
        Args:
            target_date: A feldolgozandó dátum.
            target_machine_id: (Opcionális) Ha meg van adva, csak ezt a gépet szinkronizálja.
        """
        machine_info = f" (Gép: {target_machine_id})" if target_machine_id else " (Minden gép)"
        logger.info(f"ETL folyamat indítása: {target_date}{machine_info}")
        
        try:
            self._load_excel_data(target_date)
            self._load_production_events(target_date, target_machine_id)
            self._update_daily_summaries(target_date, target_machine_id)
            logger.info(f"ETL folyamat sikeresen befejeződött: {target_date}")
        except Exception as e:
            logger.error(f"Pipeline hiba a folyamat során: {str(e)}")
            raise

    def _get_active_machines(self) -> List[str]:
        """Lekéri az adatbázisban regisztrált aktív gépek azonosítóit."""
        with get_db() as db:
            machines = db.query(MachineDB.id).all()
            return [m[0] for m in machines]

    def _load_production_events(self, target_date: date, target_machine_id: Optional[str] = None) -> None:
        """MES események kinyerése és betöltése a cél adatbázisba."""
        logger.info(f"Események betöltése... ({target_date})")
        
        if target_machine_id:
            machines = [target_machine_id]
        else:
            machines = self._get_active_machines()
            if not machines:
                logger.warning("Nincsenek aktív gépek az adatbázisban! Futtasd a seed_master_data.py-t.")
                return

        for machine_id in machines:
            events = self.events_extractor.fetch_events(machine_id, target_date)
            if events:
                self._save_events(events)
                logger.debug(f"Betöltve {len(events)} esemény: {machine_id}")
            else:
                logger.warning(f"Nem található esemény: {machine_id} | {target_date}")

    def _save_events(self, events: List[ProductionEvent]) -> None:
        """
        Események mentése az adatbázisba. 
        Gondoskodik a régi adatok törléséről az adott napra/gépre.
        """
        if not events:
            return
            
        machine_id = events[0].machine_id
        target_date = events[0].timestamp.date()
        start_dt = datetime.combine(target_date, datetime.min.time())
        end_dt = datetime.combine(target_date, datetime.max.time())

        with get_db() as db:
            # Régi adatok törlése a duplikáció elkerülése végett
            db.query(ProductionEventDB).filter(
                ProductionEventDB.machine_id == machine_id,
                ProductionEventDB.timestamp >= start_dt,
                ProductionEventDB.timestamp <= end_dt
            ).delete()
            
            # Új események beszúrása
            for event in events:
                event_data = event.model_dump()
                db.add(ProductionEventDB(**event_data))
            
            logger.info(f"Eseménynapló frissítve: {machine_id} | {target_date}")
    
    def _load_excel_data(self, target_date: date) -> None:
        """Az összes Excel típusú forrásfájl beolvasása és mentése az adott napra."""
        
        plans = self.excel_reader.read_planning(target_date)
        if plans:
            self._save_plans(plans)
        
        lab_data = self.excel_reader.read_lab_data(target_date)
        if lab_data:
            self._save_quality(lab_data)
        
        utilities = self.excel_reader.read_utilities(target_date)
        if utilities:
            self._save_utilities(utilities)
    
    def _save_plans(self, plans: List[Dict[str, Any]]) -> None:
        """Tervezési adatok mentése Upsert logikával."""
        if not plans: return
        
        to_clear = set((p['machine_id'], p['date']) for p in plans)
        
        with get_db() as db:
            for machine_id, plan_date in to_clear:
                db.query(ProductionPlanDB).filter(
                    ProductionPlanDB.machine_id == machine_id,
                    ProductionPlanDB.date == plan_date
                ).delete()
            
            for plan in plans:
                db.add(ProductionPlanDB(**plan))
            logger.info(f"Tervezési adatok (Planning) szinkronizálva: {len(plans)} rekord")
    
    def _save_quality(self, measurements: List[Dict[str, Any]]) -> None:
        """Minőségi adatok (labor) mentése Upsert logikával."""
        if not measurements: return
        
        to_clear = set((m['machine_id'], m['timestamp'].date()) for m in measurements)
        
        with get_db() as db:
            for machine_id, q_date in to_clear:
                start = datetime.combine(q_date, datetime.min.time())
                end = datetime.combine(q_date, datetime.max.time())
                db.query(QualityDataDB).filter(
                    QualityDataDB.machine_id == machine_id,
                    QualityDataDB.timestamp >= start,
                    QualityDataDB.timestamp <= end
                ).delete()
                
            for measurement in measurements:
                db.add(QualityDataDB(**measurement))
            logger.info(f"Minőségi adatok (Quality) szinkronizálva: {len(measurements)} rekord")
    
    def _save_utilities(self, utilities: List[Dict[str, Any]]) -> None:
        """Közmű adatok mentése Upsert logikával."""
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
            logger.info(f"Közműadatok (Utilities) szinkronizálva: {len(utilities)} rekord")

    def _update_daily_summaries(self, target_date: date, target_machine_id: Optional[str] = None) -> None:
        """KPI mutatók újraszámolása és mentése az összesítő táblába."""
        machines = [target_machine_id] if target_machine_id else self._get_active_machines()
        for machine_id in machines:
            summary = self.metrics_calculator.calculate_daily_metrics(machine_id, target_date)
            if summary:
                self.metrics_calculator.save_summary(summary)
        logger.info(f"Napi összesítők frissítve: {target_date}")
