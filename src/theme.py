import re
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def validate_color(color: str) -> bool:
    """Validate that a color is a valid hex code."""
    return bool(re.match(r"^#[0-9a-fA-F]{6}$", color))


THEME: Dict[str, str] = {
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
}

for key, value in THEME.items():
    if not validate_color(value):
        logger.warning(f"Invalid color format for {key}: {value}. Falling back to #000000")
        THEME[key] = "#000000"
