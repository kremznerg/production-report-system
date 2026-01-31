#!/usr/bin/env python3
"""
Termelési események szimulálása.
Generál realisztikus demo adatokat az elmúlt 30 napra
egy KÜLÖN adatbázisba (source_events.db) - ez szimulálja a MES rendszert.
"""

import sys
import os
from pathlib import Path
import random
import pandas as pd
from datetime import datetime, timedelta

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings

# --- KÜLSŐ ADATBÁZIS MODELLJE (MES rendszer szimulálása) ---

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


# --- KONSTANSOK ---

MACHINES = ["PM1", "PM2"]
ARTICLES = ["KL_150", "KL_175", "TL_100", "TL_140", "WTL_120", "FL_90"]
EVENT_INTERVAL_MINUTES = 15

STOP_REASONS = [
    "Tervezett karbantartás",
    "Anyaghiány",
    "Műszaki hiba",
    "Érzékelő tisztítás",
    "Hengercsere",
    "Szárító beállítás"
]


# Global planning cache
PLANNING_DATA = None

def get_day_planning(target_date, machine_id):
    global PLANNING_DATA
    if PLANNING_DATA is None:
        planning_file = settings.PLANNING_FILE
        if planning_file.exists():
            PLANNING_DATA = pd.read_excel(planning_file)
        else:
            return None
    
    # Filter for date and machine
    day_plan = PLANNING_DATA[
        (PLANNING_DATA['Date'].dt.date == target_date) & 
        (PLANNING_DATA['Machine'] == machine_id)
    ]
    return day_plan

def generate_events_for_day(target_date, machine_id):
    """Egy nap eseményeit generálja egy gépre."""
    import pandas as pd # Ensure pandas is available here if needed, but it's at top level in my thought
    
    events = []
    current_time = datetime.combine(target_date, datetime.min.time())
    end_time = current_time + timedelta(days=1)

    # Get target production and article for this day from plan
    day_plan = get_day_planning(target_date, machine_id)
    
    if day_plan is not None and not day_plan.empty:
        target_tons = day_plan['Target_Tons'].sum()
        planned_articles = day_plan['Article'].tolist()
    else:
        target_tons = random.uniform(100, 150) # Fallback
        planned_articles = [random.choice(ARTICLES)]
    
    current_article = planned_articles[0]
    
    # We estimate total RUN intervals to scale weight
    # 24 hours * 4 (15min intervals) * 0.88 (uptime probability)
    estimated_run_intervals = (24 * 60 / EVENT_INTERVAL_MINUTES) * 0.88
    base_weight_per_interval = (target_tons * 1000) / estimated_run_intervals
    
    while current_time < end_time:
        rand = random.random()
        
        if rand < 0.88:
            # RUN esemény (88%)
            duration = EVENT_INTERVAL_MINUTES * 60
            status = "GOOD" if random.random() < 0.95 else "SCRAP"
            base_speed = random.uniform(750, 900)
            
            # Weight is scaled to meet target_tons for the day
            weight = base_weight_per_interval * random.uniform(0.9, 1.1)
            
            if status == "SCRAP":
                # Scrap weight is still production but not 'GOOD'
                pass 
            
            events.append(SourceEvent(
                timestamp=current_time,
                duration_seconds=duration,
                event_type="RUN",
                status=status,
                weight_kg=round(weight, 1),
                average_speed=round(base_speed, 1),
                machine_id=machine_id,
                article_id=current_article,
                description=None
            ))
            current_time += timedelta(seconds=duration)
            
        elif rand < 0.92:
            # STOP esemény (4%)
            duration = random.randint(10, 45) * 60
            events.append(SourceEvent(
                timestamp=current_time,
                duration_seconds=duration,
                event_type="STOP",
                status=None,
                weight_kg=0,
                average_speed=0,
                machine_id=machine_id,
                article_id=None,
                description=random.choice(STOP_REASONS)
            ))
            current_time += timedelta(seconds=duration)
            
        else:
            # BREAK esemény (8%)
            duration = random.randint(5, 20) * 60
            events.append(SourceEvent(
                timestamp=current_time,
                duration_seconds=duration,
                event_type="BREAK",
                status=None,
                weight_kg=0,
                average_speed=0,
                machine_id=machine_id,
                article_id=None,
                description="Papírszakadás"
            ))
            current_time += timedelta(seconds=duration)
            
            # Szakadás után SCRAP
            if current_time < end_time:
                duration = EVENT_INTERVAL_MINUTES * 60
                events.append(SourceEvent(
                    timestamp=current_time,
                    duration_seconds=duration,
                    event_type="RUN",
                    status="SCRAP",
                    weight_kg=round(random.uniform(200, 500), 1),
                    average_speed=round(random.uniform(400, 600), 1),
                    machine_id=machine_id,
                    article_id=current_article,
                    description="Újraindulás szakadás után"
                ))
                current_time += timedelta(seconds=duration)
        
        # Switch article based on time slices (24h / num_articles)
        if len(planned_articles) > 1:
            slice_hours = 24 / len(planned_articles)
            article_index = int(current_time.hour / slice_hours)
            # Ensure index doesn't overshoot
            article_index = min(article_index, len(planned_articles) - 1)
            current_article = planned_articles[article_index]
    
    return events


def main():
    """Fő futtatás."""
    print("MES adatbázis létrehozása (source_events.db)...")
    
    # Külön adatbázis a "MES rendszernek"
    source_db_path = settings.DATA_DIR / "source_events.db"
    
    # Töröljük ha létezik
    if source_db_path.exists():
        print(f"Régi forrás DB törlése: {source_db_path}")
        os.remove(source_db_path)
    
    # Új engine a forrás DB-hez
    source_engine = create_engine(f"sqlite:///{source_db_path}")
    SourceBase.metadata.create_all(bind=source_engine)
    SourceSession = sessionmaker(bind=source_engine)
    
    # 30 nap visszamenőleg
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    all_events = []
    current_date = start_date
    
    while current_date <= end_date:
        for machine_id in MACHINES:
            events = generate_events_for_day(current_date, machine_id)
            all_events.extend(events)
        current_date += timedelta(days=1)
    
    print(f"Generált események: {len(all_events)}")
    
    # Mentés a FORRÁS adatbázisba
    print("Mentés source_events.db-be...")
    session = SourceSession()
    try:
        for event in all_events:
            session.add(event)
        session.commit()
    finally:
        session.close()
    
    print(f"✅ Kész! {len(all_events)} esemény mentve ide: {source_db_path}")


if __name__ == "__main__":
    main()
