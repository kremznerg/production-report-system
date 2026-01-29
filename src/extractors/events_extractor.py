"""
Events Extractor - MES adatbázisból olvassa a termelési eseményeket.
"""

import logging
from datetime import date, datetime
from typing import List

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from ..config import settings
from ..models import ProductionEvent

logger = logging.getLogger(__name__)


# --- FORRÁS ADATBÁZIS MODELLJE (csak olvasáshoz) ---

class SourceBase(DeclarativeBase):
    pass

class SourceEvent(SourceBase):
    """Termelési esemény a forrás rendszerben."""
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer)
    event_type = Column(String(20), nullable=False)
    status = Column(String(20))
    weight_kg = Column(Float)
    average_speed = Column(Float)
    machine_id = Column(String(20))
    article_id = Column(String(50))
    description = Column(String(255))


class EventsExtractor:
    """
    Extractor a MES (source_events.db) adatbázisból.
    Szimulálja egy külső rendszerből való adatlekérést.
    """
    
    def __init__(self):
        source_db_path = settings.DATA_DIR / "source_events.db"
        self.engine = create_engine(f"sqlite:///{source_db_path}")
        self.Session = sessionmaker(bind=self.engine)
    
    def fetch_events(self, machine_id: str, target_date: date) -> List[ProductionEvent]:
        """
        Lekéri egy gép egy napjának eseményeit a forrás adatbázisból.
        
        Args:
            machine_id: Gép azonosító (PM1, PM2)
            target_date: Dátum
            
        Returns:
            ProductionEvent objektumok listája
        """
        session = self.Session()
        
        try:
            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt = datetime.combine(target_date, datetime.max.time())
            
            events = session.query(SourceEvent).filter(
                SourceEvent.machine_id == machine_id,
                SourceEvent.timestamp >= start_dt,
                SourceEvent.timestamp < end_dt
            ).order_by(SourceEvent.timestamp).all()
            
            logger.info(f"Fetched {len(events)} events for {machine_id} on {target_date}")
            
            # Konvertálás Pydantic modellre
            return [
                ProductionEvent(
                    timestamp=e.timestamp,
                    duration_seconds=e.duration_seconds,
                    event_type=e.event_type,
                    status=e.status,
                    weight_kg=e.weight_kg or 0,
                    average_speed=e.average_speed or 0,
                    machine_id=e.machine_id,
                    article_id=e.article_id,
                    description=e.description
                )
                for e in events
            ]
            
        finally:
            session.close()
    
    def get_available_dates(self, machine_id: str) -> List[date]:
        """Visszaadja a géphez elérhető dátumokat."""
        session = self.Session()
        
        try:
            from sqlalchemy import func
            dates = session.query(
                func.date(SourceEvent.timestamp)
            ).filter(
                SourceEvent.machine_id == machine_id
            ).distinct().all()
            
            return sorted([d[0] for d in dates if d[0]])
            
        finally:
            session.close()
