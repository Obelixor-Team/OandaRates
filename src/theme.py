import re
from typing import Dict
import logging

from .config import config

logger = logging.getLogger(__name__)


def validate_color(color: str) -> bool:
    """Validate that a color is a valid hex code."""
    return bool(re.match(r"^#[0-9a-fA-F]{6}$", color))


THEME: Dict[str, str] = config["theme"]

for key, value in THEME.items():
    if not validate_color(value):
        logger.warning(
            f"Invalid color format for {key}: {value}. Falling back to #000000"
        )
        THEME[key] = "#000000"
