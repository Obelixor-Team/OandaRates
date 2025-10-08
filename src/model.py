import json
import yaml

from datetime import datetime

import pandas as pd
import requests
from sqlalchemy import Column, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Load configuration
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Constants
API_URL = config["api"]["url"]
HEADERS = config["api"]["headers"]
DB_FILE = config["database"]["file"]


# Database setup
class Base(DeclarativeBase):
    pass


class Rate(Base):
    """SQLAlchemy model for storing OANDA financing rates."""

    __tablename__ = "rates"
    date = Column(String, primary_key=True)
    raw_data = Column(Text)


engine = create_engine(f"sqlite:///{DB_FILE}")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


class Model:
    """Manages data operations, including fetching from OANDA API and database."""

    def categorize_instrument(self, instrument):
        """Categorizes an instrument into a specific group based on its name."""
        instrument_lower = instrument.lower().replace("/", "_")

        # Forex
        currencies = config["categories"]["currencies"]
        parts = instrument_lower.split("_")
        if len(parts) == 2 and parts[0] in currencies and parts[1] in currencies:
            return "Forex"

        # Metals
        metals = config["categories"]["metals"]
        if any(m in parts for m in metals):
            return "Metals"

        # Commodities
        commodities = config["categories"]["commodities"]
        if any(c.replace("/", "_") in instrument_lower for c in commodities):
            return "Commodities"

        # Indices
        indices = config["categories"]["indices"]
        if any(i.replace("/", "_") in instrument_lower for i in indices):
            return "Indices"

        # Bonds
        bonds = config["categories"]["bonds"]
        if any(b.replace("/", "_") in instrument_lower for b in bonds):
            return "Bonds"

        # CFDs
        if "_cfd" in instrument_lower:
            return "CFDs"

        return "Other"

    def _infer_currency(self, instrument_name: str, api_currency: str) -> str:
        """Infers the currency from the instrument name or falls back to API provided currency."""
        if "/" in instrument_name:
            return instrument_name.split("/")[1]

        # Mapping of suffixes to currencies
        suffix_to_currency = {
            "USD": "USD",
            "EUR": "EUR",
            "GBP": "GBP",
            "JPY": "JPY",
            "AUD": "AUD",
            "CAD": "CAD",
            "CHF": "CHF",
            "NZD": "NZD",
            "SGD": "SGD",
            "HKD": "HKD",
            "NOK": "NOK",
            "SEK": "SEK",
            "DKK": "DKK",
            "MXN": "MXN",
            "ZAR": "ZAR",
            "TRY": "TRY",
            "CNH": "CNH",
            "PLN": "PLN",
            "CZK": "CZK",
            "HUF": "HUF",
        }

        for suffix, currency in suffix_to_currency.items():
            if instrument_name.endswith(suffix):
                return currency

        return api_currency  # Fallback to API provided currency

    def fetch_and_save_rates(self, save_to_db: bool = True):
        """Fetch financing rates from the OANDA API and save them to the database.

        Args:
            save_to_db: Whether to save the fetched data to the database.

        Returns:
            dict: The fetched data, or None on failure.

        """
        try:
            response = requests.get(API_URL, headers=HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "financingRates" not in data:
                return None

            if save_to_db:
                today = datetime.now().strftime("%Y-%m-%d")
                session = Session()
                try:
                    existing = session.query(Rate).filter_by(date=today).first()
                    if existing:
                        existing.raw_data = json.dumps(data)  # type: ignore  # type: ignore
                    else:
                        new_rate = Rate(date=today, raw_data=json.dumps(data))  # type: ignore  # type: ignore
                        session.add(new_rate)
                    session.commit()
                except Exception:
                    session.rollback()
                    return None
                finally:
                    session.close()
            return data

        except requests.exceptions.RequestException:
            return None
        except ValueError:
            return None

    def get_latest_rates(self):
        """Load the most recent financing rates from the database.

        Returns:
            tuple: (date, data) or (None, None) if no data is found.

        """
        session = Session()
        try:
            rate = session.query(Rate).order_by(Rate.date.desc()).first()
            if rate:
                return rate.date, json.loads(rate.raw_data)
            return None, None
        finally:
            session.close()

    def get_instrument_history(self, instrument_name: str):
        """Retrieve the historical long and short rates for a specific instrument.

        Args:
            instrument_name: The name of the instrument.

        Returns:
            pandas.DataFrame: A DataFrame with the history.

        """
        session = Session()
        history = []
        try:
            rates: list[Rate] = session.query(Rate).order_by(Rate.date.asc()).all()
            for rate_entry in rates:
                data = json.loads(str(rate_entry.raw_data))
                for instrument_data in data.get("financingRates", []):
                    if instrument_data.get("instrument") == instrument_name:
                        history.append(
                            {
                                "date": rate_entry.date,
                                "long_rate": instrument_data.get("longRate"),
                                "short_rate": instrument_data.get("shortRate"),
                            }
                        )
            return pd.DataFrame(history)
        finally:
            session.close()
