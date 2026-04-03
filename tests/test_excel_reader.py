import pytest
import pandas as pd
from datetime import date
from unittest.mock import patch
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

def test_read_lab_data_file_not_found(reader):
    """Teszteli, hogy üres listát ad-e vissza, ha a laborfájl nem létezik."""
    target_date = date(2024, 1, 1)
    with patch('src.extractors.excel_reader.settings'):
        with patch('pathlib.Path.exists', return_value=False):
            result = reader.read_lab_data(target_date)
            assert result == []

def test_read_lab_data_success(reader):
    """Teszteli a laboratóriumi mérések sikeres beolvasását."""
    from pathlib import Path
    target_date = date(2024, 1, 1)
    with patch('src.extractors.excel_reader.settings') as mock_settings:
        mock_settings.LAB_DATA_DIR = Path("/tmp/lab")

        mock_df = pd.DataFrame({
            'Timestamp': [pd.Timestamp('2024-01-01 10:00:00')],
            'Gép': ['PM1'],
            'Termék': ['Kraft'],
            'Nedvesség': [7.5],
            'GSM': [125.0],
            'Szakítás': [8.2]
        })

        with patch('pandas.read_excel', return_value=mock_df):
            with patch('pathlib.Path.exists', return_value=True):
                result = reader.read_lab_data(target_date)

            assert len(result) == 1
            assert result[0]['machine_id'] == 'PM1'
            assert result[0]['moisture_pct'] == 7.5
            assert result[0]['gsm_measured'] == 125.0

def test_read_utilities_success(reader):
    """Teszteli a közműfogyasztási adatok sikeres beolvasását."""
    from pathlib import Path
    target_date = date(2024, 1, 1)
    with patch('src.extractors.excel_reader.settings') as mock_settings:
        mock_settings.UTILITIES_DIR = Path("/tmp/utilities")

        mock_df = pd.DataFrame({
            'Dátum': [pd.Timestamp('2024-01-01')],
            'Gép': ['PM1'],
            'Víz': [150.0],
            'Áram': [8500.0],
            'Gőz': [45.0],
            'Rost': [120.0],
            'Adalék': [500.0]
        })

        with patch('pandas.read_excel', return_value=mock_df):
            with patch('pathlib.Path.exists', return_value=True):
                result = reader.read_utilities(target_date)

            assert len(result) == 1
            assert result[0]['machine_id'] == 'PM1'
            assert result[0]['water_m3'] == 150.0
            assert result[0]['electricity_kwh'] == 8500.0

