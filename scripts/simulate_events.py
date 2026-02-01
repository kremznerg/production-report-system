#!/usr/bin/env python3
"""
TERMELÉSI ESEMÉNY SZIMULÁTOR
============================
Létrehoz egy külön SQLite adatbázist (source_events.db), amely a gyári MES rendszert szimulálja.
Ez az alapvető forrása a termelési eseményeknek (RUN, STOP, BREAK).
Realistiches 30 napos gyártási naplót generál.
"""

import sys
import os
from pathlib import Path
import random
import pandas as pd
from datetime import datetime, timedelta

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
    "Érzékelő tisztítás", "Hengercsere", "Szárító beállítás"
]

PLANNING_DATA = None

def get_day_planning(target_date, machine_id):
    """Lekéri az adott napra vonatkozó terveket az Excel fájlból."""
    global PLANNING_DATA
    if PLANNING_DATA is None:
        planning_file = settings.PLANNING_FILE
        if planning_file.exists():
            PLANNING_DATA = pd.read_excel(planning_file)
        else:
            return None
    
    day_plan = PLANNING_DATA[
        (PLANNING_DATA['Date'].dt.date == target_date) & 
        (PLANNING_DATA['Machine'] == machine_id)
    ]
    return day_plan

def generate_events_for_day(target_date, machine_id):
    """Generálja egy nap 24 órájának termelési eseményeit."""
    events = []
    current_time = datetime.combine(target_date, datetime.min.time())
    end_time = current_time + timedelta(days=1)

    day_plan = get_day_planning(target_date, machine_id)
    if day_plan is not None and not day_plan.empty:
        target_tons = day_plan['Target_Tons'].sum()
        planned_articles = day_plan['Article'].tolist()
    else:
        target_tons = random.uniform(100, 150)
        planned_articles = [random.choice(ARTICLES)]
    
    current_article = planned_articles[0]
    
    # Súly kalkuláció skálázása a napi célhoz (approx. 88% uptime-al számolva)
    estimated_run_intervals = (24 * 60 / EVENT_INTERVAL_MINUTES) * 0.88
    base_weight_per_interval = (target_tons * 1000) / estimated_run_intervals
    
    while current_time < end_time:
        rand = random.random()
        
        if rand < 0.88:
            # --- RUN (NORMÁL ÜZEM - 88%) ---
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
            # --- STOP (TERVEZETT/MŰSZAKI ÁLLÁS - 4%) ---
            duration = random.randint(10, 45) * 60
            events.append(SourceEvent(
                timestamp=current_time, duration_seconds=duration,
                event_type="STOP", status=None, weight_kg=0, average_speed=0,
                machine_id=machine_id, article_id=None, description=random.choice(STOP_REASONS)
            ))
            current_time += timedelta(seconds=duration)
            
        else:
            # --- BREAK (PAPÍRSZAKADÁS - 8%) ---
            duration = random.randint(5, 20) * 60
            events.append(SourceEvent(
                timestamp=current_time, duration_seconds=duration,
                event_type="BREAK", status=None, weight_kg=0, average_speed=0,
                machine_id=machine_id, article_id=None, description="Papírszakadás"
            ))
            current_time += timedelta(seconds=duration)
            
            # Szakadás után mindig van egy kis SCRAP termelés (újrabevezetés)
            if current_time < end_time:
                duration = EVENT_INTERVAL_MINUTES * 60
                events.append(SourceEvent(
                    timestamp=current_time, duration_seconds=duration,
                    event_type="RUN", status="SCRAP", weight_kg=round(random.uniform(200, 500), 1),
                    average_speed=round(random.uniform(400, 600), 1), machine_id=machine_id,
                    article_id=current_article, description="Újraindulás szakadás után"
                ))
                current_time += timedelta(seconds=duration)
        
        # Termék váltás a nap során a terv alapján
        if len(planned_articles) > 1:
            slice_hours = 24 / len(planned_articles)
            article_index = min(int(current_time.hour / slice_hours), len(planned_articles) - 1)
            current_article = planned_articles[article_index]
    
    return events

def main():
    """Forrás adatbázis (MES) inicializálása és feltöltése."""
    print("\n🏭 EcoPaper Solutions - MES Esemény Szimulátor")
    print("-" * 50)
    
    source_db_path = settings.DATA_DIR / "source_events.db"
    if source_db_path.exists():
        print(f"🗑️  Régi forrás DB törlése: {source_db_path}")
        os.remove(source_db_path)
    
    source_engine = create_engine(f"sqlite:///{source_db_path}")
    SourceBase.metadata.create_all(bind=source_engine)
    SourceSession = sessionmaker(bind=source_engine)
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    all_events = []
    current_date = start_date
    while current_date <= end_date:
        for machine_id in MACHINES:
            all_events.extend(generate_events_for_day(current_date, machine_id))
        current_date += timedelta(days=1)
    
    print(f"🔄 {len(all_events)} esemény mentése folyamatban...")
    session = SourceSession()
    try:
        session.add_all(all_events)
        session.commit()
    finally:
        session.close()
    
    print(f"✅ Kész! Forrás adatok mentve ide: {source_db_path}")
    print("-" * 50 + "\n")

if __name__ == "__main__":
    main()
