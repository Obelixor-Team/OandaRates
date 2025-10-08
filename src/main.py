import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from .model import Model
from .presenter import Presenter
from .view import View

if __name__ == "__main__":
    """The main entry point for the PyQt6 application."""
    app = QApplication(sys.argv)

    # Create instances of the MVP components
    m = Model()
    p = Presenter(m, None)
    v = View(p)
    p.view = v

    # Show the main window
    v.show()

    # Use a QTimer to create a "render loop" for processing UI updates
    # This is the PyQt equivalent of Dear PyGui's render callback
    timer = QTimer()
    timer.timeout.connect(p.process_ui_updates)
    timer.start(16)  # Check for updates roughly 60 times per second

    # Start the application event loop
    sys.exit(app.exec())
