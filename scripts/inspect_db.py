#!/usr/bin/env python3
"""
Adatbázis tartalmának ellenőrzése.
Megjeleníti az összes tábla rekordszámát és néhány példát.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.database import get_db
from src.models import (
    MachineDB,
    ArticleDB,
    ProductionPlanDB,
    QualityDataDB,
    UtilityConsumptionDB
)

def inspect_database():
    """Megjeleníti az adatbázis tartalmát."""
    print("\n" + "="*60)
    print("  ADATBÁZIS TARTALOM")
    print("="*60 + "\n")
    
    with get_db() as db:
        # Gépek
        machines = db.query(MachineDB).all()
        print(f"🔧 Gépek (Machines): {len(machines)}")
        for machine in machines:
            print(f"   - {machine.id}: {machine.name}")
        
        # Cikkek
        articles = db.query(ArticleDB).all()
        print(f"\n📦 Cikkek (Articles): {len(articles)}")
        for article in articles:
            print(f"   - {article.id}: {article.name}")
        
        # Tervezési adatok
        planning_count = db.query(ProductionPlanDB).count()
        print(f"\n📋 Tervezési adatok (Planning): {planning_count} rekord")
        if planning_count > 0:
            latest = db.query(ProductionPlanDB).order_by(ProductionPlanDB.date.desc()).first()
            print(f"   Legutóbbi: {latest.date} - {latest.machine_id} - {latest.article_id}")
        
        # Minőségi adatok
        quality_count = db.query(QualityDataDB).count()
        print(f"\n🔬 Minőségi adatok (Quality): {quality_count} rekord")
        if quality_count > 0:
            latest = db.query(QualityDataDB).order_by(QualityDataDB.timestamp.desc()).first()
            print(f"   Legutóbbi: {latest.timestamp} - {latest.machine_id}")
        
        # Közműadatok
        utility_count = db.query(UtilityConsumptionDB).count()
        print(f"\n⚡ Közműadatok (Utilities): {utility_count} rekord")
        if utility_count > 0:
            latest = db.query(UtilityConsumptionDB).order_by(UtilityConsumptionDB.date.desc()).first()
            print(f"   Legutóbbi: {latest.date} - {latest.machine_id}")
        
        # Production Events
        from src.models import ProductionEventDB
        event_count = db.query(ProductionEventDB).count()
        print(f"\n🏭 Termelési események (Events): {event_count} rekord")
        if event_count > 0:
            run_count = db.query(ProductionEventDB).filter(ProductionEventDB.event_type == "RUN").count()
            stop_count = db.query(ProductionEventDB).filter(ProductionEventDB.event_type == "STOP").count()
            break_count = db.query(ProductionEventDB).filter(ProductionEventDB.event_type == "BREAK").count()
            print(f"   RUN: {run_count} | STOP: {stop_count} | BREAK: {break_count}")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    inspect_database()
