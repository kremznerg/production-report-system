#!/usr/bin/env python3
"""
ETL PIPELINE INDÍTÓ
====================
Ez a script felelős az adatok beolvasásáért, transzformálásáért és betöltéséért (ETL).
Végigmegy a teljes mintatartományon, és minden napra lefuttatja a szinkronizációt.
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

# --- KONSTANSOK ---
END_DATE = date.today()
START_DATE = END_DATE - timedelta(days=365)

def main() -> None:
    """Végrehajtja a ciklikus adatbetöltést a teljes mintatartományra."""
    
    # Naplózás inicializálása
    setup_logging(settings.LOG_LEVEL)
    
    print("\nEcoPaper Solutions - ETL Pipeline Folyamat")
    print("-" * 60)
    
    # Pipeline példányosítása
    pipeline = Pipeline()
    
    # Időszak meghatározása
    start_date = START_DATE
    end_date = END_DATE
    
    print(f"Időszak feldolgozása: {start_date} -> {end_date}")
    
    # Ciklikus betöltés naponként
    current_date = start_date
    while current_date <= end_date:
        pipeline.run_full_load(target_date=current_date)
        current_date += timedelta(days=1)
    
    print("-" * 60)
    print(f"Pipeline folyamat sikeresen befejeződött!")

if __name__ == "__main__":
    main()
