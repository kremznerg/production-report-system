import pytest
from unittest.mock import MagicMock, patch
from datetime import date
from src.pipeline import Pipeline

@pytest.fixture
def pipeline():
    # Mock extractor, reader, calculator
    with patch('src.pipeline.EventsExtractor'), \
         patch('src.pipeline.ExcelReader'), \
         patch('src.pipeline.MetricsCalculator'):
        return Pipeline()

def test_pipeline_full_load_calls(pipeline):
    """Teszteli, hogy a pipeline megfelelően hívja meg az alrendszereket."""
    target_date = date(2024, 1, 1)
    
    # Mock-oljuk a belső metódusokat
    pipeline._load_excel_data = MagicMock()
    pipeline._load_production_events = MagicMock()
    pipeline._update_daily_summaries = MagicMock()
    
    pipeline.run_full_load(target_date)
    
    pipeline._load_excel_data.assert_called_once()
    pipeline._load_production_events.assert_called_with(target_date, None)
    pipeline._update_daily_summaries.assert_called_with(target_date, None)

def test_get_active_machines(pipeline):
    """Teszteli az aktív gépek lekérését."""
    with patch('src.pipeline.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # Mocking query result for MachineDB.id
        mock_db.query.return_value.all.return_value = [("PM1",), ("PM2",)]
        
        machines = pipeline._get_active_machines()
        assert machines == ["PM1", "PM2"]
