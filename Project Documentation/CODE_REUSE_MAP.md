# LSKP Web Conversion — Code Reuse Map

> **Status:** 📋 Reference — Use this when starting the web conversion  
> **Created:** 2026-02-27  
> **Purpose:** File-by-file guide on what carries over, what needs changes, and what gets replaced

---

## Fully Reusable (Copy As-Is)

### `src/doc_parser.py` (154 lines)

- **What it does:** Parses Google Doc text into structured entries (date, time, category, description, proof link)
- **Dependencies:** Only `re`, `typing`, and `utils.normalize_time`
- **Web usage:** Call from the API layer when user submits a Google Doc URL
- **Changes needed:** None — pure logic, no UI dependency

### `src/utils.py` — `normalize_time()` and `normalize_date()` (80 lines)

- **What they do:** Convert loose date/time formats to standard formats
- **Dependencies:** `re`, `datetime`
- **Web usage:** Used by doc_parser and form_filler
- **Changes needed:** None

### `src/utils.py` — `is_date_fillable()` (23 lines)

- **What it does:** Checks if a date is a weekday within the backtrack window
- **Web usage:** Used to filter parsed entries before submission
- **Changes needed:** None

---

## Mostly Reusable (Minor Tweaks)

### `src/calendar_scanner.py` (158 lines)

- **What it does:** Scans the BKN calendar to detect existing entries (avoids duplicates)
- **Dependencies:** Playwright `Page` object, `Logger`
- **Web usage:** Same role — called by worker before filling forms
- **Changes needed:**
  - Replace `self.logger` calls with a server-side logger (Python `logging` module or custom)
  - The `Logger` class in utils.py writes to a Tkinter widget — need a new logger that writes to a log file or sends to the API

### `src/form_filler.py` (196 lines)

- **What it does:** Fills the BKN progress form with parsed entry data
- **Dependencies:** Playwright `Page` object, `Logger`
- **Web usage:** Core of the automation worker — called for each entry
- **Changes needed:**
  - Same logger swap as calendar_scanner
  - Add credit deduction callback: after each successful `submit_form()`, trigger credit deduction

### `src/browser_controller.py` (675 lines)

- **What it does:** Manages Playwright browser lifecycle, login flow, 2FA handling, page navigation
- **Dependencies:** Playwright, `time`, `os`, `sys`
- **Web usage:** Core of the automation worker
- **Changes needed:**
  - **Remove:** `is_browser_installed()`, `install_browser()` — server has Playwright pre-installed
  - **Remove:** Local browser path detection logic (lines referencing `sys._MEIPASS`, etc.)
  - **Modify:** `handler_2fa()` — instead of waiting/polling for URL change, pause the worker and signal the API to request 2FA from the user. Resume when code is received.
  - **Modify:** `login(auth_code)` — the `auth_code` parameter already exists! Just wire it to receive the code from the API relay.
  - **Modify:** `launch_browser()` — always headless on server, remove `config['browser_headless']` toggle
  - **Modify:** `get_doc_text()` — consider fetching doc content via Google Docs API instead of browser scraping (more reliable, faster, no second tab needed)
  - **Keep:** `navigate_to_dashboard()`, `navigate_to_calendar()`, `login()` core logic — these are the heart of the automation

---

## Not Reusable (Replaced Entirely)

### `src/main.py` (1,093 lines)

- **What it does:** Tkinter GUI — user inputs, config management, automation orchestration
- **Why not reusable:** Desktop GUI → replaced by web frontend
- **Web equivalent:** Next.js pages + API routes handle all of this
- **Useful reference:** The `run_process()` method (orchestration logic) is a good reference for building the worker's job execution flow

### `src/updater.py` (175 lines)

- **What it does:** Auto-update from GitHub releases
- **Why not reusable:** Web app doesn't need client-side auto-update — you deploy directly
- **Web equivalent:** Standard deployment pipeline (git push → build → restart)

---

## New Code Needed

| Component | Purpose | Estimated Size |
| --- | --- | --- |
| Next.js frontend pages | Auth, dashboard, job submission, 2FA input, payments | ~2,000 lines |
| API routes | Job CRUD, credit management, payment webhooks | ~800 lines |
| Database schema + models | Users, credentials, jobs, transactions | ~300 lines |
| Worker service wrapper | Python script that picks up jobs from Redis and runs automation | ~200 lines |
| Server-side logger | Replaces Tkinter Logger class | ~50 lines |
| 2FA relay mechanism | Redis pub/sub between worker and API | ~150 lines |

---

## Migration Checklist

When you're ready to start, do these in order:

1. [ ] Create a new project folder for the web version (don't mix with the desktop app)
2. [ ] Copy `doc_parser.py`, `utils.py` into the new project's worker directory
3. [ ] Copy `calendar_scanner.py`, `form_filler.py` — then swap logger
4. [ ] Copy `browser_controller.py` — then strip desktop-specific code per notes above
5. [ ] Build the new server-side logger (simple Python `logging` wrapper)
6. [ ] Test the worker with a hardcoded job before wiring up the API
7. [ ] Build frontend and API around the working worker
