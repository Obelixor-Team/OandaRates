import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.model import API_URL, HEADERS, Model, Rate, Base


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def model(db_session):
    with patch("src.model.Session", return_value=db_session):
        yield Model()


def test_categorize_instrument():
    model_instance = Model()
    assert model_instance.categorize_instrument("EUR/USD") == "Forex"
    assert model_instance.categorize_instrument("XAU/USD") == "Metals"
    assert model_instance.categorize_instrument("WTICO/USD") == "Commodities"
    assert model_instance.categorize_instrument("US30/USD") == "Indices"
    assert model_instance.categorize_instrument("DE10YB/EUR") == "Bonds"
    assert model_instance.categorize_instrument("A3M_CFD.ES") == "CFDs"
    assert model_instance.categorize_instrument("UNKNOWN_INSTRUMENT") == "Other"


def test_fetch_and_save_rates_success(model, db_session):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "financingRates": [
            {"instrument": "EUR/USD", "longRate": "0.01", "shortRate": "-0.01"}
        ]
    }

    with patch("requests.get", return_value=mock_response) as mock_get:
        with patch("src.model.Session", return_value=db_session):
            with patch("src.model.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 10, 8)
                data = model.fetch_and_save_rates(save_to_db=True)
                mock_get.assert_called_once_with(API_URL, headers=HEADERS, timeout=10)
                assert data is not None
                assert "financingRates" in data

                rate_entry = db_session.query(Rate).filter_by(date="2025-10-08").first()
                assert rate_entry is not None
                assert (
                    json.loads(rate_entry.raw_data) == mock_response.json.return_value
                )


def test_fetch_and_save_rates_no_save(model, db_session):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "financingRates": [
            {"instrument": "EUR/USD", "longRate": "0.01", "shortRate": "-0.01"}
        ]
    }

    with patch("requests.get", return_value=mock_response) as mock_get:
        with patch("src.model.Session", return_value=db_session):
            with patch("src.model.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 10, 8)
                data = model.fetch_and_save_rates(save_to_db=False)
                mock_get.assert_called_once_with(API_URL, headers=HEADERS, timeout=10)
                assert data is not None

                rate_entry = db_session.query(Rate).filter_by(date="2025-10-08").first()
                assert rate_entry is None  # Should not be saved to DB


def test_get_latest_rates(model, db_session):
    # Add some dummy data to the database
    today = "2025-10-08"
    yesterday = "2025-10-07"
    mock_data_today = {
        "financingRates": [
            {"instrument": "EUR/USD", "longRate": "0.02", "shortRate": "-0.02"}
        ]
    }
    mock_data_yesterday = {
        "financingRates": [
            {"instrument": "EUR/USD", "longRate": "0.01", "shortRate": "-0.01"}
        ]
    }

    db_session.add(Rate(date=yesterday, raw_data=json.dumps(mock_data_yesterday)))
    db_session.add(Rate(date=today, raw_data=json.dumps(mock_data_today)))
    db_session.commit()

    date, data = model.get_latest_rates()
    assert date == today
    assert data == mock_data_today


def test_get_instrument_history(model, db_session):
    # Add some dummy data to the database
    day1 = "2025-10-06"
    day2 = "2025-10-07"
    day3 = "2025-10-08"

    mock_data_day1 = {
        "financingRates": [
            {"instrument": "EUR/USD", "longRate": "0.01", "shortRate": "-0.01"}
        ]
    }
    mock_data_day2 = {
        "financingRates": [
            {"instrument": "EUR/USD", "longRate": "0.02", "shortRate": "-0.02"}
        ]
    }
    mock_data_day3 = {
        "financingRates": [
            {"instrument": "GBP/JPY", "longRate": "0.03", "shortRate": "-0.03"}
        ]
    }

    db_session.add(Rate(date=day1, raw_data=json.dumps(mock_data_day1)))
    db_session.add(Rate(date=day2, raw_data=json.dumps(mock_data_day2)))
    db_session.add(Rate(date=day3, raw_data=json.dumps(mock_data_day3)))
    db_session.commit()

    history_df = model.get_instrument_history("EUR/USD")
    assert not history_df.empty
    assert len(history_df) == 2
    assert history_df["date"].tolist() == [day1, day2]
    assert history_df["long_rate"].tolist() == ["0.01", "0.02"]
    assert history_df["short_rate"].tolist() == ["-0.01", "-0.02"]
