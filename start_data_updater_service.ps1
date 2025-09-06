# PowerShell script to start the Mumbai Flood Forecast Data Updater as a background service

Write-Host "Starting Mumbai Flood Forecast Data Updater..." -ForegroundColor Green
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptPath

# Activate the virtual environment
& "$scriptPath\venv\Scripts\Activate.ps1"

# Start the data updater service that runs daily
Start-Process -FilePath "$scriptPath\venv\Scripts\pythonw.exe" -ArgumentList "$scriptPath\src\pastsevendaysData.py --time 01:00" -WindowStyle Hidden

Write-Host "Service started! The data will be updated daily at 01:00 AM." -ForegroundColor Green
Write-Host "You can close this window." -ForegroundColor Cyan
Start-Sleep -Seconds 5
