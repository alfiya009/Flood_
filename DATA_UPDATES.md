# Automated Data Updates for Mumbai Flood Prediction

This document explains how the automated data update system works for the Mumbai Flood Prediction Service.

## Overview

The system automatically fetches new weather forecast data every day and updates the forecast data file used by the prediction service. This ensures that the flood risk predictions are always based on the most current weather forecast data.

## Key Components

1. **Data Updater Script**: `src/pastsevendaysData.py` - This Python script fetches weather forecast data from the Open-Meteo API and updates the forecast data file.

2. **Static Area Data**: `src/data/mumbai_static_areas_unique.csv` - This file contains the list of areas in Mumbai along with their static attributes like latitude, longitude, ward code, etc.

3. **Forecast Data File**: `src/data/mumbai_regions_7day_forecast_fixed.csv` - This file contains the 7-day weather forecast data for all areas in Mumbai. It is used by the flood prediction model to generate risk assessments.

4. **Startup Scripts**:
   - `start_data_updater_service.bat` (Windows Command Prompt)
   - `start_data_updater_service.ps1` (Windows PowerShell)
   
   These scripts start the data updater as a background service that runs continuously and updates the data daily.

## How It Works

1. **Daily Updates**: The script is configured to run once every day at a specified time (default: 1:00 AM).

2. **Data Source**: Weather forecast data is fetched from the Open-Meteo API, which provides 7-day forecasts including rainfall amounts and intensities.

3. **Process**:
   - For each area in the static data file, the script fetches the latest 7-day forecast
   - It combines the forecast data with the static area attributes
   - It saves the combined data to the forecast data file
   - The prediction service automatically uses the updated data file

4. **Backup System**: Before updating the forecast data file, the script creates a backup of the existing file with a timestamp.

## How to Start the Data Updater Service

### Windows:

1. **Using Command Prompt**:
   ```
   start_data_updater_service.bat
   ```

2. **Using PowerShell**:
   ```
   .\start_data_updater_service.ps1
   ```

### Manual Update:

To manually update the data once without starting the continuous service:

```
python src/pastsevendaysData.py --run-once
```

## Configuration Options

When starting the data updater service, you can specify the time of day to run the update:

```
python src/pastsevendaysData.py --time 02:30
```

This would run the update daily at 2:30 AM.

## Logs

The data updater service creates log files in:
- `src/data_updater.log`

Check this file for information about update status and any errors.

## Troubleshooting

1. **Service Not Running**: Check the log file for errors. You may need to restart the service.

2. **API Errors**: The service depends on the Open-Meteo API. If there are API issues, check their status page or try again later.

3. **Data File Issues**: If the forecast data file becomes corrupted, you can restore from the latest backup or run a manual update.

## Adding New Areas

To add new areas to the prediction system:

1. Add the area information to `src/data/mumbai_static_areas_unique.csv`
2. Run a manual update with `python src/pastsevendaysData.py --run-once`
