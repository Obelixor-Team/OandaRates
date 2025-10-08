import logging

import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
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

from typing import TYPE_CHECKING, Optional, Dict

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
        # self.setMinimumSize(800, 600) # Removed to allow dynamic resizing

        layout = QVBoxLayout()

        # Stats Layout
        stats_layout = QHBoxLayout()

        long_stats_text = "Long Rates:\n"
        short_stats_text = "Short Rates:\n"

        for key, value in stats.items():
            if "Long Rate" in key:
                long_stats_text += f"{key}: {value * 100:.2f}%\n"
            elif "Short Rate" in key:
                short_stats_text += f"{key}: {value * 100:.2f}%\n"
            elif "Long Change" in key:
                long_stats_text += f"{key}: {value * 100:.2f}%\n"
            elif "Short Change" in key:
                short_stats_text += f"{key}: {value * 100:.2f}%\n"

        long_stats_label = QLabel(long_stats_text)
        short_stats_label = QLabel(short_stats_text)

        stats_layout.addWidget(long_stats_label)
        stats_layout.addWidget(short_stats_label)

        layout.addLayout(stats_layout)

        # Plot
        if not history_df.empty:
            sc = MplCanvas(self, width=5, height=4, dpi=100)
            history_df["long_rate"] = pd.to_numeric(
                history_df["long_rate"],
                errors="coerce",
            )
            history_df["short_rate"] = pd.to_numeric(
                history_df["short_rate"],
                errors="coerce",
            )
            dates = pd.to_datetime(history_df["date"])

            sc.axes.plot(dates, history_df["long_rate"], label="Long Rate")
            sc.axes.plot(dates, history_df["short_rate"], label="Short Rate")
            sc.axes.legend()
            sc.axes.set_xlabel("Date")
            sc.axes.set_ylabel("Rate (%)")
            sc.axes.grid(True, linestyle="--", alpha=0.7, color=THEME["text"])
            sc.axes.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            sc.figure.autofmt_xdate()
            sc.figure.tight_layout()  # Add tight layout for better plot spacing
            layout.addWidget(sc)

        self.setLayout(layout)
        self.resize(self.sizeHint())  # Dynamic sizing based on content


# --- Main View ---
class View(QMainWindow):
    """Main application window for displaying OANDA financing rates."""

    def __init__(self, presenter: Optional["Presenter"] = None) -> None:
        super().__init__()
        self._presenter: Optional["Presenter"] = presenter
        self._timer: Optional[QTimer] = None
        self.setWindowTitle("OANDA FINANCING TERMINAL v4.0")
        # self.setGeometry(100, 100, 1400, 900) # Removed to use saved geometry
        self._apply_stylesheet()
        self._setup_ui()
        # self.presenter.on_app_start() # This will be called from main.py after presenter is set

        # Load window settings
        self.settings = QSettings("OandaRates", "OandaFinancingTerminal")
        if self.settings.contains("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        else:
            self.setGeometry(100, 100, 1400, 900)  # Default size if no settings saved

    def set_timer(self, timer: QTimer) -> None:
        self._timer = timer

    def set_presenter(self, presenter: "Presenter") -> None:
        self._presenter = presenter
        # Connect signals to presenter methods after presenter is set
        self.filter_input.textChanged.connect(self._presenter.on_filter_text_changed)
        self.category_combo.currentTextChanged.connect(
            self._presenter.on_category_selected
        )
        self.clear_btn.clicked.connect(self._presenter.on_clear_filter)
        self.update_btn.clicked.connect(self._presenter.on_manual_update)
        self.table.itemDoubleClicked.connect(self._on_table_double_click)

    def _setup_ui(self):
        # --- Central Widget and Layouts ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        control_layout = QHBoxLayout()

        # --- Widgets ---
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter instruments...")

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

        self.clear_btn = QPushButton("Clear Filter")
        self.update_btn = QPushButton("Manual Update")

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

        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.table)

    def _on_table_double_click(self, item):
        instrument_name = self.table.item(item.row(), 0).text()
        self._presenter.on_instrument_double_clicked(instrument_name)

    def update_table(self, data):
        """Update the main table with new data."""
        # Store current sort order
        current_sort_column = self.table.horizontalHeader().sortIndicatorSection()
        current_sort_order = self.table.horizontalHeader().sortIndicatorOrder()

        self.table.setSortingEnabled(False)  # Disable sorting during update
        self.table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_data in enumerate(row_data):
                # Use NumericTableWidgetItem for numerical columns, QTableWidgetItem for others
                if col_idx in [
                    4,
                    5,
                    6,
                    7,
                ]:  # Long Rate, Short Rate, Long Charge, Short Charge
                    item = NumericTableWidgetItem()
                    try:
                        numeric_value = float(str(cell_data).replace("%", ""))
                        item.setData(Qt.ItemDataRole.UserRole, numeric_value)
                    except ValueError:
                        item.setData(
                            Qt.ItemDataRole.UserRole, str(cell_data)
                        )  # Fallback for non-numeric
                else:
                    item = QTableWidgetItem()
                    item.setData(Qt.ItemDataRole.UserRole, str(cell_data))

                item.setData(Qt.ItemDataRole.DisplayRole, str(cell_data))

                # Apply color to Long Rate, Short Rate, Long Charge, Short Charge columns
                if col_idx in [
                    4,
                    5,
                    6,
                    7,
                ]:  # Long Rate, Short Rate, Long Charge, Short Charge
                    try:
                        numeric_value = float(str(cell_data).replace("%", ""))
                        if numeric_value > 0:
                            item.setForeground(
                                QBrush(QColor(THEME["positive"]))
                            )  # Green
                        elif numeric_value < 0:
                            item.setForeground(QBrush(QColor(THEME["negative"])))  # Red
                    except ValueError:
                        pass  # Ignore if conversion fails
                self.table.setItem(row_idx, col_idx, item)

        self.table.setSortingEnabled(True)  # Re-enable sorting
        # Restore previous sort order
        if current_sort_column != -1:
            self.table.sortItems(current_sort_column, current_sort_order)

    def show_history_window(
        self, instrument_name: str, history_df: pd.DataFrame, stats: Dict[str, float]
    ) -> None:
        if not isinstance(history_df, pd.DataFrame) or history_df.empty:
            logger.error(f"Invalid history_df provided for {instrument_name}")
            self.set_status("Invalid history data", is_error=True)
            return
        if not isinstance(stats, dict):
            logger.error(f"Invalid stats provided for {instrument_name}")
            self.set_status("Invalid statistics data", is_error=True)
            return
        dialog = HistoryDialog(instrument_name, history_df, stats, self)
        dialog.exec()

    def set_status(self, text, is_error=False):
        """Set the status bar message."""
        color = THEME["negative"] if is_error else THEME["positive"]
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color};")

    def set_update_time(self, text):
        """Set the last update time in the status bar."""
        self.update_time_label.setText(f"LAST UPDATE: {text}")

    def clear_inputs(self):
        """Clear filter and category input fields."""
        self.filter_input.setText("")
        self.category_combo.setCurrentIndex(0)

    def show_progress_bar(self):
        """Show the progress bar."""
        self.progress_bar.setVisible(True)

    def hide_progress_bar(self):
        """Hide the progress bar."""
        self.progress_bar.setVisible(False)

    def _apply_stylesheet(self):
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

    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        if self._timer:
            self._timer.stop()
        super().closeEvent(event)
