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
        currencies = [
            "usd",
            "eur",
            "jpy",
            "gbp",
            "aud",
            "cad",
            "chf",
            "nzd",
            "sgd",
            "hkd",
            "nok",
            "sek",
            "dkk",
            "mxn",
            "zar",
            "try",
            "cnh",
            "pln",
            "czk",
            "huf",
        ]
        parts = instrument_lower.split("_")
        if len(parts) == 2 and parts[0] in currencies and parts[1] in currencies:
            return "Forex"

        # Metals
        metals = ["xau", "xag", "xpd", "xpt"]
        if any(m in parts for m in metals):
            return "Metals"

        # Commodities
        commodities = [
            "wtico_usd",
            "brent_crude_oil",
            "nat_gas_usd",
            "corn_usd",
            "wheat_usd",
            "soybn_usd",
            "sugar_usd",
            "cocoa_usd",
            "coffee_usd",
        ]
        if any(c.replace("/", "_") in instrument_lower for c in commodities):
            return "Commodities"

        # Indices
        indices = [
            "us30_usd",
            "us_30_usd",
            "spx500_usd",
            "us_spx_500",
            "nas100_usd",
            "us_nas_100",
            "us2000_usd",
            "us_2000",
            "uk100_gbp",
            "uk_100",
            "de40_eur",
            "de_30_eur",
            "de_40_eur",
            "eu50_eur",
            "eu_50_eur",
            "fr40_eur",
            "fr_40",
            "jp225_usd",
            "jp_225",
            "au200_aud",
            "au_200",
            "hk33_hkd",
            "hk_hsi",
            "cn50_usd",
            "cn_50",
            "sg30_sgd",
            "sg_30",
        ]
        if any(i.replace("/", "_") in instrument_lower for i in indices):
            return "Indices"

        # Bonds
        bonds = [
            "de_10yr_bund",
            "us_2yr_tnote",
            "us_5yr_tnote",
            "us_10yr_tnote",
            "usb02y_usd",
            "usb05y_usd",
            "de10yb_eur",
        ]
        if any(b.replace("/", "_") in instrument_lower for b in bonds):
            return "Bonds"

        # CFDs
        if "_cfd" in instrument_lower:
            return "CFDs"

        return "Other"

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
