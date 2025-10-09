import pytest
from unittest.mock import MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from src.view import View
from src.theme import THEME


@pytest.fixture(scope="session")
def app(request):
    """Fixture for QApplication instance."""
    _app = QApplication([])
    yield _app


@pytest.fixture
def mock_presenter():
    presenter = MagicMock()
    return presenter


@pytest.fixture
def view_instance(app, mock_presenter):
    view = View(mock_presenter)
    view.set_presenter(mock_presenter)  # Explicitly call set_presenter
    view.show()
    yield view
    view.close()


# Sample data for testing update_table
SAMPLE_TABLE_DATA = [
    ["EUR/USD", "Forex", "USD", 1, "1.00%", "-2.00%", "", "", ""],
    ["XAU/USD", "Metals", "USD", 1, "5.00%", "-6.00%", "", "", ""],
    ["US30/USD", "Indices", "USD", 1, "-0.50%", "0.75%", "", "", ""],
]


def test_update_table_basic(view_instance):
    view_instance.update_table(SAMPLE_TABLE_DATA)

    assert view_instance.table.rowCount() == len(SAMPLE_TABLE_DATA)
    assert view_instance.table.item(0, 0).text() == "EUR/USD"
    assert view_instance.table.item(1, 1).text() == "Metals"
    assert view_instance.table.item(2, 4).text() == "-0.50%"

    # Check if sorting is re-enabled
    assert view_instance.table.isSortingEnabled()


def test_update_table_colors(view_instance):
    view_instance.update_table(SAMPLE_TABLE_DATA)

    # Check colors for Long Rate (col 4) and Short Rate (col 5)
    # EUR/USD: Long Rate 1.00% (positive), Short Rate -2.00% (negative)
    assert view_instance.table.item(0, 4).foreground().color() == QColor(
        THEME["positive"]
    )
    assert view_instance.table.item(0, 5).foreground().color() == QColor(
        THEME["negative"]
    )

    # XAU/USD: Long Rate 5.00% (positive), Short Rate -6.00% (negative)
    assert view_instance.table.item(1, 4).foreground().color() == QColor(
        THEME["positive"]
    )
    assert view_instance.table.item(1, 5).foreground().color() == QColor(
        THEME["negative"]
    )

    # US30/USD: Long Rate -0.50% (negative), Short Rate 0.75% (positive)
    assert view_instance.table.item(2, 4).foreground().color() == QColor(
        THEME["negative"]
    )
    assert view_instance.table.item(2, 5).foreground().color() == QColor(
        THEME["positive"]
    )


def test_update_table_numeric_sorting(view_instance):
    # Data that would sort differently numerically vs alphabetically
    data_for_sorting = [
        ["A", "", "", "", "10.00%", "", "", "", ""],
        ["B", "", "", "", "2.00%", "", "", "", ""],
        ["C", "", "", "", "-5.00%", "", "", "", ""],
    ]
    view_instance.update_table(data_for_sorting)

    # Sort by Long Rate (column 4) ascending
    view_instance.table.sortItems(4, Qt.SortOrder.AscendingOrder)
    assert view_instance.table.item(0, 0).text() == "C"  # -5.00%
    assert view_instance.table.item(1, 0).text() == "B"  # 2.00%
    assert view_instance.table.item(2, 0).text() == "A"  # 10.00%

    # Sort by Long Rate (column 4) descending
    view_instance.table.sortItems(4, Qt.SortOrder.DescendingOrder)
    assert view_instance.table.item(0, 0).text() == "A"  # 10.00%
    assert view_instance.table.item(1, 0).text() == "B"  # 2.00%
    assert view_instance.table.item(2, 0).text() == "C"  # -5.00%


def test_update_table_empty_data(view_instance):
    view_instance.update_table([])
    assert view_instance.table.rowCount() == 0


def test_update_table_preserves_sort_order(view_instance):
    # Initial data and sort
    initial_data = [
        ["Z", "", "", "", "1.00%", "", "", "", ""],
        ["A", "", "", "", "10.00%", "", "", "", ""],
    ]
    view_instance.update_table(initial_data)
    view_instance.table.sortItems(0, Qt.SortOrder.AscendingOrder)  # Sort by Instrument

    # New data, should preserve sort order after update
    new_data = [
        ["B", "", "", "", "5.00%", "", "", "", ""],
        ["A", "", "", "", "10.00%", "", "", "", ""],
        ["C", "", "", "", "2.00%", "", "", "", ""],
    ]
    view_instance.update_table(new_data)

    # Assert that the table is still sorted by Instrument (column 0)
    assert view_instance.table.item(0, 0).text() == "A"
    assert view_instance.table.item(1, 0).text() == "B"
    assert view_instance.table.item(2, 0).text() == "C"


def test_update_table_with_non_numeric_rates(view_instance):
    data_with_non_numeric = [
        ["X", "", "", "", "N/A", "", "", "", ""],
        ["Y", "", "", "", "1.00%", "", "", "", ""],
    ]
    view_instance.update_table(data_with_non_numeric)

    assert view_instance.table.rowCount() == 2
    assert view_instance.table.item(0, 4).text() == "N/A"
    assert view_instance.table.item(1, 4).text() == "1.00%"
    # Ensure no error when sorting with non-numeric data
    view_instance.table.sortItems(4, Qt.SortOrder.AscendingOrder)
    assert view_instance.table.item(0, 0).text() == "Y"  # Fallback to string comparison


def test_update_button_click(view_instance, mock_presenter):
    view_instance.update_btn.click()
    mock_presenter.on_manual_update.assert_called_once()


def test_cancel_button_click(view_instance, mock_presenter):
    view_instance.cancel_btn.setEnabled(True)  # Enable the button
    view_instance.cancel_btn.click()
    mock_presenter.on_cancel_update.assert_called_once()


def test_clear_button_click(view_instance, mock_presenter):
    view_instance.clear_btn.click()
    mock_presenter.on_clear_filter.assert_called_once()


def test_filter_input_changed(view_instance, mock_presenter):
    test_text = "test filter"
    view_instance.filter_input.setText(test_text)
    mock_presenter.on_filter_text_changed.assert_called_once_with(test_text)


def test_category_combo_changed(view_instance, mock_presenter):
    test_category = "Forex"
    view_instance.category_combo.setCurrentText(test_category)
    mock_presenter.on_category_selected.assert_called_once_with(test_category)


def test_table_double_click(view_instance, mock_presenter):
    view_instance.update_table(SAMPLE_TABLE_DATA)
    # Simulate a double-click on the first item
    view_instance.table.itemDoubleClicked.emit(view_instance.table.item(0, 0))
    mock_presenter.on_instrument_double_clicked.assert_called_once_with("EUR/USD")


def test_set_status(view_instance):
    view_instance.set_status("Test status message")
    assert view_instance.status_label.text() == "Test status message"
    assert view_instance.status_label.styleSheet() == f"color: {THEME['positive']};"

    view_instance.set_status("Error message", is_error=True)
    assert view_instance.status_label.text() == "Error message"
    assert view_instance.status_label.styleSheet() == f"color: {THEME['negative']};"


def test_set_update_time(view_instance):
    test_time = "2025-10-09"
    view_instance.set_update_time(test_time)
    assert view_instance.update_time_label.text() == f"LAST UPDATE: {test_time}"


def test_progress_bar_visibility(view_instance):
    view_instance.show_progress_bar()
    assert view_instance.progress_bar.isVisible() is True

    view_instance.hide_progress_bar()
    assert view_instance.progress_bar.isVisible() is False
