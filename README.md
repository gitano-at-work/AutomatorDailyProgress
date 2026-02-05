# Daily Progress Reporter

Automates filling out daily progress reports from a Google Doc.

## Setup

1.  **Install Python 3.8+**
2.  Run `run.bat` (This will set up the virtual environment and install dependencies automatically).

## Usage

1.  Enter your Google Doc URL (must be accessible to you).
2.  Enter your Web App Username and Password.
3.  Click **Start Automation**.
4.  A browser will open.
5.  If 2FA is required, the automation will PAUSE. Enter your 2FA code in the browser manually.
6.  Once logged in (dashboard detected), the automation will continue (in future phases).
7.  For now (Phase 1), the browser will close after login verification.

## Configuration

Settings are saved in `config.json` automatically.

## Security Note

Passwords are currently stored in `config.json` in plain text. Do not share this file.
