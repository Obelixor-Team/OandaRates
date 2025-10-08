# Code Review Action Plan

Based on the provided code review, here's an action plan to address the identified issues and implement suggested improvements:

## Critical Issues to Address Immediately:

1.  **Type Ignoring in `model.py`**:
    *   **Issue**: The `# type: ignore` comments in `fetch_and_save_rates` are present due to `mypy`'s limitations in understanding SQLAlchemy ORM types without additional configuration (e.g., `sqlalchemy-stubs`).
    *   **Action**: While a proper long-term solution would involve setting up `sqlalchemy-stubs` and configuring `mypy` accordingly, for now, these comments are necessary to avoid `mypy` errors. This item will remain here as a reminder for future improvement, but no immediate code change will be made to remove the `type: ignore` comments themselves.

2.  **Hardcoded Constants (Completed)**:
    *   **Action**: Moved `API_URL`, `HEADERS`, and `DB_FILE` from `model.py` to `config.yaml` and updated `model.py` to read from it.

## Suggested Improvements and Next Steps:

1.  **Configuration File (Completed)**:
    *   **Action**: Implemented `config.yaml` for `API_URL`, `HEADERS`, `DB_FILE`, and instrument categorization lists.

2.  **Robust Scheduling (Completed)**:
    *   **Action**: Replaced the `schedule` library with `APScheduler` for more reliable and feature-rich scheduling, ensuring timezone awareness (5:30 PM ET).

3.  **Enhanced Type Hints (Completed)**:
    *   **Action**: Consistently added type hints across relevant methods and classes, including `Presenter.__init__`, and resolved circular dependencies for proper type enforcement.

4.  **Unit and Integration Tests (Partially Completed)**:
    *   **Action**: Developed comprehensive unit tests for `Model.categorize_instrument`, `Model.fetch_and_save_rates`, `Model.get_latest_rates`, `Model.get_instrument_history`, and `Presenter._update_display`. Implemented integration test for manual update flow. Further integration tests are pending.

5.  **Consolidate Duplicated Logic (Completed)**:
    *   **Action**: Moved the `_infer_currency` method from `presenter.py` to the `Model` class to centralize currency-related logic.

6.  **Centralized Theme**:
    *   **Action**: Define a theme dictionary in a separate file (e.g., `theme.py`) for consistent styling across the GUI and plots.

7.  **Enhanced Logging**:
    *   **Action**: Implement a rotating file handler for `oanda_instrument_log.txt` to manage log file size.

8.  **Input Validation**:
    *   **Action**: Add robust input validation in methods like `on_filter_text_changed` and `on_instrument_double_clicked` to prevent issues with malformed data.

9.  **Plot Enhancements**:
    *   **Action**: Add grid lines and better date formatting to the history plot in `MplCanvas`.

This plan prioritizes critical issues for immediate attention and outlines further improvements for a more maintainable, scalable, and production-ready application.