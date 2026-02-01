import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime
from src.transformers.production_metrics import MetricsCalculator
from src.models import (
    ProductionEventDB, ProductionPlanDB, 
    UtilityConsumptionDB, QualityDataDB
)

@pytest.fixture
def calculator():
    return MetricsCalculator()

def test_calculate_daily_metrics_empty(calculator):
    """Teszteli, hogy None-t ad-e vissza, ha nincs esemény."""
    with patch('src.transformers.production_metrics.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = calculator.calculate_daily_metrics("PM1", date(2024, 1, 1))
        assert result is None

def test_calculate_daily_metrics_with_data(calculator):
    """Teszteli a KPI számítást konkrét adatokkal."""
    with patch('src.transformers.production_metrics.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        target_date = date(2024, 1, 1)
        machine_id = "PM1"
        
        # Mock események (Összesen 1440 perc = 86400 mp egy nap)
        mock_events = [
            # RUN esemény: 20 tonna, 20 óra (72000 mp), 100 m/perc
            ProductionEventDB(
                event_type="RUN",
                status="GOOD",
                weight_kg=20000,
                duration_seconds=72000,
                average_speed=100.0,
                machine_id=machine_id,
                timestamp=datetime(2024, 1, 1, 10, 0)
            ),
            # STOP esemény: 4 óra (14400 mp)
            ProductionEventDB(
                event_type="STOP",
                duration_seconds=14400,
                machine_id=machine_id,
                timestamp=datetime(2024, 1, 1, 20, 0)
            )
        ]
        
        # Mock tervek: 25 tonna cél, 100 m/perc cél sebesség
        mock_plans = [
            ProductionPlanDB(
                machine_id=machine_id,
                date=target_date,
                target_quantity_tons=25.0,
                target_speed=100.0
            )
        ]
        
        # Mock közmű: 2000 kWh, 200 m3, 10 t gőz, 22 t rost
        mock_utility = UtilityConsumptionDB(
            machine_id=machine_id,
            date=target_date,
            electricity_kwh=2000.0,
            water_m3=200.0,
            steam_tons=10.0,
            fiber_tons=22.0
        )
        
        # Beállítjuk a mock lekérdezések válaszait
        def mock_query(model):
            mock_q = MagicMock()
            if model == ProductionEventDB:
                mock_q.filter.return_value.all.return_value = mock_events
            elif model == ProductionPlanDB:
                mock_q.filter.return_value.first.return_value = mock_plans[0]
                mock_q.filter.return_value.all.return_value = mock_plans
            elif model == UtilityConsumptionDB:
                mock_q.filter.return_value.first.return_value = mock_utility
            elif model == QualityDataDB:
                mock_q.filter.return_value.all.return_value = []
            return mock_q
            
        mock_db.query.side_effect = mock_query
        
        result = calculator.calculate_daily_metrics(machine_id, target_date)
        
        assert result is not None
        assert result.total_tons == 20.0
        assert result.target_tons == 25.0
        # Availability = 72000 / (72000 + 14400) = 72000 / 86400 = 0.8333 -> 83.33%
        assert result.availability_pct == pytest.approx(83.33, 0.01)
        # Performance = 20 / 25 = 0.8 -> 80%
        assert result.performance_pct == pytest.approx(80.0, 0.01)
        # Quality = 20 / 20 = 1.0 -> 100%
        assert result.quality_pct == 100.0
        # OEE = 0.8333 * 0.8 * 1.0 = 0.6666 -> 66.67%
        assert result.oee_pct == pytest.approx(66.67, 0.01)
        
        # Közmű fajlagosok
        assert result.spec_electricity_kwh_t == 100.0 # 2000 / 20
        assert result.spec_water_m3_t == 10.0 # 200 / 20
        assert result.spec_fiber_t_t == 1.1 # 22 / 20
