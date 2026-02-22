#!/usr/bin/env python3
"""
MINTA ADAT GENERÁTOR (EXCEL)
============================
Létrehozza a teszteléshez szükséges Excel fájlokat havi bontásban (planning, lab_data, utilities).
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

def save_by_year_month(df: pd.DataFrame, prefix: str, date_col: str, out_dir: Path):
    """
    Kimenti a DataFramet fájlokba év szerinti bontásban, fülönkénti (sheet) hónapokkal, mappa struktúrában.
    pl. network_share/lab_data/2026.xlsx, sheet: 02
    """
    # Mappa létrehozása a típusnak megfelelően
    out_dir.mkdir(parents=True, exist_ok=True)
    
    df['Year'] = pd.to_datetime(df[date_col]).dt.year
    df['Month'] = pd.to_datetime(df[date_col]).dt.strftime('%m')
    
    for year, year_df in df.groupby('Year'):
        file_path = out_dir / f"{prefix}_{year}.xlsx"
        
        # Ha létezik a fájl, meg kell tartani a korábbi füleket (amit most nem írunk felül)
        existing_sheets = {}
        if file_path.exists():
            with pd.ExcelFile(file_path) as xls:
                for sheet_name in xls.sheet_names:
                    existing_sheets[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name)
                    
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            for month, month_df in year_df.groupby('Month'):
                # Töröljük a temp oszlopokat
                out_df = month_df.drop(columns=['Year', 'Month'])
                out_df.to_excel(writer, sheet_name=month, index=False)
                existing_sheets[month] = out_df  # frissítjük az éppen írt füllel
                
            # Visszaírjuk azokat a lapokat is, mik nem frissültek (pl. korábbi hónapok)
            for sheet_name, sheet_df in existing_sheets.items():
                if sheet_name not in year_df['Month'].unique():
                    try:
                        sheet_df.drop(columns=['Year', 'Month'], inplace=True, errors='ignore')
                    except Exception:
                        pass
                    sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

    df.drop(columns=['Year', 'Month'], inplace=True)
    print(f"✅ Kész as hálózati mappában (év/hónap bontás): {prefix}")

def create_planning_data() -> None:
    print("📋 Terv (planning) generálása...")
    
    data: Dict[str, List[Any]] = {
        'Date': [], 'Machine': [], 'Article': [], 'Target_Speed': [], 'Target_Tons': []
    }
    
    end_date: date = date.today()
    start_date: date = date(2025, 1, 1)
    machines: List[str] = ['PM1', 'PM2']
    
    article_specs: Dict[str, Dict[str, float]] = {
        'KL_150': {'speed': 850,  'tons': 600},  
        'KL_175': {'speed': 800,  'tons': 620},  
        'TL_100': {'speed': 1100, 'tons': 1200}, 
        'TL_140': {'speed': 1000, 'tons': 1300}, 
        'WTL_120':{'speed': 1050, 'tons': 1250}, 
        'FL_90':  {'speed': 1200, 'tons': 1100}, 
    }
    articles = list(article_specs.keys())
    
    num_days = (end_date - start_date).days + 1
    for day in range(num_days):
        current_date: date = start_date + timedelta(days=day)
        for machine in machines:
            num_articles = random.randint(2, 4)
            chosen_articles = random.sample(articles, num_articles)
            
            for i, article in enumerate(chosen_articles):
                specs = article_specs[article]
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
    print("🔬 Minőségi adatok (lab_data) generálása...")
    
    data: Dict[str, List[Any]] = {
        'Timestamp': [], 'Machine': [], 'Article': [], 'Moisture_%': [], 'GSM': [], 'Strength_kNm': []
    }
    
    end_date = date.today()
    start_date_val = date(2025, 1, 1)
    start_date = datetime.combine(start_date_val, datetime.min.time())
    machines = ['PM1', 'PM2']
    
    article_quality = {
        'KL_150': {'gsm': 150, 'moisture': 6.5, 'strength': 5.5}, 
        'KL_175': {'gsm': 175, 'moisture': 6.3, 'strength': 6.0}, 
        'TL_100': {'gsm': 100, 'moisture': 7.5, 'strength': 4.0}, 
        'TL_140': {'gsm': 140, 'moisture': 7.2, 'strength': 4.5}, 
        'WTL_120':{'gsm': 120, 'moisture': 7.0, 'strength': 4.2}, 
        'FL_90':  {'gsm': 90,  'moisture': 7.8, 'strength': 3.5}, 
    }
    
    from sqlalchemy import create_engine, text
    engine = create_engine(settings.MES_DATABASE_URL)
    
    with engine.connect() as conn:
        q = text("SELECT machine_id, article_id, timestamp FROM events WHERE event_type='RUN'")
        events_df = pd.read_sql(q, conn)
    
    events_df['timestamp'] = pd.to_datetime(events_df['timestamp'])
    events_df.sort_values('timestamp', inplace=True)
    
    num_days = (end_date - start_date_val).days + 1
    for day in range(num_days):
        for machine in machines:
            machine_events = events_df[events_df['machine_id'] == machine]
            
            for hour in range(0, 24, 2):
                timestamp = start_date + timedelta(days=day, hours=hour, minutes=random.randint(0, 10))
                
                # Találjuk meg a legutóbbi terméket
                past_events = machine_events[machine_events['timestamp'] <= timestamp]
                if not past_events.empty:
                    article = past_events.iloc[-1]['article_id']
                else:
                    article = random.choice(list(article_quality.keys()))
                
                specs = article_quality.get(article, article_quality['TL_100'])
                
                data['Timestamp'].append(timestamp)
                data['Machine'].append(machine)
                data['Article'].append(article)
                data['Moisture_%'].append(round(specs['moisture'] * random.uniform(0.95, 1.05), 1))
                data['GSM'].append(round(specs['gsm'] * random.uniform(0.97, 1.03), 1))
                data['Strength_kNm'].append(round(specs['strength'] * random.uniform(0.95, 1.05), 1))
    
    df = pd.DataFrame(data).sort_values('Timestamp')
    save_by_year_month(df, 'lab_data', 'Timestamp', settings.LAB_DATA_DIR)

def create_utilities_data() -> None:
    print("⚡ Közműadatok (utilities) generálása...")
    
    # Közmű generáláshoz előbb tervezés adataiból szedjük a dátumokat - a legegyszerűbb futtatni a readert
    # vagy csak ugyanazokat generáljuk mint eddig.
    end_date: date = date.today()
    start_date: date = date(2025, 1, 1)
    
    from sqlalchemy import create_engine, text
    engine = create_engine(settings.MES_DATABASE_URL)
    
    data: Dict[str, List[Any]] = {
        'Date': [], 'Machine': [], 'Water_m3': [], 
        'Electricity_kWh': [], 'Steam_tons': [], 
        'Fiber_tons': [], 'Additives_kg': []
    }
    
    targets = {
        'PM1': {'elec': 343.93, 'fiber_kg': 1095.0, 'steam': 4.39, 'water': 7.46},
        'PM2': {'elec': 367.00, 'fiber_kg': 1090.0, 'steam': 3.68, 'water': 7.10}
    }

    num_days = (end_date - start_date).days + 1
    for day in range(num_days):
        current_date: date = start_date + timedelta(days=day)
        for machine in ['PM1', 'PM2']:
            with engine.connect() as conn:
                query = text("SELECT SUM(weight_kg) FROM events WHERE machine_id = :m AND date(timestamp) = :d")
                res = conn.execute(query, {"m": machine, "d": current_date.strftime('%Y-%m-%d')}).scalar()
                actual_tons = (res / 1000.0) if res else random.uniform(500, 1000)
            
            t_data = targets.get(machine, targets['PM1'])
            
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
    
    print("\n🏗️ EcoPaper Solutions - Minta Adat Generáló")
    print("-" * 50)
    
    create_planning_data()
    
    # 2. Események szimulálása
    print("\n🔄 Termelési folyamat szimulálása (MES events)...")
    import subprocess
    subprocess.run(["python3", "scripts/simulate_events.py"], check=True)
    
    create_lab_data()
    create_utilities_data()
    
    print("-" * 50)
    print("✅ Összes minta fájl sikeresen létrehozva a data/network_share/ mappában!")

if __name__ == "__main__":
    main()
