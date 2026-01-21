#!/usr/bin/env python3
"""
Teszt script az adatbázis inicializálásához.
Futtasd ezt egyszer a projekt kezdetén!
"""

from src.database import init_db

if __name__ == "__main__":
    print("Adatbázis táblák létrehozása...")
    init_db()
    print("Kész! Ellenőrizd a data/production.db fájlt.")
