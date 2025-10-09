import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import json
from sqlalchemy.exc import SQLAlchemyError
import requests

from src.presenter import Presenter

# Mock configuration for testing
MOCK_CONFIG = {
    "api": {
        "url": "https://labs-api.oanda.com/v1/financing-rates",
        "headers": {"Authorization": "test_key", "Accept": "application/json"},
        "timeout": 10,
    },
    "database": {"file": ":memory:"},
    "categories": {
        "currencies": ["usd", "eur", "jpy"],
        "metals": ["xau", "xag"],
        "commodities": ["wtico_usd"],
        "indices": ["spx500_usd"],
        "bonds": ["us_10yr_tnote"],
        "currency_suffixes": {"USD": "USD", "EUR": "EUR"},
    },
    "ui": {"timer_interval": 16},
    "logging": {"level": "INFO", "file_path": "test.log"},
}

# Patch the config object before importing Model
# This ensures Model uses our mock config for API_URL, HEADERS, DB_FILE
with patch("src.model.config", MOCK_CONFIG):
    from src.model import Model, Rate, Base, API_URL


@pytest.fixture
def mock_model():
    # Create a Model instance which will set up its own in-memory database
    # by patching DB_FILE to ':memory:'
    with patch("src.model.DB_FILE", ":memory:"):
        model = Model()
        yield model
    # The engine is disposed when the model instance goes out of scope,
    # or explicitly by calling model.close() if needed.


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
                    mock_view_instance.table.setItem(
                        row_idx, col_idx, MagicMock(text=str(item))
                    )

        mock_view_instance.update_table.side_effect = update_table_side_effect
        return mock_view_instance


@pytest.fixture
def mock_presenter(mock_model, mock_view):
    from src.presenter import Presenter

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
@patch("src.model.HEADERS", MOCK_CONFIG["api"]["headers"])
def test_fetch_and_save_rates_success(mock_get, mock_model):
    """Test Model.fetch_and_save_rates with a successful API response."""
    model = mock_model
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "financingRates": [
            {"instrument": "EUR_USD", "longRate": "0.0083", "shortRate": "-0.0133"}
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = model.fetch_and_save_rates(save_to_db=True)
    assert result == mock_response.json.return_value

    with model.Session() as session:
        assert session.query(Rate).count() == 1
        rate = session.query(Rate).first()
        assert rate.date == datetime.now().strftime("%Y-%m-%d")
        assert json.loads(rate.raw_data) == mock_response.json.return_value


@patch("src.model.requests.get")
def test_fetch_and_save_rates_api_failure(mock_get, mock_model):
    """Test Model.fetch_and_save_rates when API request fails."""
    model = mock_model
    mock_get.side_effect = requests.exceptions.RequestException("API failure")
    result = model.fetch_and_save_rates(save_to_db=True)
    assert result is None
    with model.Session() as session:
        assert session.query(Rate).count() == 0


def test_fetch_and_save_rates_db_error(mock_model):
    """Test Model.fetch_and_save_rates when database commit fails."""
    model = mock_model
    with (
        patch("src.model.requests.get") as mock_get,
        patch("src.model.HEADERS", MOCK_CONFIG["api"]["headers"]),
    ):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "financingRates": [
                {"instrument": "EUR_USD", "longRate": "0.01", "shortRate": "-0.02"}
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
            mock_get.assert_called_once_with(
                API_URL, headers=MOCK_CONFIG["api"]["headers"], timeout=10
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
        ["EUR_USD", "Forex", "USD", "1.23", "0.01%", "-0.02%", "0.05", "-0.07"],
        ["XAU_USD", "Metals", "USD", "1750.50", "0.03%", "-0.04%", "0.10", "-0.12"],
    ]
    mock_view.update_table(data)
    presenter_instance.process_ui_updates()
    mock_view.update_table.assert_called_once_with(data)
    mock_view.table.setRowCount.assert_called_once_with(2)
    assert mock_view.table.setItem.call_count == 16  # 2 rows * 8 columns
