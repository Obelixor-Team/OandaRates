# OANDA Financing Terminal

The OANDA Financing Terminal is a Python-based desktop application for retrieving, displaying, and analyzing financing rates from the OANDA API. Built with PyQt6, SQLAlchemy, and pandas, it provides a user-friendly interface to view real-time and historical rates, filter by instrument or category, and visualize trends.

## Features
- Fetches financing rates from the OANDA API and stores them in a SQLite database.
- Displays rates in a sortable table with filtering by instrument or category.
- Shows historical rate trends in a dialog with statistical summaries.
- Supports cancellation of long-running API requests.
- Configurable themes, logging, and API settings via `config.yaml`.

## Prerequisites
- Python 3.8 or higher
- An OANDA API key (obtain from [OANDA Labs](https://labs.oanda.com/))
- A compatible operating system (Windows, macOS, Linux)

## Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-repo/oanda-financing-terminal.git
   cd oanda-financing-terminal
   ```

2. **Install Dependencies**:
   Create a virtual environment and install required packages:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. **Set Environment Variables**:
   Set the `OANDA_API_KEY` environment variable for secure API access:
   - On Windows:
     ```bash
     set OANDA_API_KEY=your_api_key_here
     ```
   - On macOS/Linux:
     ```bash
     export OANDA_API_KEY=your_api_key_here
     ```

## Configuration
The application uses a `config.yaml` file for customization. If not present, it defaults to built-in settings. Create a `config.yaml` in the project root with the following structure:

```yaml
api:
  url: "https://labs-api.oanda.com"
  timeout: 10
database:
  file: "oanda_rates.db"
logging:
  level: "INFO"
  file_path: "oanda_terminal.log"
theme:
  background: "#0a0a12"
  text: "#e0e0e0"
  positive: "#00ff9d"
  negative: "#ff5555"
  plot_background: "#121220"
  table_background: "#1a1a2e"
  table_gridline: "#2a2a3e"
  header_background: "#121220"
  header_text: "#00ff9d"
  selected_background: "#0095ff"
  selected_text: "#ffffff"
  button_background: "#0095ff"
  button_hover: "#0077cc"
  button_text: "#ffffff"
  input_background: "#1a1a2e"
  input_border: "#2a2a3e"
  status_text: "#a0a0b0"
  plot_long_rate_color: "#00ff9d"
  plot_short_rate_color: "#ff5555"
ui:
  timer_interval: 16
categories:
  currencies: ["usd", "eur", "jpy", "gbp", "aud", "cad", "chf", "nzd", "sgd", "hkd", "nok", "sek", "dkk", "mxn", "zar", "try", "cnh", "pln", "czk", "huf"]
  metals: ["xau", "xag", "xpd", "xpt"]
  commodities: ["wtico_usd", "brent_crude_oil", "nat_gas_usd", "corn_usd", "wheat_usd", "soybn_usd", "sugar_usd", "cocoa_usd", "coffee_usd"]
  indices: ["us30_usd", "us_30_usd", "spx500_usd", "us_spx_500", "nas100_usd", "us_nas_100", "us2000_usd", "us_2000", "uk100_gbp", "uk_100", "de40_eur", "de_30_eur", "de_40_eur", "eu50_eur", "eu_50_eur", "fr40_eur", "fr_40", "jp225_usd", "jp_225", "au200_aud", "au_200", "hk33_hkd", "hk_hsi", "cn50_usd", "cn_50", "sg30_sgd", "sg_30"]
  bonds: ["de_10yr_bund", "us_2yr_tnote", "us_5yr_tnote", "us_10yr_tnote", "usb02y_usd", "usb05y_usd", "de10yb_eur"]
  currency_suffixes:
    USD: "USD"
    EUR: "EUR"
    GBP: "GBP"
    JPY: "JPY"
    AUD: "AUD"
    CAD: "CAD"
    CHF: "CHF"
    NZD: "NZD"
    SGD: "SGD"
    HKD: "HKD"
    NOK: "NOK"
    SEK: "SEK"
    DKK: "DKK"
    MXN: "MXN"
    ZAR: "ZAR"
    TRY: "TRY"
    CNH: "CNH"
    PLN: "PLN"
    CZK: "CZK"
    HUF: "HUF"
```

- **Key Fields**:
  - `api.url`: OANDA API endpoint for financing rates.
  - `logging.level`: Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
  - `theme.*`: UI colors for customization.
  - `categories.*`: Instrument categorization rules.

## Usage
1. **Run the Application**:
   ```bash
   python src/main.py
   ```
2. **Interact with the UI**:
   - **Filter**: Enter an instrument name (e.g., "EUR_USD") in the filter input.
   - **Category**: Select a category (e.g., "Forex", "Metals") from the dropdown.
   - **Manual Update**: Click "Manual Update" to fetch new rates from the API.
   - **Cancel Update**: Click "Cancel Update" to stop an ongoing fetch.
   - **Clear Filter**: Reset filters and category selection.
   - **View History**: Double-click a table row to see historical rates and statistics in a dialog.
3. **View Logs**:
   Logs are written to the file specified in `logging.file_path` (default: `oanda_terminal.log`).

## Development
- **Run Tests**:
  Install development dependencies:
  ```bash
  pip install -r requirements-dev.txt
  ```
  Run tests with `pytest`:
  ```bash
  pytest
  ```
- **Code Style**:
  Use `ruff` for linting and `black` for formatting:
  ```bash
  ruff check .
  black .
  ```
- **Type Checking**:
  Run `mypy` for static type checking:
  ```bash
  mypy src
  ```

## Contributing
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

## License
This project is licensed under the MIT License. See `LICENSE` for details.