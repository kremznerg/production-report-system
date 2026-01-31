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

def inspect_db():
    """Lekérdezi az adatbázis aktuális tartalmát és kiírja a konzolra."""
    print("\n" + "="*60)
    print("  ADATBÁZIS TARTALOM ELLENŐRZÉSE")
    print("="*60)
    
    with get_db() as db:
        # Gépek
        machine_count = db.query(MachineDB).count()
        print(f"\n🔧 Gépek (Machines): {machine_count}")
        for m in db.query(MachineDB).all():
            print(f"   - {m.id}: {m.name}")
            
        # Cikkek
        article_count = db.query(ArticleDB).count()
        print(f"\n📦 Termékek (Articles): {article_count}")
        for a in db.query(ArticleDB).limit(10).all():
            print(f"   - {a.id}: {a.name}")
            
        # Tervezés
        plan_count = db.query(ProductionPlanDB).count()
        print(f"\n📋 Tervezési adatok (Planning): {plan_count} rekord")
        if plan_count > 0:
            latest = db.query(ProductionPlanDB).order_by(ProductionPlanDB.date.desc()).first()
            print(f"   Legutóbbi: {latest.date} - {latest.machine_id} - {latest.article_id}")

        # Minőség
        quality_count = db.query(QualityDataDB).count()
        print(f"\n🔬 Minőségi adatok (Quality): {quality_count} rekord")
        if quality_count > 0:
            latest = db.query(QualityDataDB).order_by(QualityDataDB.timestamp.desc()).first()
            print(f"   Legutóbbi: {latest.timestamp} - {latest.machine_id}")

        # Közművek
        util_count = db.query(UtilityConsumptionDB).count()
        print(f"\n⚡ Közműadatok (Utilities): {util_count} rekord")
        if util_count > 0:
            latest = db.query(UtilityConsumptionDB).order_by(UtilityConsumptionDB.date.desc()).first()
            print(f"   Legutóbbi: {latest.date} - {latest.machine_id}")

        # Production Events
        from src.models import ProductionEventDB
        event_count = db.query(ProductionEventDB).count()
        run_count = db.query(ProductionEventDB).filter(ProductionEventDB.event_type == "RUN").count()
        stop_count = db.query(ProductionEventDB).filter(ProductionEventDB.event_type == "STOP").count()
        print(f"\n🏭 Termelési események (Events): {event_count} rekord")
        print(f"   RUN (Gyártás): {run_count} | STOP (Leállás): {stop_count}")

        # Daily Summaries
        from src.models import DailySummaryDB
        summary_count = db.query(DailySummaryDB).count()
        print(f"\n📊 Napi összesítők (Daily Summaries): {summary_count} rekord")
        if summary_count > 0:
            latest = db.query(DailySummaryDB).order_by(DailySummaryDB.date.desc()).first()
            print(f"   Legutóbbi: {latest.date} - {latest.machine_id}")
            print(f"   - OEE: {latest.oee_pct}% | Termelés: {latest.total_tons} t / Terv: {latest.target_tons} t")
            print(f"   - Állásidő: {latest.total_downtime_min} perc | Szakadások: {latest.break_count} db")
            print(f"   - Minőség: Nedvesség {latest.avg_moisture_pct}% | Súly: {latest.avg_gsm_measured} gsm")
            print(f"   - Fajlagos Rost: {latest.spec_fiber_t_t} t/t | Fajlagos Áram: {latest.spec_electricity_kwh_t} kWh/t")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    inspect_db()
