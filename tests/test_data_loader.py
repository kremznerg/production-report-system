import pandas as pd
from unittest.mock import MagicMock, patch
from datetime import date
from ui.data_loader import load_machines, get_daily_data, get_pareto_data
from src.models import MachineDB, ProductionEventDB

def test_load_machines():
    """Teszteli a gépek betöltését."""
    with patch('ui.data_loader.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        mock_db_machines = [
            MachineDB(id="PM1", name="Paper Machine 1", location="Plant A"),
            MachineDB(id="PM2", name="Paper Machine 2", location="Plant B")
        ]
        mock_db.query.return_value.all.return_value = mock_db_machines
        
        machines = load_machines()
        assert len(machines) == 2
        assert machines[0].id == "PM1"
        assert machines[1].name == "Paper Machine 2"

def test_get_daily_data_not_found():
    """Teszteli, ha nincs adat az adott napra."""
    with patch('ui.data_loader.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # Üres eredmények szimulálása
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        events, summary, quality = get_daily_data("PM1", date(2024, 1, 1))
        assert events == []
        assert summary is None
        assert quality == []

def test_get_pareto_data():
    """Teszteli a Pareto adatok aggregálását."""
    with patch('ui.data_loader.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # Szimulált leállási események
        mock_stops = [
            ProductionEventDB(event_type="BREAK", description="Press part split", duration_seconds=1200), # 20 min
            ProductionEventDB(event_type="BREAK", description="Press part split", duration_seconds=600),  # 10 min
            ProductionEventDB(event_type="STOP", description="Mechanical fail", duration_seconds=3600),   # 60 min
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_stops
        
        df = get_pareto_data("PM1", date(2024, 1, 1))
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2 # Két egyedi ok
        
        # Ellenőrizzük az összegeket
        press_split = df[df["Ok"] == "Press part split"]["Időtartam (perc)"].values[0]
        mech_fail = df[df["Ok"] == "Mechanical fail"]["Időtartam (perc)"].values[0]
        
        assert press_split == 30.0
        assert mech_fail == 60.0
        # A sorrendnek csökkenőnek kell lennie
        assert df.iloc[0]["Ok"] == "Mechanical fail"
