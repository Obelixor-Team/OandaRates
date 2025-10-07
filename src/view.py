import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


# --- Matplotlib Canvas for plotting ---
class MplCanvas(FigureCanvas):
    """Matplotlib canvas for embedding plots in PyQt6 applications."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, facecolor="#121220")
        self.axes = fig.add_subplot(111)
        self.axes.set_facecolor("#121220")
        self.axes.spines["top"].set_color("#e0e0e0")
        self.axes.spines["bottom"].set_color("#e0e0e0")
        self.axes.spines["left"].set_color("#e0e0e0")
        self.axes.spines["right"].set_color("#e0e0e0")
        self.axes.tick_params(axis="x", colors="#e0e0e0")
        self.axes.tick_params(axis="y", colors="#e0e0e0")
        self.axes.xaxis.label.set_color("#e0e0e0")
        self.axes.yaxis.label.set_color("#e0e0e0")
        self.axes.title.set_color("#e0e0e0")
        super(MplCanvas, self).__init__(fig)


# --- History Dialog ---
class HistoryDialog(QDialog):
    """Dialog to display historical instrument data and statistics."""

    def __init__(self, instrument_name, history_df, stats, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"History for {instrument_name}")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout()

        # Stats
        stats_text = ""
        for key, value in stats.items():
            stats_text += f"{key}: {value * 100:.2f}%\n"
        stats_label = QLabel(stats_text)
        layout.addWidget(stats_label)

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
            sc.figure.autofmt_xdate()
            layout.addWidget(sc)

        self.setLayout(layout)


# --- Main View ---
class View(QMainWindow):
    """Main application window for displaying OANDA financing rates."""

    def __init__(self, presenter):
        super().__init__()
        self.presenter = presenter
        self.setWindowTitle("OANDA FINANCING TERMINAL v4.0")
        self.setGeometry(100, 100, 1400, 900)
        self._apply_stylesheet()
        self._setup_ui()
        self.presenter.on_app_start()

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
        self.table.setHorizontalHeaderLabels(
            [
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
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        # --- Status Bar ---
        self.status_label = QLabel("TERMINAL READY")
        self.update_time_label = QLabel("LAST UPDATE: NEVER")
        self.statusBar().addPermanentWidget(self.status_label)
        self.statusBar().addPermanentWidget(self.update_time_label)

        # --- Layout Management ---
        control_layout.addWidget(QLabel("FILTER:"))
        control_layout.addWidget(self.filter_input)
        control_layout.addWidget(QLabel("CATEGORY:"))
        control_layout.addWidget(self.category_combo)
        control_layout.addWidget(self.clear_btn)
        control_layout.addWidget(self.update_btn)

        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.table)

        # --- Connect Signals ---
        self.filter_input.textChanged.connect(self.presenter.on_filter_text_changed)
        self.category_combo.currentTextChanged.connect(
            self.presenter.on_category_selected
        )
        self.clear_btn.clicked.connect(self.presenter.on_clear_filter)
        self.update_btn.clicked.connect(self.presenter.on_manual_update)
        self.table.itemDoubleClicked.connect(self._on_table_double_click)

    def _on_table_double_click(self, item):
        instrument_name = self.table.item(item.row(), 0).text()
        self.presenter.on_instrument_double_clicked(instrument_name)

    def update_table(self, data):
        """Update the main table with new data."""
        self.table.setRowCount(0)
        self.table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_data in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_data)))

    def show_history_window(self, instrument_name, history_df, stats):
        """Display a dialog with historical data and stats for an instrument."""
        dialog = HistoryDialog(instrument_name, history_df, stats, self)
        dialog.exec()

    def set_status(self, text, is_error=False):
        """Set the status bar message."""
        color = "#ff5555" if is_error else "#00ff9d"
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color};")

    def set_update_time(self, text):
        """Set the last update time in the status bar."""
        self.update_time_label.setText(f"LAST UPDATE: {text}")

    def clear_inputs(self):
        """Clear filter and category input fields."""
        self.filter_input.setText("")
        self.category_combo.setCurrentIndex(0)

    def _apply_stylesheet(self):
        qss = """
            QMainWindow, QDialog {
                background-color: #0a0a12;
                color: #e0e0e0;
            }
            QWidget {
                background-color: #0a0a12;
                color: #e0e0e0;
            }
            QTableView, QTableWidget {
                background-color: #1a1a2e;
                gridline-color: #2a2a3e;
            }
            QHeaderView::section {
                background-color: #121220;
                color: #00ff9d;
                padding: 4px;
                border: 1px solid #2a2a3e;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #0095ff;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0095ff;
                color: #ffffff;
                border: none;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0077cc;
            }
            QLineEdit, QComboBox {
                background-color: #1a1a2e;
                border: 1px solid #2a2a3e;
                padding: 5px;
            }
            QStatusBar {
                color: #a0a0b0;
            }
            QLabel {
                color: #a0a0b0;
            }
        """
        self.setStyleSheet(qss)
