#!/usr/bin/env python3
"""
MES ESEMÉNY SZIMULÁTOR (Source System Simulator)
================================================
Létrehoz egy külön PostgreSQL adatbázist (mes_db), amely a gyári MES rendszert szimulálja.
Ez az alapforrása a termelési eseményeknek (RUN, STOP, BREAK).
Realisztikus gyártási naplót generál a teljes mintatartományra.
"""

import sys
from pathlib import Path
import random
from typing import List, Optional
import pandas as pd
from datetime import datetime, timedelta, date
from functools import lru_cache
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Projekt gyökérkönyvtár hozzáadása a Python elérési úthoz
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings

# --- FORRÁS ADATBÁZIS MODELL (MES SIMULATION) ---
class SourceBase(DeclarativeBase):
    pass

class SourceEvent(SourceBase):
    """Termelési esemény rekordja a forrás rendszerben."""
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

# --- KONSTANSOK ÉS BEÁLLÍTÁSOK ---
MACHINES = ["PM1", "PM2"]
ARTICLES = ["KL_150", "KL_175", "TL_100", "TL_140", "WTL_120", "FL_90"]
EVENT_INTERVAL_MINUTES = 15

STOP_REASONS = [
    "Tervezett karbantartás", "Anyaghiány", "Műszaki hiba",
    "Takarítás", "Kaparócsere", "Erőmű leállás", "Tekercsvágó hiba"
]

# --- IDŐTARTAM BEÁLLÍTÁSOK ---
START_DATE = date.today() - timedelta(days=365)
END_DATE = date.today()
NUM_DAYS = (END_DATE - START_DATE).days

@lru_cache(maxsize=None)
def load_planning_data_for_year(year: int) -> Optional[pd.DataFrame]:
    """Betölti és memóriában tartja az adott év tervezési adatait."""
    planning_file = settings.PLANNING_DIR / f"planning_{year}.xlsx"
    if planning_file.exists():
        return pd.concat(pd.read_excel(planning_file, sheet_name=None), ignore_index=True)
    return None

def get_day_planning(target_date: date, machine_id: str) -> Optional[pd.DataFrame]:
    """Lekéri az adott napra vonatkozó terveket az Excel fájlból."""
    df = load_planning_data_for_year(target_date.year)
    if df is None:
        return None
        
    day_plan = df[
        (df['Date'].dt.date == target_date) & 
        (df['Machine'] == machine_id)
    ]
    return day_plan

def generate_events_for_day(target_date: date, machine_id: str) -> List[SourceEvent]:
    """Generálja egy nap 24 órájának termelési eseményeit."""
    events = []
    current_time = datetime.combine(target_date, datetime.min.time())
    end_time = current_time + timedelta(days=1)

    day_plan = get_day_planning(target_date, machine_id)
    if day_plan is None or day_plan.empty:
        raise ValueError(f"HIBA: Nincs gyártási terv a(z) {machine_id} géphez a mai napon ({target_date})!")

    target_tons = float(day_plan['Target_Tons'].sum())
    planned_articles = day_plan['Article'].tolist()
    
    current_article = planned_articles[0]
    
    estimated_run_intervals = (24 * 60 / EVENT_INTERVAL_MINUTES) * 0.88
    base_weight_per_interval = float((target_tons * 1000) / estimated_run_intervals)
    
    while current_time < end_time:
        rand = random.random()
        
        if rand < 0.88:
            duration = EVENT_INTERVAL_MINUTES * 60
            status = "GOOD" if random.random() < 0.95 else "SCRAP"
            base_speed = random.uniform(750, 900)
            weight = base_weight_per_interval * random.uniform(0.9, 1.1)
            
            events.append(SourceEvent(
                timestamp=current_time, duration_seconds=duration,
                event_type="RUN", status=status, weight_kg=round(weight, 1),
                average_speed=round(base_speed, 1), machine_id=machine_id,
                article_id=current_article, description=None
            ))
            current_time += timedelta(seconds=duration)
            
        elif rand < 0.92:
            duration = random.randint(10, 45) * 60
            events.append(SourceEvent(
                timestamp=current_time, duration_seconds=duration,
                event_type="STOP", status=None, weight_kg=0, average_speed=0,
                machine_id=machine_id, article_id=None, description=random.choice(STOP_REASONS)
            ))
            current_time += timedelta(seconds=duration)
            
        else:
            duration = random.randint(5, 20) * 60
            events.append(SourceEvent(
                timestamp=current_time, duration_seconds=duration,
                event_type="BREAK", status=None, weight_kg=0, average_speed=0,
                machine_id=machine_id, article_id=None, description="Papírszakadás"
            ))
            current_time += timedelta(seconds=duration)
            
            if current_time < end_time:
                duration = EVENT_INTERVAL_MINUTES * 60
                events.append(SourceEvent(
                    timestamp=current_time, duration_seconds=duration,
                    event_type="RUN", status="SCRAP", weight_kg=round(random.uniform(200, 500), 1),
                    average_speed=round(random.uniform(400, 600), 1), machine_id=machine_id,
                    article_id=current_article, description="Felvezetés szakadás után"
                ))
                current_time += timedelta(seconds=duration)
        
        if len(planned_articles) > 1:
            slice_hours = 24 / len(planned_articles)
            article_index = min(int(current_time.hour / slice_hours), len(planned_articles) - 1)
            current_article = planned_articles[article_index]
    
    return events

def main() -> None:
    """Forrás adatbázis (MES) inicializálása és feltöltése."""
    print("\nEcoPaper Solutions - MES Esemény Szimulátor")
    print("-" * 50)
    
    print(f"Kapcsolódás a forrás (MES) szerverhez")
    source_engine = create_engine(settings.MES_DATABASE_URL)
    
    # Adatbázis resetelése
    SourceBase.metadata.drop_all(bind=source_engine)
    SourceBase.metadata.create_all(bind=source_engine)
    SourceSession = sessionmaker(bind=source_engine)
    
    all_events = []
    current_date = START_DATE
    while current_date <= END_DATE:
        for machine_id in MACHINES:
            all_events.extend(generate_events_for_day(current_date, machine_id))
        current_date += timedelta(days=1)
    
    print(f"{len(all_events)} esemény mentése folyamatban...")
    session = SourceSession()
    try:
        session.add_all(all_events)
        session.commit()
    finally:
        session.close()
    
    print(f"Kész! Forrás adatok mentve a MES SQL szerverre.")
    print("-" * 50 + "\n")

if __name__ == "__main__":
    main()
