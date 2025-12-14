import sys
import os
import logging
from PyQt6.QtWidgets import QApplication
from src.main import run_app, Presenter

# Determine if the application is running as a bundled executable
if getattr(sys, 'frozen', False):
    # If frozen, add the 'lib' directory within the executable's directory to sys.path
    bundle_dir = os.path.dirname(sys.executable)
    sys.path.insert(0, os.path.join(bundle_dir, "lib"))
else:
    # If not frozen, add the script's directory to sys.path (for development)
    sys.path.insert(0, os.path.dirname(__file__))


if __name__ == "__main__":
    presenter_instance: Presenter | None = None
    try:
        app = QApplication(sys.argv)
        view_instance, timer, presenter_instance = run_app(app)
        sys.exit(app.exec())
    except KeyboardInterrupt:
        logging.info(
            "Application interrupted by user (Ctrl+C). Shutting down gracefully."
        )
        sys.exit(0)
    except SystemExit as e:
        logging.info(f"Application exiting with code {e.code}.")
        # Allow SystemExit to propagate with its code
        raise
    except Exception as e:
        logging.exception(f"Unhandled exception occurred: {e}. Application will terminate.")
        sys.exit(1)
    finally:
        if presenter_instance:
            presenter_instance.shutdown()
