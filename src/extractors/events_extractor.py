"""
TERMELÉSI ESEMÉNY KINYERŐ (EVENTS EXTRACTOR)
===========================================
Felelős a termelési események (RUN, STOP, BREAK) kinyeréséért a "külső" MES 
(Manufacturing Execution System) adatbázisból. Ez a modul szimulálja a gyári 
adatgyűjtő rendszerrel való kapcsolatot.
"""

import logging
from datetime import date, datetime
from typing import List

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from ..config import settings
from ..models import ProductionEvent

# Naplózás beállítása a modulhoz
logger = logging.getLogger(__name__)


# --- FORRÁS ADATBÁZIS MODELLJE (Csak olvasáshoz használt sémák) ---

class SourceBase(DeclarativeBase):
    """Alaposztály a forrás adatbázis sémáihoz."""
    pass

class SourceEvent(SourceBase):
    """
    Termelési esemény rekordja a forrás (MES) rendszerben.
    Ez a tábla tartalmazza a nyers, feldolgozatlan gépadatokat.
    """
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
    Adatkinyerő osztály a MES (source_events.db) adatbázishoz.
    Feladata a nyers adatok transzformálása a belső Pydantic modellekre.
    """
    
    def __init__(self) -> None:
        """Adatbázis kapcsolat inicializálása a konfiguráció alapján."""
        self.engine = create_engine(settings.MES_DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
    
    def fetch_events(self, machine_id: str, target_date: date) -> List[ProductionEvent]:
        """
        Lekéri egy meghatározott gép adott napi eseményeit.
        
        Args:
            machine_id: A gép egyedi azonosítója (pl. PM1, PM2).
            target_date: A vizsgált nap dátuma.
            
        Returns:
            List[ProductionEvent]: Az események listája Pydantic objektumokba csomagolva.
        """
        session = self.Session()
        
        try:
            # Időtartomány meghatározása (nap eleje és vége)
            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt = datetime.combine(target_date, datetime.max.time())
            
            # Lekérdezés hatékony szűréssel és sorbarendezéssel
            events = session.query(SourceEvent).filter(
                SourceEvent.machine_id == machine_id,
                SourceEvent.timestamp >= start_dt,
                SourceEvent.timestamp <= end_dt
            ).order_by(SourceEvent.timestamp).all()
            
            logger.info(f"Sikeresen kinyerve {len(events)} esemény: {machine_id} | {target_date}")
            
            # Konvertálás belső Pydantic modellekre a további validációhoz
            return [
                ProductionEvent(
                    timestamp=e.timestamp,
                    duration_seconds=e.duration_seconds,
                    event_type=e.event_type,
                    status=e.status,
                    weight_kg=e.weight_kg or 0.0,
                    average_speed=e.average_speed or 0.0,
                    machine_id=e.machine_id,
                    article_id=e.article_id,
                    description=e.description
                )
                for e in events
            ]
            
        except Exception as e:
            logger.error(f"Hiba az események kinyerésekor ({machine_id}, {target_date}): {e}")
            return []
        finally:
            session.close()
    
    def get_available_dates(self, machine_id: str) -> List[date]:
        """
        Lekéri a forrás adatbázisból az összes olyan dátumot, amihez tartozik adat.
        Ezt a Dashboard naptárának inicializálásához használjuk.
        
        Args:
            machine_id: A gép azonosítója.
            
        Returns:
            List[date]: Elérhető dátumok listája, sorbarendezve.
        """
        session = self.Session()
        
        try:
            from sqlalchemy import func
            # Egyedi dátumok kinyerése az időbélyegekből
            dates = session.query(
                func.date(SourceEvent.timestamp)
            ).filter(
                SourceEvent.machine_id == machine_id
            ).distinct().all()
            
            # Konvertálás date objektumokká (Postgres date objektumot, SQLite string-et ad vissza)
            result = []
            for d in dates:
                if d[0]:
                    if isinstance(d[0], date):
                        result.append(d[0])
                    elif isinstance(d[0], str):
                        try:
                            result.append(datetime.strptime(d[0], '%Y-%m-%d').date())
                        except ValueError:
                            continue
            
            return sorted(result)
            
        except Exception as e:
            logger.error(f"Hiba a dátumok lekérésekor ({machine_id}): {e}")
            return []
        finally:
            session.close()
