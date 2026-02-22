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
    DATABASE_URL: str = "sqlite:///./data/production.db"
    MES_DATABASE_URL: str = "sqlite:///./data/source_events.db"

    # Egy "hálózati meghajtót" szimulálunk, ahol évekre és hónapokra vannak bontva az Excel fájlok
    NETWORK_SHARE_DIR: Path = DATA_DIR / "network_share"
    
    # Hálózati almappák
    PLANNING_DIR: Path = NETWORK_SHARE_DIR / "planning"
    LAB_DATA_DIR: Path = NETWORK_SHARE_DIR / "lab_data"
    UTILITIES_DIR: Path = NETWORK_SHARE_DIR / "utilities"

    # Pydantic-specifikus konfiguráció
    model_config = SettingsConfigDict(
        env_file=".env",              # .env fájl keresése
        env_file_encoding="utf-8",    # Karakterkódolás
        extra="ignore"                # Felesleges környezeti változók figyelmen kívül hagyása
    )

# Globálisan elérhető settings példány
settings = Settings()
