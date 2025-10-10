import pytest
from PyQt6.QtWidgets import (
    QLineEdit,
    QComboBox,
    QPushButton,
    QTableWidget,
    QProgressBar,
    QLabel,
)
from unittest.mock import patch

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

# Patch the config object before importing Presenter and View
with patch("src.config.config", MOCK_CONFIG):
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
