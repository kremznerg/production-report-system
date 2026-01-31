"""
Excel data reader for planning, lab, and utility data.
"""

import pandas as pd
import logging
from pathlib import Path
from datetime import date
from typing import List, Dict, Any

from ..config import settings

logger = logging.getLogger(__name__)

class ExcelReader:
    """
    Általános Excel olvasó osztály.
    Beolvassa a tervezési, labor és közmű adatokat a megadott fájlokból.
    """
    
    def read_planning(self) -> List[Dict[str, Any]]:
        """
        Beolvassa a napi termelési tervet az Excel fájlból.
        
        Elvárt oszlopok:
        - Dátum, Gép, Termék, Terv_Sebesség, Terv_Tonna
        
        Returns:
            Tervezési adatok listája (dict formátumban)
        """
        file_path = settings.PLANNING_FILE
        
        if not file_path.exists():
            logger.warning(f"Tervezési fájl nem található: {file_path}")
            return []
        
        logger.info(f"Tervezési adatok beolvasása: {file_path}")
        
        try:
            df = pd.read_excel(file_path)
            
            # Oszlopok átnevezése a belső modellnek megfelelően
            df.columns = ['date', 'machine_id', 'article_id', 'target_speed', 'target_quantity_tons']
            
            # Dátum konverzió
            df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
            df.dropna(subset=['date'], inplace=True)
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Hiba a tervezési fájl olvasásakor: {e}")
            return []
    
    def read_lab_data(self) -> List[Dict[str, Any]]:
        """
        Beolvassa a laboratóriumi minőségi méréseket.
        
        Elvárt oszlopok:
        - Időbélyeg, Gép, Termék, Nedvesség_%, Súly_GSM, Szilárdság_kNm
        
        Returns:
            Minőségi mérések listája (dict formátumban)
        """
        file_path = settings.LAB_DATA_FILE
        
        if not file_path.exists():
            logger.warning(f"Labor adatfájl nem található: {file_path}")
            return []
        
        logger.info(f"Labor adatok beolvasása: {file_path}")
        
        try:
            df = pd.read_excel(file_path)
            
            # Oszlopok átnevezése
            df.columns = ['timestamp', 'machine_id', 'article_id', 'moisture_pct', 'gsm_measured', 'strength_knm']
            
            # Időbélyeg konverzió
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df.dropna(subset=['timestamp'], inplace=True)
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Hiba a labor fájl olvasásakor: {e}")
            return []
    
    def read_utilities(self) -> List[Dict[str, Any]]:
        """
        Beolvassa a közműfogyasztási adatokat.
        
        Elvárt oszlopok:
        - Dátum, Gép, Víz_m3, Áram_kWh, Gőz_tonna, Rost_tonna, Adalékanyag_kg
        
        Returns:
            Közműadatok listája (dict formátumban)
        """
        file_path = settings.UTILITIES_FILE
        
        if not file_path.exists():
            logger.warning(f"Közmű adatfájl nem található: {file_path}")
            return []
        
        logger.info(f"Közműadatok beolvasása: {file_path}")
        
        try:
            df = pd.read_excel(file_path)
            
            # Oszlopok átnevezése
            df.columns = ['date', 'machine_id', 'water_m3', 'electricity_kwh', 'steam_tons', 'fiber_tons', 'additives_kg']
            
            # Dátum konverzió
            df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
            df.dropna(subset=['date'], inplace=True)
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Hiba a közmű fájl olvasásakor: {e}")
            return []
