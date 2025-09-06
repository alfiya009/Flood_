@echo off
REM This script starts the Mumbai Flood Forecast Data Updater as a background service

echo Starting Mumbai Flood Forecast Data Updater...
cd "%~dp0"

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Start the data updater service that runs daily
start /B pythonw src/pastsevendaysData.py --time 01:00 > nul 2>&1

echo Service started! The data will be updated daily at 01:00 AM.
echo You can close this window.
timeout /t 5
