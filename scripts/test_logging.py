#!/usr/bin/env python3
"""
LOGGING RENDSZER TESZTELÉSE
===========================
Ellenőrzi, hogy a naplózási rendszer (logging) megfelelően működik-e:
- INFO és felette -> logs/app.log fájlba
- WARNING és felette -> Konzolra is
"""

import logging
import sys
from pathlib import Path

# Projekt gyökérkönyvtár hozzáadása a Python elérési úthoz
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.logging_config import setup_logging
from src.config import settings

def main():
    # Naplózás beállítása a konfiguráció alapján
    setup_logging(settings.LOG_LEVEL)
    logger = logging.getLogger(__name__)

    print("\nEcoPaper Solutions - Logging Teszt")
    print("-" * 40)

    # Különböző szintek tesztelése
    logger.debug("DEBUG üzenet: Csak fájlba kerül, ha a LOG_LEVEL=DEBUG.")
    logger.info("INFO üzenet: Rögzítve az app.log fájlban.")
    logger.warning("WARNING figyelmeztetés: Látható a konzolon és a fájlban is!")
    logger.error("ERROR hiba: Kritikus üzenet, mindenhol megjelenik.")

    print("-" * 40)
    print("Teszt üzenetek elküldve.")
    print("Ellenőrizd a 'logs/app.log' fájlt a teljes tartalomhoz!\n")

if __name__ == "__main__":
    main()
