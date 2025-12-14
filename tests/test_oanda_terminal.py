import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import json
from sqlalchemy.exc import SQLAlchemyError
import requests

from src.presenter import Presenter

# Mock configuration for testing
# MOCK_CONFIG is removed as settings are now managed via Model instance


# Patch the config object before importing Model
# This ensures Model uses our mock config for DB_FILE
with patch("src.model.config", {"database": {"file": ":memory:"}}):
    from src.model import Model, Rate


@pytest.fixture
def mock_model():
    model = Model()
    # Set dummy API settings for tests
    model.api_key = "test_api_key"
    model.base_url = "https://api-fxpractice.oanda.com"
    model.account_id = "test_account_id"
    yield model


@pytest.fixture
def mock_view():
    with patch("src.view.View") as MockView:
        mock_view_instance = MockView()
        mock_view_instance.set_status = MagicMock(
            side_effect=lambda text, is_error=False: None
        )
        mock_view_instance.update_table = MagicMock()
        mock_view_instance.set_update_buttons_enabled = MagicMock()
        mock_view_instance.table = MagicMock()
        mock_view_instance.table.setRowCount = MagicMock()
        mock_view_instance.table.setItem = MagicMock()

        def update_table_side_effect(data):
            mock_view_instance.table.setRowCount(len(data))
            for row_idx, row_data in enumerate(data):
                for col_idx, item in enumerate(row_data):
                    # Mocking QTableWidgetItem as a string directly for this test
                    mock_view_instance.table.setItem(
                        row_idx, col_idx, MagicMock(text=str(item))
                    )

        mock_view_instance.update_table.side_effect = update_table_side_effect
        return mock_view_instance


@pytest.fixture
def mock_presenter(mock_model, mock_view):
    presenter = Presenter(mock_model, mock_view)
    return presenter


@pytest.fixture
def presenter_instance(mock_model, mock_view):
    presenter = Presenter(mock_model, mock_view)
    # Manually set the presenter in the mock view, as it's done in main.py
    mock_view._presenter = presenter
    mock_view.set_presenter(presenter)  # Call the set_presenter method
    return presenter


def test_categorize_instrument(mock_model):
    """Test Model.categorize_instrument for various instrument types."""
    model = mock_model
    assert model.categorize_instrument("EUR_USD") == "Forex"
    assert model.categorize_instrument("XAU_USD") == "Metals"
    assert model.categorize_instrument("WTICO_USD") == "Commodities"
    assert model.categorize_instrument("SPX500_USD") == "Indices"
    assert model.categorize_instrument("US_10YR_TNOTE") == "Bonds"
    assert model.categorize_instrument("BTC_CFD") == "CFDs"
    assert model.categorize_instrument("UNKNOWN") == "Other"


@patch("src.model.requests.get")
def test_fetch_and_save_rates_success(mock_get, mock_model):
    """Test Model.fetch_and_save_rates with a successful API response."""
    model = mock_model
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "instruments": [
            {"name": "EUR_USD", "financing": {"longRate": "0.0083", "shortRate": "-0.0133"}, "quoteCurrency": "USD"}
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    expected_url = f"{model.base_url}/v3/accounts/{model.account_id}/instruments"
    expected_headers = {"Authorization": f"Bearer {model.api_key}", "Content-Type": "application/json"}

    result = model.fetch_and_save_rates(save_to_db=True)
    assert result == {"financingRates": [
        {"instrument": "EUR_USD", "longRate": "0.0083", "shortRate": "-0.0133", "currency": "USD", "days": None, "longCharge": None, "shortCharge": None, "units": None}
    ]}

    mock_get.assert_called_once_with(
        expected_url, headers=expected_headers, timeout=10
    )

    with model.get_session() as session:
        assert session.query(Rate).count() == 1
        rate = session.query(Rate).first()
        assert rate.date == datetime.now().strftime("%Y-%m-%d")
        assert json.loads(rate.raw_data) == {
            "financingRates": [
                {"instrument": "EUR_USD", "longRate": "0.0083", "shortRate": "-0.0133", "currency": "USD", "days": None, "longCharge": None, "shortCharge": None, "units": None}
            ]
        }


@patch("src.model.requests.get")
def test_fetch_and_save_rates_api_failure(mock_get, mock_model):
    """Test Model.fetch_and_save_rates when API request fails."""
    model = mock_model
    mock_get.side_effect = requests.exceptions.RequestException("API failure")

    expected_url = f"{model.base_url}/v3/accounts/{model.account_id}/instruments"
    expected_headers = {"Authorization": f"Bearer {model.api_key}", "Content-Type": "application/json"}

    with pytest.raises(requests.exceptions.RequestException):
        model.fetch_and_save_rates(save_to_db=True)

    assert mock_get.call_count == 3
    mock_get.assert_called_with(
        expected_url, headers=expected_headers, timeout=10
    )
    with model.get_session() as session:
        assert session.query(Rate).count() == 0


@patch("src.model.requests.get")
def test_fetch_and_save_rates_db_error(mock_get, mock_model):
    """Test Model.fetch_and_save_rates when database commit fails."""
    model = mock_model
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "instruments": [
            {"name": "EUR_USD", "financing": {"longRate": "0.01", "shortRate": "-0.02"}, "quoteCurrency": "USD"}
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    # Temporarily patch model.get_session to raise an error
    with patch.object(
        model, "get_session", side_effect=SQLAlchemyError("DB Error")
    ):
        result = model.fetch_and_save_rates(save_to_db=True)

        assert result is None
        mock_get.assert_called_once()
        expected_url = f"{model.base_url}/v3/accounts/{model.account_id}/instruments"
        expected_headers = {"Authorization": f"Bearer {model.api_key}", "Content-Type": "application/json"}
        mock_get.assert_called_once_with(
            expected_url, headers=expected_headers, timeout=10
        )


def test_on_filter_text_changed_valid(mock_presenter, mock_view):
    """Test Presenter.on_filter_text_changed with valid input."""
    mock_presenter.on_filter_text_changed("eur")
    assert mock_presenter.filter_text == "eur"
    mock_presenter.process_ui_updates()
    mock_view.set_status.assert_not_called()


def test_on_filter_text_changed_too_long(mock_presenter, mock_view):
    """Test Presenter.on_filter_text_changed with overly long input."""
    long_text = "a" * 51  # MAX_FILTER_LENGTH + 1
    mock_presenter.on_filter_text_changed(long_text)
    assert mock_presenter.filter_text == "a" * 50  # MAX_FILTER_LENGTH
    mock_presenter.process_ui_updates()
    mock_view.set_status.assert_called_once()
    call_args, call_kwargs = mock_view.set_status.call_args
    assert call_args[0] == "Filter text too long (max 50 chars)"
    assert call_kwargs["is_error"] is True


def test_update_table(mock_view, presenter_instance):
    """Test View.update_table with sample data."""
    data = [
        ["EUR_USD", "Forex", "USD", "1.23", "0.01%", "-0.02%", "0.05", "-0.07", "100"],
        ["XAU_USD", "Metals", "USD", "1750.50", "0.03%", "-0.04%", "0.10", "-0.12", "10"],
    ]
    mock_view.update_table(data)
    presenter_instance.process_ui_updates()
    mock_view.update_table.assert_called_once_with(data)
    mock_view.table.setRowCount.assert_called_once_with(2)
    # The number of call.setItem should be 2 rows * 9 columns (after the recent model changes)
    assert mock_view.table.setItem.call_count == 18
