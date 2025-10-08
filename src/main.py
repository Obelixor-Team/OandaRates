import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from .model import Model
from .presenter import Presenter
from .view import View

from typing import Optional  # Add this import


def run_app(app: QApplication, mock_presenter: Optional[Presenter] = None) -> View:
    """Encapsulates the application setup and returns the main View instance."""
    # Create instances of the MVP components
    m = Model()
    v = View()  # Instantiate View without presenter initially
    if mock_presenter:
        p = mock_presenter
    else:
        p = Presenter(m, v)  # Instantiate Presenter with Model and View
    v.set_presenter(p)  # Set the presenter in the View
    p.on_app_start()  # Call on_app_start after everything is set up

    # Show the main window
    v.show()

    # Use a QTimer to create a "render loop" for processing UI updates
    # This is the PyQt equivalent of Dear PyGui's render callback
    timer = QTimer()
    timer.timeout.connect(p.process_ui_updates)
    timer.start(16)  # Check for updates roughly 60 times per second

    return v


if __name__ == "__main__":
    app = QApplication(sys.argv)
    view_instance = run_app(app)
    sys.exit(app.exec())
