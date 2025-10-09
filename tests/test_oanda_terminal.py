import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import json
from sqlalchemy.exc import SQLAlchemyError
import requests

from src.model import Model, Rate
from src.presenter import Presenter
from src.view import View


# Mock configuration for testing
@pytest.fixture
def mock_config():
    return {
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


@pytest.fixture
def mock_model(mock_config, db_session):
    with patch("src.model.config", mock_config):
        model = Model()
        model.session = db_session  # Use the in-memory session
        yield model
        model.session.close()


@pytest.fixture
def mock_view():
    app = MagicMock()
    view = View(app)
    view.set_status = MagicMock(side_effect=lambda text, is_error=False: None)
    view.update_table = MagicMock()
    view.set_update_buttons_enabled = MagicMock()
    view.table = MagicMock()
    view.table.setRowCount = MagicMock()
    view.table.setItem = MagicMock()

    def update_table_side_effect(data):
        view.table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, item in enumerate(row_data):
                view.table.setItem(row_idx, col_idx, MagicMock(text=str(item)))

    view.update_table.side_effect = update_table_side_effect
    return view


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
    assert mock_model.categorize_instrument("EUR_USD") == "Forex"
    assert mock_model.categorize_instrument("XAU_USD") == "Metals"
    assert mock_model.categorize_instrument("WTICO_USD") == "Commodities"
    assert mock_model.categorize_instrument("SPX500_USD") == "Indices"
    assert mock_model.categorize_instrument("US_10YR_TNOTE") == "Bonds"
    assert mock_model.categorize_instrument("BTC_CFD") == "CFDs"
    assert mock_model.categorize_instrument("UNKNOWN") == "Other"


@patch("src.model.requests.get")
def test_fetch_and_save_rates_success(mock_get, mock_model):
    """Test Model.fetch_and_save_rates with a successful API response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "financingRates": [
            {"instrument": "EUR_USD", "longRate": "0.0083", "shortRate": "-0.0133"}
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = mock_model.fetch_and_save_rates(save_to_db=True)
    assert result == mock_response.json.return_value
    assert mock_model.session.query(Rate).count() == 1
    rate = mock_model.session.query(Rate).first()
    assert rate.date == datetime.now().strftime("%Y-%m-%d")
    assert json.loads(rate.raw_data) == mock_response.json.return_value


@patch("src.model.requests.get")
def test_fetch_and_save_rates_api_failure(mock_get, mock_model):
    """Test Model.fetch_and_save_rates when API request fails."""
    mock_get.side_effect = requests.exceptions.RequestException("API failure")
    result = mock_model.fetch_and_save_rates(save_to_db=True)
    assert result is None
    assert mock_model.session.query(Rate).count() == 0


def test_fetch_and_save_rates_db_error(mock_model):
    """Test Model.fetch_and_save_rates when database commit fails."""
    with patch("src.model.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "financingRates": [
                {"instrument": "EUR_USD", "longRate": "0.01", "shortRate": "-0.02"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch.object(
            mock_model.session, "commit", side_effect=SQLAlchemyError("DB error")
        ):
            result = mock_model.fetch_and_save_rates(save_to_db=True)
            assert result is None
            assert mock_model.session.query(Rate).count() == 0


def test_on_filter_text_changed_valid(mock_presenter, mock_view):
    """Test Presenter.on_filter_text_changed with valid input."""
    mock_presenter.on_filter_text_changed("eur")
    assert mock_presenter.filter_text == "eur"
    mock_presenter.process_ui_updates()
    mock_view.set_status.assert_not_called()


def test_on_filter_text_changed_too_long(mock_presenter, mock_view):
    """Test Presenter.on_filter_text_changed with overly long input."""
    long_text = "a" * 101
    mock_presenter.on_filter_text_changed(long_text)
    assert mock_presenter.filter_text == "a" * 100
    mock_presenter.process_ui_updates()
    mock_view.set_status.assert_called_once()
    call_args, call_kwargs = mock_view.set_status.call_args
    assert call_args[0] == "Filter text too long (max 100 chars)"
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
