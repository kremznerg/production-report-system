#!/usr/bin/env python3
"""
MINTA ADAT GENERÁTOR (EXCEL)
============================
Létrehozza a teszteléshez szükséges Excel fájlokat havi bontásban (planning, lab_data, utilities).
Realisztikus, ipari adatokkal tölti fel a rendszert a demózáshoz.
"""

import sys
import random
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Any
import pandas as pd
from sqlalchemy import create_engine, text
import subprocess

project_root: Path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings

SAMPLE_START_DATE: date = date.today() - timedelta(days=365)
SAMPLE_END_DATE: date = date.today()
NUM_DAYS: int = (SAMPLE_END_DATE - SAMPLE_START_DATE).days + 1
MACHINES: List[str] = ['PM1', 'PM2']

ARTICLE_SPECS: Dict[str, Dict[str, float]] = {
    'KL_150': {'speed': 850,  'tons': 600},  
    'KL_175': {'speed': 800,  'tons': 620},  
    'TL_100': {'speed': 1100, 'tons': 1200}, 
    'TL_140': {'speed': 1000, 'tons': 1300}, 
    'WTL_120':{'speed': 1050, 'tons': 1250}, 
    'FL_90':  {'speed': 1200, 'tons': 1100}, 
}

ARTICLE_QUALITY: Dict[str, Dict[str, float]] = {
    'KL_150': {'gsm': 150, 'moisture': 6.5, 'strength': 5.5}, 
    'KL_175': {'gsm': 175, 'moisture': 6.3, 'strength': 6.0}, 
    'TL_100': {'gsm': 100, 'moisture': 7.5, 'strength': 4.0}, 
    'TL_140': {'gsm': 140, 'moisture': 7.2, 'strength': 4.5}, 
    'WTL_120':{'gsm': 120, 'moisture': 7.0, 'strength': 4.2}, 
    'FL_90':  {'gsm': 90,  'moisture': 7.8, 'strength': 3.5}, 
}

MACHINE_TARGETS: Dict[str, Dict[str, float]] = {
    'PM1': {'elec': 343.93, 'fiber_kg': 1095.0, 'steam': 4.39, 'water': 7.46},
    'PM2': {'elec': 367.00, 'fiber_kg': 1090.0, 'steam': 3.68, 'water': 7.10}
}

engine = create_engine(settings.MES_DATABASE_URL)

def save_by_year_month(df: pd.DataFrame, prefix: str, date_col: str, out_dir: Path) -> None:
    """
    Kimenti a DataFramet fájlokba év szerinti bontásban, laponként hónapokkal, mappa struktúrában.
    pl. network_share/lab_data/lab_data_2026.xlsx, lap: 02
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    
    df['Year'] = pd.to_datetime(df[date_col]).dt.year
    df['Month'] = pd.to_datetime(df[date_col]).dt.strftime('%m')
    
    for year, year_df in df.groupby('Year'):
        file_path = out_dir / f"{prefix}_{year}.xlsx"
        
        mode = 'a' if file_path.exists() else 'w'
        if_sheet_exists = 'replace' if mode == 'a' else None
        
        with pd.ExcelWriter(file_path, engine='openpyxl', mode=mode, if_sheet_exists=if_sheet_exists) as writer:
            for month, month_df in year_df.groupby('Month'):
                out_df = month_df.drop(columns=['Year', 'Month'])
                out_df.to_excel(writer, sheet_name=month, index=False)

    df.drop(columns=['Year', 'Month'], inplace=True)
    print(f"A mintaadatok generálása sikeresen befejeződött: {prefix}")

def create_planning_data() -> None:
    """
    Gyártási terv adatok szimulálása és generálása.
    
    Létrehoz egy fiktív gyártási tervet (célsebesség, célmennyiség) 2025. januártól máig,
    amely papírgépekre (PM1, PM2) és cikkekre van lebontva, 
    majd ezeket Excel fájlokba menti.
    """
    print("Terv adatok generálása...")
    
    data: Dict[str, List[Any]] = {
        'Date': [], 'Machine': [], 'Article': [], 'Target_Speed': [], 'Target_Tons': []
    }
    
    articles = list(ARTICLE_SPECS.keys())
    
    for day in range(NUM_DAYS):
        current_date: date = SAMPLE_START_DATE + timedelta(days=day)
        for machine in MACHINES:
            num_articles = random.randint(2, 4)
            chosen_articles = random.sample(articles, num_articles)
            
            for i, article in enumerate(chosen_articles):
                specs = ARTICLE_SPECS[article]
                capacity = 0.95 if machine == 'PM1' else 1.05
                
                target_speed = round(specs['speed'] * capacity, 0)
                target_tons = round((specs['tons'] * capacity) / num_articles, 0)
                
                data['Date'].append(current_date)
                data['Machine'].append(machine)
                data['Article'].append(article)
                data['Target_Speed'].append(target_speed)
                data['Target_Tons'].append(target_tons)
    
    df = pd.DataFrame(data)
    save_by_year_month(df, 'planning', 'Date', settings.PLANNING_DIR)

def create_lab_data() -> None:
    """
    Laboratóriumi (minőségi) adatok szimulálása.
    
    Lekéri a tényleges termelési eseményeket az SQL adatbázisból, 
    és azok alapján generál véletlenszerű labor-méréseket (nedvesség, súly, szakítás)
    a megadott termék specifikációk alapján.
    """
    print("Minőségi adatok (lab_data) generálása...")
    
    data: Dict[str, List[Any]] = {
        'Timestamp': [], 'Machine': [], 'Article': [], 'Moisture_%': [], 'GSM': [], 'Strength_kNm': []
    }
    
    start_date = datetime.combine(SAMPLE_START_DATE, datetime.min.time())
        
    with engine.connect() as conn:
        q = text("SELECT machine_id, article_id, timestamp FROM events WHERE event_type='RUN'")
        events_df = pd.read_sql(q, conn)
    
    events_df['timestamp'] = pd.to_datetime(events_df['timestamp'])
    events_df.sort_values('timestamp', inplace=True)
    
    for day in range(NUM_DAYS):
        for machine in MACHINES:
            machine_events = events_df[events_df['machine_id'] == machine]
            
            for hour in range(0, 24, 2):
                timestamp = start_date + timedelta(days=day, hours=hour, minutes=random.randint(0, 10))
                past_events = machine_events[machine_events['timestamp'] <= timestamp]
                if not past_events.empty:
                    article = past_events.iloc[-1]['article_id']
                else:
                    article = random.choice(list(ARTICLE_QUALITY.keys()))
                
                specs = ARTICLE_QUALITY[article]
                
                data['Timestamp'].append(timestamp)
                data['Machine'].append(machine)
                data['Article'].append(article)
                data['Moisture_%'].append(round(specs['moisture'] * random.uniform(0.95, 1.05), 1))
                data['GSM'].append(round(specs['gsm'] * random.uniform(0.97, 1.03), 1))
                data['Strength_kNm'].append(round(specs['strength'] * random.uniform(0.95, 1.05), 1))
    
    df = pd.DataFrame(data).sort_values('Timestamp')
    save_by_year_month(df, 'lab_data', 'Timestamp', settings.LAB_DATA_DIR)

def create_utilities_data() -> None:
    """
    Közműfogyasztási adatok (víz, áram, gőz, alapanyag) szimulálása.
    
    A ténylegesen legyártott papírmennyiség (tonna) alapján számolja ki 
    a fajlagos közműfogyasztást gépenként, némi véletlenszerű ingadozással.
    """
    print("Közműadatok (utilities) generálása...")
    
    data: Dict[str, List[Any]] = {
        'Date': [], 'Machine': [], 'Water_m3': [], 
        'Electricity_kWh': [], 'Steam_tons': [], 
        'Fiber_tons': [], 'Additives_kg': []
    }
    
    for day in range(NUM_DAYS):
        current_date: date = SAMPLE_START_DATE + timedelta(days=day)
        for machine in MACHINES:
            with engine.connect() as conn:
                query = text("SELECT SUM(weight_kg) FROM events WHERE machine_id = :m AND date(timestamp) = :d")
                res = conn.execute(query, {"m": machine, "d": current_date.strftime('%Y-%m-%d')}).scalar()
                actual_tons = (res / 1000.0) if res else 0.0
            
            t_data = MACHINE_TARGETS[machine]
            
            data['Date'].append(current_date)
            data['Machine'].append(machine)
            data['Water_m3'].append(round(actual_tons * t_data['water'] * random.uniform(0.95, 1.05), 1))
            data['Electricity_kWh'].append(round(actual_tons * t_data['elec'] * random.uniform(0.98, 1.02), 0))
            data['Steam_tons'].append(round(actual_tons * t_data['steam'] * random.uniform(0.97, 1.03), 2))
            data['Fiber_tons'].append(round(actual_tons * (t_data['fiber_kg'] / 1000) * random.uniform(1.01, 1.03), 2))
            data['Additives_kg'].append(round(actual_tons * random.uniform(10, 15), 1))
    
    df = pd.DataFrame(data)
    save_by_year_month(df, 'utilities', 'Date', settings.UTILITIES_DIR)

def main():
    settings.DATA_DIR.mkdir(exist_ok=True)
    settings.NETWORK_SHARE_DIR.mkdir(parents=True, exist_ok=True)
    
    print("\nEcoPaper Solutions - Minta Adat Generáló")
    print("-" * 50)
    
    create_planning_data()
    
    print("\nTermelési folyamat szimulálása (MES events)...")
    subprocess.run(["python3", "scripts/simulate_events.py"], check=True)
    
    create_lab_data()
    create_utilities_data()
    
    print("-" * 50)
    print("Összes minta fájl sikeresen létrehozva a data/network_share/ mappában!")

if __name__ == "__main__":
    main()
