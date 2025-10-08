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
            logging.FileHandler("/home/skum/Dev/PycharmProjects/OandaRates/oanda_terminal.log"),
            logging.StreamHandler(),
        ],
    )


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
    ]
    for key in required_keys:
        parent, child = key.split(".")
        if parent not in config or child not in config[parent]:
            raise ValueError(f'Missing required config key: "{key}" in config.yaml')


def load_config() -> Dict:
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
            validate_config(config)
        return config
    except FileNotFoundError:
        raise FileNotFoundError("config.yaml not found. Please ensure the file exists.")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing config.yaml: {str(e)}")


config = load_config()
setup_logging()
