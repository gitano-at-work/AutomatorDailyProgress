# LSKP (Lha Saya Kerja Pak) - Implementation Plan

## Overview

LSKP is a desktop automation tool that auto-fills daily work reports on the ASN Digital (BKN) portal. It reads structured entries from a Google Doc and submits them via browser automation.

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌────────────┐
│  Tkinter GUI │────>│  Doc Parser  │────>│ Browser Controller│────>│ Form Filler│
│  (main.py)   │     │(doc_parser.py│     │(browser_         │     │(form_      │
│              │     │)             │     │ controller.py)   │     │ filler.py) │
└──────────────┘     └──────────────┘     └──────────────────┘     └────────────┘
       │                                          │
       ▼                                          ▼
┌──────────────┐                          ┌──────────────────┐
│   Updater    │                          │ Calendar Scanner │
│ (updater.py) │                          │(calendar_        │
│              │                          │ scanner.py)      │
└──────────────┘                          └──────────────────┘
```

### Core Modules

| Module | Purpose |
|---|---|
| `main.py` | Tkinter GUI — user inputs, config management, automation orchestration |
| `doc_parser.py` | Parses Google Doc text into structured daily entries (date, time, category, description, proof link) |
| `browser_controller.py` | Playwright-based browser automation — login, navigation, 2FA handling |
| `form_filler.py` | Fills the ASN Digital progress form with parsed entries |
| `calendar_scanner.py` | Scans the calendar page to detect which dates already have entries |
| `updater.py` | Auto-update system — checks GitHub releases, downloads, and applies updates |
| `utils.py` | Shared utilities — logging, date/time normalization, date validation |

### Build & Distribution

- **`build.bat`** — Packages the app into a standalone `.exe` using PyInstaller. Auto-generates version from the current date (YYYY.MM.DD format).
- **`run.bat`** — Development launcher. Sets up venv, installs dependencies, and runs `main.py`.
- Updates are distributed via GitHub Releases. The app checks for new versions on startup.

## Dependencies

| Package | Version | Why |
|---|---|---|
| `playwright` | >=1.40.0 | Browser automation engine — controls Chromium to navigate web pages, fill forms, and handle 2FA |
| `pyinstaller` | latest | Packages the Python app + Playwright into a single `.exe` for easy distribution |
| `Pillow` | latest | Image processing — used for asset handling (logo rendering) |

## Future Considerations

- Password encryption in config (currently plain text, mitigated by `.gitignore`)
- Support for multiple users / profiles
- Scheduling / auto-run via Windows Task Scheduler
