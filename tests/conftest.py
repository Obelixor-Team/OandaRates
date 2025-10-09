import pytest
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.model import Base, Model

@pytest.fixture
def mock_requests(mocker):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "financingRates": [
            {"instrument": "EUR_USD", "longRate": "0.0083", "shortRate": "-0.0133"}
        ]
    }
    mocker.patch("requests.get", return_value=mock_response)
    return mock_response

@pytest.fixture
def mock_view():
    view = MagicMock()
    view.table = MagicMock()
    view.table.setRowCount = MagicMock()
    view.table.setItem = MagicMock()
    return view

@pytest.fixture
def mock_model():
    model = MagicMock()
    model.categorize_instrument.return_value = "Forex"
    model.infer_currency.return_value = "USD"
    return model

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)