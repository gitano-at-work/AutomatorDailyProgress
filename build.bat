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
echo 2. Auto-generating version from current date...
:: Generate version as YYYY.MM.DD
for /f "tokens=1-3 delims=/" %%a in ('%SystemRoot%\System32\wbem\wmic.exe os get localdatetime /value ^| find "="') do set DT=%%a
set YEAR=%DT:~14,4%
set MONTH=%DT:~18,2%
set DAY=%DT:~20,2%
set APP_VERSION=%YEAR%.%MONTH%.%DAY%
echo    Version: %APP_VERSION%
echo %APP_VERSION%> src\version.txt
echo    Written to src\version.txt

echo.
echo 3. Ensuring assets folder exists...
if not exist assets mkdir assets

echo.
echo 4. Building Executable with PyInstaller...
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
echo 5. Copying updater.bat to dist folder...
copy /Y updater.bat dist\updater.bat >nul

echo.
echo ==========================================
echo    BUILD SUCCESSFUL!  (v%APP_VERSION%)
echo ==========================================
echo.
echo Your executable is located in the 'dist' folder:
echo   dist\DailyReporter.exe
echo   dist\updater.bat
echo.
echo To release an update:
echo   1. Create a GitHub Release with tag "v%APP_VERSION%"
echo   2. Upload dist\DailyReporter.exe as a release asset
echo.
echo Keep 'config.json' next to the exe to persist settings.
echo.
pause
