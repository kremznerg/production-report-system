from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os

class Settings(BaseSettings):
    """
    Alkalmazás szintű beállítások. 
    A Pydantic automatikusan beolvassa a .env fájlt, ha létezik.
    """
    
    # --- PROJEKT ALAPOK ---
    PROJECT_NAME: str = "Production Report System"
    LOG_LEVEL: str = "INFO"

    # --- ÚTVONALAK ---
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    
    # --- ADATBÁZIS ---
    DATABASE_URL: str = f"sqlite:///{DATA_DIR}/production.db"

    # --- ADATFORRÁSOK (API & EXCEL) ---
    API_BASE_URL: str = "https://api.example.com/v1"
    
    PLANNING_FILE: Path = DATA_DIR / "planning.xlsx"
    LAB_DATA_FILE: Path = DATA_DIR / "lab_data.xlsx"
    UTILITIES_FILE: Path = DATA_DIR / "utilities.xlsx"

    # Pydantic konfiguráció
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" 
    )

settings = Settings()
