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

def inspect_db() -> None:
    """Lekérdezi az adatbázis aktuális állapotát és strukturált formában kiírja a konzolra."""
    
    print("\n" + "═"*60)
    print("ECOPAPER SOLUTIONS - ADATBÁZIS ELLENŐRZÉS")
    print("═"*60)
    
    with get_db() as db:
        try:
            machine_count = db.query(MachineDB).count()
            print(f"\nGÉPEK (Machines): {machine_count}")
            for m in db.query(MachineDB).all():
                print(f"{m.id}: {m.name} ({m.location})")
                
            article_count = db.query(ArticleDB).count()
            print(f"\nTERMÉKEK (Articles): {article_count}")
            for a in db.query(ArticleDB).all():
                print(f"{a.id}: {a.name} ({a.nominal_gsm} gsm)")
                
            plan_count = db.query(ProductionPlanDB).count()
            print(f"\nTERVEZÉSI ADATOK (Planning): {plan_count} rekord")
            if plan_count > 0:
                latest = db.query(ProductionPlanDB).order_by(ProductionPlanDB.date.desc()).first()
                print(f"Legutóbbi terv dátuma: {latest.date}")

            quality_count = db.query(QualityDataDB).count()
            print(f"\nMINŐSÉGI ADATOK (Quality): {quality_count} rekord")
            
            util_count = db.query(UtilityConsumptionDB).count()
            print(f"\nKÖZMŰADATOK (Utilities): {util_count} rekord")

            event_count = db.query(ProductionEventDB).count()
            run_count = db.query(ProductionEventDB).filter(ProductionEventDB.event_type == "RUN").count()
            stop_count = db.query(ProductionEventDB).filter(ProductionEventDB.event_type == "STOP").count()
            print(f"\nESEMÉNYNAPLÓ (Events): {event_count} rekord")
            print(f"RUN (Gyártás): {run_count} | STOP (Leállás): {stop_count}")

            summary_count = db.query(DailySummaryDB).count()
            print(f"\nNAPI ÖSSZESÍTŐK (Daily Summaries): {summary_count} rekord")
            if summary_count > 0:
                latest = db.query(DailySummaryDB).order_by(DailySummaryDB.date.desc()).first()
                print("─" * 60)
                print(f"LEGUTÓBBI RIPORT ADATAI ({latest.date} | {latest.machine_id})")
                print(f"OEE Mutató: {latest.oee_pct if latest.oee_pct else 0}%")
                print(f"Termelés: {latest.total_tons if latest.total_tons else 0:.1f} t (Terv: {latest.target_tons if latest.target_tons else 0:.1f} t)")
                print(f"Állásidő: {latest.total_downtime_min} perc | Szakadások: {latest.break_count} db")
                print(f"Átlagos nedvesség: {latest.avg_moisture_pct}%")
                print(f"Fajlagos rost: {latest.spec_fiber_t_t if latest.spec_fiber_t_t else 0:.2f} t/t")
                print("─" * 60)
        except Exception as e:
            print(f"\nHIBA az adatok lekérdezése közben: {e}")
    
    print("\n" + "═" * 60 + "\n")

if __name__ == "__main__":
    inspect_db()
