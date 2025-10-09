import json
from datetime import datetime
from typing import Dict, Optional, Any, Callable
import time
from .performance import log_performance
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


# REMOVED: Global engine creation - now handled by Model class
Session = None  # Will be initialized in Model.__init__


class Model:
    """Manages data operations, including fetching from OANDA API and database."""

    def __init__(self):
        # Create engine instance specifically for this Model
        self.engine = create_engine(
            f"sqlite:///{DB_FILE}",
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=config.get("database", {}).get("echo_sql", False)  # Optional: for debugging
        )
        
        # Create all tables if they don't exist
        Base.metadata.create_all(self.engine)
        
        # Create sessionmaker bound to this engine
        self.Session = sessionmaker(bind=self.engine)
        
        logger.debug("Database engine and sessionmaker initialized")

    @contextmanager
    def get_session(self):
        """Context manager for database sessions."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self):
        """Dispose of the database engine."""
        if hasattr(self, 'engine'):
            self.engine.dispose()
            logger.debug("Database engine disposed")

    def _parse_json_data(
        self, raw_data_str: str, date: str
    ) -> Optional[Dict[str, Any]]:
        """Helper to parse JSON data and handle errors."""
        try:
            return json.loads(raw_data_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON for rate on {date}: {e}")
            return None

    def _retry_with_backoff(
        self,
        func: Callable,
        max_retries: int = 3,
        initial_delay: float = 1.0,
    ) -> Optional[Dict]:
        """Retry a function with exponential backoff.

        Args:
            func: The function to retry
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds (doubles each retry)

        Returns:
            Result from func or None if all retries failed
        """
        delay = initial_delay

        for attempt in range(max_retries):
            try:
                return func()
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"API request failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    logger.error(
                        f"API request failed after {max_retries} attempts: {e}"
                    )

        return None

    def _query_all_rates_ordered(self, ascending: bool = True) -> list[Dict[str, Any]]:
        """Query all rates ordered by date, returning their date and raw data.

        Args:
            ascending: If True, order ascending; else descending

        Returns:
            List of dictionaries, each with 'date' and 'raw_data'
        """
        with self.get_session() as session:
            order = Rate.date.asc() if ascending else Rate.date.desc()
            rates = session.query(Rate).order_by(order).all()
            # Extract data INSIDE the session context
            result = [
                {"date": str(rate.date), "raw_data": str(rate.raw_data)}
                for rate in rates
            ]
            return result

    def _query_latest_rate(self) -> Optional[Dict[str, Any]]:
        """Query the most recent rate entry and return its raw data and date.

        Returns:
            Dictionary with 'date' and 'raw_data' or None
        """
        with self.get_session() as session:
            rate = session.query(Rate).order_by(Rate.date.desc()).first()
            if rate:
                # Extract data INSIDE the session context
                return {"date": str(rate.date), "raw_data": str(rate.raw_data)}
            return None

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

        Args:
            instrument_name: The name of the instrument.
            api_currency: The currency provided by the API.

        Returns:
            str: The inferred currency.

        Example:
            >>> model = Model()
            >>> model.infer_currency("EUR/USD", "USD")
            'USD'
            >>> model.infer_currency("DE30_EUR", "EUR")
            'EUR'
        """
        if "/" in instrument_name:
            return instrument_name.split("/")[1]

        suffix_to_currency = config["categories"]["currency_suffixes"]
        for suffix, currency in suffix_to_currency.items():
            if instrument_name.endswith(suffix):
                return currency
        return api_currency

    @log_performance
    def fetch_and_save_rates(self, save_to_db: bool = True) -> Optional[Dict]:
        """Fetches the latest financing rates from the OANDA API.

        This method attempts to retrieve financing rate data from the configured
        OANDA API endpoint. It includes retry logic with exponential backoff
        to handle transient network issues. If successful, the fetched data
        can optionally be saved to the local SQLite database.

        Args:
            save_to_db (bool): If True, the fetched data will be saved to the
                               database. Defaults to True.

        Returns:
            Optional[Dict]: A dictionary containing the fetched financing rates
                            if the API call is successful and the response is valid,
                            otherwise None.

        Raises:
            ValueError: If the OANDA API key is not configured.
            requests.exceptions.RequestException: For network-related errors during API calls.
            json.JSONDecodeError: If the API response is not valid JSON.
            sqlalchemy.exc.SQLAlchemyError: For errors during database operations.
        """
        if not HEADERS.get("Authorization"):
            raise ValueError(
                "OANDA_API_KEY environment variable is not set or is empty."
            )

        def _fetch_from_api() -> Dict:
            """Inner function for the actual API call."""
            response = requests.get(  # nosec B113
                API_URL,
                headers=HEADERS,
                timeout=config.get("api", {}).get("timeout", 10),
            )
            response.raise_for_status()
            return response.json()

        try:
            # Use retry logic for API call
            data = self._retry_with_backoff(_fetch_from_api)

            if data is None:
                return None

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
                    # Cache clear AFTER context manager closes
                    self.get_instrument_history.cache_clear()
                except exc.SQLAlchemyError as e:
                    logger.error(f"Database error occurred: {e}")
                    logger.info("Database session rolled back.")
                    return None

            return data

        except ValueError as e:
            logger.error(f"Failed to parse API response: {e}")
            return None

    def get_latest_rates(self) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Load the most recent financing rates from the database."""
        rate_data = self._query_latest_rate()  # This now returns a dict or None

        if rate_data:
            date = rate_data["date"]
            raw_data_str = rate_data["raw_data"]
            data = self._parse_json_data(raw_data_str, date)
            if data:
                return date, data
            return None, None

        return None, None

    @functools.lru_cache(maxsize=50)
    @log_performance  # ⭐ NEW
    def get_instrument_history(self, instrument_name: str) -> pd.DataFrame:
        """Retrieve the historical long and short rates for a specific instrument."""
        if not isinstance(instrument_name, str) or not instrument_name.strip():
            logger.warning(
                f"Invalid instrument_name provided to get_instrument_history: '{instrument_name}'"
            )
            return pd.DataFrame()  # Return empty DataFrame for invalid input

        history = []
        rates_data = self._query_all_rates_ordered(
            ascending=True
        )  # This now returns list of dicts

        for rate_entry_data in rates_data:
            date = rate_entry_data["date"]
            raw_data_str = rate_entry_data["raw_data"]
            data = self._parse_json_data(raw_data_str, date)
            if not data:
                continue

            for instrument_data in data.get("financingRates", []):
                if instrument_data.get("instrument") == instrument_name:
                    history.append(
                        {
                            "date": date,
                            "long_rate": instrument_data.get("longRate"),
                            "short_rate": instrument_data.get("shortRate"),
                        }
                    )

        return pd.DataFrame(history)
