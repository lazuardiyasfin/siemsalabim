import pytest
from unittest.mock import MagicMock, patch
from dashboard_backend.enrich import (
    get_reader,
    enrich_geoip,
    close_geoip_reader,
)
import dashboard_backend.enrich as enrich


@pytest.fixture(autouse=True)
def reset_global_reader():
    """Fixture to ensure global _reader state isolation before and after tests."""
    enrich._reader = None
    yield
    enrich._reader = None


@patch("dashboard_backend.enrich.DB_PATH")
@patch("dashboard_backend.enrich.maxminddb.open_database")
def test_get_reader_success(mock_open_db, mock_db_path):
    """Ensure the reader is successfully initialized if the DB file exists."""
    mock_db_path.exists.return_value = True
    mock_instance = MagicMock()
    mock_open_db.return_value = mock_instance

    reader = get_reader()
    assert reader == mock_instance
    mock_open_db.assert_called_once_with(str(mock_db_path))


@patch("dashboard_backend.enrich.DB_PATH")
@patch("dashboard_backend.enrich.maxminddb.open_database")
def test_get_reader_db_missing_or_failed(mock_open_db, mock_db_path):
    """Ensure get_reader returns None if the file is missing or fails to open."""
    # Scenario 1: File does not exist
    mock_db_path.exists.return_value = False
    assert get_reader() is None

    # Scenario 2: File exists but is corrupt / triggers an Exception
    mock_db_path.exists.return_value = True
    mock_open_db.side_effect = Exception("Database error")
    assert get_reader() is None


def test_enrich_geoip_missing_source_events():
    """Ensure the event is returned unchanged if 'source_events' is empty or missing."""
    event_empty = {"type": "ALERT"}
    assert enrich_geoip(event_empty) == event_empty

    event_none = {"type": "ALERT", "source_events": []}
    assert enrich_geoip(event_none) == event_none


@patch("dashboard_backend.enrich.get_reader")
def test_enrich_geoip_success(mock_get_reader):
    """Ensure coordinates are correctly populated from the MaxMind database record."""
    mock_reader = MagicMock()
    mock_reader.get.return_value = {
        "location": {"latitude": -7.2575, "longitude": 112.7521}
    }
    mock_get_reader.return_value = mock_reader

    event = {"source_events": [{"decoded": {"src_ip": "1.1.1.1"}}]}

    result = enrich_geoip(event)
    assert result["lat"] == -7.2575
    assert result["lon"] == 112.7521


@patch("dashboard_backend.enrich.get_reader")
def test_enrich_geoip_fallback_on_missing_ip_or_location(mock_get_reader):
    """Ensure fallback coordinates for Jakarta are used if the IP is empty or location data is missing."""
    # Scenario 1: Record exists but does not contain the 'location' key
    mock_reader = MagicMock()
    mock_reader.get.return_value = {"country": "ID"}
    mock_get_reader.return_value = mock_reader

    event_no_loc = {"source_events": [{"decoded": {"src_ip": "1.1.1.1"}}]}
    result = enrich_geoip(event_no_loc)
    assert result["lat"] == -6.2088
    assert result["lon"] == 106.8456

    # Scenario 2: 'src_ip' key is not found in the payload structure
    event_no_ip = {"source_events": [{"decoded": {}}]}
    result_no_ip = enrich_geoip(event_no_ip)
    assert "lat" not in result_no_ip
    assert "lon" not in result_no_ip


@patch("dashboard_backend.enrich.get_reader")
def test_enrich_geoip_fallback_on_value_error(mock_get_reader):
    """Ensure ValueError handling (invalid IP string format) switches to the Jakarta fallback."""
    mock_reader = MagicMock()
    mock_reader.get.side_effect = ValueError("Invalid IP string")
    mock_get_reader.return_value = mock_reader

    event = {"source_events": [{"decoded": {"src_ip": "invalid_ip_format"}}]}

    result = enrich_geoip(event)
    assert result["lat"] == -6.2088
    assert result["lon"] == 106.8456


def test_close_geoip_reader():
    """Ensure the close() method is called on the reader object and state resets to None."""
    mock_reader = MagicMock()
    enrich._reader = mock_reader

    close_geoip_reader()
    mock_reader.close.assert_called_once()
    assert enrich._reader is None
