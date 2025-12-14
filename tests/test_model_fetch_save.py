import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json
import requests
from sqlalchemy import exc

from src.model import Model, Rate


@pytest.fixture
def model_instance():
    # Create a Model instance which will set up its own in-memory database
    # by patching DB_FILE to ':memory:'
    with patch("src.model.DB_FILE", ":memory:"):
        model = Model()
        # Set dummy API settings for tests
        model.api_key = "test_api_key"
        model.base_url = "https://api-fxpractice.oanda.com"
        model.account_id = "test_account_id"
        yield model

@pytest.fixture
def mock_requests_get():
    with patch("requests.get") as mock_get:
        yield mock_get

@pytest.fixture
def mock_datetime_now():
    with patch("src.model.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2023, 1, 1)
        mock_dt.strftime = datetime.strftime
        yield mock_dt

def test_fetch_and_save_rates_success(
    model_instance, mock_requests_get, mock_datetime_now
):
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"instruments": [{"name": "EUR_USD", "financing": {"longRate": "0.0083", "shortRate": "-0.0133"}, "quoteCurrency": "USD"}]}
    mock_requests_get.return_value = mock_response

    expected_url = f"{model_instance.base_url}/v3/accounts/{model_instance.account_id}/instruments"
    expected_headers = {"Authorization": f"Bearer {model_instance.api_key}", "Content-Type": "application/json"}

    # Act
    result = model_instance.fetch_and_save_rates(save_to_db=True)

    # Assert
    assert result == {"financingRates": [
        {"instrument": "EUR_USD", "longRate": "0.0083", "shortRate": "-0.0133", "currency": "USD", "days": None, "longCharge": None, "shortCharge": None, "units": None}
    ]}
    mock_requests_get.assert_called_once_with(
        expected_url, headers=expected_headers, timeout=10
    )

    # Verify data in the database
    with model_instance.get_session() as session:
        rate = session.query(Rate).filter_by(date="2023-01-01").first()
        assert rate is not None
        assert json.loads(rate.raw_data) == {
            "financingRates": [
                {"instrument": "EUR_USD", "longRate": "0.0083", "shortRate": "-0.0133", "currency": "USD", "days": None, "longCharge": None, "shortCharge": None, "units": None}
            ]
        }

def test_fetch_and_save_rates_api_error(
    model_instance, mock_requests_get, mock_datetime_now
):
    # Arrange
    mock_requests_get.side_effect = requests.exceptions.RequestException("API Error")

    expected_url = f"{model_instance.base_url}/v3/accounts/{model_instance.account_id}/instruments"
    expected_headers = {"Authorization": f"Bearer {model_instance.api_key}", "Content-Type": "application/json"}

    # Act & Assert
    with pytest.raises(requests.exceptions.RequestException):
        model_instance.fetch_and_save_rates(save_to_db=True)

    assert mock_requests_get.call_count == 3
    mock_requests_get.assert_called_with(
        expected_url, headers=expected_headers, timeout=10
    )
    with model_instance.get_session() as session:
        assert session.query(Rate).count() == 0

def test_fetch_and_save_rates_invalid_json(
    model_instance, mock_requests_get, mock_datetime_now
):
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"instruments": [{"name": "EUR_USD", "financing": {"longRate": "0.0083", "shortRate": "-0.0133"}, "quoteCurrency": "USD"}]} # Changed to v20 format
    mock_requests_get.return_value = mock_response

    # Act
    result = model_instance.fetch_and_save_rates(save_to_db=True)

    # Assert
    assert result is not None  # Should return a transformed data structure now
    assert "financingRates" in result
    assert len(result["financingRates"]) == 1

def test_fetch_and_save_rates_db_error(
    model_instance, mock_requests_get, mock_datetime_now
):
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"instruments": [{"name": "EUR_USD", "financing": {"longRate": "0.0083", "shortRate": "-0.0133"}, "quoteCurrency": "USD"}]}
    mock_requests_get.return_value = mock_response

    # Temporarily patch model_instance.get_session to raise an error
    with patch.object(model_instance, "get_session") as mock_get_session:
        mock_get_session.side_effect = exc.SQLAlchemyError("DB Error")

        # Act
        result = model_instance.fetch_and_save_rates(save_to_db=True)

        # Assert
        assert result is not None
        assert mock_requests_get.call_count == 1
        expected_url = f"{model_instance.base_url}/v3/accounts/{model_instance.account_id}/instruments"
        expected_headers = {"Authorization": f"Bearer {model_instance.api_key}", "Content-Type": "application/json"}
        mock_requests_get.assert_called_with(
            expected_url, headers=expected_headers, timeout=10
        )

def test_fetch_and_save_rates_no_save_to_db(
    model_instance, mock_requests_get, mock_datetime_now
):
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"instruments": [{"name": "EUR_USD", "financing": {"longRate": "0.0083", "shortRate": "-0.0133"}, "quoteCurrency": "USD"}]}
    mock_requests_get.return_value = mock_response

    # Act
    result = model_instance.fetch_and_save_rates(save_to_db=False)

    # Assert
    assert result == {"financingRates": [
        {"instrument": "EUR_USD", "longRate": "0.0083", "shortRate": "-0.0133", "currency": "USD", "days": None, "longCharge": None, "shortCharge": None, "units": None}
    ]}
    expected_url = f"{model_instance.base_url}/v3/accounts/{model_instance.account_id}/instruments"
    expected_headers = {"Authorization": f"Bearer {model_instance.api_key}", "Content-Type": "application/json"}
    mock_requests_get.assert_called_once_with(
        expected_url, headers=expected_headers, timeout=10
    )
    # Ensure no interaction with the database
    with model_instance.get_session() as session:
        assert session.query(Rate).count() == 0

def test_fetch_and_save_rates_update_existing(
    model_instance, mock_requests_get, mock_datetime_now
):
    # Arrange
    initial_data_transformed = {"financingRates": [{"instrument": "EUR_USD", "longRate": 0.005, "shortRate": -0.01, "currency": "USD", "days": None, "longCharge": None, "shortCharge": None, "units": None}]}
    updated_data_raw = {"instruments": [{"name": "EUR_USD", "financing": {"longRate": "0.01", "shortRate": "-0.02"}, "quoteCurrency": "USD"}]}
    updated_data_transformed = {"financingRates": [{"instrument": "EUR_USD", "longRate": "0.01", "shortRate": "-0.02", "currency": "USD", "days": None, "longCharge": None, "shortCharge": None, "units": None}]}

    # Insert an existing rate into the in-memory DB
    with model_instance.get_session() as session:
        existing_rate = Rate(date="2023-01-01", raw_data=json.dumps(initial_data_transformed))
        session.add(existing_rate)
        session.commit()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = updated_data_raw
    mock_requests_get.return_value = mock_response

    expected_url = f"{model_instance.base_url}/v3/accounts/{model_instance.account_id}/instruments"
    expected_headers = {"Authorization": f"Bearer {model_instance.api_key}", "Content-Type": "application/json"}

    # Act
    model_instance.fetch_and_save_rates(save_to_db=True)

    # Assert
    mock_requests_get.assert_called_once_with(
        expected_url, headers=expected_headers, timeout=10
    )
    # Verify the existing rate was updated
    with model_instance.get_session() as session:
        rate = session.query(Rate).filter_by(date="2023-01-01").first()
        assert rate is not None
        assert json.loads(rate.raw_data) == updated_data_transformed

def test_fetch_and_save_rates_no_financing_rates_in_response(
    model_instance, mock_requests_get, mock_datetime_now
):
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"someOtherKey": "value"} # No 'instruments' key in v20 API
    mock_requests_get.return_value = mock_response

    # Act
    result = model_instance.fetch_and_save_rates(save_to_db=True)

    # Assert
    assert result is None # Should be None if 'instruments' key is missing after transformation
    # No data should be saved to DB
    with model_instance.get_session() as session:
        assert session.query(Rate).count() == 0

def test_get_latest_rates_no_data(model_instance):
    # Arrange: DB is empty by default from fixture

    # Act
    date, data = model_instance.get_latest_rates()

    # Assert
    assert date is None
    assert data is None

def test_get_latest_rates_with_data(model_instance):
    # Arrange
    expected_data = {"financingRates": [{"instrument": "EUR_USD"}]}
    with model_instance.get_session() as session:
        session.add(Rate(date="2023-01-01", raw_data=json.dumps(expected_data)))
        session.commit()

    # Act
    date, data = model_instance.get_latest_rates()

    # Assert
    assert date == "2023-01-01"
    assert data == expected_data

def test_get_instrument_history_no_data(model_instance):
    # Arrange: DB is empty by default from fixture

    # Act
    history_df = model_instance.get_instrument_history("EUR_USD")

    # Assert
    assert history_df.empty

def test_get_instrument_history_with_data(model_instance):
    # Arrange
    data1 = {
        "financingRates": [
            {"instrument": "EUR_USD", "longRate": 0.01, "shortRate": -0.02},
            {"instrument": "GBP_USD", "longRate": 0.03, "shortRate": -0.04},
        ]
    }
    data2 = {
        "financingRates": [
            {"instrument": "EUR_USD", "longRate": 0.015, "shortRate": -0.025},
            {"instrument": "GBP_USD", "longRate": 0.035, "shortRate": -0.045},
        ]
    }
    with model_instance.get_session() as session:
        session.add(Rate(date="2023-01-01", raw_data=json.dumps(data1)))
        session.add(Rate(date="2023-01-02", raw_data=json.dumps(data2)))
        session.commit()

    # Act
    history_df = model_instance.get_instrument_history("EUR_USD")

    # Assert
    assert not history_df.empty
    assert len(history_df) == 2
    assert history_df["date"].tolist() == ["2023-01-01", "2023-01-02"]
    assert history_df["long_rate"].tolist() == [0.01, 0.015]
    assert history_df["short_rate"].tolist() == [-0.02, -0.025]

def test_get_instrument_history_no_matching_instrument(model_instance):
    # Arrange
    data1 = {
        "financingRates": [
            {"instrument": "GBP_USD", "longRate": 0.03, "shortRate": -0.04},
        ]
    }
    with model_instance.get_session() as session:
        session.add(Rate(date="2023-01-01", raw_data=json.dumps(data1)))
        session.commit()

    # Act
    history_df = model_instance.get_instrument_history("EUR_USD")

    # Assert
    assert history_df.empty
