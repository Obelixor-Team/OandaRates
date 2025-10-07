# OANDA Financing Rates Terminal

A desktop application built with Python and PyQt6 to fetch, store, and display OANDA financing rates. This tool provides a clear, interactive interface to monitor financing rates, filter instruments by category or text, and view historical rate data with statistical analysis.

## Features

*   **Real-time Data Fetching:** Fetches the latest financing rates from the OANDA API.
*   **Local Data Storage:** Stores historical rate data in a SQLite database for persistent access.
*   **Interactive GUI:** A modern, terminal-themed graphical user interface built with PyQt6.
*   **Filtering & Categorization:** Filter instruments by text search or pre-defined categories (Forex, Indices, Commodities, Metals, CFDs, Bonds, Other).
*   **Automated Updates:** Automatically updates data daily at 10:30 PM GMT.
*   **Historical Data Visualization:** Double-click an instrument to view a line plot of its historical rates and key statistics.
*   **Percentage Display:** Long and Short rates are displayed as percentages with two decimal places.

## Tech Stack

*   **Python 3.11+**
*   **PyQt6:** For the graphical user interface.
*   **SQLAlchemy:** For Object Relational Mapping (ORM) with the SQLite database.
*   **Requests:** For making HTTP requests to the OANDA API.
*   **Pandas:** For data manipulation and statistical analysis.
*   **Matplotlib:** For plotting historical data.
*   **Schedule:** For scheduling automated data updates.
*   **pytz:** For accurate timezone handling in scheduling.

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

Install the project dependencies using `pip` and the `pyproject.toml` file:

```bash
pip install .
```

### 5. Run the Application

```bash
python src/main.py
```

The application window will appear, displaying the OANDA financing rates. Data will automatically update daily at 10:30 PM GMT.

## Screenshot

*(Placeholder for a screenshot of the application in action)*
