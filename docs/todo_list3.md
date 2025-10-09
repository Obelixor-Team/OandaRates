Absolutely — here’s a detailed **to-do list and workflow plan** tailored to your codebase (`OANDA Financing Terminal`).
It covers practical next steps, refactors, testing, packaging, and example commands for each phase.

---

# 🧭 Project To-Do List & Workflow

### 🎯 Goal

Polish the existing MVP architecture, harden for production use, add automated testing, and streamline deployment.

---

## 1️⃣ **Configuration & Logging Improvements**

### ✅ Tasks

* [ ] **Add missing theme keys**
  Your config validation expects `plot_long_rate_color` and `plot_short_rate_color`, but they aren’t in `DEFAULT_CONFIG["theme"]`.

  ```python
  "plot_long_rate_color": "#00ff9d",
  "plot_short_rate_color": "#ff5555",
  ```

* [ ] **Guard against `None` YAML**
  Handle the case when `yaml.safe_load()` returns `None`.

  ```python
  data = yaml.safe_load(f) or {}
  ```

* [ ] **Move `setup_logging()` call**
  Right now it runs on import; instead, call it explicitly in `main.py`.
  Example:

  ```python
  from .config import config, setup_logging
  setup_logging()
  ```

* [ ] **Add rotating file handler**

  ```python
  from logging.handlers import RotatingFileHandler

  handler = RotatingFileHandler("oanda_terminal.log", maxBytes=1_000_000, backupCount=3)
  logging.basicConfig(handlers=[handler, logging.StreamHandler()], ...)
  ```

---

## 2️⃣ **Thread-Safety and Shutdown**

### ✅ Tasks

* [ ] **Ensure all View updates occur on the main thread**

  * Move every `view.*` call from worker threads into queued messages.
  * Example change in `Presenter._fetch_job()`:

    ```python
    self.ui_update_queue.put({
        "type": "set_buttons_enabled",
        "payload": {"enabled": True}
    })
    ```

    and handle that in `process_ui_updates()`:

    ```python
    elif msg_type == "set_buttons_enabled":
        self.view.set_update_buttons_enabled(payload["enabled"])
    ```

* [ ] **Fix shutdown exit codes**

  * Modify `main.py`:

    ```python
    try:
        ...
        sys.exit(app.exec())
    except Exception:
        logging.exception("Unhandled exception")
        sys.exit(1)
    finally:
        if presenter_instance:
            presenter_instance.shutdown()
    ```

* [ ] **Add `Model.close()` and call it from `Presenter.shutdown()`**
  Ensures database session is closed even if `__del__` isn’t triggered.

---

## 3️⃣ **Unit & Integration Testing**

### ✅ Setup

Create `tests/` directory.

Install dev tools:

```bash
pip install pytest pytest-qt pytest-mock
```

### ✅ Tasks

* [ ] **Model tests**

  * Mock requests and database session:

    ```python
    @pytest.mark.parametrize("save", [True, False])
    def test_fetch_and_save_rates(mock_requests, tmp_path, save):
        model = Model()
        data = model.fetch_and_save_rates(save_to_db=save)
        assert "financingRates" in data
    ```

* [ ] **Presenter tests**

  * Test filter and queue logic with mock view:

    ```python
    def test_on_filter_text_changed_triggers_update(mock_view, model):
        p = Presenter(model, mock_view)
        p.raw_data = {"financingRates": [{"instrument": "EUR_USD"}]}
        p.on_filter_text_changed("eur")
        mock_view.update_table.assert_called()
    ```

* [ ] **View tests (pytest-qt)**

  * Use `qtbot` fixture to test widget interaction.

    ```python
    def test_clear_inputs(qtbot):
        view = View()
        view.filter_input.setText("test")
        view.category_combo.setCurrentIndex(2)
        view.clear_inputs()
        assert view.filter_input.text() == ""
        assert view.category_combo.currentIndex() == 0
    ```

* [ ] **Integration smoke test**
  Launch the app headless (e.g., with `QT_QPA_PLATFORM=offscreen`) and ensure no exceptions.

---

## 4️⃣ **Refactor Improvements**

### ✅ Tasks

* [ ] **Encapsulate `_infer_currency()`**
  Rename it to `infer_currency()` (public) since it’s used by Presenter.

* [ ] **Batch updates in View.update_table()**
  Example:

  ```python
  self.table.setUpdatesEnabled(False)
  # ... update loop ...
  self.table.setUpdatesEnabled(True)
  ```

* [ ] **Non-blocking history window**
  Replace `dialog.exec()` with `dialog.show()` to prevent freezing UI during long runs.

* [ ] **Add context management for Model**

  ```python
  class Model:
      def __enter__(self): return self
      def __exit__(self, *args): self.session.close()
  ```

  Example:

  ```python
  with Model() as m:
      m.fetch_and_save_rates()
  ```

---

## 5️⃣ **Packaging & Environment**

### ✅ Tasks

* [ ] **Add a CLI entry point**
  In `pyproject.toml`:

  ```toml
  [project.scripts]
  oanda-terminal = "main:run_app"
  ```

* [ ] **Virtual environment reproducibility**
  Use `requirements.txt` or `poetry.lock`.
  Example:

  ```bash
  pip freeze > requirements.txt
  ```

* [ ] **PyInstaller or cx_Freeze packaging**
  Create desktop binary:

  ```bash
  pyinstaller --noconfirm --onedir --name OandaTerminal main.py
  ```

* [ ] **Environment variables**

  * Add `.env` or instruct users to export API key:

    ```bash
    export OANDA_API_KEY="your_key_here"
    ```

---

## 6️⃣ **UI / UX Polish**

### ✅ Tasks

* [ ] **Add “Auto Refresh” toggle**
  Connect it to scheduler enable/disable:

  ```python
  self.auto_refresh_checkbox.stateChanged.connect(presenter.toggle_scheduler)
  ```

* [ ] **Remember window layout**
  Already partially implemented via QSettings.
  Extend it to remember splitter positions or column widths:

  ```python
  self.settings.setValue("table_header", self.table.horizontalHeader().saveState())
  ```

* [ ] **Dark/light theme switch**
  Load theme from YAML:

  ```yaml
  theme_mode: dark
  theme_dark: {...}
  theme_light: {...}
  ```

  and toggle via menu action.

---

## 7️⃣ **Documentation & CI**

### ✅ Tasks

* [ ] **Auto-generate docs**

  ```bash
  pip install pdoc
  pdoc src -o docs/
  ```

* [ ] **Add GitHub Actions workflow**
  Example `.github/workflows/tests.yml`:

  ```yaml
  name: Tests
  on: [push, pull_request]
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with: {python-version: '3.11'}
        - run: pip install -r requirements.txt
        - run: pytest -v
  ```

---

# 🧩 Example Daily Workflow

| Step                      | Command                              | Purpose                  |
| ------------------------- | ------------------------------------ | ------------------------ |
| 1. Create feature branch  | `git checkout -b feature/threadsafe` | Work in isolation        |
| 2. Run tests continuously | `pytest -v --maxfail=1`              | Detect regressions early |
| 3. Launch app             | `python -m main`                     | Manual test UI           |
| 4. Build binary           | `pyinstaller main.py --noconfirm`    | Test packaging           |
| 5. Push and PR            | `git push origin feature/threadsafe` | Trigger CI               |

---

Would you like me to turn this into a **Markdown project checklist file** (`TODO.md`) you can drop into your repo (with checkboxes and formatted code blocks)?
