#!/usr/bin/env python3
"""
ADATBÁZIS INICIALIZÁLÓ SCRIPT
==============================
Felelős a projekt PostgreSQL adatbázisának inicializálásáért és a táblák létrehozásáért.
A script a SQLAlchemy modellek (src/database/models.py) alapján építi fel a sémát.
"""

import sys
from pathlib import Path

project_root: Path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.database import init_db
from src.config import settings

def main() -> None:
    """A fő futtató függvény, ami elindítja a táblák létrehozását."""
    
    print("\nEcoPaper Solutions - Adatbázis Kezelő (PostgreSQL)")
    print("-" * 50)
    
    print(f"Kapcsolódás a szerverhez")
    
    print("Táblák létrehozása folyamatban...")
    try:
        init_db()
        print("\nKész! Az adatbázis sémája sikeresen inicializálva.")
    except Exception as e:
        print(f"\nHiba történt az inicializálás során: {e}")
        print("Ellenőrizd, hogy a Docker konténerek (Postgres) futnak-e!")
        
    print("-" * 50 + "\n")

if __name__ == "__main__":
    main()
