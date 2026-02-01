#!/usr/bin/env python3
"""
ADATBÁZIS INSPEKTOR
====================
Segédeszköz az adatbázis tartalmának gyors áttekintéséhez.
Megjeleníti az összes tábla rekordszámát, a legfrissebb adatokat és a főbb mutatókat.
"""

import sys
from pathlib import Path

# Projekt gyökérkönyvtár hozzáadása a Python elérési úthoz
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.database import get_db
from src.models import (
    MachineDB, ArticleDB, ProductionPlanDB, 
    QualityDataDB, UtilityConsumptionDB, 
    ProductionEventDB, DailySummaryDB
)

def inspect_db():
    """Lekérdezi az adatbázis aktuális állapotát és strukturált formában kiírja a konzolra."""
    
    print("\n" + "═"*60)
    print(" 🛠️  ECOPAPER SOLUTIONS - ADATBÁZIS ELLENŐRZÉS")
    print("═"*60)
    
    with get_db() as db:
        # 1. Törzsdatok
        machine_count = db.query(MachineDB).count()
        print(f"\n🏭 GÉPEK (Machines): {machine_count}")
        for m in db.query(MachineDB).all():
            print(f"   • {m.id}: {m.name} ({m.location})")
            
        article_count = db.query(ArticleDB).count()
        print(f"\n📦 TERMÉKEK (Articles): {article_count}")
        for a in db.query(ArticleDB).limit(5).all():
            print(f"   • {a.id}: {a.name} ({a.nominal_gsm} gsm)")
        if article_count > 5:
            print(f"   ... és további {article_count - 5} termék")
            
        # 2. Ütemezés és Input adatok
        plan_count = db.query(ProductionPlanDB).count()
        print(f"\n📋 TERVEZÉSI ADATOK (Planning): {plan_count} rekord")
        if plan_count > 0:
            latest = db.query(ProductionPlanDB).order_by(ProductionPlanDB.date.desc()).first()
            print(f"   ℹ️ Legutóbbi terv dátuma: {latest.date}")

        # 3. Mért adatok
        quality_count = db.query(QualityDataDB).count()
        print(f"\n🔬 MINŐSÉGI ADATOK (Quality): {quality_count} rekord")
        
        util_count = db.query(UtilityConsumptionDB).count()
        print(f"\n⚡ KÖZMŰADATOK (Utilities): {util_count} rekord")

        # 4. Termelési Események (MES adatok)
        event_count = db.query(ProductionEventDB).count()
        run_count = db.query(ProductionEventDB).filter(ProductionEventDB.event_type == "RUN").count()
        stop_count = db.query(ProductionEventDB).filter(ProductionEventDB.event_type == "STOP").count()
        print(f"\n🏭 ESEMÉNYNAPLÓ (Events): {event_count} rekord")
        print(f"   🟢 RUN (Gyártás): {run_count} | 🔴 STOP (Leállás): {stop_count}")

        # 5. Összesített eredmények (Dashboard alapja)
        summary_count = db.query(DailySummaryDB).count()
        print(f"\n📊 NAPI ÖSSZESÍTŐK (Daily Summaries): {summary_count} rekord")
        if summary_count > 0:
            latest = db.query(DailySummaryDB).order_by(DailySummaryDB.date.desc()).first()
            print("─" * 60)
            print(f" 🚩 LEGUTÓBBI RIAPORT ADATAI ({latest.date} | {latest.machine_id})")
            print(f"   • OEE Mutató: {latest.oee_pct}%")
            print(f"   • Termelés: {latest.total_tons:.1f} t (Terv: {latest.target_tons:.1f} t)")
            print(f"   • Állásidő: {latest.total_downtime_min} perc | Szakadások: {latest.break_count} db")
            print(f"   • Átlagos nedvesség: {latest.avg_moisture_pct}%")
            print(f"   • Fajlagos rost: {latest.spec_fiber_t_t:.2f} t/t")
            print("─" * 60)
    
    print("\n" + "═" * 60 + "\n")

if __name__ == "__main__":
    inspect_db()
