import pytest
from src.model import Model

@pytest.mark.parametrize("save", [True, False])
def test_fetch_and_save_rates(mock_requests, tmp_path, save):
    model = Model()
    data = model.fetch_and_save_rates(save_to_db=save)
    assert "financingRates" in data
    assert len(data["financingRates"]) > 0
    assert "instrument" in data["financingRates"][0]
