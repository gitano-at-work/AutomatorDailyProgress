@echo off
:: Auto-Update Helper Script
:: Usage: updater.bat "path\to\current.exe" "path\to\new.exe"
:: Waits for the app to exit, replaces the exe, and restarts it.

:: Wait for the app to fully exit
timeout /t 3 /nobreak >nul

:: Replace the current exe with the new one
move /Y "%~2" "%~1"

:: Restart the updated app
start "" "%~1"

:: Clean up - delete this script
(goto) 2>nul & del "%~f0"
