#!/usr/bin/env python3
"""
Seed master data (machines and articles) into the database.
Run this once after initializing the database.
"""

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
        
        # Articles
        articles = [
            ArticleDB(
                id="ART001",
                name="Brown Containerboard",
                product_group="Brown",
                nominal_gsm=125.0
            ),
            ArticleDB(
                id="ART002",
                name="White Testliner",
                product_group="White",
                nominal_gsm=130.0
            ),
            ArticleDB(
                id="ART003",
                name="Kraftliner",
                product_group="Brown",
                nominal_gsm=150.0
            ),
        ]
        
        for machine in machines:
            db.merge(machine)  
        
        for article in articles:
            db.merge(article)
        
        print(f"✅ Seeded {len(machines)} machines and {len(articles)} articles")

if __name__ == "__main__":
    seed_master_data()
