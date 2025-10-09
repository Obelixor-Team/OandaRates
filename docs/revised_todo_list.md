#### **1. Testing**
- [x] **Add Unit Tests for Core Logic** (High Priority, High Effort)
  - Write tests for `Model.categorize_instrument`, `Model.get_instrument_history`, `Presenter._update_display`, and `View.update_table` using `pytest` or `unittest`.
  - Use `unittest.mock` to mock API and database interactions.
  - Example: Test `categorize_instrument` with inputs like `"EUR_USD"`, `"XAU_USD"`, and `"SPX500_USD"`.

- [ ] **Test UI Components with `pytest-qt`** (Medium Priority, High Effort)
  - Write tests for `View` methods (e.g., `update_table`, `show_history_window`) to verify UI updates and interactions.
  - Benefit: Validates UI behavior and improves code confidence.

#### **2. Security**
- [x] **Secure API Headers in `config.py`** (High Priority, Medium Effort) - **INVALID**
  - *This task was marked as invalid because the application does not use any sensitive API keys. The headers only contain non-sensitive information like User-Agent and Accept.*

#### **3. Performance Optimization**
- [x] **Optimize `get_instrument_history` in `model.py`** (Medium Priority, High Effort)
  - Create a separate table for instrument-specific data (e.g., `InstrumentRate` with columns `date`, `instrument`, `long_rate`, `short_rate`) to avoid JSON parsing.
  - Alternatively, cache results for frequently accessed instruments using an in-memory cache (e.g., `functools.lru_cache`).
  - Benefit: Reduces query time for large datasets.

#### **4. UI Enhancements**
- [x] **Complete Accessibility Support in `view.py`** (Low Priority, High Effort)
  - Added accessible names and descriptions to the main UI components for better screen reader support.
  - Basic keyboard navigation for the table is provided by default `QTableWidget` behavior.
  - Further enhancements for dynamic content could be explored if specific needs arise.

- [x] **Add Cancel Button for Manual Updates in `view.py`** (Low Priority, Medium Effort)
  - Add a “Cancel” button to interrupt long-running API fetches in `Presenter.on_manual_update`.
  - Use a flag in `Presenter` to signal cancellation to the `ThreadPoolExecutor`.
  - Benefit: Enhances user control during slow operations.

#### **5. Documentation**
- [x] **Enhance Docstrings with Examples** (Medium Priority, Medium Effort)
  - Add usage examples to docstrings for `Model.get_instrument_history`, `View.update_table`, and other complex methods.
  - Benefit: Improves code understanding for developers.

- [x] **Update `README.md`** (Low Priority, Medium Effort)
  - Add setup instructions (e.g., installing dependencies, creating `config.yaml`), configuration details, and usage examples to `README.md`.
  - Benefit: Simplifies onboarding for new developers or users.

#### **6. Logging Enhancements**
- [x] **Configure Log Levels via `config.yaml`** (Low Priority, Low Effort)
  - Allow log level (e.g., `DEBUG`, `INFO`) to be set in `config.yaml` and update `setup_logging` to respect it.
  - Example: `config["logging"]["level"] = "DEBUG"`.
  - Benefit: Provides flexibility for debugging vs. production logging.

- [x] **Log JSON Parsing Errors in `model.py`** (Low Priority, Low Effort)
  - Add logging for potential JSON parsing failures in `get_instrument_history`.
  - Example: `logger.error(f"Failed to parse JSON for rate on {rate_entry.date}: {e}")`.
  - Benefit: Improves traceability of data issues.

#### **7. Additional Considerations**
- [x] **Validate Configuration Types in `config.py`** (Low Priority, Medium Effort)
  - Add type validation for critical config fields (e.g., ensure `api.timeout` is an integer, `theme` values are strings).
  - Benefit: Prevents runtime errors due to misconfigured values.
- [x] **Add Plot Customization in `HistoryDialog`** (Low Priority, Medium Effort)
  - Allow users to configure plot colors or styles via `config.yaml` or a UI option.
  - Benefit: Enhances user experience for visualizing historical rates.
