# LSKP - Changelog

All notable changes to this project will be documented in this file.

---

## [2026.02.20] - Latest Build

- Current stable version
- Full automation pipeline: Google Doc → parse → login → fill forms
- Auto-updater checks GitHub releases on startup
- First-time setup screen for browser download
- Headless browser mode
- Calendar scanning to skip already-filled dates

## [Pre-2026.02.20] - Initial Development

- Built core Tkinter GUI with login form and log display
- Implemented Google Doc text parser (supports Indonesian & English date formats)
- Implemented Playwright browser controller with 2FA handling
- Built form filler for ASN Digital progress reports
- Added calendar scanner to detect existing entries
- Created `build.bat` for PyInstaller packaging
- Created `run.bat` for development workflow
- Added auto-update system via GitHub releases

---

## [2026.02.27] - Documentation Update

- Added `Project Documentation` folder per global project rules
- Created `IMPLEMENTATION_PLAN.md`, `TASK_LIST.md`, `CHANGELOG.md`, `ENV_SETUP.md`
- Updated `.gitignore` to exclude runtime data files
- Shelved web conversion research:
  - `WEB_CONVERSION_ANALYSIS.md` — feasibility, value prop, risks, credit system
  - `WEB_CONVERSION_PLAN.md` — phased execution checklist
  - `CODE_REUSE_MAP.md` — file-by-file reusability guide
