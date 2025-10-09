### **Detailed To-Do List for OANDA Financing Terminal**

Based on a thorough review of the provided codebase and prior recommendations, the following to-do list outlines the remaining items needed to complete the application's development. This list focuses on unresolved high-impact areas such as testing, along with lower-priority enhancements in UI accessibility, theme application, and documentation. Tasks are categorized for clarity, prioritized by impact (High, Medium, Low), and include detailed descriptions, rationale, estimated effort levels (Low: <1 hour, Medium: 1-4 hours, High: >4 hours), and suggested steps for implementation. Priorities consider factors like reliability, user experience, and maintainability.

#### **1. Testing**
Testing remains a critical gap, as no test files or suites are present in the codebase. Implementing these will ensure the application's logic, error handling, and UI interactions function correctly, preventing regressions during future updates.

- [ ] **Add Unit Tests for Core Logic** (High Priority, High Effort)
  - **Description**: Develop a comprehensive suite of unit tests covering key methods in `model.py` (e.g., `categorize_instrument`, `fetch_and_save_rates`, `get_instrument_history`), `presenter.py` (e.g., `on_manual_update`, `on_cancel_update`, `process_ui_updates`), and `config.py` (e.g., `validate_config`, `_validate_config_types`). Use `pytest` with `unittest.mock` to isolate dependencies like API calls, database sessions, and threading.
  - **Rationale**: Unit tests validate business logic and edge cases (e.g., API failures, invalid inputs, database errors), improving reliability in a data-driven application.
  - **Suggested Steps**:
    1. Create a `tests/` directory and install `pytest` via `pip install pytest`.
    2. Write fixtures for mocking `config`, database sessions (use in-memory SQLite), and API responses.
    3. Test success/failure scenarios, e.g., `fetch_and_save_rates` with mocked HTTP responses and database commits.
    4. Aim for 80%+ code coverage using `pytest-cov`.
    5. Run tests with `pytest tests/` and integrate into CI/CD if applicable.
  - **Dependencies**: Requires access to the full codebase for mocking.

- [ ] **Test UI Components with `pytest-qt`** (Medium Priority, High Effort)
  - **Description**: Create integration tests for UI elements in `view.py` (e.g., `update_table`, `show_history_window`, `set_update_buttons_enabled`, `closeEvent`) and their interactions with `presenter.py`. Use `pytest-qt` to simulate Qt events like button clicks, text changes, and double-clicks on the table.
  - **Rationale**: UI tests ensure interactive features (e.g., filtering, updating, canceling) behave as expected, catching issues in event handling and state management.
  - **Suggested Steps**:
    1. Install `pytest-qt` via `pip install pytest-qt`.
    2. Mock `QApplication` and other Qt components in fixtures.
    3. Test scenarios like table sorting, progress bar visibility during updates, and history dialog rendering with sample data.
    4. Verify accessibility properties (e.g., `accessibleName`) are set correctly.
    5. Run tests and document any Qt-specific setup in the `README.md`.
  - **Dependencies**: Builds on unit tests; requires PyQt6 environment.

#### **2. UI Enhancements**
These tasks focus on improving usability and consistency, particularly for accessibility and theme integration. While not critical for core functionality, they enhance the application's professionalism and inclusivity.

- [ ] **Complete Accessibility Support in `view.py`** (Low Priority, High Effort)
  - **Description**: Extend accessibility features to include full keyboard navigation (e.g., arrow keys for table row selection, Tab/Shift+Tab for focus order) and ensure dynamic elements like the history dialog and progress bar are accessible. Use PyQt6's `setFocusPolicy`, `keyPressEvent`, and additional properties (e.g., `QAccessibleInterface` for screen reader descriptions).
  - **Rationale**: Full accessibility ensures compliance with standards (e.g., WCAG) and usability for users with disabilities, making the application more inclusive.
  - **Suggested Steps**:
    1. Override `keyPressEvent` in `QTableWidget` for arrow key navigation.
    2. Set focus order explicitly with `setTabOrder` for controls like `filter_input`, `category_combo`, buttons.
    3. Add descriptive text for screen readers on dynamic content (e.g., table rows, status bar updates).
    4. Test with tools like NVDA (screen reader) or Qt's accessibility inspector.
    5. Document accessibility features in the `README.md`.
  - **Dependencies**: None; can be done independently.

- [ ] **Apply Plot Colors from Theme in `HistoryDialog`** (Low Priority, Low Effort)
  - **Description**: Update the Matplotlib plot in `HistoryDialog.plot_history` to use configurable colors from `THEME["plot_long_rate_color"]` and `THEME["plot_short_rate_color"]` for long/short rate lines.
  - **Rationale**: This ensures consistent theming across the UI, allowing users to customize plot visuals via `config.yaml` without code changes.
  - **Suggested Steps**:
    1. Import `THEME` from `theme.py` (or access via `config["theme"]`).
    2. In `plot_history`, set line colors: `self.axes.plot(history_df['date'], history_df['long_rate'], label='Long Rate', color=THEME['plot_long_rate_color'])`.
    3. Similarly for short rate.
    4. Test by updating `config.yaml` and verifying color changes.
    5. Add a note in the `README.md` under "Configuration" about plot customization.
  - **Dependencies**: Assumes `theme.py` or config handles color validation.

#### **3. Documentation**
Documentation is partially addressed with existing docstrings (e.g., in `model.py` and `view.py`), but further enhancements will improve developer onboarding and code maintainability.

- [ ] **Enhance Docstrings with Examples** (Medium Priority, Medium Effort)
  - **Description**: Add usage examples to remaining complex methods, such as `Presenter.process_ui_updates`, `Presenter.on_cancel_update`, `View.set_update_buttons_enabled`, and `View.show_history_window`. Use the format seen in `model.py` (e.g., doctest-style with expected outputs).
  - **Rationale**: Comprehensive docstrings aid in understanding and testing, especially for intertwined MVP components.
  - **Suggested Steps**:
    1. Review all methods in `presenter.py` and `view.py` for missing examples.
    2. Add examples using mocks (e.g., `unittest.mock`) for simulated scenarios.
    3. Ensure examples cover edge cases (e.g., empty data, errors).
    4. Run `pydocstyle` or similar to validate docstring format.
    5. Update any existing examples if outdated.
  - **Dependencies**: Builds on current docstrings.

- [ ] **Update `README.md`** (Low Priority, Medium Effort)
  - **Description**: Expand the `README.md` (listed in `SOURCES.txt`) with sections on troubleshooting (e.g., API key issues, database errors), screenshots of the UI, and advanced usage (e.g., customizing themes, running tests). Include a "Known Issues" section if applicable.
  - **Rationale**: A complete `README.md` facilitates user adoption and contributor involvement, especially for open-source potential.
  - **Suggested Steps**:
    1. Add troubleshooting tips (e.g., "If API fetches fail, verify `OANDA_API_KEY` is set.").
    2. Include UI screenshots (e.g., main window, history dialog) using Markdown embeds.
    3. Document development setup, including running tests and linters from `requires.txt [dev]`.
    4. Version the `README.md` and link to `LICENSE`.
    5. Commit and push updates to the repository.
  - **Dependencies**: None; can reference testing setup.

---

### **Prioritization and Timeline Guidance**
- **High Priority Tasks**: Complete testing first, as it directly impacts reliability. Allocate 1-2 days for unit tests before moving to UI tests.
- **Medium Priority Tasks**: Address docstrings next to support testing and maintenance.
- **Low Priority Tasks**: Tackle UI enhancements last, as they are polish items.
- **Overall Timeline**: Assuming a single developer, aim to complete all tasks in 1-2 weeks, starting with testing. Re-evaluate after implementation using tools like `coverage.py` for test completeness.
- **Resources Needed**: `pytest`, `pytest-qt`, and mocking libraries (already in dev requirements). For accessibility testing, use free tools like WAVE or screen readers.

This list represents the final steps to achieve a production-ready application. If additional details or adjustments are needed (e.g., based on specific priorities), please provide further guidance.