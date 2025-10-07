
import json
import logging
from datetime import datetime

import pandas as pd
import requests
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

# Setup logging
logging.basicConfig(
    filename="oanda_instrument_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

# Constants
API_URL = "https://labs-api.oanda.com/v1/financing-rates?divisionId=4&tradingGroupId=1"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}
DB_FILE = "oanda_rates.db"

# Database setup
Base = declarative_base()

class Rate(Base):
    __tablename__ = "rates"
    date = Column(String, primary_key=True)
    raw_data = Column(Text)

engine = create_engine(f"sqlite:///{DB_FILE}")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

class Model:
    def categorize_instrument(self, instrument):
        """
        Categorizes an instrument into a specific group based on its name.
        """
        instrument_lower = instrument.lower().replace("/", "_")

        # Forex
        currencies = [
            "usd", "eur", "jpy", "gbp", "aud", "cad", "chf", "nzd", "sgd",
            "hkd", "nok", "sek", "dkk", "mxn", "zar", "try", "cnh", "pln",
            "czk", "huf",
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
            "wtico_usd", "brent_crude_oil", "nat_gas_usd", "corn_usd",
            "wheat_usd", "soybn_usd", "sugar_usd", "cocoa_usd", "coffee_usd",
        ]
        if any(c.replace("/", "_") in instrument_lower for c in commodities):
            return "Commodities"

        # Indices
        indices = [
            "us30_usd", "us_30_usd", "spx500_usd", "us_spx_500", "nas100_usd",
            "us_nas_100", "us2000_usd", "us_2000", "uk100_gbp", "uk_100",
            "de40_eur", "de_30_eur", "de_40_eur", "eu50_eur", "eu_50_eur",
            "fr40_eur", "fr_40", "jp225_usd", "jp_225", "au200_aud", "au_200",
            "hk33_hkd", "hk_hsi", "cn50_usd", "cn_50", "sg30_sgd", "sg_30",
        ]
        if any(i.replace("/", "_") in instrument_lower for i in indices):
            return "Indices"

        # Bonds
        bonds = [
            "de_10yr_bund", "us_2yr_tnote", "us_5yr_tnote", "us_10yr_tnote",
            "usb02y_usd", "usb05y_usd", "de10yb_eur",
        ]
        if any(b.replace("/", "_") in instrument_lower for b in bonds):
            return "Bonds"

        # CFDs
        if "_cfd" in instrument_lower:
            return "CFDs"

        logging.info(f"Uncategorized instrument: {instrument} -> Other")
        return "Other"

    def fetch_and_save_rates(self):
        """
        Fetches financing rates from the OANDA API and saves them to the database.
        Returns the fetched data or None on failure.
        """
        try:
            response = requests.get(API_URL, headers=HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "financingRates" not in data:
                logging.error("API response format is unexpected.")
                return None

            today = datetime.now().strftime("%Y-%m-%d")
            session = Session()
            try:
                existing = session.query(Rate).filter_by(date=today).first()
                if existing:
                    existing.raw_data = json.dumps(data)
                else:
                    new_rate = Rate(date=today, raw_data=json.dumps(data))
                    session.add(new_rate)
                session.commit()
                logging.info(f"Successfully fetched and saved data for {today}.")
                return data
            except Exception as e:
                session.rollback()
                logging.error(f"Database error: {e}")
                return None
            finally:
                session.close()

        except requests.exceptions.RequestException as e:
            logging.error(f"Fetch error: {e}")
            return None
        except ValueError as e:
            logging.error(f"Data error: {e}")
            return None

    def get_latest_rates(self):
        """
        Loads the most recent financing rates from the database.
        Returns a tuple of (date, data) or (None, None) if no data is found.
        """
        session = Session()
        try:
            rate = session.query(Rate).order_by(Rate.date.desc()).first()
            if rate:
                return rate.date, json.loads(rate.raw_data)
            return None, None
        finally:
            session.close()

    def get_instrument_history(self, instrument_name):
        """
        Retrieves the historical long and short rates for a specific instrument.
        Returns a pandas DataFrame with the history.
        """
        session = Session()
        history = []
        try:
            rates = session.query(Rate).order_by(Rate.date.asc()).all()
            for rate_entry in rates:
                data = json.loads(rate_entry.raw_data)
                for instrument_data in data.get("financingRates", []):
                    if instrument_data.get("instrument") == instrument_name:
                        history.append({
                            "date": rate_entry.date,
                            "long_rate": instrument_data.get("longRate"),
                            "short_rate": instrument_data.get("shortRate"),
                        })
            return pd.DataFrame(history)
        finally:
            session.close()

