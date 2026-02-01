#!/usr/bin/env python3
"""
MINTA ADAT GENERÁTOR (EXCEL)
============================
Létrehozza a teszteléshez szükséges Excel fájlokat (planning, lab_data, utilities).
Realistiches, ipari adatokkal tölti fel a rendszert a demózáshoz.
"""

import sys
import random
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Any

import pandas as pd

# Projekt gyökérkönyvtár hozzáadása a Python elérési úthoz
project_root: Path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings

def create_planning_data() -> None:
    """Termelési terv (planning.xlsx) létrehozása 30 napra."""
    
    print("📋 Terv (planning.xlsx) generálása...")
    
    data: Dict[str, List[Any]] = {
        'Date': [],
        'Machine': [],
        'Article': [],
        'Target_Speed': [],
        'Target_Tons': []
    }
    
    end_date: date = date.today()
    start_date: date = end_date - timedelta(days=30)
    machines: List[str] = ['PM1', 'PM2']
    
    # Termék specifikációk - reális sebesség és tonna célok
    article_specs: Dict[str, Dict[str, float]] = {
        'KL_150':   {'speed': 850,  'tons': 600},  
        'KL_175':   {'speed': 800,  'tons': 620},  
        'TL_100':   {'speed': 1100, 'tons': 1200}, 
        'TL_140':   {'speed': 1000, 'tons': 1300}, 
        'WTL_120':  {'speed': 1050, 'tons': 1250}, 
        'FL_90':    {'speed': 1200, 'tons': 1100}, 
    }
    articles = list(article_specs.keys())
    
    for day in range(31):
        current_date: date = start_date + timedelta(days=day)
        for machine in machines:
            # Naponta 2-4 különböző termék gyártása gépnélként
            num_articles = random.randint(2, 4)
            chosen_articles = random.sample(articles, num_articles)
            
            for i, article in enumerate(chosen_articles):
                specs = article_specs[article]
                # Kapacitás skálázás (PM2 nagyobb gép, mint a PM1)
                capacity = 0.95 if machine == 'PM1' else 1.05
                
                target_speed = round(specs['speed'] * capacity, 0)
                target_tons = round((specs['tons'] * capacity) / num_articles, 0)
                
                data['Date'].append(current_date)
                data['Machine'].append(machine)
                data['Article'].append(article)
                data['Target_Speed'].append(target_speed)
                data['Target_Tons'].append(target_tons)
    
    df = pd.DataFrame(data)
    file_path = settings.PLANNING_FILE
    df.to_excel(file_path, index=False)
    print(f"✅ Kész: {file_path} ({len(df)} sor)")

def create_lab_data() -> None:
    """Minőségi mérések (lab_data.xlsx) létrehozása 30 napra."""
    
    print("🔬 Minőségi adatok (lab_data.xlsx) generálása...")
    
    data: Dict[str, List[Any]] = {
        'Timestamp': [],
        'Machine': [],
        'Article': [],
        'Moisture_%': [],
        'GSM': [],
        'Strength_kNm': []
    }
    
    end_date = date.today()
    start_date_val = end_date - timedelta(days=30)
    start_date = datetime.combine(start_date_val, datetime.min.time())
    machines = ['PM1', 'PM2']
    
    # Cél minőségi paraméterek
    article_quality = {
        'KL_150':   {'gsm': 150, 'moisture': 6.5, 'strength': 5.5}, 
        'KL_175':   {'gsm': 175, 'moisture': 6.3, 'strength': 6.0}, 
        'TL_100':   {'gsm': 100, 'moisture': 7.5, 'strength': 4.0}, 
        'TL_140':   {'gsm': 140, 'moisture': 7.2, 'strength': 4.5}, 
        'WTL_120':  {'gsm': 120, 'moisture': 7.0, 'strength': 4.2}, 
        'FL_90':    {'gsm': 90,  'moisture': 7.8, 'strength': 3.5}, 
    }
    
    from sqlalchemy import create_engine, text
    source_db_path = settings.DATA_DIR / "source_events.db"
    engine = create_engine(f"sqlite:///{source_db_path}")
    
    for day in range(31):
        for machine in machines:
            # 2 óránkénti labor mérések
            for hour in range(0, 24, 2):
                minute_offset = random.randint(0, 10)
                timestamp = start_date + timedelta(days=day, hours=hour, minutes=minute_offset)
                
                # Valós gyártás lekérése a szimulált eseményekből
                with engine.connect() as conn:
                    query = text("SELECT article_id FROM events WHERE machine_id = :m AND timestamp <= :t ORDER BY timestamp DESC LIMIT 1")
                    res = conn.execute(query, {"m": machine, "t": timestamp}).scalar()
                    article = res if res else random.choice(list(article_quality.keys()))
                
                specs = article_quality.get(article, article_quality['TL_100'])
                
                # Reális mérési szórás (variáció) hozzáadása
                gsm = round(specs['gsm'] * random.uniform(0.97, 1.03), 1)
                moisture = round(specs['moisture'] * random.uniform(0.95, 1.05), 1)
                strength = round(specs['strength'] * random.uniform(0.95, 1.05), 1)
                
                data['Timestamp'].append(timestamp)
                data['Machine'].append(machine)
                data['Article'].append(article)
                data['Moisture_%'].append(moisture)
                data['GSM'].append(gsm)
                data['Strength_kNm'].append(strength)
    
    df = pd.DataFrame(data).sort_values('Timestamp')
    file_path = settings.LAB_DATA_FILE
    df.to_excel(file_path, index=False)
    print(f"✅ Kész: {file_path} ({len(df)} rekord)")

def create_utilities_data() -> None:
    """Közműfogyasztás (utilities.xlsx) létrehozása a termelés alapján."""
    
    print("⚡ Közműadatok (utilities.xlsx) generálása...")
    
    planning_file = settings.PLANNING_FILE
    if not planning_file.exists():
        create_planning_data()
    
    df_plan = pd.read_excel(planning_file)
    
    from sqlalchemy import create_engine, text
    source_db_path = settings.DATA_DIR / "source_events.db"
    engine = create_engine(f"sqlite:///{source_db_path}")
    
    data: Dict[str, List[Any]] = {
        'Date': [], 'Machine': [], 'Water_m3': [], 
        'Electricity_kWh': [], 'Steam_tons': [], 
        'Fiber_tons': [], 'Additives_kg': []
    }
    
    # Ipari fogyasztási benchmarkok gépenként
    targets = {
        'PM1': {'elec': 343.93, 'fiber_kg': 1095.0, 'steam': 4.39, 'water': 7.46},
        'PM2': {'elec': 367.00, 'fiber_kg': 1090.0, 'steam': 3.68, 'water': 7.10}
    }
    
    for _, row in df_plan.iterrows():
        machine = row['Machine']
        target_date = row['Date']
        
        # Tényleges termelés lekérése a szimulált eseményekből
        with engine.connect() as conn:
            query = text("SELECT SUM(weight_kg) FROM events WHERE machine_id = :m AND date(timestamp) = :d")
            res = conn.execute(query, {"m": machine, "d": target_date.strftime('%Y-%m-%d')}).scalar()
            actual_tons = (res / 1000.0) if res else row['Target_Tons']
        
        t_data = targets.get(machine, targets['PM1'])
        
        # Fogyasztási adatok skálázása a termelt tonnához
        fiber = round(actual_tons * (t_data['fiber_kg'] / 1000) * random.uniform(1.01, 1.03), 2)
        water = round(actual_tons * t_data['water'] * random.uniform(0.95, 1.05), 1)
        electricity = round(actual_tons * t_data['elec'] * random.uniform(0.98, 1.02), 0)
        steam = round(actual_tons * t_data['steam'] * random.uniform(0.97, 1.03), 2)
        additives = round(actual_tons * random.uniform(10, 15), 1)
        
        data['Date'].append(row['Date'])
        data['Machine'].append(machine)
        data['Water_m3'].append(water)
        data['Electricity_kWh'].append(electricity)
        data['Steam_tons'].append(steam)
        data['Fiber_tons'].append(fiber)
        data['Additives_kg'].append(additives)
    
    df = pd.DataFrame(data)
    file_path = settings.UTILITIES_FILE
    df.to_excel(file_path, index=False)
    print(f"✅ Kész: {file_path} ({len(df)} nap)")

def main():
    """Összes minta fájl generálása egy lépésben."""
    settings.DATA_DIR.mkdir(exist_ok=True)
    
    print("\n🏗️  EcoPaper Solutions - Minta Adat Generáló")
    print("-" * 50)
    
    # 1. Terv generálása
    create_planning_data()
    
    # 2. Események szimulálása (Ez az alapja a többinek)
    print("\n🔄 Termelési folyamat szimulálása (MES events)...")
    import subprocess
    subprocess.run(["python3", "scripts/simulate_events.py"], check=True)
    
    # 3. Labor és Közmű adatok generálása (a szimulált termeléshez igazítva)
    print("\n🧪 Labor és fogyasztási adatok szinkronizálása...")
    create_lab_data()
    create_utilities_data()
    
    print("-" * 50)
    print("✅ Összes minta fájl sikeresen létrehozva a data/ mappában!")
    print("🚀 Most már futtathatod az ETL pipeline-t:\n   python scripts/run_pipeline.py\n")

if __name__ == "__main__":
    main()
