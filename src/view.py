from datetime import datetime
import logging

import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,  # NEW
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtCore import QSettings, Qt, QTimer

from typing import TYPE_CHECKING, Optional, Dict, Any

from .theme import THEME

if TYPE_CHECKING:
    from .presenter import Presenter

logger = logging.getLogger(__name__)


class NumericTableWidgetItem(QTableWidgetItem):
    """Custom QTableWidgetItem for numerical sorting."""

    def __lt__(self, other):
        if isinstance(other, QTableWidgetItem):
            try:
                return float(self.data(Qt.ItemDataRole.UserRole)) < float(
                    other.data(Qt.ItemDataRole.UserRole)
                )
            except (ValueError, TypeError):
                pass  # Fallback to default string comparison
        return super().__lt__(other)


# --- Matplotlib Canvas for plotting ---
class MplCanvas(FigureCanvas):
    """Matplotlib canvas for embedding plots in PyQt6 applications."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(
            figsize=(width, height), dpi=dpi, facecolor=THEME["plot_background"]
        )
        self.axes = fig.add_subplot(111)
        self.axes.set_facecolor(THEME["plot_background"])
        self.axes.spines["top"].set_color(THEME["text"])
        self.axes.spines["bottom"].set_color(THEME["text"])
        self.axes.spines["left"].set_color(THEME["text"])
        self.axes.spines["right"].set_color(THEME["text"])
        self.axes.tick_params(axis="x", colors=THEME["text"])
        self.axes.tick_params(axis="y", colors=THEME["text"])
        self.axes.xaxis.label.set_color(THEME["text"])
        self.axes.yaxis.label.set_color(THEME["text"])
        self.axes.title.set_color(THEME["text"])
        super(MplCanvas, self).__init__(fig)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


# --- History Dialog ---
class HistoryDialog(QDialog):
    """Dialog to display historical instrument data and statistics."""

    def __init__(self, instrument_name, history_df, stats, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"History for {instrument_name}")

        layout = QVBoxLayout()

        # Stats Layout
        stats_layout = QHBoxLayout()
        long_stats_text, short_stats_text = self._format_stats_text(stats)

        long_stats_label = QLabel(long_stats_text)
        short_stats_label = QLabel(short_stats_text)

        stats_layout.addWidget(long_stats_label)
        stats_layout.addWidget(short_stats_label)
        layout.addLayout(stats_layout)

        # Plot
        if not history_df.empty:
            plot_canvas = self._create_plot_canvas(history_df)
            layout.addWidget(plot_canvas)

        self.setLayout(layout)
        self.resize(self.sizeHint())

    def _format_stats_text(self, stats: Dict[str, float]) -> tuple[str, str]:
        """Format statistics into long and short rate text sections.

        Args:
            stats: Dictionary of statistics

        Returns:
            Tuple of (long_stats_text, short_stats_text)
        """
        long_stats_text = "Long Rates:\n"
        short_stats_text = "Short Rates:\n"

        for key, value in stats.items():
            formatted_line = f"{key}: {value * 100:.2f}%\n"

            if "Long" in key:
                long_stats_text += formatted_line
            elif "Short" in key:
                short_stats_text += formatted_line

        return long_stats_text, short_stats_text

    def _create_plot_canvas(self, history_df: pd.DataFrame) -> MplCanvas:
        """Create matplotlib canvas with rate history plot.

        Args:
            history_df: DataFrame with historical rate data

        Returns:
            Configured MplCanvas
        """
        sc = MplCanvas(self, width=5, height=4, dpi=100)

        # Ensure numeric data
        history_df["long_rate"] = pd.to_numeric(
            history_df["long_rate"], errors="coerce"
        )
        history_df["short_rate"] = pd.to_numeric(
            history_df["short_rate"], errors="coerce"
        )
        dates = pd.to_datetime(history_df["date"])

        # Plot both rates
        sc.axes.plot(
            dates,
            history_df["long_rate"],
            label="Long Rate",
            color=THEME["plot_long_rate_color"],
        )
        sc.axes.plot(
            dates,
            history_df["short_rate"],
            label="Short Rate",
            color=THEME["plot_short_rate_color"],
        )

        # Configure plot
        sc.axes.legend()
        sc.axes.set_xlabel("Date")
        sc.axes.set_ylabel("Rate (%)")
        sc.axes.grid(True, linestyle="--", alpha=0.7, color=THEME["text"])
        sc.axes.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        sc.figure.autofmt_xdate()
        sc.figure.tight_layout()

        return sc


# --- Settings Dialog ---
class SettingsDialog(QDialog):
    """Dialog for application settings, e.g., API key and URL."""

    def __init__(self, current_api_key: str, current_base_url: str, current_account_id: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        layout = QVBoxLayout()

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your OANDA API Key")
        self.api_key_input.setText(current_api_key)
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password) # Mask API key

        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("Enter OANDA API Base URL")
        self.base_url_input.setText(current_base_url)

        self.account_id_input = QLineEdit()
        self.account_id_input.setPlaceholderText("Enter your OANDA Account ID")
        self.account_id_input.setText(current_account_id)

        layout.addWidget(QLabel("OANDA API Key:"))
        layout.addWidget(self.api_key_input)
        layout.addWidget(QLabel("OANDA API Base URL (e.g., https://api-fxpractice.oanda.com):"))
        layout.addWidget(self.base_url_input)
        layout.addWidget(QLabel("OANDA Account ID:"))
        layout.addWidget(self.account_id_input)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Connect signals
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_settings(self) -> tuple[str, str, str]:
        """Returns the entered API key, base URL, and account ID."""
        return self.api_key_input.text(), self.base_url_input.text(), self.account_id_input.text()


# --- Main View ---
class View(QMainWindow):
    """Main application window for displaying OANDA financing rates."""

    def __init__(self, presenter: Optional["Presenter"] = None) -> None:
        """Initializes the main application window.

        Sets up the window title, applies the stylesheet, sets up the UI
        elements, and loads/saves window geometry settings.

        Args:
            presenter: An optional Presenter instance to connect UI events to.

        Example:
            >>> from unittest.mock import MagicMock
            >>> view = View(MagicMock())
            >>> view.setWindowTitle("Test Window")
            >>> assert view.windowTitle() == "Test Window"
        """
        super().__init__()
        self._presenter: Optional["Presenter"] = presenter
        self._timer: Optional[QTimer] = None
        self.setWindowTitle("OANDA FINANCING TERMINAL v4.0")
        self._apply_stylesheet()
        self._setup_ui()
        # self.presenter.on_app_start() # This will be called from main.py after presenter is set

        # Load window settings
        self.settings = QSettings("OandaRates", "OandaFinancingTerminal")
        if self.settings.contains("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        else:
            self.resize(self.sizeHint())  # Use sizeHint for default size

    def set_timer(self, timer: QTimer) -> None:
        """Sets the QTimer instance for the view.

        This timer is typically used to periodically process UI updates from
        the presenter's queue.

        Args:
            timer: The QTimer instance to be set.

        Example:
            >>> from PyQt6.QtCore import QTimer
            >>> from unittest.mock import MagicMock
            >>> view = View(MagicMock())
            >>> timer = QTimer()
            >>> view.set_timer(timer)
            >>> assert view._timer is timer
        """
        self._timer = timer

    def set_presenter(self, presenter: "Presenter") -> None:
        """Sets the presenter for the view and connects UI signals to presenter slots.

        This method establishes the communication link between the view's UI
        elements and the presenter's logic, ensuring that user interactions
        trigger the appropriate actions in the presenter.

        Args:
            presenter: The Presenter instance to associate with this view.

        Example:
            >>> from unittest.mock import MagicMock
            >>> view = View()
            >>> mock_presenter = MagicMock()
            >>> view.set_presenter(mock_presenter)
            >>> assert view._presenter is mock_presenter
            >>> # Verify a connection (conceptual check, actual assertion is complex)
            >>> view.filter_input.textChanged.emit("test")
            >>> mock_presenter.on_filter_text_changed.assert_called_with("test")
        """
        self._presenter = presenter
        # Connect signals to presenter methods after presenter is set
        self.filter_input.textChanged.connect(self._presenter.on_filter_text_changed)
        self.category_combo.currentTextChanged.connect(
            self._presenter.on_category_selected
        )
        self.clear_btn.clicked.connect(self._presenter.on_clear_filter)
        self.update_btn.clicked.connect(self._presenter.on_manual_update)
        self.cancel_btn.clicked.connect(self._presenter.on_cancel_update)
        self.export_btn.clicked.connect(self._presenter.on_export_data)  # NEW
        self.settings_btn.clicked.connect(self._presenter.on_settings_clicked)

        self.table.itemDoubleClicked.connect(self._on_table_double_click)

    def show_settings_dialog(self, current_api_key: str, current_base_url: str, current_account_id: str) -> Optional[tuple[str, str, str]]:
        """Opens the settings dialog and returns the new settings if saved."""
        dialog = SettingsDialog(current_api_key, current_base_url, current_account_id, self)
        if dialog.exec():  # exec() returns 1 (Accepted) or 0 (Rejected)
            return dialog.get_settings()
        return None

    def set_update_buttons_enabled(self, enabled: bool):
        """Enables or disables the update and cancel buttons.

        This method is used to control the interactivity of the update and
        cancel buttons, typically to prevent multiple simultaneous updates
        or to indicate an ongoing operation.

        Args:
            enabled: A boolean value; True to enable, False to disable.

        Example:
            >>> from unittest.mock import MagicMock
            >>> view = View(MagicMock())
            >>> view._setup_ui() # Ensure buttons are initialized
            >>> view.set_update_buttons_enabled(False)
            >>> assert not view.update_btn.isEnabled()
            >>> assert view.cancel_btn.isEnabled()
            >>> view.set_update_buttons_enabled(True)
            >>> assert view.update_btn.isEnabled()
            >>> assert not view.cancel_btn.isEnabled()
        """
        self.update_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(not enabled)

    def _setup_ui(self):
        """Sets up the user interface elements of the main window.

        This private method initializes and arranges all widgets, including
        input fields, buttons, tables, and status bar components. It also
        configures their properties and accessibility attributes.

        Example:
            >>> from unittest.mock import MagicMock
            >>> view = View(MagicMock())
            >>> view._setup_ui()
            >>> # After setup, you can assert properties of created widgets
            >>> assert isinstance(view.filter_input, QLineEdit)
            >>> assert view.table.columnCount() == 9
            >>> assert view.status_label.text() == "TERMINAL READY"
        """
        # --- Central Widget and Layouts ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        control_layout = QHBoxLayout()

        # --- Widgets ---
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter instruments...")
        self.filter_input.setAccessibleName("Instrument Filter")
        self.filter_input.setAccessibleDescription(
            "Enter text to filter the list of instruments."
        )

        self.category_combo = QComboBox()
        self.category_combo.addItems(
            [
                "All",
                "Forex",
                "Indices",
                "Commodities",
                "Metals",
                "CFDs",
                "Bonds",
                "Other",
            ]
        )
        self.category_combo.setAccessibleName("Category Filter")
        self.category_combo.setAccessibleDescription(
            "Select a category to filter the list of instruments."
        )

        self.clear_btn = QPushButton("Clear Filter")
        self.clear_btn.setAccessibleName("Clear Filter Button")
        self.clear_btn.setAccessibleDescription(
            "Clears the instrument and category filters."
        )

        self.update_btn = QPushButton("Manual Update")
        self.update_btn.setAccessibleName("Manual Update Button")
        self.update_btn.setAccessibleDescription(
            "Manually fetches the latest financing rates from the OANDA API."
        )

        self.cancel_btn = QPushButton("Cancel Update")
        self.cancel_btn.setAccessibleName("Cancel Update Button")
        self.cancel_btn.setAccessibleDescription(
            "Cancels the ongoing manual update of financing rates."
        )
        self.cancel_btn.setEnabled(False)  # Initially disabled

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setAccessibleName("Settings Button")
        self.settings_btn.setAccessibleDescription(
            "Opens the settings dialog to configure the API key and URL."
        )

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        headers = [
            "Instrument",
            "Category",
            "Currency",
            "Days",
            "Long Rate",
            "Short Rate",
            "Long Charge",
            "Short Charge",
            "Units",
        ]
        self.table.setHorizontalHeaderLabels(headers)
        for i, label in enumerate(headers):
            self.table.horizontalHeaderItem(i).setToolTip(f"Column: {label}")
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setSortingEnabled(True)  # Enable sorting
        self.table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Make table focusable
        self.table.setAccessibleName("Financing Rates Table")
        self.table.setAccessibleDescription(
            "Displays the OANDA financing rates. Double-click on an instrument to view its history."
        )

        # --- Status Bar ---
        self.status_label = QLabel("TERMINAL READY")
        self.update_time_label = QLabel("LAST UPDATE: NEVER")
        self.statusBar().addPermanentWidget(self.status_label)
        self.statusBar().addPermanentWidget(self.update_time_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress_bar)

        # --- Layout Management ---
        control_layout.addWidget(QLabel("FILTER:"))
        control_layout.addWidget(self.filter_input)
        control_layout.addWidget(QLabel("CATEGORY:"))
        control_layout.addWidget(self.category_combo)
        control_layout.addWidget(self.clear_btn)
        control_layout.addWidget(self.update_btn)
        control_layout.addWidget(self.cancel_btn)
        control_layout.addWidget(self.settings_btn)

        self.export_btn = QPushButton("Export to CSV")
        self.export_btn.setAccessibleName("Export to CSV Button")
        self.export_btn.setAccessibleDescription(
            "Exports the currently displayed table data to a CSV file."
        )
        control_layout.addWidget(self.export_btn)

        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.table)

        # Set tab order
        self.setTabOrder(self.filter_input, self.category_combo)
        self.setTabOrder(self.category_combo, self.clear_btn)
        self.setTabOrder(self.clear_btn, self.update_btn)
        self.setTabOrder(self.update_btn, self.cancel_btn)
        self.setTabOrder(self.cancel_btn, self.settings_btn)
        self.setTabOrder(self.settings_btn, self.export_btn)
        self.setTabOrder(self.export_btn, self.table)

    def _on_table_double_click(self, item):
        """Handles the double-click event on a table item.

        When a user double-clicks on a row in the instrument table, this method
        extracts the instrument name from the clicked row and delegates the
        action to the presenter to show the historical data.

        Args:
            item: The QTableWidgetItem that was double-clicked.

        Example:
            >>> from unittest.mock import MagicMock
            >>> from PyQt6.QtWidgets import QTableWidgetItem
            >>> view = View(MagicMock())
            >>> view._setup_ui()
            >>> view.table.setRowCount(1)
            >>> view.table.setItem(0, 0, QTableWidgetItem("EUR_USD"))
            >>> mock_presenter = MagicMock()
            >>> view.set_presenter(mock_presenter)
            >>> view._on_table_double_click(view.table.item(0, 0))
            >>> mock_presenter.on_instrument_double_clicked.assert_called_once_with("EUR_USD")
        """
        instrument_name = self.table.item(item.row(), 0).text()
        self._presenter.on_instrument_double_clicked(instrument_name)

    def update_table(self, data: list[list[Any]]):
        """Updates the main display table with new data.

        This method populates the QTableWidget with the provided data,
        handling numeric column formatting and coloring. It temporarily
        disables sorting during the update to prevent visual glitches
        and restores the previous sort order afterward.

        Args:
            data (list[list[Any]]): A list of lists, where each inner list
                                    represents a row of data for the table.
        """
        # Store current sort order
        current_sort_column = self.table.horizontalHeader().sortIndicatorSection()
        current_sort_order = self.table.horizontalHeader().sortIndicatorOrder()

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(data))

        # Define which columns are numeric
        NUMERIC_COLUMNS = {
            4,
            5,
            6,
            7,
        }  # Long Rate, Short Rate, Long Charge, Short Charge

        for row_idx, row_data in enumerate(data):
            for col_idx, cell_data in enumerate(row_data):
                is_numeric = col_idx in NUMERIC_COLUMNS
                item = self._create_table_item(cell_data, is_numeric)
                self.table.setItem(row_idx, col_idx, item)

        self.table.setSortingEnabled(True)

        # Restore previous sort order
        if current_sort_column != -1:
            self.table.sortItems(current_sort_column, current_sort_order)

    def show_history_window(
        self, instrument_name: str, history_df: pd.DataFrame, stats: Dict[str, float]
    ) -> None:
        """Displays a dialog with historical data and statistics for a given instrument.

        Args:
            instrument_name: The name of the instrument (e.g., "EUR_USD").
            history_df: A pandas DataFrame containing the historical long and short rates.
                        Expected columns: "date", "long_rate", "short_rate".
            stats: A dictionary of statistical summaries for the rates.

        Example:
            >>> import pandas as pd
            >>> from unittest.mock import MagicMock
            >>> view = View(MagicMock())
            >>> history_data = {
            ...     "date": ["2023-01-01", "2023-01-02"],
            ...     "long_rate": [0.01, 0.015],
            ...     "short_rate": [-0.02, -0.025]
            ... }
            >>> history_df = pd.DataFrame(history_data)
            >>> stats_data = {
            ...     "Mean Long Rate": 0.0125,
            ...     "Mean Short Rate": -0.0225
            ... }
            >>> # To test, you would typically mock the QDialog.exec() method
            >>> # with unittest.mock.patch('src.view.HistoryDialog.exec', return_value=0):
            >>> view.show_history_window("EUR_USD", history_df, stats_data)
            # This would open the HistoryDialog for EUR_USD.
        """
        if not isinstance(history_df, pd.DataFrame) or history_df.empty:
            logger.error(f"Invalid history_df provided for {instrument_name}")
            self.set_status("Invalid history data", is_error=True)
            return
        if not isinstance(stats, dict):
            logger.error(f"Invalid stats provided for {instrument_name}")
            self.set_status("Invalid statistics data", is_error=True)
            return
        dialog = HistoryDialog(instrument_name, history_df, stats, self)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dialog.exec()

    def set_status(self, text, is_error=False):
        """Set the status bar message.

        Updates the text in the status bar and applies a color based on whether
        the message is an error or a regular status update.

        Args:
            text: The message string to display in the status bar.
            is_error: A boolean indicating if the message is an error (True) or not (False).

        Example:
            >>> from unittest.mock import MagicMock
            >>> view = View(MagicMock())
            >>> view._setup_ui()
            >>> view.set_status("Operation successful", is_error=False)
            >>> assert view.status_label.text() == "Operation successful"
            >>> # assert "color: #00FF00" in view.status_label.styleSheet() # Assuming green for positive
            >>> view.set_status("Operation failed", is_error=True)
            >>> assert view.status_label.text() == "Operation failed"
            >>> # assert "color: #FF0000" in view.status_label.styleSheet() # Assuming red for negative
        """
        color = THEME["negative"] if is_error else THEME["positive"]
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color};")

    def _is_data_stale(self, last_update_text: str) -> bool:
        """Checks if the data is stale (older than 24 hours)."""
        if last_update_text == "NEVER":
            return True
        try:
            last_update_date = datetime.strptime(last_update_text, "%Y-%m-%d")
            # Data is stale if it's from a previous day
            return last_update_date.date() < datetime.now().date()
        except ValueError:
            logger.warning(f"Could not parse last update time: {last_update_text}")
            return True  # Assume stale if parsing fails

    def set_update_time(self, text):
        """Set the last update time in the status bar.

        Updates the label in the status bar that displays the timestamp of
        the last data update.

        Args:
            text: The time string to display (e.g., "2023-10-27 10:30:00").

        Example:
            >>> from unittest.mock import MagicMock
            >>> view = View(MagicMock())
            >>> view._setup_ui()
            >>> view.set_update_time("2023-10-27 10:30:00")
            >>> assert view.update_time_label.text() == "LAST UPDATE: 2023-10-27 10:30:00"
        """
        self.update_time_label.setText(f"LAST UPDATE: {text}")
        # Add visual indicator when data is stale
        if self._is_data_stale(text):
            self.update_time_label.setStyleSheet(f"color: {THEME['negative']};")
        else:
            self.update_time_label.setStyleSheet(f"color: {THEME['positive']};")

    def clear_inputs(self):
        """Clears the instrument filter input field and resets the category selection.

        Resets the text in the instrument filter input field to an empty string
        and sets the category dropdown to its default "All" selection (index 0).
        """
        self.filter_input.setText("")
        self.category_combo.setCurrentIndex(0)

    def show_progress_bar(self):
        """Makes the indeterminate progress bar visible in the status bar.

        This indicates to the user that a background operation is currently
        in progress, such as fetching data from the API or performing
        a lengthy calculation.
        """
        self.progress_bar.setVisible(True)

    def hide_progress_bar(self):
        """Hides the indeterminate progress bar from the status bar.

        This signals the completion of a background operation, such as
        a data fetch or calculation, and restores the status bar to its
        normal state.
        """
        self.progress_bar.setVisible(False)

    def show_save_file_dialog(self, default_filename: str) -> Optional[str]:
        """Opens a save file dialog and returns the selected file path.

        Args:
            default_filename (str): The default filename to suggest to the user.

        Returns:
            Optional[str]: The absolute path to the selected file, or None if the dialog was cancelled.
        """
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data to CSV",
            default_filename,
            "CSV Files (*.csv);;All Files (*)",
        )
        return file_path if file_path else None

    def _apply_stylesheet(self):
        """Applies a CSS-like stylesheet to the application based on the current theme."""
        qss = f"""
            QMainWindow, QDialog {{
                background-color: {THEME["background"]};
                color: {THEME["text"]};
            }}
            QWidget {{
                background-color: {THEME["background"]};
                color: {THEME["text"]};
            }}
            QTableView, QTableWidget {{
                background-color: {THEME["table_background"]};
                gridline-color: {THEME["table_gridline"]};
            }}
            QHeaderView::section {{
                background-color: {THEME["header_background"]};
                color: {THEME["header_text"]};
                padding: 4px;
                border: 1px solid {THEME["table_gridline"]};
            }}
            QTableWidget::item {{
                padding: 5px;
            }}
            QTableWidget::item:selected {{
                background-color: {THEME["selected_background"]};
                color: {THEME["selected_text"]};
            }}
            QPushButton {{
                background-color: {THEME["button_background"]};
                color: {THEME["button_text"]};
                border: none;
                padding: 8px 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {THEME["button_hover"]};
            }}
            QLineEdit, QComboBox {{
                background-color: {THEME["input_background"]};
                border: 1px solid {THEME["input_border"]};
                padding: 5px;
            }}
            QStatusBar {{
                color: {THEME["status_text"]};
            }}
            QLabel {{
                color: {THEME["status_text"]};
            }}
        """
        self.setStyleSheet(qss)

    def _parse_numeric_value(self, cell_data: Any) -> tuple[Optional[float], str]:
        """Parse cell data into numeric value and display string.

        Returns:
            Tuple of (numeric_value or None, display_string)
        """
        display_str = str(cell_data)
        try:
            numeric_value = float(display_str.replace("%", ""))
            return numeric_value, display_str
        except (ValueError, AttributeError):
            return None, display_str

    def _apply_value_color(
        self, item: QTableWidgetItem, numeric_value: Optional[float]
    ) -> None:
        """Apply color to table item based on numeric value.

        Args:
            item: The table widget item to color
            numeric_value: The numeric value (positive=green, negative=red, None=default)
        """
        if numeric_value is None:
            return

        if numeric_value > 0:
            item.setForeground(QBrush(QColor(THEME["positive"])))
        elif numeric_value < 0:
            item.setForeground(QBrush(QColor(THEME["negative"])))

    def _create_table_item(
        self, cell_data: Any, is_numeric_column: bool = False
    ) -> QTableWidgetItem:
        """Create a table item with appropriate formatting.

        Args:
            cell_data: The data to display
            is_numeric_column: Whether this column contains numeric data

        Returns:
            Configured QTableWidgetItem
        """
        if is_numeric_column:
            item = NumericTableWidgetItem()
            numeric_value, display_str = self._parse_numeric_value(cell_data)

            if numeric_value is not None:
                item.setData(Qt.ItemDataRole.UserRole, numeric_value)
            else:
                item.setData(Qt.ItemDataRole.UserRole, display_str)

            item.setData(Qt.ItemDataRole.DisplayRole, display_str)
            self._apply_value_color(item, numeric_value)
        else:
            item = NumericTableWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, str(cell_data))
            item.setData(Qt.ItemDataRole.DisplayRole, str(cell_data))

        return item

    def closeEvent(self, event):
        """Handles the close event for the main window.

        This method is overridden to save the window's geometry before closing
        and to stop any running QTimer to ensure a clean shutdown.

        Args:
            event: The QCloseEvent object.

        Example:
            >>> from unittest.mock import MagicMock
            >>> from PyQt6.QtGui import QCloseEvent
            >>> view = View(MagicMock())
            >>> view._setup_ui()
            >>> mock_timer = MagicMock()
            >>> view.set_timer(mock_timer)
            >>> event = QCloseEvent()
            >>> view.closeEvent(event)
            >>> view.settings.setValue.assert_called_with("geometry", view.saveGeometry())
            >>> mock_timer.stop.assert_called_once()
            >>> assert event.isAccepted()
        """
        self.settings.setValue("geometry", self.saveGeometry())
        if self._timer:
            self._timer.stop()
        super().closeEvent(event)
