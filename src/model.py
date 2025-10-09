import json
from datetime import datetime
from typing import Dict, Optional, Any
import logging
import functools
from contextlib import contextmanager

import pandas as pd
import requests
from sqlalchemy import Column, String, Text, create_engine, exc
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column

from .config import config

# Constants
API_URL = config["api"]["url"]
HEADERS = config["api"]["headers"]
DB_FILE = config["database"]["file"]
logger = logging.getLogger(__name__)


# Database setup
class Base(DeclarativeBase):
    pass


class Rate(Base):
    """SQLAlchemy model for storing OANDA financing rates."""

    __tablename__ = "rates"
    date = Column(String, primary_key=True, index=True)
    raw_data: Mapped[str] = mapped_column(Text, nullable=False)


engine = create_engine(f"sqlite:///{DB_FILE}")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


class Model:
    """Manages data operations, including fetching from OANDA API and database."""

    def __init__(self):
        self.engine = engine
        self.Session = Session

    @contextmanager
    def get_session(self):
        session = Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self):
        """Closes the database session."""
        pass

    def categorize_instrument(self, instrument: str) -> str:
        """Categorizes an instrument into a specific group based on its name.

        Args:
            instrument: The name of the instrument.

        Returns:
            str: The category of the instrument (e.g., 'Forex', 'Metals').

        Example:
            >>> model = Model()
            >>> model.categorize_instrument("EUR_USD")
            'Forex'
            >>> model.categorize_instrument("XAU_USD")
            'Metals'
            >>> model.categorize_instrument("DE30_EUR")
            'Indices'
        """
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

    def infer_currency(self, instrument_name: str, api_currency: str) -> str:
        """Infers the currency from the instrument name or falls back to API provided currency.
        Returns:
            str: The inferred currency.

        Example:
            >>> model = Model()
            >>> model._infer_currency("EUR/USD", "USD")
            'USD'
            >>> model._infer_currency("XAU_USD", "USD") # Assuming XAU_USD is configured to map to USD
            'USD'
            >>> model._infer_currency("DE30_EUR", "EUR")
            'EUR'
        """ ""
        if "/" in instrument_name:
            return instrument_name.split("/")[1]

        suffix_to_currency = config["categories"]["currency_suffixes"]
        for suffix, currency in suffix_to_currency.items():
            if instrument_name.endswith(suffix):
                return currency
        return api_currency

    def fetch_and_save_rates(self, save_to_db: bool = True) -> Optional[Dict]:
        """Fetch financing rates from the OANDA API and optionally save to the database.

        This method sends a GET request to the OANDA API to retrieve the latest
        financing rates. If `save_to_db` is True, it will store the raw JSON
        response in the SQLite database.

        Args:
            save_to_db: Whether to save the fetched data to the database.

        Returns:
            Optional[Dict]: The fetched data as a dictionary, or None on failure.
            Example of returned data:
            {
                "financingRates": [
                    {
                        "instrument": "EUR_USD",
                        "longRate": "0.0083",
                        "shortRate": "-0.0133"
                    },
                    ...
                ]
            }

        Raises:
            requests.exceptions.RequestException: If the API request fails.
            ValueError: If the API response is malformed.
            sqlalchemy.exc.SQLAlchemyError: If database operations fail.

        Example:
            >>> model = Model()
            >>> rates_data = model.fetch_and_save_rates(save_to_db=False)
            >>> if rates_data:
            ...     print(rates_data['financingRates'][0]['instrument'])
            EUR_USD
        """
        if not HEADERS.get("Authorization"):
            raise ValueError(
                "OANDA_API_KEY environment variable is not set or is empty."
            )
        try:
            response = requests.get(  # nosec B113
                API_URL,
                headers=HEADERS,
                timeout=config.get("api", {}).get("timeout", 10),
            )
            response.raise_for_status()
            data = response.json()

            if "financingRates" not in data:
                logger.warning("API response did not contain 'financingRates' key.")
                return None

            if save_to_db:
                try:
                    with self.get_session() as session:
                        today = datetime.now().strftime("%Y-%m-%d")
                        existing = session.query(Rate).filter_by(date=today).first()
                        raw_data_str = json.dumps(data)
                        if existing:
                            existing.raw_data = raw_data_str
                        else:
                            new_rate = Rate(date=today, raw_data=raw_data_str)
                            session.add(new_rate)
                        self.get_instrument_history.cache_clear()
                        return data
                except exc.SQLAlchemyError as e:
                    logger.error(f"Database error occurred: {e}")
                    logger.info("Database session rolled back.")
                    return None
            else:
                return data

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except ValueError as e:
            logger.error(f"Failed to parse API response: {e}")
            return None

    def get_latest_rates(self) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Load the most recent financing rates from the database.

        Returns:
            tuple[Optional[str], Optional[Dict]]: (date, data) or (None, None) if no data is found.

        Raises:
            sqlalchemy.exc.SQLAlchemyError: If database query fails.

        Example:
            >>> model = Model()
            >>> # Assuming there is some data in the database
            >>> date, rates_data = model.get_latest_rates()
            >>> if date and rates_data:
            ...     print(f"Latest rates on {date}: {rates_data['financingRates'][0]['instrument']}")
            # Output might look like:
            # Latest rates on 2023-10-27: EUR_USD
        """
        with self.get_session() as session:
            rate = session.query(Rate).order_by(Rate.date.desc()).first()
            if rate:
                return str(rate.date), json.loads(rate.raw_data)
            return None, None

    @functools.lru_cache(maxsize=128)
    def get_instrument_history(self, instrument_name: str) -> pd.DataFrame:
        """Retrieve the historical long and short rates for a specific instrument.

        This method queries the database for all historical rate entries and
        filters them to extract the long and short rates for the specified
        instrument. The results are returned as a pandas DataFrame.
        The results are cached using `functools.lru_cache` for performance.

        Args:
            instrument_name: The name of the instrument (e.g., "EUR_USD").

        Returns:
            pd.DataFrame: A DataFrame with columns "date", "long_rate", and "short_rate".
            Returns an empty DataFrame if no history is found for the instrument.

        Raises:
            sqlalchemy.exc.SQLAlchemyError: If database query fails.

        Example:
            >>> model = Model()
            >>> # Assuming some data is in the database for "EUR_USD"
            >>> history_df = model.get_instrument_history("EUR_USD")
            >>> if not history_df.empty:
            ...     print(history_df.head())
            # Output might look like:
            #          date  long_rate  short_rate
            # 0  2023-01-01       0.01       -0.02
            # 1  2023-01-02      0.015      -0.025
        """
        history = []
        with self.get_session() as session:
            rates: list[Rate] = session.query(Rate).order_by(Rate.date.asc()).all()
            for rate_entry in rates:
                try:
                    data = json.loads(str(rate_entry.raw_data))
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Failed to parse JSON for rate on {rate_entry.date}: {e}"
                    )
                    continue  # Skip this entry and continue with the next

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
