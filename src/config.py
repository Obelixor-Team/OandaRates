import yaml
from typing import Dict
import logging
import logging.config


def setup_logging():
    """Set up logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(
                "/home/skum/Dev/PycharmProjects/OandaRates/oanda_terminal.log"
            ),
            logging.StreamHandler(),
        ],
    )


DEFAULT_CONFIG = {
    "api": {
        "url": "https://labs-api.oanda.com/v1/financing-rates?divisionId=4&tradingGroupId=1",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        },
        "timeout": 10,
    },
    "database": {
        "file": "oanda_rates.db",
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
    },
}


def validate_config(config: Dict) -> None:
    """Validate the configuration file for required keys.

    Args:
        config: The loaded configuration dictionary.

    Raises:
        ValueError: If a required key is missing.
    """
    required_keys = [
        "api.url",
        "api.headers",
        "api.timeout",
        "database.file",
        "categories.currencies",
        "categories.metals",
        "categories.commodities",
        "categories.indices",
        "categories.bonds",
        "categories.currency_suffixes",
        "ui.timer_interval",
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
    ]
    for key in required_keys:
        parent, child = key.split(".")
        if parent not in config or child not in config[parent]:
            raise ValueError(f'Missing required config key: "{key}" in config.yaml')


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
            config = yaml.safe_load(f)
            # Merge with default config to ensure all keys are present
            merged_config = DEFAULT_CONFIG.copy()
            _deep_merge(merged_config, config)
            validate_config(merged_config)
        return merged_config
    except (FileNotFoundError, yaml.YAMLError) as e:
        logging.warning(f"Error loading config.yaml: {e}. Using default configuration.")
        validate_config(DEFAULT_CONFIG)  # Validate default config as well
        return DEFAULT_CONFIG


config = load_config()
setup_logging()
