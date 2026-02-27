# LSKP - Environment & Configuration Setup

## Prerequisites

- **Python 3.8+** — [Download](https://python.org)
- **pip** — comes bundled with Python
- No additional system-level dependencies required

## Quick Start (Development)

Run `run.bat` from the project root. It will:
1. Create a virtual environment (`venv/`)
2. Install all dependencies from `requirements.txt`
3. Install Playwright Chromium browser
4. Launch the app

## Configuration File: `config.json`

> ⚠️ **This file contains sensitive credentials. It is gitignored and must NEVER be committed or shared.**

The app creates/reads `config.json` in the project root. Here are the fields:

| Field | Type | Description | Where to Get It |
|---|---|---|---|
| `last_doc_url` | string | URL of your Google Doc containing daily entries | Your Google Docs |
| `web_app_url` | string | Base URL of the ASN Digital portal | Provided by your organization |
| `calendar_url` | string | URL of the progress calendar page | Derived from `web_app_url` + `/progress/calendar` |
| `new_entry_url` | string | URL of the new progress entry form | Derived from `web_app_url` + `/progress/new` |
| `username` | string | Your ASN Digital login username (NIP) | Your HR/admin department |
| `password` | string | Your ASN Digital login password | Set by you on the ASN Digital portal |
| `max_backtrack_days` | integer | How many days back to check for unfilled entries (default: 3) | Configure as needed |
| `browser_headless` | boolean | Run browser without visible window (default: true) | Toggle in app settings |
| `keep_browser` | boolean | Keep browser open after automation completes (default: false) | Toggle in app settings |
| `completion_mode` | integer | How the app behaves after finishing (1 = close browser) | Configure in app settings |

## Building the Executable

Run `build.bat` from the project root. It will:
1. Install/update dependencies
2. Auto-generate version from current date
3. Package everything into `dist/DailyReporter.exe` using PyInstaller

## Distributing Updates

1. Build using `build.bat`
2. Create a GitHub Release with tag `vYYYY.MM.DD`
3. Upload `dist/DailyReporter.exe` as a release asset
4. Users with the app will auto-detect the update on next launch
