#!/usr/bin/env python3
"""
Create sample Excel files for testing the ETL pipeline.
Run this after initializing the database to have demo data.
"""

import sys
import random
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Any

import pandas as pd

# Add project root to Python path
project_root: Path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings


def create_planning_data() -> None:
    """Create planning.xlsx with 30 days of sample production plan data."""
    
    data: Dict[str, List[Any]] = {
        'Date': [],
        'Machine': [],
        'Article': [],
        'Target_Speed': [],
        'Target_Tons': []
    }
    
    # Generate 31 days of data ending today (inclusive)
    end_date: date = date.today()
    start_date: date = end_date - timedelta(days=30)
    machines: List[str] = ['PM1', 'PM2']
    
    # Article specs - scaled to meet daily production targets
    # PM1 (33) target: ~590 t/day | PM2 (35) target: ~1370 t/day
    article_specs: Dict[str, Dict[str, float]] = {
        'KL_150':   {'gsm': 150, 'speed': 850,  'tons': 600},  
        'KL_175':   {'gsm': 175, 'speed': 800,  'tons': 620},  
        'TL_100':   {'gsm': 100, 'speed': 1100, 'tons': 1200}, 
        'TL_140':   {'gsm': 140, 'speed': 1000, 'tons': 1300}, 
        'WTL_120':  {'gsm': 120, 'speed': 1050, 'tons': 1250}, 
        'FL_90':    {'gsm': 90,  'speed': 1200, 'tons': 1100}, 
    }
    articles: List[str] = list(article_specs.keys())
    
    # Machine capacity scaling to reach the specific targets
    machine_capacity: Dict[str, float] = {
        'PM1': 0.95,   # Aims for ~590t (weighted avg of articles)
        'PM2': 1.05    # Aims for ~1350t (weighted avg of articles)
    }
    
    for day in range(31):
        current_date: date = start_date + timedelta(days=day)
        
        for machine in machines:
            # 2 to 4 distinct articles per day
            num_articles = random.randint(2, 4)
            chosen_articles = random.sample(articles, num_articles)
            
            for i, article in enumerate(chosen_articles):
                specs: Dict[str, float] = article_specs[article]
                capacity: float = machine_capacity[machine]
                
                # Split targets among articles
                target_speed: float = round(specs['speed'] * capacity, 0)
                target_tons: float = round((specs['tons'] * capacity) / num_articles, 0)
                
                data['Date'].append(current_date)
                data['Machine'].append(machine)
                data['Article'].append(article)
                data['Target_Speed'].append(target_speed)
                data['Target_Tons'].append(target_tons)
    
    df: pd.DataFrame = pd.DataFrame(data)
    
    file_path: Path = settings.PLANNING_FILE
    df.to_excel(file_path, index=False)
    print(f"✅ Created: {file_path}")
    print(f"   - {len(df)} planning records (30 days × 2 machines)")


def create_lab_data() -> None:
    """Create lab_data.xlsx with 30 days of realistic quality measurements."""
    
    data: Dict[str, List[Any]] = {
        'Timestamp': [],
        'Machine': [],
        'Article': [],
        'Moisture_%': [],
        'GSM': [],
        'Strength_kNm': []
    }
    
    end_date: date = date.today()
    start_date_val: date = end_date - timedelta(days=30)
    start_date: datetime = datetime.combine(start_date_val, datetime.min.time())
    machines: List[str] = ['PM1', 'PM2']
    
    # Quality specs per article (GSM is nominal, with measurement variation)
    article_quality: Dict[str, Dict[str, float]] = {
        'KL_150':   {'gsm': 150, 'moisture': 6.5, 'strength': 5.5}, 
        'KL_175':   {'gsm': 175, 'moisture': 6.3, 'strength': 6.0}, 
        'TL_100':   {'gsm': 100, 'moisture': 7.5, 'strength': 4.0}, 
        'TL_140':   {'gsm': 140, 'moisture': 7.2, 'strength': 4.5}, 
        'WTL_120':  {'gsm': 120, 'moisture': 7.0, 'strength': 4.2}, 
        'FL_90':    {'gsm': 90,  'moisture': 7.8, 'strength': 3.5}, 
    }
    
    # Connect to MES DB to find out what was REALLY running at a given time
    from sqlalchemy import create_engine, text
    source_db_path = settings.DATA_DIR / "source_events.db"
    if not source_db_path.exists():
        print("⚠️ Source events DB missing. Lab data might be inaccurate.")
        # We assume simulate_events.py will be run before this
    
    engine = create_engine(f"sqlite:///{source_db_path}")
    
    for day in range(31):
        for machine in machines:
            # Exact 2-hour intervals (0, 2, 4, ..., 22)
            for hour in range(0, 24, 2):
                # Small variation in timing (+/- 5 minutes) for realism
                minute_offset: int = random.randint(0, 10)
                timestamp: datetime = start_date + timedelta(days=day, hours=hour, minutes=minute_offset)
                
                # LOOKUP article from MES DB for this specific time
                with engine.connect() as conn:
                    query = text("SELECT article_id FROM events WHERE machine_id = :m AND timestamp <= :t ORDER BY timestamp DESC LIMIT 1")
                    res = conn.execute(query, {"m": machine, "t": timestamp}).scalar()
                    article = res if res else random.choice(list(article_quality.keys()))
                
                specs: Dict[str, float] = article_quality.get(article, article_quality['TL_100'])
                
                # Add realistic measurement variation
                gsm: float = round(specs['gsm'] * random.uniform(0.97, 1.03), 1)
                moisture: float = round(specs['moisture'] * random.uniform(0.95, 1.05), 1)
                strength: float = round(specs['strength'] * random.uniform(0.95, 1.05), 1)
                
                data['Timestamp'].append(timestamp)
                data['Machine'].append(machine)
                data['Article'].append(article)
                data['Moisture_%'].append(moisture)
                data['GSM'].append(gsm)
                data['Strength_kNm'].append(strength)
    
    df: pd.DataFrame = pd.DataFrame(data)
    df = df.sort_values('Timestamp').reset_index(drop=True)  # Sort by timestamp
    
    file_path: Path = settings.LAB_DATA_FILE
    df.to_excel(file_path, index=False)
    print(f"✅ Created: {file_path}")
    print(f"   - {len(df)} quality measurements (31 days, 12 per day per machine)")


def create_utilities_data() -> None:
    """Create utilities.xlsx with 30 days of realistic utility consumption data."""
    
    # Read planning data to get realistic production tons for scaling
    planning_file = settings.PLANNING_FILE
    if not planning_file.exists():
        create_planning_data()
    
    df_plan = pd.read_excel(planning_file)
    
    # Connect to source events to get ACTUAL production for scaling
    from sqlalchemy import create_engine, func
    from sqlalchemy.orm import sessionmaker
    source_db_path = settings.DATA_DIR / "source_events.db"
    engine = create_engine(f"sqlite:///{source_db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    data: Dict[str, List[Any]] = {
        'Date': [],
        'Machine': [],
        'Water_m3': [],
        'Electricity_kWh': [],
        'Steam_tons': [],
        'Fiber_tons': [],
        'Additives_kg': []
    }
    
    # Industry targets for Machines
    targets = {
        'PM1': {'elec': 343.93, 'fiber_kg': 1095.0, 'steam': 4.39, 'water': 7.46},
        'PM2': {'elec': 367.00, 'fiber_kg': 1090.0, 'steam': 3.68, 'water': 7.10}
    }
    
    for _, row in df_plan.iterrows():
        machine = row['Machine']
        target_date = row['Date']
        
        # Get actual tons from source DB for this machine and day
        # We need to sum weight_kg from the 'events' table
        from sqlalchemy import text
        query = text("SELECT SUM(weight_kg) FROM events WHERE machine_id = :m AND date(timestamp) = :d")
        result = session.execute(query, {"m": machine, "d": target_date.strftime('%Y-%m-%d')}).scalar()
        actual_tons = (result / 1000.0) if result else row['Target_Tons']
        
        t_data = targets.get(machine, targets['PM1'])
        
        # Fiber: conversion from kg/t to absolute tons (target ~1.09-1.10)
        # MUST BE BASED ON ACTUAL PRODUCTION TO BE > 1 t/t
        fiber = round(actual_tons * (t_data['fiber_kg'] / 1000) * random.uniform(1.01, 1.03), 2)
        
        # Water: target m3/t
        water = round(actual_tons * t_data['water'] * random.uniform(0.95, 1.05), 1)
        
        # Electricity: target kWh/t
        electricity = round(actual_tons * t_data['elec'] * random.uniform(0.98, 1.02), 0)
        
        # Steam: target t/t
        steam = round(actual_tons * t_data['steam'] * random.uniform(0.97, 1.03), 2)
        
        # Additives: ~12 kg per ton (generic)
        additives = round(actual_tons * random.uniform(10, 15), 1)
        
        data['Date'].append(row['Date'])
        data['Machine'].append(machine)
        data['Water_m3'].append(water)
        data['Electricity_kWh'].append(electricity)
        data['Steam_tons'].append(steam)
        data['Fiber_tons'].append(fiber)
        data['Additives_kg'].append(additives)
    
    session.close()
    df = pd.DataFrame(data)
    
    file_path: Path = settings.UTILITIES_FILE
    df.to_excel(file_path, index=False)
    print(f"✅ Created: {file_path}")
    print(f"   - {len(df)} utility records (scaled to production tons)")


def main() -> None:
    """Create all sample Excel files."""
    
    # Ensure data directory exists
    settings.DATA_DIR.mkdir(exist_ok=True)
    
    print("📊 Creating sample Excel files...")
    print(f"Data directory: {settings.DATA_DIR}\n")
    
    create_planning_data()
    
    # NEW STEP: Run event simulation BEFORE lab/utilities to have a reference
    print("\n🔄 Simulating MES events (source_events.db)...")
    import subprocess
    subprocess.run(["python3", "scripts/simulate_events.py"], check=True)
    
    print("\n🧪 Generating lab and utility data based on actual production...")
    create_lab_data()
    create_utilities_data()
    
    print("\n✅ All sample files created successfully!")
    print("\nYou can now run the ETL pipeline:")
    print("  python scripts/run_pipeline.py")


if __name__ == "__main__":
    main()
