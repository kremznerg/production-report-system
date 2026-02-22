"""
EXCEL ADATBEOLVASÓ (EXCEL READER)
=================================
Ez a modul felelős a külső fájlokból (Excel) érkező adatok beolvasásáért.
Kezeli a termelési tervet, a laboratóriumi méréseket és a közműfogyasztásokat.
Képes célzottan adott napra szűrni a beolvasást, csökkentve a terhelést.
"""

import pandas as pd
import logging
from pathlib import Path
from datetime import date
from typing import List, Dict, Any, Optional

from ..config import settings

# Naplózás beállítása a modulhoz
logger = logging.getLogger(__name__)

class ExcelReader:
    """
    Általános Excel olvasó osztály.
    Centralizáltan kezeli az Excel alapú forrásfájlok beolvasását év/hónap bontású
    strukturált mappákból, és opcionálisan szűri a betöltött adatokat.
    """
    
    def _read_and_filter(self, dir_path: Path, prefix: str, target_date: date, columns: List[str], date_col_idx: int) -> List[Dict[str, Any]]:
        """
        Belső segédfüggvény az év és hónap alapján szervezett Excel fájlok és fülek olvasásához,
        és egy adott napra történő szűréséhez.
        """
        year = target_date.year
        month = target_date.strftime('%m')
        
        file_path: Path = dir_path / f"{prefix}_{year}.xlsx"
        
        if not file_path.exists():
            logger.warning(f"Adatfájl nem található: {file_path}")
            return []
            
        try:
            # Csak az adott hónapnak megfelelő fület olvassuk be (memory efficient)
            df = pd.read_excel(file_path, sheet_name=month)
            
            # Oszlopok átnevezése
            df.columns = columns
            
            date_col_name = columns[date_col_idx]
            
            # Dátum/Idő formázás
            if date_col_name == 'timestamp':
                df[date_col_name] = pd.to_datetime(df[date_col_name], errors='coerce')
                df.dropna(subset=[date_col_name], inplace=True)
                # Szűrés a kért napra
                df = df[df[date_col_name].dt.date == target_date]
            else:
                df[date_col_name] = pd.to_datetime(df[date_col_name], errors='coerce').dt.date
                df.dropna(subset=[date_col_name], inplace=True)
                # Szűrés a kért napra
                df = df[df[date_col_name] == target_date]
            
            return df.to_dict('records')
            
        except ValueError:
            # Ha nem létezik az adott nevű munkalap (hónap sheet)
            logger.warning(f"Nincs adat erre a hónapra ({month}) a '{file_path}' fájlban.")
            return []
        except Exception as e:
            logger.error(f"Hiba a fájl olvasásakor ({file_path}): {e}")
            return []

    def read_planning(self, target_date: date) -> List[Dict[str, Any]]:
        """Beolvassa a napi termelési tervet az adott napra."""
        logger.info(f"Tervezési adatok beolvasása: {target_date}")
        columns = ['date', 'machine_id', 'article_id', 'target_speed', 'target_quantity_tons']
        return self._read_and_filter(settings.PLANNING_DIR, 'planning', target_date, columns, date_col_idx=0)
    
    def read_lab_data(self, target_date: date) -> List[Dict[str, Any]]:
        """Beolvassa a laboratóriumi minőségi méréseket az adott napra."""
        logger.info(f"Labor adatok beolvasása: {target_date}")
        columns = ['timestamp', 'machine_id', 'article_id', 'moisture_pct', 'gsm_measured', 'strength_knm']
        return self._read_and_filter(settings.LAB_DATA_DIR, 'lab_data', target_date, columns, date_col_idx=0)
    
    def read_utilities(self, target_date: date) -> List[Dict[str, Any]]:
        """Beolvassa a közműfogyasztási adatokat az adott napra."""
        logger.info(f"Közműadatok beolvasása: {target_date}")
        columns = ['date', 'machine_id', 'water_m3', 'electricity_kwh', 'steam_tons', 'fiber_tons', 'additives_kg']
        return self._read_and_filter(settings.UTILITIES_DIR, 'utilities', target_date, columns, date_col_idx=0)
