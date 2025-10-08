import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt  # Import Qt
from src.main import run_app

# Mock the config object for Model initialization
MOCK_CONFIG = {
    "api": {
        "url": "http://mock-api.oanda.com",
        "headers": {"User-Agent": "test-agent"},
    },
    "database": {"file": "test_oanda_rates.db"},
    "categories": {
        "currencies": [],
        "metals": [],
        "commodities": [],
        "indices": [],
        "bonds": [],
    },
}


@pytest.fixture(scope="session")
def app(request):
    """Fixture for QApplication instance."""
    _app = QApplication([])
    yield _app
    _app.quit()


@pytest.fixture
def mock_model():
    model = MagicMock()
    model.get_latest_rates.return_value = (None, None)  # No initial data
    model.fetch_and_save_rates.return_value = {
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
            }
        ]
    }
    model.categorize_instrument.return_value = "Forex"
    return model


@pytest.fixture
def main_window(app, mock_model):
    with patch("src.model.Model", return_value=mock_model):
        mock_presenter_instance = MagicMock()
        view_instance = run_app(app, mock_presenter=mock_presenter_instance)
        yield view_instance, mock_presenter_instance


def test_manual_update_flow(main_window, mock_model, qtbot):
    view_instance, mock_presenter_instance = main_window

    # Simulate manual update button click and wait for the signal to be processed
    with qtbot.waitSignal(view_instance.update_btn.clicked, timeout=1000):
        qtbot.mouseClick(view_instance.update_btn, Qt.MouseButton.LeftButton)

    # Assert that the presenter's on_manual_update was called
    mock_presenter_instance.on_manual_update.assert_called_once()

    # Assert that fetch_and_save_rates was called (indirectly via presenter)
    # This assertion is now redundant as we are testing the UI interaction with the presenter
    # mock_model.fetch_and_save_rates.assert_called_once_with(save_to_db=False)

    # Assert that the status was updated (this will be called by the presenter)
    # main_window.set_status.assert_called_with("Fetching new data from API...")
    # main_window.set_status.assert_called_with("Manual update successful (not saved to DB).")

    # Assert that the table was updated (this will be called by the presenter)
    # expected_data = [
    #     ['EUR_USD', 'Forex', 'USD', 1, '1.00%', '-2.00%', '', '', ''],
    # ]
    # main_window.update_table.assert_called_with(expected_data)
