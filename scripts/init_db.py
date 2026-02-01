#!/usr/bin/env python3
"""
ADATBÁZIS INICIALIZÁLÓ SCRIPTM
==============================
Felelős a projekt SQLite adatbázisának létrehozásáért és a táblák inicializálásáért.
VIGYÁZAT: A script futtatása törli a meglévő adatbázist (Clean Slate)!
"""

import sys
import os
from pathlib import Path

# Projekt gyökérkönyvtár hozzáadása a Python elérési úthoz
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.database import init_db
from src.config import settings

def main():
    """Adatbázis fájl takarítása és újratöltése."""
    # Adatbázis elérési útjának kinyerése a konfigurációból
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    
    print("\n🏗️  EcoPaper Solutions - Adatbázis Kezelő")
    print("-" * 40)
    
    # Régi fájl törlése, ha létezik (biztonságos inicializálás)
    if os.path.exists(db_path):
        print(f"🗑️  Régi adatbázis törlése: {db_path}")
        os.remove(db_path)
    
    # Táblák létrehozása a SQLAlchemy modellek alapján
    print("📋 Adatbázis táblák létrehozása...")
    init_db()
    
    print("✅ Kész! Az üres adatbázis létrejött: data/production.db")
    print("-" * 40 + "\n")

if __name__ == "__main__":
    main()
