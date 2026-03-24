#!/usr/bin/env python3
"""
TELJES RENDSZER SETUP (Full Installation)
=========================================
Ez a szkript a helyes sorrendben futtatja le az összes inicializáló lépést, 
hogy a projektet nulláról teljesen működőképessé tegye.
"""

import subprocess
import sys
import time
from pathlib import Path

def run_script(script_path: str) -> bool:
    """Lefuttat egy Python szkriptet és ellenőrzi a sikerességét."""
    print(f"\nFuttatás: {script_path}...")
    try:
        # A projekt gyökérkönyvtárából futtatjuk
        result = subprocess.run(["python3", script_path], check=True, capture_output=False)
        return True
    except subprocess.CalledProcessError as e:
        print(f"HIBA a(z) {script_path} futtatása közben!")
        return False

def main() -> None:
    print("="*60)
    print("ECOPAPER SOLUTIONS - TELJES RENDSZER SETUP")
    print("="*60)
    print("Ez a folyamat teljesen inicializálja az adatbázist és generálja az adatokat.")
    
    steps = [
        "scripts/init_db.py",           
        "scripts/seed_master_data.py",   
        "scripts/create_sample_data.py", 
        "scripts/run_pipeline.py",       
        "scripts/inspect_db.py"          
    ]
    
    start_time = time.time()
    
    for step in steps:
        if not run_script(step):
            print("\nA folyamat hiba miatt megszakadt.")
            sys.exit(1)
            
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "="*60)
    print(f"RENDSZER SIKERESEN SETUPOLVA! ({duration:.1f} másodperc)")
    print("="*60)

if __name__ == "__main__":
    main()
