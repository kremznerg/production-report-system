#!/usr/bin/env python3
"""
TÖRZSDATOK BETÖLTÉSE
====================
Feltölti az adatbázist az alapvető törzsadatokkal (gépek és termékek/cikkek).
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.database import get_db
from src.models import MachineDB, ArticleDB

def seed_master_data() -> None:
    """Gépek és termékek (cikkek) feltöltése demo adatokkal."""
    
    print("\nEcoPaper Solutions - Törzsdatok Betöltése")
    print("-" * 40)
    
    with get_db() as db:
        machines = [
            MachineDB(id="PM1", name="Paper Machine 1", location="Budapest Plant"),
            MachineDB(id="PM2", name="Paper Machine 2", location="Budapest Plant"),
        ]
        
        articles = [
            ArticleDB(id="KL_150", name="Kraftliner", product_group="Liner", nominal_gsm=150.0),
            ArticleDB(id="KL_175", name="Kraftliner", product_group="Liner", nominal_gsm=175.0),
            
            ArticleDB(id="TL_100", name="Testliner", product_group="Liner", nominal_gsm=100.0),
            ArticleDB(id="TL_140", name="Testliner", product_group="Liner", nominal_gsm=140.0),
            
            ArticleDB(id="WTL_120", name="White-Top Liner", product_group="Liner", nominal_gsm=120.0),
            
            ArticleDB(id="FL_90", name="Fluting", product_group="Medium", nominal_gsm=90.0),
        ]
        
        print("Gépek regisztrálása...")
        for machine in machines:
            db.merge(machine)  
        
        print("Termékkatalógus frissítése...")
        for article in articles:
            db.merge(article)
        
        print(f"Sikeresen betöltve {len(machines)} gép és {len(articles)} termék.")
        print("-" * 40 + "\n")

if __name__ == "__main__":
    seed_master_data()
