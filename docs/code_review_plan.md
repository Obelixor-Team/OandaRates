# Code Review Action Plan

Based on the provided code review, here's an action plan to address the identified issues and implement suggested improvements:

## Critical Issues to Address Immediately:

1.  **Empty Log File (`oanda_instrument_log.txt`)**:
    *   **Action**: Verify the log file path, permissions, and ensure logging statements are being triggered. Test logging in a controlled environment.

2.  **Type Ignoring in `model.py`**:
    *   **Action**: Investigate the root cause of `# type: ignore` comments in `fetch_and_save_rates` (e.g., missing type hints in SQLAlchemy models) and add proper type annotations.

3.  **Hardcoded Constants**:
    *   **Action**: Move `API_URL`, `HEADERS`, and `DB_FILE` from `model.py` to a configuration file (e.g., `config.yaml`) or environment variables.

## Suggested Improvements and Next Steps:

1.  **Configuration File**:
    *   **Action**: Implement a `config.yaml` file for settings like `API_URL`, `DB_FILE`, and instrument categorization lists.

2.  **Robust Scheduling**:
    *   **Action**: Replace the `schedule` library with `APScheduler` for more reliable and feature-rich scheduling.

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