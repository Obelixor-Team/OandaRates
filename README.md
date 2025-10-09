# OANDA Financing Rates Terminal

A desktop application built with Python and PyQt6 to fetch, store, and display OANDA financing rates. This tool provides a clear, interactive interface to monitor financing rates, filter instruments by category or text, and view historical rate data with statistical analysis.

## Features

*   **Real-time Data Fetching:** Fetches the latest financing rates from the OANDA API.
*   **Local Data Storage:** Stores historical rate data in a SQLite database for persistent access.
*   **Interactive GUI:** A modern, terminal-themed graphical user interface built with PyQt6.
*   **Filtering & Categorization:** Filter instruments by text search or pre-defined categories (Forex, Indices, Commodities, Metals, CFDs, Bonds, Other).
*   **Automated Updates:** Automatically updates data daily at 10:30 PM GMT (market close) and saves to the database.
*   **Manual Updates:** Users can manually fetch and display the latest rates, but these are *not* saved to the database to preserve the integrity of settled rates.
*   **Sortable Columns:** Click on column headers to sort data in ascending or descending order.
*   **Color-coded Rates & Charges:** Long/Short Rate and Charge columns are color-coded (green for positive, red for negative) for quick visual analysis.
*   **Enhanced Historical Statistics:** Double-click an instrument to view a line plot of its historical rates, along with comprehensive statistics including Mean, Median, Standard Deviation, Min/Max, and Average Daily Change for both long and short rates.
*   **Window Persistence:** The application remembers and restores the main window's size and position upon reopening.

## Tech Stack

*   **Python 3.11+**
*   **PyQt6:** For the graphical user interface.
*   **SQLAlchemy:** For Object Relational Mapping (ORM) with the SQLite database.
*   **Requests:** For making HTTP requests to the OANDA API.
*   **Pandas:** For data manipulation and statistical analysis.
*   **Matplotlib:** For plotting historical data.
*   **Schedule:** For scheduling automated data updates.
*   **Bandit:** Security linter.
*   **Radon:** Code complexity analysis.

## Setup and Running

Follow these steps to set up and run the application:

### 1. Clone the Repository

```bash
git clone <repository_url>
cd OandaRates
```

### 2. Set up Python Environment (using pyenv)

Ensure you have `pyenv` installed and set your local Python version to 3.11.13 (or a compatible version).

```bash
pyenv install 3.11.13 # If you don't have it already
pyenv local 3.11.13
```

### 3. Create and Activate Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies

Install the project's core dependencies:

```bash
pip install .
```

For development, install optional dependencies including code quality tools:

```bash
pip install .[dev]
```

### 5. Run the Application

```bash
make run
```

The application window will appear, displaying the OANDA financing rates. Data will automatically update daily at 10:30 PM GMT.

## Configuration

The application's behavior can be customized through the `config.yaml` file.

*   **`api`**: Configuration for the OANDA API.
    *   `url`: The API endpoint for fetching financing rates.
    *   `headers`: HTTP headers to be sent with the API request. The `Authorization` header is read from the `OANDA_API_KEY` environment variable for security. The default `User-Agent` mimics a browser.
    *   `timeout`: The timeout in seconds for the API request.
*   **`database`**: Configuration for the local database.
    *   `file`: The name of the SQLite database file.
*   **`categories`**: Lists of keywords used to categorize instruments.
    *   `currencies`, `metals`, `commodities`, `indices`, `bonds`: These lists contain keywords that are used to identify the category of an instrument based on its name.
    *   `currency_suffixes`: A mapping of instrument name suffixes to their corresponding currency.
*   `ui`: Configuration for the user interface.
    *   `timer_interval`: The interval in milliseconds for the UI update timer.

*   **`logging`**: Configuration for application logging.
    *   `level`: The minimum logging level (e.g., `INFO`, `DEBUG`, `WARNING`, `ERROR`).
    *   `file_path`: The path to the log file. Defaults to `oanda_terminal.log` in the project root.

*   **`theme`**: Customization options for the application\'s visual theme.
    *   Various keys like `background`, `text`, `positive`, `negative`, `etc.`: These define the colors for different UI elements. You can adjust these hexadecimal color codes to match your preferences.

    Example `config.yaml` snippet for theme and logging:
    ```yaml
    logging:
      level: DEBUG
      file_path: /var/log/oanda_app.log
    theme:
      background: "#1e1e1e"
      text: "#d4d4d4"
      positive: "#60a060"
      negative: "#e06060"
    ```

## Usage

*   **Filtering:**
    *   **By Text:** Type in the "Filter instruments..." input box to filter the table by instrument name.
    *   **By Category:** Select a category from the dropdown menu to show only instruments from that category.
*   **Clear Filter:** Click the "Clear Filter" button to reset both the text and category filters.
*   **Manual Update:** Click the "Manual Update" button to fetch the latest rates from the API. Note that this will not save the data to the database.
*   **View History:** Double-click on any instrument in the table to open a new window showing a plot of its historical rates and related statistics.

## Code Quality

This project uses several tools to maintain code quality. A `Makefile` is provided to automate running these checks.

### Available Commands:

*   **`make all`**: Runs all code quality checks and tests.
*   **`make check`**: Runs all code quality checks.
*   **`make format`**: Runs `black` to format the code.
*   **`make lint`**: Runs `ruff` to lint the code.
*   **`make typecheck`**: Runs `mypy` to type check the code.
*   **`make security`**: Runs `bandit` to check for security issues.
*   **`make complexity`**: Runs `radon` to check code complexity.
*   **`make test`**: Runs `pytest` to execute tests.
*   **`make clean`**: Cleans up generated files (e.g., `__pycache__`, `.mypy_cache`, build artifacts).
*   **`make run`**: Runs the application.
*   **`make help`**: Displays this help message.