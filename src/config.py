import yaml
from typing import Dict
import logging
import os
import logging.config


def setup_logging():
    """Set up logging for the application."""
    log_level_str = config["logging"]["level"].upper()
    log_level = getattr(
        logging, log_level_str, logging.INFO
    )  # Default to INFO if not found

    from logging.handlers import RotatingFileHandler

    handler = RotatingFileHandler(
        config["logging"]["file_path"], maxBytes=1_000_000, backupCount=3
    )
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[handler, logging.StreamHandler()],
    )


# Default configuration settings for the OANDA Financing Terminal application.
#
# This dictionary defines the default values for various application
# parameters, including API settings, database configuration, instrument
# categorization, UI behavior, theme colors, and logging preferences.
# These defaults can be overridden by a `config.yaml` file.
#
# Structure:
# - api (dict): API connection settings.
#     - url (str): The OANDA API endpoint for financing rates.
#     - headers (dict): HTTP headers for API requests.
#         - User-Agent (str): User-Agent string for requests.
#         - Accept (str): Accept header for requests.
#         - Authorization (str): OANDA API key (loaded from OANDA_API_KEY env var).
#     - timeout (int/float): Request timeout in seconds.
#     - max_retries (int): Maximum number of retry attempts for failed API calls.
#     - retry_delay (float): Initial delay for exponential backoff in retries.
# - database (dict): Database settings.
#     - file (str): Path to the SQLite database file.
# - categories (dict): Rules for categorizing financial instruments.
#     - currencies (list): List of currency codes.
#     - metals (list): List of metal codes.
#     - commodities (list): List of commodity codes.
#     - indices (list): List of index codes.
#     - bonds (list): List of bond codes.
#     - currency_suffixes (dict): Mapping of suffixes to currency codes for inference.
# - ui (dict): User interface settings.
#     - timer_interval (int): Interval (in milliseconds) for UI update timer.
# - theme (dict): UI theme color palette.
#     - background (str): Main background color.
#     - text (str): General text color.
#     - positive (str): Color for positive values/indicators.
#     - negative (str): Color for negative values/indicators.
#     - plot_background (str): Background color for plots.
#     - table_background (str): Background color for tables.
#     - table_gridline (str): Color for table gridlines.
#     - header_background (str): Background color for table headers.
#     - header_text (str): Text color for table headers.
#     - selected_background (str): Background color for selected items.
#     - selected_text (str): Text color for selected items.
#     - button_background (str): Background color for buttons.
#     - button_hover (str): Background color for buttons on hover.
#     - button_text (str): Text color for buttons.
#     - input_background (str): Background color for input fields.
#     - input_border (str): Border color for input fields.
#     - status_text (str): Text color for status messages.
#     - plot_long_rate_color (str): Color for long rate plots.
#     - plot_short_rate_color (str): Color for short rate plots.
# - logging (dict): Logging settings.
#     - level (str): Logging level (e.g., "INFO", "DEBUG").
#     - file_path (str): Path to the log file.
DEFAULT_CONFIG = {
    "api": {
        "url": "https://labs-api.oanda.com/v1/financing-rates?divisionId=4&tradingGroupId=1",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Authorization": os.getenv("OANDA_API_KEY", ""),
        },
        "timeout": 10,
        "max_retries": 3,  # NEW
        "retry_delay": 1.0,  # NEW
    },
    "database": {
        "file": "oanda_rates.db",
        "timeout": 10, # NEW: Database connection timeout in seconds
    },
    "categories": {
        "currencies": [
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
        ],
        "metals": ["xau", "xag", "xpd", "xpt"],
        "commodities": [
            "wtico_usd",
            "brent_crude_oil",
            "nat_gas_usd",
            "corn_usd",
            "wheat_usd",
            "soybn_usd",
            "sugar_usd",
            "cocoa_usd",
            "coffee_usd",
        ],
        "indices": [
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
        ],
        "bonds": [
            "de_10yr_bund",
            "us_2yr_tnote",
            "us_5yr_tnote",
            "us_10yr_tnote",
            "usb02y_usd",
            "usb05y_usd",
            "de10yb_eur",
        ],
        "currency_suffixes": {
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
        },
    },
    "ui": {
        "timer_interval": 16,
        "rate_display_format": "percentage", # NEW: Default rate display format ('percentage' or 'basis_points')
    },
    "theme": {
        "background": "#0a0a12",
        "text": "#e0e0e0",
        "positive": "#00ff9d",
        "negative": "#ff5555",
        "plot_background": "#121220",
        "table_background": "#1a1a2e",
        "table_gridline": "#2a2a3e",
        "header_background": "#121220",
        "header_text": "#00ff9d",
        "selected_background": "#0095ff",
        "selected_text": "#ffffff",
        "button_background": "#0095ff",
        "button_hover": "#0077cc",
        "button_text": "#ffffff",
        "input_background": "#1a1a2e",
        "input_border": "#2a2a3e",
        "status_text": "#a0a0b0",
        "plot_long_rate_color": "#00ff9d",
        "plot_short_rate_color": "#ff5555",
    },
    "logging": {"level": "INFO", "file_path": "oanda_terminal.log"},
}


def _validate_config_types(config: Dict) -> None:
    """Validate the types of critical configuration values."""
    # Validate api.max_retries NEW
    if not isinstance(config["api"]["max_retries"], int):
        raise TypeError("Config error: api.max_retries must be an integer.")
    if config["api"]["max_retries"] < 1 or config["api"]["max_retries"] > 10:
        raise ValueError("Config error: api.max_retries must be between 1 and 10.")

    # Validate api.retry_delay NEW
    if not isinstance(config["api"]["retry_delay"], (int, float)):
        raise TypeError("Config error: api.retry_delay must be a number.")
    if config["api"]["retry_delay"] < 0.1 or config["api"]["retry_delay"] > 60:
        raise ValueError("Config error: api.retry_delay must be between 0.1 and 60.")

    # Validate api.timeout
    if not isinstance(config["api"]["timeout"], (int, float)):
        raise TypeError("Config error: api.timeout must be a number.")

    # Validate database.timeout NEW
    if not isinstance(config["database"]["timeout"], (int, float)):
        raise TypeError("Config error: database.timeout must be a number.")
    if config["database"]["timeout"] < 1 or config["database"]["timeout"] > 60:
        raise ValueError("Config error: database.timeout must be between 1 and 60.")

    # Validate theme colors
    for key, value in config["theme"].items():
        if not isinstance(value, str):
            raise TypeError(f"Config error: theme.{key} must be a string.")

    # Validate logging.level
    if not isinstance(config["logging"]["level"], str):
        raise TypeError("Config error: logging.level must be a string.")
    valid_log_levels = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]
    if config["logging"]["level"].upper() not in valid_log_levels:
        raise ValueError(
            f"Config error: logging.level must be one of {valid_log_levels}."
        )

    if not isinstance(config["logging"]["file_path"], str):
        raise TypeError("Config error: logging.file_path must be a string.")

    # Validate ui.timer_interval
    if not isinstance(config["ui"]["timer_interval"], int):
        raise TypeError("Config error: ui.timer_interval must be an integer.")

    # Validate ui.rate_display_format NEW
    if not isinstance(config["ui"]["rate_display_format"], str):
        raise TypeError("Config error: ui.rate_display_format must be a string.")
    if config["ui"]["rate_display_format"] not in ["percentage", "basis_points"]:
        raise ValueError("Config error: ui.rate_display_format must be 'percentage' or 'basis_points'.")

    if not isinstance(config["theme"]["plot_long_rate_color"], str):
        raise TypeError("Config error: theme.plot_long_rate_color must be a string.")
    if not isinstance(config["theme"]["plot_short_rate_color"], str):
        raise TypeError("Config error: theme.plot_short_rate_color must be a string.")


def validate_config(config: Dict) -> None:
    """Validate the configuration file for required keys and types.

    Args:
        config: The loaded configuration dictionary.

    Raises:
        ValueError: If a required key is missing.
        TypeError: If a configuration value has an incorrect type.
    """
    required_keys = [
        "api.url",
        "api.headers",
        "api.timeout",
        "api.max_retries",  # NEW
        "api.retry_delay",  # NEW
        "database.file",
        "database.timeout", # NEW
        "categories.currencies",
        "categories.metals",
        "categories.commodities",
        "categories.indices",
        "categories.bonds",
        "categories.currency_suffixes",
        "ui.timer_interval",
        "ui.rate_display_format", # NEW
        "theme.background",
        "theme.text",
        "theme.positive",
        "theme.negative",
        "theme.plot_background",
        "theme.table_background",
        "theme.table_gridline",
        "theme.header_background",
        "theme.header_text",
        "theme.selected_background",
        "theme.selected_text",
        "theme.button_background",
        "theme.button_hover",
        "theme.button_text",
        "theme.input_background",
        "theme.input_border",
        "theme.status_text",
        "theme.plot_long_rate_color",
        "theme.plot_short_rate_color",
        "logging.level",
        "logging.file_path",
    ]
    for key in required_keys:
        parent, child = key.split(".")
        if parent not in config or child not in config[parent]:
            raise ValueError(f'Missing required config key: "{key}" in config.yaml')

    _validate_config_types(config)  # Call type validation

    # NEW: API Key Validation
    if not config["api"]["headers"].get("Authorization"):
        logging.warning(
            "OANDA_API_KEY environment variable not set. API features may be disabled or fail."
        )


def _deep_merge(base, new):
    """Recursively merges two dictionaries."""
    for k, v in new.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


def load_config() -> Dict:
    try:
        with open("config.yaml", "r") as f:
            config_from_file = yaml.safe_load(f) or {}
            # Merge with default config to ensure all keys are present
            merged_config = DEFAULT_CONFIG.copy()
            _deep_merge(merged_config, config_from_file)
            validate_config(merged_config)
        return merged_config
    except (FileNotFoundError, yaml.YAMLError) as e:
        logging.warning(f"Error loading config.yaml: {e}. Using default configuration.")
        validate_config(DEFAULT_CONFIG)  # Validate default config as well
        return DEFAULT_CONFIG


config = load_config()
