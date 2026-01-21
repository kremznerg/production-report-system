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
    """Generic Excel reader for production data files."""
    
    def read_planning(self) -> List[Dict[str, Any]]:
        """
        Read daily production plan from Excel.
        
        Expected columns:
        - Date, Machine, Article, Target_Speed, Target_Tons
        
        Returns:
            List of planning dictionaries
        """
        file_path = settings.PLANNING_FILE
        
        if not file_path.exists():
            logger.warning(f"Planning file not found: {file_path}")
            return []
        
        logger.info(f"Reading planning data from {file_path}")
        
        try:
            df = pd.read_excel(file_path)
            
            # Rename columns to match our model
            df.columns = ['date', 'machine_id', 'article_id', 'target_speed', 'target_quantity_tons']
            
            # Convert date column
            df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
            df.dropna(subset=['date'], inplace=True)
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error reading planning file: {e}")
            return []
    
    def read_lab_data(self) -> List[Dict[str, Any]]:
        """
        Read laboratory quality measurements from Excel.
        
        Expected columns:
        - Timestamp, Machine, Article, Moisture_%, GSM, Strength_kNm
        
        Returns:
            List of quality measurement dictionaries
        """
        file_path = settings.LAB_DATA_FILE
        
        if not file_path.exists():
            logger.warning(f"Lab data file not found: {file_path}")
            return []
        
        logger.info(f"Reading lab data from {file_path}")
        
        try:
            df = pd.read_excel(file_path)
            
            # Rename columns
            df.columns = ['timestamp', 'machine_id', 'article_id', 'moisture_pct', 'gsm_measured', 'strength_knm']
            
            # Convert timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df.dropna(subset=['timestamp'], inplace=True)
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error reading lab data: {e}")
            return []
    
    def read_utilities(self) -> List[Dict[str, Any]]:
        """
        Read utility consumption data from Excel.
        
        Expected columns:
        - Date, Machine, Water_m3, Electricity_kWh, Steam_tons, Fiber_tons, Additives_kg
        
        Returns:
            List of utility consumption dictionaries
        """
        file_path = settings.UTILITIES_FILE
        
        if not file_path.exists():
            logger.warning(f"Utilities file not found: {file_path}")
            return []
        
        logger.info(f"Reading utilities data from {file_path}")
        
        try:
            df = pd.read_excel(file_path)
            
            # Rename columns
            df.columns = ['date', 'machine_id', 'water_m3', 'electricity_kwh', 'steam_tons', 'fiber_tons', 'additives_kg']
            
            # Convert date
            df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
            df.dropna(subset=['date'], inplace=True)
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error reading utilities data: {e}")
            return []
