
@echo off
title WiFi Connector Builder

echo ==========================================
echo       WiFi Connector - Build Tool
echo ==========================================
echo.

echo [1/4] Installing project dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 goto error

echo.
echo [2/4] Installing PyInstaller...
python -m pip install pyinstaller
if errorlevel 1 goto error

echo.
echo [3/4] Checking Chromium folder...
set PLAYWRIGHT_BROWSERS_PATH=0

set "BROWSER_DIR=C:\Users\Kamal Dhali\AppData\Local\Programs\Python\Python314\Lib\site-packages\playwright\driver\package\.local-browsers"

if not exist "%BROWSER_DIR%" (
    echo ERROR: Chromium folder not found!
    goto error
)

echo Chromium folder found.

echo.
echo [4/4] Building WiFi Connector...

python -m PyInstaller --noconfirm --clean --onedir --console --name WiFiConnector --collect-all playwright --collect-all pystray --collect-all PIL --collect-all keyring --collect-all plyer --add-data "%BROWSER_DIR%;playwright\driver\package\.local-browsers" main.py

if errorlevel 1 goto error

echo.
echo ==========================================
echo BUILD COMPLETED!
echo ==========================================
echo.
echo Check the dist\WiFiConnector folder.
echo.
pause
exit /b 0

:error
echo.
echo BUILD FAILED!
echo Check the error messages above.
pause
exit /b 1
