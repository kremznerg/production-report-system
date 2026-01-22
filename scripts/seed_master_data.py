#!/usr/bin/env python3
"""
Seed master data (machines and articles) into the database.
Run this once after initializing the database.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.database import get_db
from src.models import MachineDB, ArticleDB

def seed_master_data():
    """Populate machines and articles tables with demo data."""
    
    with get_db() as db:
        # Machines
        machines = [
            MachineDB(id="PM1", name="Paper Machine 1", location="Plant A"),
            MachineDB(id="PM2", name="Paper Machine 2", location="Plant B"),
        ]
        
        # Articles - industry-standard containerboard types
        articles = [
            # Kraftliner - virgin kraft pulp, high strength
            ArticleDB(
                id="KL_150",
                name="Kraftliner",
                product_group="Liner",
                nominal_gsm=150.0
            ),
            ArticleDB(
                id="KL_175",
                name="Kraftliner",
                product_group="Liner",
                nominal_gsm=175.0
            ),
            # Testliner - 100% recycled fibers
            ArticleDB(
                id="TL_100",
                name="Testliner",
                product_group="Liner",
                nominal_gsm=100.0
            ),
            ArticleDB(
                id="TL_140",
                name="Testliner",
                product_group="Liner",
                nominal_gsm=140.0
            ),
            # White-Top Liner - bleached top layer for printing
            ArticleDB(
                id="WTL_120",
                name="White-Top Liner",
                product_group="Liner",
                nominal_gsm=120.0
            ),
            # Fluting (Corrugating Medium) - wavy inner layer
            ArticleDB(
                id="FL_90",
                name="Fluting",
                product_group="Medium",
                nominal_gsm=90.0
            ),
        ]
        
        for machine in machines:
            db.merge(machine)  
        
        for article in articles:
            db.merge(article)
        
        print(f"✅ Seeded {len(machines)} machines and {len(articles)} articles")

if __name__ == "__main__":
    seed_master_data()
