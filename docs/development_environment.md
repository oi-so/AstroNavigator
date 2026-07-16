# Development Environment

## Python

- Python 3.12

---

## Package Manager

- uv

### Create virtual environment

```bash
uv venv
```

### Activate

macOS / Linux

```bash
source .venv/bin/activate
```

Windows

```powershell
.venv\Scripts\activate
```

---

## Install dependencies

```bash
uv sync
```

---

## Add dependency

```bash
uv add <package>
```

Development dependency

```bash
uv add --dev <package>
```

---

## Run

```bash
uv run python -m astronavigator
```

---

## Test

```bash
uv run pytest
```

---

## Formatter / Linter

Ruff

```bash
uv run ruff check .
uv run ruff format .
```

---

## IDE

Recommended

- Visual Studio Code

---

## Project Structure

- src layout
- pyproject.toml
- uv.lock