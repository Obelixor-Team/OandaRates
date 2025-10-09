import queue
import logging
import threading
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional, TypedDict
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore

if TYPE_CHECKING:
    from .model import Model
    from .view import View

logger = logging.getLogger(__name__)

MAX_FILTER_LENGTH = 100


class UIUpdate(TypedDict):
    type: str
    payload: Dict[str, Any]


class Presenter:
    """The presenter acts as the middleman between the View (UI) and the Model (data).

    It contains the core application logic and ensures thread-safe UI updates.
    """

    def __init__(self, model: "Model", view: "View") -> None:
        self.model = model
        self.view = view
        self.latest_date: Optional[str] = None
        self.raw_data: Dict[str, Any] = {}
        self.filter_text: str = ""
        self.selected_category: str = "All"
        self.ui_update_queue: queue.Queue[UIUpdate] = queue.Queue()
        self.scheduler: Optional[BackgroundScheduler] = None
        self.executor = ThreadPoolExecutor(max_workers=2)  # Limit concurrent tasks
        self._cancellation_event = threading.Event()

    def shutdown(self) -> None:
        """Shuts down the scheduler and thread pool executor gracefully."""
        if self.scheduler:
            try:
                if self.scheduler.running:
                    self.scheduler.shutdown(wait=True)
                    logger.info("Scheduler shut down.")
            except Exception as e:
                logger.warning(f"Error shutting down scheduler: {e}")

        self.executor.shutdown(wait=True)
        logger.info("ThreadPoolExecutor shut down.")
        self.model.close()
        logger.info("Model cleanup completed.")

    def _queue_error(self, message: str) -> None:
        self.ui_update_queue.put(
            {"type": "status", "payload": {"text": message, "is_error": True}}
        )

    def _queue_status(self, message: str) -> None:
        self.ui_update_queue.put(
            {"type": "status", "payload": {"text": message, "is_error": False}}
        )

    def _queue_show_progress(self) -> None:
        """Show progress bar via queue."""
        self.ui_update_queue.put({"type": "show_progress", "payload": {}})

    def _queue_hide_progress(self) -> None:
        """Hide progress bar via queue."""
        self.ui_update_queue.put({"type": "hide_progress", "payload": {}})

    def _queue_enable_buttons(self, enabled: bool = True) -> None:
        """Enable/disable update buttons via queue."""
        self.ui_update_queue.put(
            {"type": "set_buttons_enabled", "payload": {"enabled": enabled}}
        )

    def _queue_update_table(self, data: list) -> None:
        """Update table data via queue."""
        self.ui_update_queue.put({"type": "update_table", "payload": {"data": data}})

    def _queue_clear_inputs(self) -> None:
        """Clear input fields via queue."""
        self.ui_update_queue.put({"type": "clear_inputs", "payload": {}})

    def _calculate_rate_statistics(
        self, 
        series: pd.Series, 
        rate_type: str
    ) -> Dict[str, float]:
        """Calculate statistical measures for a rate series.
        
        Args:
            series: Pandas series containing rate data
            rate_type: Type of rate ("Long" or "Short")
            
        Returns:
            Dictionary of statistics
        """
        return {
            f"Mean {rate_type} Rate": series.mean(),
            f"Median {rate_type} Rate": series.median(),
            f"Std Dev {rate_type} Rate": series.std(),
            f"Min {rate_type} Rate": series.min(),
            f"Max {rate_type} Rate": series.max(),
        }

    def _calculate_daily_change_stats(
        self, 
        history_df: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate average daily change statistics.
        
        Args:
            history_df: DataFrame with 'long_rate' and 'short_rate' columns
            
        Returns:
            Dictionary with daily change statistics
        """
        if len(history_df) > 1:
            history_df = history_df.copy()  # Avoid modifying original
            history_df["long_rate_diff"] = history_df["long_rate"].diff().abs()
            history_df["short_rate_diff"] = history_df["short_rate"].diff().abs()
            return {
                "Avg Daily Change Long Rate": history_df["long_rate_diff"].mean(),
                "Avg Daily Change Short Rate": history_df["short_rate_diff"].mean(),
            }
        return {
            "Avg Daily Change Long Rate": 0.0,
            "Avg Daily Change Short Rate": 0.0,
        }

    # --- Event Handlers (called by View) ---

    def on_app_start(self):
        """Start initial data load and scheduler threads."""
        self.executor.submit(self._initial_load_job)
        self._start_scheduler()

    def on_manual_update(self):
        """Handle the 'Manual Update' button click."""
        self._cancellation_event.clear()
        self._queue_enable_buttons(False)
        self._queue_status("Fetching new data from API...")
        self._queue_show_progress()
        self.executor.submit(self._fetch_job, "manual")

    def on_cancel_update(self):
        """Handle the 'Cancel Update' button click."""
        self._cancellation_event.set()
        self._queue_status(
            "Cancellation requested. Waiting for current operation to finish..."
        )
        self._queue_enable_buttons(True)

    def on_filter_text_changed(self, filter_text: str):
        """Handle changes in the filter input text."""
        if not isinstance(filter_text, str):
            logger.warning(f"Invalid type for filter_text: {type(filter_text)}")
            return
        if len(filter_text) > MAX_FILTER_LENGTH:
            logger.warning(
                f"Filter text exceeds maximum length of {MAX_FILTER_LENGTH} characters."
            )
            self._queue_error(f"Filter text too long (max {MAX_FILTER_LENGTH} chars)")
            filter_text = filter_text[:MAX_FILTER_LENGTH]
        self.filter_text = filter_text.lower()
        self._update_display()

    def on_category_selected(self, category: str):
        """Handle changes in the category dropdown."""
        self.selected_category = category
        self._update_display()

    def on_clear_filter(self):
        """Handle the 'Clear Filter' button click."""
        self.filter_text = ""
        self.selected_category = "All"
        self._queue_clear_inputs()
        self._update_display()

    def on_instrument_double_clicked(self, instrument_name: str):
        """Handle a double-click event on the table to show history."""
        if not isinstance(instrument_name, str) or not instrument_name.strip():
            logger.warning(f"Invalid instrument_name: '{instrument_name}'")
            self._queue_error("Invalid instrument name provided.")
            return

        self._queue_status(f"Loading history for {instrument_name}...")
        history_df = self.model.get_instrument_history(instrument_name)
        
        if history_df.empty:
            self._queue_error(f"No history found for {instrument_name}")
            return

        # Convert data to numeric before calculating stats
        history_df["long_rate"] = pd.to_numeric(history_df["long_rate"], errors="coerce")
        history_df["short_rate"] = pd.to_numeric(history_df["short_rate"], errors="coerce")

        # Calculate statistics
        stats = {}
        stats.update(self._calculate_rate_statistics(history_df["long_rate"], "Long"))
        stats.update(self._calculate_rate_statistics(history_df["short_rate"], "Short"))
        stats.update(self._calculate_daily_change_stats(history_df))

        self.ui_update_queue.put({
            "type": "show_history_window",
            "payload": {
                "instrument_name": instrument_name,
                "history_df": history_df,
                "stats": stats,
            },
        })
        self._queue_status("History window displayed.")

    # --- Core Logic (UI-Thread Safe) ---

    def _process_and_cache_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and cache the raw data.

        This method takes raw financing rate data, calculates percentage values
        for long and short rates, and prepares it for display. It also serves
        as a point for caching the processed data within the presenter.

        Args:
            data: A dictionary containing the raw financing rates, typically
                  fetched from the OANDA API.

        Returns:
            Dict[str, Any]: The processed data with 'longRate_pct' and
                            'shortRate_pct' added to each financing rate entry.

        Example:
            >>> presenter = Presenter(model, view) # Assume model and view are initialized
            >>> raw_data = {
            ...     "financingRates": [
            ...         {"instrument": "EUR_USD", "longRate": "0.0083", "shortRate": "-0.0133"}
            ...     ]
            ... }
            >>> processed_data = presenter._process_and_cache_data(raw_data)
            >>> print(processed_data['financingRates'][0]['longRate_pct'])
            0.83
        """
        if "financingRates" in data:
            for rate in data["financingRates"]:
                rate["longRate_pct"] = float(rate.get("longRate", 0.0)) * 100
                rate["shortRate_pct"] = float(rate.get("shortRate", 0.0)) * 100
        return data

    def process_ui_updates(self):
        """Check the queue for UI updates and apply them. Runs on the main thread.

        This method is typically called periodically by a QTimer in the View.
        It dequeues UIUpdate messages and dispatches them to the appropriate
        View methods or updates internal state.

        Example:
            >>> # Assuming a Presenter instance 'p' and a View instance 'v'
            >>> # A message is put into the queue (e.g., from a background thread)
            >>> p.ui_update_queue.put({
            ...     "type": "status",
            ...     "payload": {"text": "Loading data...", "is_error": False}
            ... })
            >>> p.process_ui_updates()
            >>> v.set_status.assert_called_once_with("Loading data...", is_error=False)

            >>> p.ui_update_queue.put({
            ...     "type": "data",
            ...     "payload": {"financingRates": []}
            ... })
            >>> p.process_ui_updates()
            >>> v.hide_progress_bar.assert_called_once()
            >>> v.set_update_time.assert_called_once()
        """
        try:
            while not self.ui_update_queue.empty():
                message = self.ui_update_queue.get_nowait()
                msg_type = message.get("type")
                payload = message.get("payload")

                if msg_type == "status":
                    self.view.set_status(
                        payload.get("text"),
                        is_error=payload.get("is_error", False),
                    )
                elif msg_type == "data":
                    self._queue_hide_progress()
                    self.raw_data = self._process_and_cache_data(payload)
                    self.latest_date = datetime.now().strftime("%Y-%m-%d")
                    self.view.set_update_time(self.latest_date)
                    self._update_display()
                elif msg_type == "initial_data":
                    self._queue_hide_progress()
                    self.latest_date, raw_data = payload
                    self.raw_data = self._process_and_cache_data(raw_data)
                    self.view.set_update_time(self.latest_date or "NEVER")
                    self._update_display()
                elif msg_type == "show_progress":
                    self.view.show_progress_bar()
                elif msg_type == "hide_progress":
                    self.view.hide_progress_bar()
                elif msg_type == "set_buttons_enabled":
                    self.view.set_update_buttons_enabled(payload["enabled"])
                elif msg_type == "clear_inputs":
                    self.view.clear_inputs()
                elif msg_type == "show_history_window":
                    self.view.show_history_window(
                        payload["instrument_name"],
                        payload["history_df"],
                        payload["stats"],
                    )
                elif msg_type == "update_table":
                    self.view.update_table(payload["data"])

        except queue.Empty:
            pass

    def _update_display(self):
        """Filter the current data and update the view's table.

        This method applies the current filter text and category selection
        to the raw data and then updates the main table in the view with
        the filtered results. It also updates the status bar with the
        number of instruments displayed.

        Example:
            >>> # Assuming 'presenter' has loaded some data and has a view attached
            >>> presenter.filter_text = "eur"
            >>> presenter.selected_category = "Forex"
            >>> presenter._update_display()
            # Expected: The view's table is updated with filtered data,
            # and the status bar reflects the update.
        """

        if not self.raw_data or "financingRates" not in self.raw_data:
            self._queue_update_table(data=[])
            return

        filtered_data = []
        for rate in self.raw_data.get("financingRates", []):
            try:
                instrument = rate.get("instrument", "")
                if not instrument:
                    continue

                category = self.model.categorize_instrument(instrument)
                if (
                    self.selected_category != "All"
                    and category != self.selected_category
                ):
                    continue
                if self.filter_text and self.filter_text not in instrument.lower():
                    continue

                currency = self.model.infer_currency(
                    instrument, rate.get("currency", "")
                )

                row_data = [
                    instrument,
                    category,  # Use the calculated category
                    currency,
                    str(rate.get("days", "")),
                    f"{float(rate.get('longRate_pct', 0.0)):.2f}%",
                    f"{float(rate.get('shortRate_pct', 0.0)):.2f}%",
                    str(rate.get("longCharge", "")),
                    str(rate.get("shortCharge", "")),
                    str(rate.get("units", "")),
                ]
                filtered_data.append(row_data)
            except (ValueError, TypeError, KeyError) as e:
                logger.warning(f"Error processing rate for {instrument}: {e}")
                continue

        self._queue_update_table(data=filtered_data)
        self._queue_status(
            f"Display updated. Showing {len(filtered_data)} instruments."
        )

    # --- Background Jobs (Worker Threads) ---

    def _initial_load_job(self):
        """Load initial data from DB or API.

        This method is executed in a background thread upon application start.
        It first attempts to load the latest rates from the local database.
        If no data is found in the database, it then triggers a fetch from the
        OANDA API and saves it to the database.

        Example:
            >>> # This method is typically called by on_app_start:
            >>> # presenter.executor.submit(presenter._initial_load_job)
            >>> # Direct call for testing (requires mocking queue and model interactions):
            >>> # presenter._initial_load_job()
            # Expected: UI is updated with progress, status messages, and eventually
            # the main table is populated with data from DB or API.
        """
        self._queue_show_progress()
        self._queue_status("Loading latest data from database...")
        date, data = self.model.get_latest_rates()
        if data:

            self.ui_update_queue.put({"type": "initial_data", "payload": (date, data)})
            self._queue_status("Data loaded successfully.")
        else:
            self._fetch_job(source="initial", is_initial=True)

    def _fetch_job(self, source: str = "manual", is_initial: bool = False):
        """Fetch new data from the API."""
        if self._cancellation_event.is_set():
            self._cancellation_event.clear()
            self._queue_error("Update cancelled.")
            self._queue_hide_progress()
            self._queue_enable_buttons(True)
            return

    # --- Scheduler Logic ---

    def _start_scheduler(self) -> None:
        try:
            self.scheduler = BackgroundScheduler(timezone="America/New_York")
            self.scheduler.add_job(
                self._scheduled_update_job, "cron", hour=17, minute=30
            )
            self.scheduler.start()
            logger.info("Scheduler started successfully.")
        except Exception as e:
            logger.exception("Scheduler failed to start.")
            self._queue_error(f"Scheduler failed to start: {str(e)}")

    def _scheduled_update_job(self):
        """Perform the scheduled update job."""
        self._queue_show_progress()
        self._queue_status("Performing scheduled update...")
        self._fetch_job(source="scheduled")
