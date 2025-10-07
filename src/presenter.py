
import queue
import schedule
import threading
import time
from datetime import datetime
import pytz
import pandas as pd

class Presenter:
    """
    The presenter acts as the middleman between the View (UI) and the Model (data).
    It contains the core application logic and ensures thread-safe UI updates.
    """

    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.latest_date = None
        self.raw_data = {}
        self.filter_text = ""
        self.selected_category = "All"
        self.ui_update_queue = queue.Queue()

    # --- Event Handlers (called by View) ---

    def on_app_start(self):
        """Called when the application starts."""
        threading.Thread(target=self._initial_load_job, daemon=True).start()
        self._start_scheduler()

    def on_manual_update(self):
        """Handles the 'Manual Update' button click."""
        self.ui_update_queue.put({"type": "status", "payload": {"text": "Fetching new data from API..."}})
        threading.Thread(target=self._fetch_job, daemon=True).start()

    def on_filter_text_changed(self, filter_text):
        self.filter_text = filter_text.lower()
        self._update_display()

    def on_category_selected(self, category):
        self.selected_category = category
        self._update_display()

    def on_clear_filter(self):
        self.filter_text = ""
        self.selected_category = "All"
        self.view.clear_inputs()
        self._update_display()

    def on_instrument_double_clicked(self, instrument_name):
        """Handles a double-click event on the table to show history."""
        if not instrument_name:
            return

        self.view.set_status(f"Loading history for {instrument_name}...")
        history_df = self.model.get_instrument_history(instrument_name)
        if history_df.empty:
            self.view.set_status(f"No history found for {instrument_name}", is_error=True)
            return

        # Convert data to numeric before calculating stats
        history_df['long_rate'] = pd.to_numeric(history_df['long_rate'], errors='coerce')
        history_df['short_rate'] = pd.to_numeric(history_df['short_rate'], errors='coerce')

        # Calculate stats
        stats = {
            "Mean Long Rate": history_df['long_rate'].mean(),
            "Median Long Rate": history_df['long_rate'].median(),
            "Std Dev Long Rate": history_df['long_rate'].std(),
            "Mean Short Rate": history_df['short_rate'].mean(),
            "Median Short Rate": history_df['short_rate'].median(),
            "Std Dev Short Rate": history_df['short_rate'].std(),
        }

        self.view.show_history_window(instrument_name, history_df, stats)
        self.view.set_status("History window displayed.")

    # --- Core Logic (UI-Thread Safe) ---

    def process_ui_updates(self):
        """Checks the queue for UI updates and applies them. Runs on the main thread."""
        try:
            while not self.ui_update_queue.empty():
                message = self.ui_update_queue.get_nowait()
                msg_type = message.get("type")
                payload = message.get("payload")

                if msg_type == "status":
                    self.view.set_status(payload.get("text"), payload.get("is_error", False))
                elif msg_type == "data":
                    self.raw_data = payload
                    self.latest_date = datetime.now().strftime("%Y-%m-%d")
                    self.view.set_update_time(self.latest_date)
                    self._update_display()
                elif msg_type == "initial_data":
                    self.latest_date, self.raw_data = payload
                    self.view.set_update_time(self.latest_date or "NEVER")
                    self._update_display()

        except queue.Empty:
            pass

    def _update_display(self):
        """Filters the current data and updates the view's table."""
        if not self.raw_data or "financingRates" not in self.raw_data:
            self.view.update_table([])
            return

        filtered_data = []
        for rate in self.raw_data.get("financingRates", []):
            instrument = rate.get("instrument", "")
            category = self.model.categorize_instrument(instrument)
            if self.selected_category != "All" and category != self.selected_category:
                continue
            if self.filter_text and self.filter_text not in instrument.lower():
                continue
            long_rate = float(rate.get("longRate", 0.0)) * 100
            short_rate = float(rate.get("shortRate", 0.0)) * 100

            row_data = [
                instrument,
                category,  # Use the calculated category
                rate.get("currency", ""),
                rate.get("days", ""),
                f"{long_rate:.2f}%",
                f"{short_rate:.2f}%",
                rate.get("longCharge", ""),
                rate.get("shortCharge", ""),
                rate.get("units", ""),
            ]
            filtered_data.append(row_data)
        
        self.view.update_table(filtered_data)
        self.view.set_status(f"Display updated. Showing {len(filtered_data)} instruments.")

    # --- Background Jobs (Worker Threads) ---

    def _initial_load_job(self):
        """Job to load initial data from DB or API."""
        self.ui_update_queue.put({"type": "status", "payload": {"text": "Loading latest data from database..."}})
        date, data = self.model.get_latest_rates()
        if data:
            self.ui_update_queue.put({"type": "initial_data", "payload": (date, data)})
            self.ui_update_queue.put({"type": "status", "payload": {"text": "Data loaded successfully."}})
        else:
            self._fetch_job(is_initial=True)

    def _fetch_job(self, is_initial=False):
        """Job to fetch new data from the API."""
        if is_initial:
            self.ui_update_queue.put({"type": "status", "payload": {"text": "No local data. Fetching from API..."}})
        
        new_data = self.model.fetch_and_save_rates()
        if new_data:
            self.ui_update_queue.put({"type": "data", "payload": new_data})
            self.ui_update_queue.put({"type": "status", "payload": {"text": "API fetch successful."}})
        else:
            self.ui_update_queue.put({"type": "status", "payload": {"text": "API fetch failed. Check logs.", "is_error": True}})

    # --- Scheduler Logic ---

    def _start_scheduler(self):
        schedule.every().day.at("22:30").do(self._scheduled_update_job)
        scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        scheduler_thread.start()

    def _run_scheduler(self):
        while True:
            schedule.run_pending()
            time.sleep(60)

    def _scheduled_update_job(self):
        self.ui_update_queue.put({"type": "status", "payload": {"text": "Performing scheduled update..."}})
        self._fetch_job()
