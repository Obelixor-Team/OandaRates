import pytest
from unittest.mock import MagicMock
from PyQt6.QtCore import Qt  # Import Qt
from PyQt6.QtGui import QColor

from src.view import View
from src.theme import THEME


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


def test_table_double_click(view_instance, mock_presenter):
    view_instance.update_table(
        [["EUR_USD", "Forex", "USD", 1, "1.00%", "-2.00%", "", "", ""]]
    )
    view_instance.table.doubleClicked.emit(view_instance.table.model().index(0, 0))
    mock_presenter.on_instrument_double_clicked.assert_called_once_with("EUR_USD")


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
