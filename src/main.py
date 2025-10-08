import sys
import logging

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from .model import Model
from .presenter import Presenter
from .view import View

from typing import Optional, Tuple
from .config import config  # Import config from config.py

logger = logging.getLogger(__name__)


def run_app(
    app: QApplication, mock_presenter: Optional[Presenter] = None
) -> Tuple[View, QTimer, Presenter]:
    """Initialize the MVP components and start the application.

    Args:
        app: The QApplication instance for the PyQt6 application.
        mock_presenter: Optional mock Presenter for testing purposes.

    Returns:
        View: The initialized main View instance.

    Raises:
        RuntimeError: If the Presenter or View initialization fails.
    """
    logger.info("Application starting...")
    # Create instances of the MVP components
    m = Model()
    v = View()  # Instantiate View without presenter initially
    if mock_presenter:
        p = mock_presenter
    else:
        p = Presenter(m, v)  # Instantiate Presenter with Model and View
    v.set_presenter(p)  # Set the presenter in the View

    # Use a QTimer to create a "render loop" for processing UI updates
    # This is the PyQt equivalent of Dear PyGui's render callback
    timer = QTimer()
    timer.timeout.connect(p.process_ui_updates)
    timer_interval = config.get("ui", {}).get("timer_interval", 16)

    v.set_timer(timer)
    p.on_app_start()  # Call on_app_start after everything is set up
    p.process_ui_updates()  # Process initial UI updates immediately

    # Show the main window
    v.show()

    timer.start(timer_interval)

    logger.info("Application started successfully.")
    return v, timer, p


if __name__ == "__main__":
    presenter_instance: Optional[Presenter] = None
    try:
        app = QApplication(sys.argv)
        view_instance, timer, presenter_instance = run_app(app)
        sys.exit(app.exec())
    except Exception:
        logging.exception("Unhandled exception caught.")
    finally:
        if "presenter_instance" in locals() and presenter_instance:
            presenter_instance.shutdown()
        sys.exit(1)
