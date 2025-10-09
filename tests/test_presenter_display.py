import pytest
from unittest.mock import MagicMock, patch
import time

# Mock configuration for testing (similar to test_oanda_terminal.py)
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
    "ui": {"timer_interval": 16, "rate_display_format": "percentage"}, # NEW: Add rate_display_format
    "logging": {"level": "INFO", "file_path": "test.log"},
}

# Patch the config object before importing Presenter
with patch("src.config.config", MOCK_CONFIG):
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
    model.infer_currency = MagicMock(
        side_effect=lambda instrument, api_currency: {
            "EUR_USD": "USD",
            "XAU_USD": "USD",
            "WTICO_USD": "USD",
            "US30_USD": "USD",
            "DE10YB_EUR": "EUR",
            "SOME_INSTRUMENT_CFD": "USD",
            "UNKNOWN": "GBP",
            "AUD/CAD": "CAD",
            "GBP_USD": "USD",
            "UNKNOWN_CURRENCY": "JPY",
        }.get(instrument, api_currency)
    )
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
    presenter_instance.process_ui_updates()
    mock_view.update_table.assert_called_once_with([])


def test_update_display_with_raw_data_no_filter(
    presenter_instance, mock_model, mock_view
):
    presenter_instance.raw_data = presenter_instance._process_and_cache_data(
        SAMPLE_RAW_DATA
    )
    presenter_instance.filter_text = ""
    presenter_instance.selected_category = "All"
    presenter_instance._update_display()
    presenter_instance.process_ui_updates()

    expected_data = [
        [
            "EUR_USD",
            "Forex",
            mock_model.infer_currency("EUR_USD", "USD"),
            "1",
            "1.00%",
            "-2.00%",
            "",
            "",
            "",
        ],
        [
            "XAU_USD",
            "Metals",
            mock_model.infer_currency("XAU_USD", "USD"),
            "1",
            "5.00%",
            "-6.00%",
            "",
            "",
            "",
        ],
        [
            "WTICO_USD",
            "Commodities",
            mock_model.infer_currency("WTICO_USD", "USD"),
            "1",
            "10.00%",
            "-11.00%",
            "",
            "",
            "",
        ],
        [
            "US30_USD",
            "Indices",
            mock_model.infer_currency("US30_USD", "USD"),
            "1",
            "2.00%",
            "-3.00%",
            "",
            "",
            "",
        ],
        [
            "DE10YB_EUR",
            "Bonds",
            mock_model.infer_currency("DE10YB_EUR", "EUR"),
            "1",
            "0.50%",
            "-0.60%",
            "",
            "",
            "",
        ],
        [
            "SOME_INSTRUMENT_CFD",
            "CFDs",
            mock_model.infer_currency("SOME_INSTRUMENT_CFD", "USD"),
            "1",
            "3.00%",
            "-4.00%",
            "",
            "",
            "",
        ],
        [
            "UNKNOWN",
            "Other",
            mock_model.infer_currency("UNKNOWN", "GBP"),
            "1",
            "7.00%",
            "-8.00%",
            "",
            "",
            "",
        ],
    ]
    mock_view.update_table.assert_called_once_with(expected_data)
    mock_view.set_status.assert_called_once_with(
        "Display updated. Showing 7 instruments.", is_error=False
    )


def test_update_display_with_filter_text(presenter_instance, mock_model, mock_view):
    presenter_instance.raw_data = presenter_instance._process_and_cache_data(
        SAMPLE_RAW_DATA
    )
    presenter_instance.filter_text = "eur"
    presenter_instance.selected_category = "All"
    presenter_instance._update_display()
    presenter_instance.process_ui_updates()

    expected_data = [
        [
            "EUR_USD",
            "Forex",
            mock_model.infer_currency("EUR_USD", "USD"),
            "1",
            "1.00%",
            "-2.00%",
            "",
            "",
            "",
        ],
        [
            "DE10YB_EUR",
            "Bonds",
            mock_model.infer_currency("DE10YB_EUR", "EUR"),
            "1",
            "0.50%",
            "-0.60%",
            "",
            "",
            "",
        ],
    ]
    mock_view.update_table.assert_called_once_with(expected_data)
    mock_view.set_status.assert_called_once_with(
        "Display updated. Showing 2 instruments.", is_error=False
    )


def test_update_display_with_selected_category(
    presenter_instance, mock_model, mock_view
):
    presenter_instance.raw_data = presenter_instance._process_and_cache_data(
        SAMPLE_RAW_DATA
    )
    presenter_instance.filter_text = ""
    presenter_instance.selected_category = "Metals"
    presenter_instance._update_display()
    presenter_instance.process_ui_updates()

    expected_data = [
        [
            "XAU_USD",
            "Metals",
            mock_model.infer_currency("XAU_USD", "USD"),
            "1",
            "5.00%",
            "-6.00%",
            "",
            "",
            "",
        ],
    ]
    mock_view.update_table.assert_called_once_with(expected_data)
    mock_view.set_status.assert_called_once_with(
        "Display updated. Showing 1 instruments.", is_error=False
    )


def test_update_display_with_filter_and_category(
    presenter_instance, mock_model, mock_view
):
    presenter_instance.raw_data = presenter_instance._process_and_cache_data(
        SAMPLE_RAW_DATA
    )
    presenter_instance.filter_text = "us"
    presenter_instance.selected_category = "Indices"
    presenter_instance._update_display()
    presenter_instance.process_ui_updates()

    expected_data = [
        [
            "US30_USD",
            "Indices",
            mock_model.infer_currency("US30_USD", "USD"),
            "1",
            "2.00%",
            "-3.00%",
            "",
            "",
            "",
        ],
    ]
    mock_view.update_table.assert_called_once_with(expected_data)
    mock_view.set_status.assert_called_once_with(
        "Display updated. Showing 1 instruments.", is_error=False
    )


def test_update_display_currency_inference(presenter_instance, mock_model, mock_view):
    presenter_instance.raw_data = presenter_instance._process_and_cache_data(
        {
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
    )
    presenter_instance.filter_text = ""
    presenter_instance.selected_category = "All"
    presenter_instance._update_display()
    presenter_instance.process_ui_updates()

    expected_data = [
        [
            "AUD/CAD",
            "Other",
            mock_model.infer_currency("AUD/CAD", "CAD"),
            "1",
            "1.00%",
            "-2.00%",
            "",
            "",
            "",
        ],
        [
            "GBP_USD",
            "Forex",
            mock_model.infer_currency("GBP_USD", "USD"),
            "1",
            "1.00%",
            "-2.00%",
            "",
            "",
            "",
        ],
        [
            "UNKNOWN_CURRENCY",
            "Other",
            mock_model.infer_currency("UNKNOWN_CURRENCY", "JPY"),
            "1",
            "1.00%",
            "-2.00%",
            "",
            "",
            "",
        ],
    ]
    mock_view.update_table.assert_called_once_with(expected_data)
    mock_view.set_status.assert_called_once_with(
        "Display updated. Showing 3 instruments.", is_error=False
    )

    def test_on_manual_update_success(presenter_instance, mock_model, mock_view):
        # Mock the model's fetch_and_save_rates to return sample data
        mock_model.fetch_and_save_rates.return_value = SAMPLE_RAW_DATA

        # Call the method under test
        presenter_instance.on_manual_update()

        # Wait for the executor to complete the _fetch_job
        presenter_instance.executor.shutdown(wait=True)

        # Process all UI updates from the queue
        while not presenter_instance.ui_update_queue.empty():
            presenter_instance.process_ui_updates()

        # Assert that view methods are called correctly
        mock_view.set_update_buttons_enabled.assert_any_call(False)
        mock_view.set_update_buttons_enabled.assert_any_call(True)
        mock_view.set_status.assert_any_call(
            "Fetching new data from API...", is_error=False
        )
        mock_view.show_progress_bar.assert_called_once()
        mock_model.fetch_and_save_rates.assert_called_once_with(save_to_db=False)
        mock_view.set_status.assert_any_call(
            "Manual update successful (not saved to DB).", is_error=False
        )
        mock_view.hide_progress_bar.assert_called()
        mock_view.set_update_time.assert_called_once()
        mock_view.update_table.assert_called_once()


def test_on_manual_update_cancellation(presenter_instance, mock_model, mock_view):
    # Mock the model's fetch_and_save_rates to simulate a long-running operation
    # that checks for cancellation
    mock_model.fetch_and_save_rates.side_effect = lambda save_to_db: (
        presenter_instance._cancellation_event.is_set()
        and time.sleep(0.1)  # Simulate work
    )

    with patch.object(presenter_instance.executor, "submit"):
        # Start the manual update
        presenter_instance.on_manual_update()

        # Request cancellation
        presenter_instance.on_cancel_update()

        # Manually call the _fetch_job, which will now see _is_cancellation_requested as True
        presenter_instance._fetch_job("manual")

        # Process all UI updates from the queue
        while not presenter_instance.ui_update_queue.empty():
            presenter_instance.process_ui_updates()

        from unittest.mock import call

        # Assert that cancellation was handled
        assert (
            presenter_instance._cancellation_event.is_set() is False
        )  # It should be cleared after handling
        mock_view.set_status.assert_any_call(
            "Cancellation requested. Waiting for current operation to finish...",
            is_error=False,
        )
        mock_view.set_update_buttons_enabled.assert_any_call(True)
        assert (
            call("Update cancelled.", is_error=True)
            in mock_view.set_status.call_args_list
        )
        mock_view.hide_progress_bar.assert_called_once()
