import pytest
from PyQt6.QtWidgets import (
    QLineEdit,
    QComboBox,
    QPushButton,
    QTableWidget,
    QProgressBar,
    QLabel,
)
from src.view import View
from src.presenter import Presenter


@pytest.fixture
def view_instance(qapp):
    presenter = Presenter(None, None)  # Mock presenter for View initialization
    view = View(presenter)
    view.show()
    yield view
    view.close()


def test_view_initialization(view_instance):
    view = view_instance
    assert isinstance(view.filter_input, QLineEdit)
    assert isinstance(view.category_combo, QComboBox)
    assert isinstance(view.update_btn, QPushButton)
    assert isinstance(view.cancel_btn, QPushButton)
    assert isinstance(view.clear_btn, QPushButton)
    assert isinstance(view.table, QTableWidget)
    assert isinstance(view.status_label, QLabel)
    assert isinstance(view.update_time_label, QLabel)
    assert isinstance(view.progress_bar, QProgressBar)

    assert not view.cancel_btn.isEnabled()
    assert view.table.columnCount() == 9
    assert view.status_label.text() == "TERMINAL READY"
    assert view.update_time_label.text() == "LAST UPDATE: NEVER"
    assert not view.progress_bar.isVisible()
