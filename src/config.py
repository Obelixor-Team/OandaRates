import yaml
from typing import Dict

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
            raise ValueError(f"Missing required config key: {key}")


def load_config() -> Dict:
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
        validate_config(config)
    return config

config = load_config()