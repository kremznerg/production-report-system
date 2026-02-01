import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from src.extractors.excel_reader import ExcelReader

@pytest.fixture
def reader():
    return ExcelReader()

def test_read_planning_file_not_found(reader):
    """Teszteli, hogy üres listát ad-e vissza, ha a fájl nem létezik."""
    with patch('src.extractors.excel_reader.settings') as mock_settings:
        mock_settings.PLANNING_FILE.exists.return_value = False
        result = reader.read_planning()
        assert result == []

def test_read_planning_success(reader):
    """Teszteli a tervezési adatok beolvasását mockolt pandas-szal."""
    with patch('src.extractors.excel_reader.settings') as mock_settings:
        mock_settings.PLANNING_FILE.exists.return_value = True
        
        # Mocking pandas.read_excel
        mock_df = pd.DataFrame({
            'Dátum': ['2024-01-01'],
            'Gép': ['PM1'],
            'Termék': ['Kraft'],
            'Terv_Sebesség': [100],
            'Terv_Tonna': [50]
        })
        
        with patch('pandas.read_excel', return_value=mock_df):
            result = reader.read_planning()
            
            assert len(result) == 1
            assert result[0]['machine_id'] == 'PM1'
            assert result[0]['target_speed'] == 100
            assert result[0]['target_quantity_tons'] == 50
