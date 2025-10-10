import pytest
from unittest.mock import MagicMock, patch # NEW: Import patch
from PyQt6.QtCore import Qt  # Import Qt
from PyQt6.QtGui import QColor
import pandas as pd # NEW: Import pandas

from src.view import View
from src.theme import THEME

# Mock configuration for testing (similar to other test files)
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
    "ui": {"timer_interval": 16, "rate_display_format": "percentage"},
    "logging": {"level": "INFO", "file_path": "test.log"},
}

# Patch the config object before importing View
with patch("src.config.config", MOCK_CONFIG): # NEW: Patch src.config.config
    from src.view import View


@pytest.fixture
def mock_presenter():
    presenter = MagicMock()
    presenter.on_manual_update = MagicMock()
    presenter.on_cancel_update = MagicMock()
    presenter.on_clear_filter = MagicMock()
    presenter.on_category_selected = MagicMock()
    presenter.on_filter_text_changed = MagicMock()
    presenter.on_instrument_double_clicked = MagicMock()
    return presenter


@pytest.fixture
def view_instance(qapp, mock_presenter):
    view = View(mock_presenter)
    view.set_presenter(mock_presenter)  # Explicitly call set_presenter
    view.show()
    yield view
    view.close()


def test_update_table_basic(view_instance):
    view_instance.update_table(
        [["EUR_USD", "Forex", "USD", 1, "1.00%", "-2.00%", "", "", ""]]
    )
    assert view_instance.table.rowCount() == 1
    assert view_instance.table.item(0, 0).text() == "EUR_USD"


def test_update_table_colors(view_instance):
    view_instance.update_table(
        [["EUR_USD", "Forex", "USD", 1, "1.00%", "-2.00%", "", "", ""]]
    )
    assert view_instance.table.item(0, 4).foreground().color() == QColor(
        THEME["plot_long_rate_color"]
    )
    assert view_instance.table.item(0, 5).foreground().color() == QColor(
        THEME["plot_short_rate_color"]
    )


def test_update_table_numeric_sorting(view_instance):
    view_instance.update_table(
        [
            ["EUR_USD", "Forex", "USD", 1, "0.01", "-0.02", "", "", ""],
            ["GBP_USD", "Forex", "USD", 1, "0.03", "-0.01", "", "", ""],
        ]
    )
    view_instance.table.sortByColumn(4, Qt.SortOrder.AscendingOrder)
    assert view_instance.table.item(0, 0).text() == "EUR_USD"


def test_update_table_empty_data(view_instance):
    view_instance.update_table([])
    assert view_instance.table.rowCount() == 0


def test_update_table_preserves_sort_order(view_instance):
    view_instance.update_table(
        [
            ["EUR_USD", "Forex", "USD", 1, "0.01", "-0.02", "", "", ""],
            ["GBP_USD", "Forex", "USD", 1, "0.03", "-0.01", "", "", ""],
        ]
    )
    view_instance.table.sortByColumn(4, Qt.SortOrder.AscendingOrder)
    view_instance.update_table(
        [
            ["AUD_USD", "Forex", "USD", 1, "0.005", "-0.001", "", "", ""],
            ["EUR_USD", "Forex", "USD", 1, "0.01", "-0.02", "", "", ""],
            ["GBP_USD", "Forex", "USD", 1, "0.03", "-0.01", "", "", ""],
        ]
    )
    assert view_instance.table.item(0, 0).text() == "AUD_USD"


def test_update_table_with_non_numeric_rates(view_instance):
    view_instance.update_table(
        [["EUR_USD", "Forex", "USD", 1, "N/A", "-0.02", "", "", ""]]
    )
    assert view_instance.table.item(0, 4).text() == "N/A"


def test_update_button_click(view_instance, mock_presenter):
    view_instance.update_btn.click()
    mock_presenter.on_manual_update.assert_called_once()


def test_cancel_button_click(qtbot, view_instance, mock_presenter):
    view_instance.cancel_btn.setEnabled(True)  # Enable the button before clicking
    qtbot.mouseClick(view_instance.cancel_btn, Qt.MouseButton.LeftButton)
    qtbot.wait(10)  # Give event loop time to process
    mock_presenter.on_cancel_update.assert_called_once()


def test_clear_button_click(qtbot, view_instance, mock_presenter):
    qtbot.mouseClick(view_instance.clear_btn, Qt.MouseButton.LeftButton)
    mock_presenter.on_clear_filter.assert_called_once()


def test_filter_input_changed(view_instance, mock_presenter):
    view_instance.filter_input.setText("EUR")
    mock_presenter.on_filter_text_changed.assert_called_once_with("EUR")


def test_category_combo_changed(qtbot, view_instance, mock_presenter):
    view_instance.category_combo.setCurrentText("Forex")
    qtbot.wait(10)  # Give event loop time to process
    mock_presenter.on_category_selected.assert_called_once_with("Forex")


@patch("src.view.HistoryDialog")
def test_table_double_click(mock_history_dialog, view_instance, mock_presenter):
    mock_history_dialog.return_value.exec.return_value = 0
    view_instance.update_table(
        [["EUR_USD", "Forex", "USD", 1, "1.00%", "-2.00%", "", "", ""]]
    )
    # Simulate the double-click event, which would normally call presenter.on_instrument_double_clicked
    # and then view.show_history_window. For testing, we directly call show_history_window.
    instrument_name = "EUR_USD"
    history_df = pd.DataFrame({ # Create a dummy DataFrame for testing
        "date": ["2023-01-01"],
        "long_rate": [0.01],
        "short_rate": [-0.02]
    })
    stats = {"Mean Long Rate": 0.01, "Mean Short Rate": -0.02}
    view_instance.show_history_window(instrument_name, history_df, stats) # Directly call show_history_window
    mock_history_dialog.assert_called_once_with(instrument_name, history_df, stats, view_instance) # Assert HistoryDialog was called with correct arguments


def test_set_status(view_instance):
    view_instance.set_status("Test Status")
    assert view_instance.status_label.text() == "Test Status"


def test_set_update_time(view_instance):
    view_instance.set_update_time("2025-10-09 10:00:00")
    assert view_instance.update_time_label.text() == "LAST UPDATE: 2025-10-09 10:00:00"


def test_progress_bar_visibility(view_instance):
    view_instance.show_progress_bar()
    assert view_instance.progress_bar.isVisible() is True

    view_instance.hide_progress_bar()
    assert view_instance.progress_bar.isVisible() is False


def test_clear_inputs(qtbot, view_instance):
    view_instance.filter_input.setText("test")
    view_instance.category_combo.setCurrentIndex(2)
    view_instance.clear_inputs()
    assert view_instance.filter_input.text() == ""
    assert view_instance.category_combo.currentIndex() == 0
