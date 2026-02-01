"""
KONFIGURÁCIÓS MODUL (SETTINGS)
==============================
Ez a modul felelős az alkalmazás globális beállításainak kezeléséért.
A Pydantic BaseSettings osztályát használjuk, amely lehetővé teszi a 
beállítások automatikus beolvasását .env fájlból vagy környezeti változókból.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os

class Settings(BaseSettings):
    """
    Központi beállítások osztálya.
    Típuskényszerítést és alapértelmezett értékeket biztosít a projekt számára.
    """
    
    # --- PROJEKT INFORMÁCIÓK ---
    PROJECT_NAME: str = "EcoPaper Solutions Operations Dashboard"
    LOG_LEVEL: str = "INFO" # Naplózási szint (DEBUG, INFO, WARNING, ERROR)

    # --- KÖNYVTÁRSTRUKTÚRA ---
    # A projekt gyökérkönyvtárának meghatározása a fájl helye alapján
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    
    # --- ADATBÁZIS ELÉRÉS ---
    # SQLite adatfájl helye
    DATABASE_URL: str = f"sqlite:///{DATA_DIR}/production.db"

    # --- KÜLSŐ FORRÁSOK (EXCEL) ---
    PLANNING_FILE: Path = DATA_DIR / "planning.xlsx"
    LAB_DATA_FILE: Path = DATA_DIR / "lab_data.xlsx"
    UTILITIES_FILE: Path = DATA_DIR / "utilities.xlsx"

    # Pydantic-specifikus konfiguráció
    model_config = SettingsConfigDict(
        env_file=".env",              # .env fájl keresése
        env_file_encoding="utf-8",    # Karakterkódolás
        extra="ignore"                # Felesleges környezeti változók figyelmen kívül hagyása
    )

# Globálisan elérhető settings példány
settings = Settings()
