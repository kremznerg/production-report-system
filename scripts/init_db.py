#!/usr/bin/env python3
"""
Teszt script az adatbázis inicializálásához.
Futtasd ezt egyszer a projekt kezdetén!
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.database import init_db
from src.config import settings

if __name__ == "__main__":
    # Töröljük a régi adatbázis fájlt (clean slate)
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    if os.path.exists(db_path):
        print(f"Régi adatbázis törlése: {db_path}")
        os.remove(db_path)
    
    print("Adatbázis táblák létrehozása...")
    init_db()
    print("Kész! Ellenőrizd a data/production.db fájlt.")
