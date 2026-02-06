@echo off
echo ==========================================
echo    Daily Progress Reporter - Build Tool
echo ==========================================

echo 1. Installing/Updating Dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b %errorlevel%
)

echo.
echo 2. ensuring assets folder exists...
if not exist assets mkdir assets

echo.
echo 3. Building Executable with PyInstaller...
echo    (This may take a few minutes, please wait...)
echo.

:: Note: We use --collect-all playwright to ensure browser binaries/drivers are handled correctly.
:: We use --add-data to include source code and assets if needed at runtime.

:: Invoke PyInstaller as a module to avoid PATH issues
python -m PyInstaller --noconfirm --onefile --windowed --name "DailyReporter" ^
 --add-data "src;src" ^
 --add-data "assets;assets" ^
 --collect-all playwright ^
 src/main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed! Check the error messages above.
    pause
    exit /b %errorlevel%
)

echo.
echo ==========================================
echo    BUILD SUCCESSFUL!
echo ==========================================
echo.
echo Your executable is located in the 'dist' folder:
echo   dist\DailyReporter.exe
echo.
echo You can move this .exe anywhere, but keep 'config.json' 
echo next to it if you want to persist settings.
echo.
pause
