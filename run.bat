@echo off
echo Starting Lha Saya Kerja Pak (LSKP)...

REM Detect Python command
set PYTHON_CMD=python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 'python' command not found, checking for 'py'...
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo Error: Python is not installed or not in PATH.
        echo Please install Python from https://python.org
        pause
        exit /b
    )
    set PYTHON_CMD=py
)

echo Using Python command: %PYTHON_CMD%

REM Check/Create Venv
if not exist "venv" (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv venv
)

REM Activate Venv
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment.
    pause
    exit /b
)

REM Install Dependencies
if not exist "venv\installed.flag" (
    echo Installing dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Failed to install dependencies.
        pause
        exit /b
    )
    
    echo Installing Playwright browsers...
    playwright install chromium
    if %errorlevel% neq 0 (
        echo Failed to install Playwright browsers.
        pause
        exit /b
    )
    
    type nul > venv\installed.flag
)

REM Run App
echo Launching Application...
python src/main.py
pause
