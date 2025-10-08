import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json
import requests

# Patch the config object before importing Model
# This ensures Model uses our mock config for API_URL, HEADERS, DB_FILE
MOCK_CONFIG = {
    "api": {
        "url": "http://mock-api.oanda.com",
        "headers": {"User-Agent": "test-agent"},
    },
    "database": {"file": "test_oanda_rates.db"},
    "categories": {
        "currencies": [], "metals": [], "commodities": [], "indices": [], "bonds": []
    }
}

with patch('src.model.config', MOCK_CONFIG):
    from src.model import Model, Rate, Session, API_URL, HEADERS


@pytest.fixture
def model_instance():
    return Model()


@pytest.fixture
def mock_session():
    with patch('src.model.Session') as mock_session_class:
        session = MagicMock()
        mock_session_class.return_value = session
        yield session


@pytest.fixture
def mock_requests_get():
    with patch('requests.get') as mock_get:
        yield mock_get


@pytest.fixture
def mock_datetime_now():
    with patch('src.model.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2023, 1, 1)
        mock_dt.strftime = datetime.strftime # Ensure strftime works as expected
        yield mock_dt


def test_fetch_and_save_rates_success(model_instance, mock_session, mock_requests_get, mock_datetime_now):
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"financingRates": [{"instrument": "EUR_USD"}]}
    mock_requests_get.return_value = mock_response

    mock_session.query.return_value.filter_by.return_value.first.return_value = None # Ensure no existing rate

    # Act
    result = model_instance.fetch_and_save_rates(save_to_db=True)

    # Assert
    assert result == {"financingRates": [{"instrument": "EUR_USD"}]}
    mock_requests_get.assert_called_once_with(API_URL, headers=HEADERS, timeout=10)
    mock_session.query.return_value.filter_by.return_value.first.assert_called_once_with()
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.close.assert_called_once()


def test_fetch_and_save_rates_api_error(model_instance, mock_session, mock_requests_get, mock_datetime_now):
    # Arrange
    mock_requests_get.side_effect = requests.exceptions.RequestException("API Error")

    # Act
    result = model_instance.fetch_and_save_rates(save_to_db=True)

    # Assert
    assert result is None
    mock_requests_get.assert_called_once_with(API_URL, headers=HEADERS, timeout=10)
    mock_session.rollback.assert_not_called()
    mock_session.close.assert_not_called()


def test_fetch_and_save_rates_invalid_json(model_instance, mock_session, mock_requests_get, mock_datetime_now):
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_requests_get.return_value = mock_response

    # Act
    result = model_instance.fetch_and_save_rates(save_to_db=True)

    # Assert
    assert result is None
    mock_requests_get.assert_called_once_with(API_URL, headers=HEADERS, timeout=10)
    mock_session.rollback.assert_not_called()
    mock_session.close.assert_not_called()


def test_fetch_and_save_rates_db_error(model_instance, mock_session, mock_requests_get, mock_datetime_now):
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"financingRates": [{"instrument": "EUR_USD"}]}
    mock_requests_get.return_value = mock_response
    mock_session.commit.side_effect = Exception("DB Error")

    # Act
    result = model_instance.fetch_and_save_rates(save_to_db=True)

    # Assert
    assert result is None
    mock_requests_get.assert_called_once_with(API_URL, headers=HEADERS, timeout=10)
    mock_session.rollback.assert_called_once()
    mock_session.close.assert_called_once()


def test_fetch_and_save_rates_no_save_to_db(model_instance, mock_session, mock_requests_get, mock_datetime_now):
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"financingRates": [{"instrument": "EUR_USD"}]}
    mock_requests_get.return_value = mock_response

    # Act
    result = model_instance.fetch_and_save_rates(save_to_db=False)

    # Assert
    assert result == {"financingRates": [{"instrument": "EUR_USD"}]}
    mock_requests_get.assert_called_once_with(API_URL, headers=HEADERS, timeout=10)
    mock_session.query.assert_not_called()
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()
    mock_session.rollback.assert_not_called()
    mock_session.close.assert_not_called()


def test_fetch_and_save_rates_update_existing(model_instance, mock_session, mock_requests_get, mock_datetime_now):
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"financingRates": [{"instrument": "EUR_USD", "longRate": 0.01}]}.copy()
    mock_requests_get.return_value = mock_response

    # Simulate an existing rate in the DB
    existing_rate = Rate(date="2023-01-01", raw_data=json.dumps({"financingRates": [{"instrument": "EUR_USD", "longRate": 0.005}]}))
    mock_session.query.return_value.filter_by.return_value.first.return_value = existing_rate

    # Act
    result = model_instance.fetch_and_save_rates(save_to_db=True)

    # Assert
    assert result == {"financingRates": [{"instrument": "EUR_USD", "longRate": 0.01}]}
    mock_requests_get.assert_called_once_with(API_URL, headers=HEADERS, timeout=10)
    mock_session.query.return_value.filter_by.return_value.first.assert_called_once_with()
    assert existing_rate.raw_data == json.dumps({"financingRates": [{"instrument": "EUR_USD", "longRate": 0.01}]})
    mock_session.add.assert_not_called() # Should not add a new one
    mock_session.commit.assert_called_once()
    mock_session.close.assert_called_once()


def test_fetch_and_save_rates_no_financing_rates_in_response(model_instance, mock_session, mock_requests_get, mock_datetime_now):
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"someOtherKey": "value"}
    mock_requests_get.return_value = mock_response

    # Act
    result = model_instance.fetch_and_save_rates(save_to_db=True)

    # Assert
    assert result is None
    mock_requests_get.assert_called_once_with(API_URL, headers=HEADERS, timeout=10)
    mock_session.query.assert_not_called()
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()
    mock_session.rollback.assert_not_called()
    mock_session.close.assert_not_called()
