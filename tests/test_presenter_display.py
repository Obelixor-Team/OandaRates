import pytest
from unittest.mock import MagicMock
from src.presenter import Presenter


# Mock the Model and View for the Presenter
@pytest.fixture
def mock_model():
    model = MagicMock()
    # Configure categorize_instrument to return a predictable category
    model.categorize_instrument.side_effect = lambda instrument: {
        "EUR_USD": "Forex",
        "GBP_USD": "Forex",  # Added for currency inference test
        "XAU_USD": "Metals",
        "WTICO_USD": "Commodities",
        "US30_USD": "Indices",
        "DE10YB_EUR": "Bonds",
        "SOME_INSTRUMENT_CFD": "CFDs",
        "UNKNOWN": "Other",
        "AUD/CAD": "Other",  # For currency inference test
        "UNKNOWN_CURRENCY": "Other",  # For currency inference test
    }.get(instrument, "Other")
    return model


@pytest.fixture
def mock_view():
    view = MagicMock()
    return view


@pytest.fixture
def presenter_instance(mock_model, mock_view):
    presenter = Presenter(mock_model, mock_view)
    # Manually set the presenter in the mock view, as it's done in main.py
    mock_view._presenter = presenter
    mock_view.set_presenter(presenter)  # Call the set_presenter method
    return presenter


# Sample raw data for testing
SAMPLE_RAW_DATA = {
    "financingRates": [
        {
            "instrument": "EUR_USD",
            "longRate": 0.01,
            "shortRate": -0.02,
            "currency": "USD",
            "days": 1,
            "longCharge": "",
            "shortCharge": "",
            "units": "",
        },
        {
            "instrument": "XAU_USD",
            "longRate": 0.05,
            "shortRate": -0.06,
            "currency": "USD",
            "days": 1,
            "longCharge": "",
            "shortCharge": "",
            "units": "",
        },
        {
            "instrument": "WTICO_USD",
            "longRate": 0.10,
            "shortRate": -0.11,
            "currency": "USD",
            "days": 1,
            "longCharge": "",
            "shortCharge": "",
            "units": "",
        },
        {
            "instrument": "US30_USD",
            "longRate": 0.02,
            "shortRate": -0.03,
            "currency": "USD",
            "days": 1,
            "longCharge": "",
            "shortCharge": "",
            "units": "",
        },
        {
            "instrument": "DE10YB_EUR",
            "longRate": 0.005,
            "shortRate": -0.006,
            "currency": "EUR",
            "days": 1,
            "longCharge": "",
            "shortCharge": "",
            "units": "",
        },
        {
            "instrument": "SOME_INSTRUMENT_CFD",
            "longRate": 0.03,
            "shortRate": -0.04,
            "currency": "USD",
            "days": 1,
            "longCharge": "",
            "shortCharge": "",
            "units": "",
        },
        {
            "instrument": "UNKNOWN",
            "longRate": 0.07,
            "shortRate": -0.08,
            "currency": "GBP",
            "days": 1,
            "longCharge": "",
            "shortCharge": "",
            "units": "",
        },
    ]
}


def test_update_display_no_raw_data(presenter_instance, mock_view):
    presenter_instance.raw_data = {}
    presenter_instance._update_display()
    mock_view.update_table.assert_called_once_with([])


def test_update_display_with_raw_data_no_filter(presenter_instance, mock_view):
    presenter_instance.raw_data = SAMPLE_RAW_DATA
    presenter_instance.filter_text = ""
    presenter_instance.selected_category = "All"
    presenter_instance._update_display()

    expected_data = [
        ["EUR_USD", "Forex", "USD", 1, "1.00%", "-2.00%", "", "", ""],
        ["XAU_USD", "Metals", "USD", 1, "5.00%", "-6.00%", "", "", ""],
        ["WTICO_USD", "Commodities", "USD", 1, "10.00%", "-11.00%", "", "", ""],
        ["US30_USD", "Indices", "USD", 1, "2.00%", "-3.00%", "", "", ""],
        ["DE10YB_EUR", "Bonds", "EUR", 1, "0.50%", "-0.60%", "", "", ""],
        ["SOME_INSTRUMENT_CFD", "CFDs", "USD", 1, "3.00%", "-4.00%", "", "", ""],
        ["UNKNOWN", "Other", "GBP", 1, "7.00%", "-8.00%", "", "", ""],
    ]
    mock_view.update_table.assert_called_once_with(expected_data)
    mock_view.set_status.assert_called_once_with(
        "Display updated. Showing 7 instruments."
    )


def test_update_display_with_filter_text(presenter_instance, mock_view):
    presenter_instance.raw_data = SAMPLE_RAW_DATA
    presenter_instance.filter_text = "eur"
    presenter_instance.selected_category = "All"
    presenter_instance._update_display()

    expected_data = [
        ["EUR_USD", "Forex", "USD", 1, "1.00%", "-2.00%", "", "", ""],
        ["DE10YB_EUR", "Bonds", "EUR", 1, "0.50%", "-0.60%", "", "", ""],
    ]
    mock_view.update_table.assert_called_once_with(expected_data)
    mock_view.set_status.assert_called_once_with(
        "Display updated. Showing 2 instruments."
    )


def test_update_display_with_selected_category(presenter_instance, mock_view):
    presenter_instance.raw_data = SAMPLE_RAW_DATA
    presenter_instance.filter_text = ""
    presenter_instance.selected_category = "Metals"
    presenter_instance._update_display()

    expected_data = [
        ["XAU_USD", "Metals", "USD", 1, "5.00%", "-6.00%", "", "", ""],
    ]
    mock_view.update_table.assert_called_once_with(expected_data)
    mock_view.set_status.assert_called_once_with(
        "Display updated. Showing 1 instruments."
    )


def test_update_display_with_filter_and_category(presenter_instance, mock_view):
    presenter_instance.raw_data = SAMPLE_RAW_DATA
    presenter_instance.filter_text = "us"
    presenter_instance.selected_category = "Indices"
    presenter_instance._update_display()

    expected_data = [
        ["US30_USD", "Indices", "USD", 1, "2.00%", "-3.00%", "", "", ""],
    ]
    mock_view.update_table.assert_called_once_with(expected_data)
    mock_view.set_status.assert_called_once_with(
        "Display updated. Showing 1 instruments."
    )


def test_update_display_currency_inference(presenter_instance, mock_view):
    presenter_instance.raw_data = {
        "financingRates": [
            {
                "instrument": "AUD/CAD",
                "longRate": 0.01,
                "shortRate": -0.02,
                "currency": "CAD",
                "days": 1,
                "longCharge": "",
                "shortCharge": "",
                "units": "",
            },
            {
                "instrument": "GBP_USD",
                "longRate": 0.01,
                "shortRate": -0.02,
                "currency": "USD",
                "days": 1,
                "longCharge": "",
                "shortCharge": "",
                "units": "",
            },
            {
                "instrument": "UNKNOWN_CURRENCY",
                "longRate": 0.01,
                "shortRate": -0.02,
                "currency": "JPY",
                "days": 1,
                "longCharge": "",
                "shortCharge": "",
                "units": "",
            },
        ]
    }
    presenter_instance.filter_text = ""
    presenter_instance.selected_category = "All"
    presenter_instance._update_display()

    expected_data = [
        ["AUD/CAD", "Other", "CAD", 1, "1.00%", "-2.00%", "", "", ""],
        ["GBP_USD", "Forex", "USD", 1, "1.00%", "-2.00%", "", "", ""],
        ["UNKNOWN_CURRENCY", "Other", "JPY", 1, "1.00%", "-2.00%", "", "", ""],
    ]
    mock_view.update_table.assert_called_once_with(expected_data)
    mock_view.set_status.assert_called_once_with(
        "Display updated. Showing 3 instruments."
    )
