#!/usr/bin/env python3
"""
ETL PIPELINE INDÍTÓ
====================
Ez a script felelős az adatok beolvasásáért, transzformálásáért és betöltéséért (ETL).
Végigmegy az elmúlt 30 napon, és minden napra lefuttatja a teljes szinkronizációt.
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# Projekt gyökérkönyvtár hozzáadása a Python elérési úthoz
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.logging_config import setup_logging
from src.config import settings
from src.pipeline import Pipeline

def main():
    """Végrehajtja a ciklikus adatbetöltést az elmúlt 30 napra."""
    
    # Naplózás inicializálása (szintek: INFO, DEBUG, WARNING, ERROR)
    setup_logging(settings.LOG_LEVEL)
    
    print("\n🔄 EcoPaper Solutions - ETL Pipeline Folyamat")
    print("-" * 60)
    
    # Pipeline példányosítása
    pipeline = Pipeline()
    
    # Időszak meghatározása: elmúlt 30 nap visszamenőleg máig
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    print(f"📅 Időszak feldolgozása: {start_date} -> {end_date}")
    
    # Ciklikus betöltés naponként
    current_date = start_date
    while current_date <= end_date:
        pipeline.run_full_load(target_date=current_date)
        current_date += timedelta(days=1)
    
    print("-" * 60)
    print(f"✅ Pipeline folyamat sikeresen befejeződött!")
    print(f"ℹ️  Részletes napló a logs/app.log fájlban található.\n")

if __name__ == "__main__":
    main()
