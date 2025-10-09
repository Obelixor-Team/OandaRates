import pytest
from PyQt6.QtWidgets import QApplication, QLineEdit, QComboBox, QPushButton, QTableWidget, QLabel, QProgressBar
from src.view import View
from unittest.mock import MagicMock

@pytest.fixture
def view(qapp, qtbot):
    """Fixture for the View class, initialized with a mock presenter."""
    mock_presenter = MagicMock()
    view_instance = View(presenter=mock_presenter)
    qtbot.addWidget(view_instance)
    return view_instance

def test_view_initialization(view):
    """Test that the View initializes correctly and its main components are present."""
    assert view.windowTitle() == "OANDA FINANCING TERMINAL v4.0"
    assert isinstance(view.filter_input, QLineEdit)
    assert isinstance(view.category_combo, QComboBox)
    assert isinstance(view.clear_btn, QPushButton)
    assert isinstance(view.update_btn, QPushButton)
    assert isinstance(view.cancel_btn, QPushButton)
    assert isinstance(view.table, QTableWidget)
    assert isinstance(view.status_label, QLabel)
    assert isinstance(view.update_time_label, QLabel)
    assert isinstance(view.progress_bar, QProgressBar)

    assert view.cancel_btn.isEnabled() == False
    assert view.table.columnCount() == 9
    assert view.status_label.text() == "TERMINAL READY"
    assert view.update_time_label.text() == "LAST UPDATE: NEVER"
    assert view.progress_bar.isVisible() == False
