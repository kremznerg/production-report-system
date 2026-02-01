"""
EXCEL ADATBEOLVASÓ (EXCEL READER)
=================================
Ez a modul felelős a külső fájlokból (Excel) érkező adatok beolvasásáért.
Kezeli a termelési tervet, a laboratóriumi méréseket és a közműfogyasztásokat.
"""

import pandas as pd
import logging
from pathlib import Path
from datetime import date
from typing import List, Dict, Any

from ..config import settings

# Naplózás beállítása a modulhoz
logger = logging.getLogger(__name__)

class ExcelReader:
    """
    Általános Excel olvasó osztály.
    Centralizáltan kezeli az Excel alapú forrásfájlok beolvasását és oszlop-mappingjét.
    """
    
    def read_planning(self) -> List[Dict[str, Any]]:
        """
        Beolvassa a napi termelési tervet (planning.xlsx).
        
        Elvárt oszlopok a fájlban:
        - Date, Machine, Article, Target_Speed, Target_Tons
        
        Returns:
            List[Dict[str, Any]]: Tervezési rekordok listája a belső modellnek megfelelő kulcsokkal.
        """
        file_path: Path = settings.PLANNING_FILE
        
        if not file_path.exists():
            logger.warning(f"Tervezési fájl nem található: {file_path}")
            return []
        
        logger.info(f"Tervezési adatok beolvasása: {file_path}")
        
        try:
            df = pd.read_excel(file_path)
            
            # Oszlopok átnevezése a belső adatbázis sémának megfelelően
            df.columns = ['date', 'machine_id', 'article_id', 'target_speed', 'target_quantity_tons']
            
            # Dátum típus kényszerítése és hibakezelés
            df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
            df.dropna(subset=['date'], inplace=True)
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Hiba a tervezési fájl olvasásakor: {e}")
            return []
    
    def read_lab_data(self) -> List[Dict[str, Any]]:
        """
        Beolvassa a laboratóriumi minőségi méréseket (lab_data.xlsx).
        
        Elvárt oszlopok:
        - Timestamp, Machine, Article, Moisture_%, GSM, Strength_kNm
        
        Returns:
            List[Dict[str, Any]]: Minőségi mérések listája szótár formátumban.
        """
        file_path: Path = settings.LAB_DATA_FILE
        
        if not file_path.exists():
            logger.warning(f"Labor adatfájl nem található: {file_path}")
            return []
        
        logger.info(f"Labor adatok beolvasása: {file_path}")
        
        try:
            df = pd.read_excel(file_path)
            
            # Oszlopok átnevezése a belső modellek kulcsaihoz igazítva
            df.columns = ['timestamp', 'machine_id', 'article_id', 'moisture_pct', 'gsm_measured', 'strength_knm']
            
            # Időbélyegek konvertálása és érvénytelen sorok szűrése
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df.dropna(subset=['timestamp'], inplace=True)
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Hiba a labor fájl olvasásakor: {e}")
            return []
    
    def read_utilities(self) -> List[Dict[str, Any]]:
        """
        Beolvassa a közműfogyasztási (energia, víz, stb.) adatokat (utilities.xlsx).
        
        Elvárt oszlopok:
        - Date, Machine, Water_m3, Electricity_kWh, Steam_tons, Fiber_tons, Additives_kg
        
        Returns:
            List[Dict[str, Any]]: Közműfogyasztási adatok listája.
        """
        file_path: Path = settings.UTILITIES_FILE
        
        if not file_path.exists():
            logger.warning(f"Közmű adatfájl nem található: {file_path}")
            return []
        
        logger.info(f"Közműadatok beolvasása: {file_path}")
        
        try:
            df = pd.read_excel(file_path)
            
            # Oszlopok leképezése az adatbázis sémára
            df.columns = ['date', 'machine_id', 'water_m3', 'electricity_kwh', 'steam_tons', 'fiber_tons', 'additives_kg']
            
            # Dátum validáció és tisztítás
            df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
            df.dropna(subset=['date'], inplace=True)
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Hiba a közmű fájl olvasásakor: {e}")
            return []
