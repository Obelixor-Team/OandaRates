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

3.  **Enhanced Type Hints**:
    *   **Action**: Consistently add type hints across all methods and classes, especially in `Presenter.__init__`, and leverage `mypy` to enforce them.

4.  **Unit and Integration Tests**:
    *   **Action**: Develop comprehensive unit tests for `Model.categorize_instrument`, `Model.fetch_and_save_rates`, and `Presenter._update_display`. Also, create integration tests for the full MVP flow.

5.  **Consolidate Duplicated Logic**:
    *   **Action**: Move the `_infer_currency` method from `presenter.py` to the `Model` class to centralize currency-related logic.

6.  **Centralized Theme**:
    *   **Action**: Define a theme dictionary in a separate file (e.g., `theme.py`) for consistent styling across the GUI and plots.

7.  **Enhanced Logging**:
    *   **Action**: Implement a rotating file handler for `oanda_instrument_log.txt` to manage log file size.

8.  **Input Validation**:
    *   **Action**: Add robust input validation in methods like `on_filter_text_changed` and `on_instrument_double_clicked` to prevent issues with malformed data.

9.  **Plot Enhancements**:
    *   **Action**: Add grid lines and better date formatting to the history plot in `MplCanvas`.

This plan prioritizes critical issues for immediate attention and outlines further improvements for a more maintainable, scalable, and production-ready application.