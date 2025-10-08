import queue
import threading
import time
from datetime import datetime

import pandas as pd
import schedule


class Presenter:
    """The presenter acts as the middleman between the View (UI) and the Model (data).

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
        """Start initial data load and scheduler threads.

        Called when the application starts.
        """
        threading.Thread(target=self._initial_load_job, daemon=True).start()
        self._start_scheduler()

    def on_manual_update(self):
        """Handle the 'Manual Update' button click."""
        self.ui_update_queue.put(
            {"type": "status", "payload": {"text": "Fetching new data from API..."}}
        )
        threading.Thread(target=self._fetch_job, args=("manual",), daemon=True).start()

    def on_filter_text_changed(self, filter_text: str):
        """Handle changes in the filter input text."""
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
        self.view.clear_inputs()
        self._update_display()

    def on_instrument_double_clicked(self, instrument_name: str):
        """Handle a double-click event on the table to show history."""
        if not instrument_name:
            return

        self.view.set_status(f"Loading history for {instrument_name}...")
        history_df = self.model.get_instrument_history(instrument_name)
        if history_df.empty:
            self.view.set_status(
                f"No history found for {instrument_name}",
                is_error=True,
            )
            return

        # Convert data to numeric before calculating stats
        history_df["long_rate"] = pd.to_numeric(
            history_df["long_rate"],
            errors="coerce",
        )
        history_df["short_rate"] = pd.to_numeric(
            history_df["short_rate"],
            errors="coerce",
        )

        # Calculate stats
        stats = {
            "Mean Long Rate": history_df["long_rate"].mean(),
            "Median Long Rate": history_df["long_rate"].median(),
            "Std Dev Long Rate": history_df["long_rate"].std(),
            "Min Long Rate": history_df["long_rate"].min(),
            "Max Long Rate": history_df["long_rate"].max(),
            "Mean Short Rate": history_df["short_rate"].mean(),
            "Median Short Rate": history_df["short_rate"].median(),
            "Std Dev Short Rate": history_df["short_rate"].std(),
            "Min Short Rate": history_df["short_rate"].min(),
            "Max Short Rate": history_df["short_rate"].max(),
        }

        # Calculate daily changes and their averages
        if len(history_df) > 1:
            history_df["long_rate_diff"] = history_df["long_rate"].diff().abs()
            history_df["short_rate_diff"] = history_df["short_rate"].diff().abs()
            stats["Avg Daily Change Long Rate"] = history_df["long_rate_diff"].mean()
            stats["Avg Daily Change Short Rate"] = history_df["short_rate_diff"].mean()
        else:
            stats["Avg Daily Change Long Rate"] = 0.0
            stats["Avg Daily Change Short Rate"] = 0.0

        self.view.show_history_window(instrument_name, history_df, stats)
        self.view.set_status("History window displayed.")

    # --- Core Logic (UI-Thread Safe) ---

    def process_ui_updates(self):
        """Check the queue for UI updates and apply them. Runs on the main thread."""
        try:
            while not self.ui_update_queue.empty():
                message = self.ui_update_queue.get_nowait()
                msg_type = message.get("type")
                payload = message.get("payload")

                if msg_type == "status":
                    self.view.set_status(
                        payload.get("text"),
                        payload.get("is_error", False),
                    )
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
        """Filter the current data and update the view's table."""
        if not self.raw_data or "financingRates" not in self.raw_data:
            self.view.update_table([])
            print("No raw data or financingRates found.")  # Debug print
            return

        filtered_data = []
        print(
            f"Raw data financingRates count: {len(self.raw_data.get('financingRates', []))}"
        )  # Debug print
        for rate in self.raw_data.get("financingRates", []):
            instrument = rate.get("instrument", "")
            category = self.model.categorize_instrument(instrument)
            if self.selected_category != "All" and category != self.selected_category:
                continue
            if self.filter_text and self.filter_text not in instrument.lower():
                continue
            long_rate = float(rate.get("longRate", 0.0)) * 100
            short_rate = float(rate.get("shortRate", 0.0)) * 100

            # Infer currency from instrument name
            if "/" in instrument:
                currency = instrument.split("/")[1]
            elif "_" in instrument and instrument.endswith("USD"):
                currency = "USD"
            elif "_" in instrument and instrument.endswith("EUR"):
                currency = "EUR"
            elif "_" in instrument and instrument.endswith("GBP"):
                currency = "GBP"
            elif "_" in instrument and instrument.endswith("JPY"):
                currency = "JPY"
            elif "_" in instrument and instrument.endswith("AUD"):
                currency = "AUD"
            elif "_" in instrument and instrument.endswith("CAD"):
                currency = "CAD"
            elif "_" in instrument and instrument.endswith("CHF"):
                currency = "CHF"
            elif "_" in instrument and instrument.endswith("NZD"):
                currency = "NZD"
            elif "_" in instrument and instrument.endswith("SGD"):
                currency = "SGD"
            elif "_" in instrument and instrument.endswith("HKD"):
                currency = "HKD"
            elif "_" in instrument and instrument.endswith("NOK"):
                currency = "NOK"
            elif "_" in instrument and instrument.endswith("SEK"):
                currency = "SEK"
            elif "_" in instrument and instrument.endswith("DKK"):
                currency = "DKK"
            elif "_" in instrument and instrument.endswith("MXN"):
                currency = "MXN"
            elif "_" in instrument and instrument.endswith("ZAR"):
                currency = "ZAR"
            elif "_" in instrument and instrument.endswith("TRY"):
                currency = "TRY"
            elif "_" in instrument and instrument.endswith("CNH"):
                currency = "CNH"
            elif "_" in instrument and instrument.endswith("PLN"):
                currency = "PLN"
            elif "_" in instrument and instrument.endswith("CZK"):
                currency = "CZK"
            elif "_" in instrument and instrument.endswith("HUF"):
                currency = "HUF"
            else:
                currency = rate.get("currency", "")  # Fallback to API provided currency

            row_data = [
                instrument,
                category,  # Use the calculated category
                currency,
                rate.get("days", ""),
                f"{long_rate:.2f}%",
                f"{short_rate:.2f}%",
                rate.get("longCharge", ""),
                rate.get("shortCharge", ""),
                rate.get("units", ""),
            ]
            filtered_data.append(row_data)

        print(f"Filtered data count: {len(filtered_data)}")  # Debug print
        # print(f"Filtered data: {filtered_data}") # Uncomment for detailed debug
        self.view.update_table(filtered_data)
        self.view.set_status(
            f"Display updated. Showing {len(filtered_data)} instruments."
        )

    # --- Background Jobs (Worker Threads) ---

    def _initial_load_job(self):
        """Load initial data from DB or API."""
        self.ui_update_queue.put(
            {
                "type": "status",
                "payload": {"text": "Loading latest data from database..."},
            }
        )
        date, data = self.model.get_latest_rates()
        if data:
            self.ui_update_queue.put({"type": "initial_data", "payload": (date, data)})
            self.ui_update_queue.put(
                {
                    "type": "status",
                    "payload": {"text": "Data loaded successfully."},
                }
            )
        else:
            self._fetch_job(source="initial", is_initial=True)

    def _fetch_job(self, source: str = "manual", is_initial: bool = False):
        """Fetch new data from the API."""
        if is_initial:
            self.ui_update_queue.put(
                {
                    "type": "status",
                    "payload": {"text": "No local data. Fetching from API..."},
                }
            )

        new_data = None
        if source == "manual":
            new_data = self.model.fetch_and_save_rates(save_to_db=False)
            if new_data:
                self.ui_update_queue.put(
                    {
                        "type": "status",
                        "payload": {
                            "text": "Manual update successful (not saved to DB).",
                            "is_error": False,
                        },
                    }
                )
            else:
                self.ui_update_queue.put(
                    {
                        "type": "status",
                        "payload": {
                            "text": "Manual update failed. Check logs.",
                            "is_error": True,
                        },
                    }
                )
        elif source == "scheduled" or source == "initial":
            new_data = self.model.fetch_and_save_rates(save_to_db=True)
            if new_data:
                self.ui_update_queue.put(
                    {
                        "type": "status",
                        "payload": {
                            "text": "API fetch successful and saved to DB.",
                            "is_error": False,
                        },
                    }
                )
            else:
                self.ui_update_queue.put(
                    {
                        "type": "status",
                        "payload": {
                            "text": "API fetch failed. Check logs.",
                            "is_error": True,
                        },
                    }
                )

        if new_data:
            self.ui_update_queue.put({"type": "data", "payload": new_data})

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
        """Perform the scheduled update job."""
        self.ui_update_queue.put(
            {
                "type": "status",
                "payload": {"text": "Performing scheduled update..."},
            }
        )
        self._fetch_job(source="scheduled")
