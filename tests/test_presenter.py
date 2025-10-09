import pytest
from src.presenter import Presenter

def test_on_filter_text_changed_triggers_update(mock_view, mock_model):
    p = Presenter(mock_model, mock_view)
    p.raw_data = {"financingRates": [{"instrument": "EUR_USD"}]}
    p.on_filter_text_changed("eur")
    p.process_ui_updates()
    mock_view.update_table.assert_called()
