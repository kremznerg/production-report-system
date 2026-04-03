import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime
from src.extractors.events_extractor import EventsExtractor


@pytest.fixture
def extractor():
    """EventsExtractor példányosítása mock adatbázis-kapcsolattal."""
    with patch('src.extractors.events_extractor.create_engine'), \
         patch('src.extractors.events_extractor.sessionmaker') as mock_sm:
        mock_sm.return_value = MagicMock()
        ext = EventsExtractor()
        return ext


def test_fetch_events_success(extractor):
    """Teszteli az események sikeres lekérését és Pydantic konverzióját."""
    mock_session = MagicMock()
    extractor.Session.return_value = mock_session

    mock_event = MagicMock()
    mock_event.timestamp = datetime(2024, 1, 1, 8, 0, 0)
    mock_event.duration_seconds = 3600
    mock_event.event_type = "RUN"
    mock_event.status = "GOOD"
    mock_event.weight_kg = 5000.0
    mock_event.average_speed = 120.0
    mock_event.machine_id = "PM1"
    mock_event.article_id = "Kraft"
    mock_event.description = None

    mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_event]

    result = extractor.fetch_events("PM1", date(2024, 1, 1))

    assert len(result) == 1
    assert result[0].event_type == "RUN"
    assert result[0].weight_kg == 5000.0
    assert result[0].machine_id == "PM1"
    mock_session.close.assert_called_once()


def test_fetch_events_empty(extractor):
    """Teszteli, hogy üres listát ad vissza, ha nincs esemény az adott napra."""
    mock_session = MagicMock()
    extractor.Session.return_value = mock_session

    mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    result = extractor.fetch_events("PM1", date(2024, 1, 1))

    assert result == []
    mock_session.close.assert_called_once()


def test_fetch_events_database_error(extractor):
    """Teszteli az adatbázis-hiba graceful kezelését (üres lista, nem kivétel)."""
    mock_session = MagicMock()
    extractor.Session.return_value = mock_session

    mock_session.query.side_effect = Exception("Connection refused")

    result = extractor.fetch_events("PM1", date(2024, 1, 1))

    assert result == []
    mock_session.close.assert_called_once()
