#!/usr/bin/env python3
"""
Teszt script az adatbázis inicializálásához.
Futtasd ezt egyszer a projekt kezdetén!
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.database import init_db

if __name__ == "__main__":
    print("Adatbázis táblák létrehozása...")
    init_db()
    print("Kész! Ellenőrizd a data/production.db fájlt.")
