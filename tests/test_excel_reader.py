import pytest
import pandas as pd
from datetime import date
from unittest.mock import MagicMock, patch
from src.extractors.excel_reader import ExcelReader

@pytest.fixture
def reader():
    return ExcelReader()

def test_read_planning_file_not_found(reader):
    """Teszteli, hogy üres listát ad-e vissza, ha a fájl nem létezik."""
    target_date = date(2024, 1, 1)
    with patch('src.extractors.excel_reader.settings'):
        # A könyvtár vagy fájl nem létezik szimulálása
        with patch('pathlib.Path.exists', return_value=False):
            result = reader.read_planning(target_date)
            assert result == []

def test_read_planning_success(reader):
    """Teszteli a tervezési adatok beolvasását mockolt pandas-szal."""
    from pathlib import Path
    target_date = date(2024, 1, 1)
    with patch('src.extractors.excel_reader.settings') as mock_settings:
        mock_settings.PLANNING_DIR = Path("/tmp/planning")
        
        # Mocking pandas.read_excel hívást a _read_and_filter-ben
        mock_df = pd.DataFrame({
            'Dátum': [pd.Timestamp('2024-01-01')],
            'Gép': ['PM1'],
            'Termék': ['Kraft'],
            'Terv_Sebesség': [100.0],
            'Terv_Tonna': [50.0]
        })
        
        with patch('pandas.read_excel', return_value=mock_df):
            with patch('pathlib.Path.exists', return_value=True):
                result = reader.read_planning(target_date)
            
            assert len(result) == 1
            assert result[0]['machine_id'] == 'PM1'
            assert result[0]['target_speed'] == 100.0
            assert result[0]['target_quantity_tons'] == 50.0
