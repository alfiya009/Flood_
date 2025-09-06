import pandas as pd
import requests
import time
import os
import logging
import schedule
import argparse
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_updater.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("flood_data_updater")

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
# Get the absolute path to the src directory
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SRC_DIR, "data")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Input and output files with absolute paths
INPUT_CSV = os.path.join(DATA_DIR, "mumbai_static_areas_unique.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "mumbai_regions_7day_forecast.csv")

# Open-Meteo URLs
OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Check if the input file exists
try:
    if os.path.exists(INPUT_CSV):
        df = pd.read_csv(INPUT_CSV)
    else:
        # Fallback to using the existing forecast file as input
        logger.warning(f"Static areas file not found: {INPUT_CSV}")
        logger.warning("Using existing forecast file as input instead")
        df = pd.read_csv(OUTPUT_CSV)
        # Extract unique areas
        df = df[['Ward Code', 'Areas', 'Latitude', 'Longitude', 'Nearest Station', 
                'Elevation', 'Land Use Classes', 'Population', 'Road Density_m',
                'Distance_to_water_m', 'Soil Type', 'Built_up%', 'True_nearest_distance_m']].drop_duplicates()
except Exception as e:
    logger.error(f"Error loading input data: {str(e)}")
    # Use a fallback solution - create a small sample dataframe with Mumbai locations
    logger.warning("Using fallback sample data for Mumbai locations")
    df = pd.DataFrame({
        "Ward Code": ["A", "A", "A", "A", "A"],
        "Areas": ["Colaba", "Cuffe Parade", "CST", "Churchgate", "Fort"],
        "Latitude": [18.9067, 18.9156, 18.9402, 18.9322, 18.9340],
        "Longitude": [72.8147, 72.8173, 72.8359, 72.8264, 72.8346]
    })

results = []

# -------------------------------------------------
# FUNCTIONS
# -------------------------------------------------
def get_weather_data(lat, lon):
    """
    Fetch past 7-day weather history with rainfall + precipitation hours.
    If historical data fails, generates synthetic data based on forecast.
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        List of tuples with (date, rainfall_mm, intensity, rainfall_flag, rainfall_hours)
    """
    today = datetime.today().date()
    
    # First try to get past 7-day history
    try:
        # Get past 7-day history
        url = OPEN_METEO_URL
        end_date = today - timedelta(days=1)  # yesterday
        start_date = end_date - timedelta(days=6)  # last 7 days
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": ["precipitation_sum", "precipitation_hours"],
            "hourly": "precipitation",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "timezone": "auto"
        }
        
        logger.info(f"Requesting past 7-day weather data for lat={lat}, lon={lon}")
        r = requests.get(url, params=params, timeout=20)
        
        if r.status_code != 200:
            logger.error(f"API request failed with status {r.status_code}: {r.text}")
            raise Exception(f"API request failed with status {r.status_code}")
        
        data = r.json()
        
        daily_precip = data["daily"]["precipitation_sum"]
        daily_hours = data["daily"]["precipitation_hours"]
        daily_dates = data["daily"]["time"]

        # Compute daily max rainfall intensity (mm/hr)
        intensity_per_day = []
        for d in range(len(daily_dates)):
            day_start = datetime.fromisoformat(daily_dates[d])
            day_end = day_start + timedelta(days=1)
            # collect hourly precip for that day
            daily_vals = [
                val for t, val in zip(data["hourly"]["time"], data["hourly"]["precipitation"])
                if day_start <= datetime.fromisoformat(t) < day_end
            ]
            intensity_per_day.append(max(daily_vals) if daily_vals else 0)

        # Rainfall days count (binary 1 if >0 rain else 0)
        rainfall_day_flags = [1 if v > 0 else 0 for v in daily_precip]

        return list(zip(daily_dates, daily_precip, intensity_per_day, rainfall_day_flags, daily_hours))
        
    except Exception as e:
        logger.warning(f"Error getting historical data: {str(e)}. Trying fallback method...")
        
        # FALLBACK: Use current forecast data to simulate past data
        try:
            # Get current forecast data
            url = OPEN_METEO_FORECAST_URL
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": ["precipitation_sum"],
                "hourly": "precipitation",
                "forecast_days": 7,
                "timezone": "auto"
            }
            
            logger.info(f"Requesting forecast data for lat={lat}, lon={lon} as fallback")
            r = requests.get(url, params=params, timeout=20)
            
            if r.status_code != 200:
                logger.error(f"Fallback API request failed with status {r.status_code}: {r.text}")
                return None
                
            data = r.json()
            
            # Generate past dates
            past_dates = [(today - timedelta(days=7-i)).isoformat() for i in range(7)]
            
            # Use forecast data values but assign to past dates
            daily_precip = data["daily"]["precipitation_sum"][:7]  # take only up to 7 days
            
            # Fill in missing data
            while len(daily_precip) < 7:
                daily_precip.append(0.0)
                
            # Calculate intensity from hourly data
            intensity_per_day = []
            hourly_precip = data["hourly"]["precipitation"]
            
            # Split hourly data into days
            for i in range(min(7, len(daily_precip))):
                day_hours = hourly_precip[i*24:(i+1)*24]
                intensity_per_day.append(max(day_hours) if day_hours else 0)
            
            # Fill in missing intensity data
            while len(intensity_per_day) < 7:
                intensity_per_day.append(0.0)
                
            # Generate rainfall hours (roughly estimated from rainfall amount)
            daily_hours = [min(24, max(0, int(p * 5))) for p in daily_precip]
            
            # Rainfall days count (binary 1 if >0 rain else 0)
            rainfall_day_flags = [1 if v > 0 else 0 for v in daily_precip]
            
            logger.info(f"Successfully generated synthetic past weather data for lat={lat}, lon={lon}")
            return list(zip(past_dates, daily_precip, intensity_per_day, rainfall_day_flags, daily_hours))
            
        except Exception as e:
            logger.error(f"Fallback method also failed: {str(e)}")
            return None
        
def update_forecast_data():
    """Update the 7-day forecast data file."""
    logger.info("Starting 7-day forecast data update")
    
    try:
        # Check if input file exists
        if not os.path.exists(INPUT_CSV):
            logger.error(f"Input file not found: {INPUT_CSV}")
            return False
            
        # Load static input CSV
        df = pd.read_csv(INPUT_CSV)
        
        results = []
        processed_count = 0
        
        for idx, row in df.iterrows():
            lat, lon = row["Latitude"], row["Longitude"]
            
            # Get past 7 days weather data
            weather_data = get_weather_data(lat, lon)
            
            if weather_data:
                for day, rain_mm, intensity, rain_flag, rain_hours in weather_data:
                    results.append({
                        "Date": day,
                        "Ward Code": row.get("Ward Code", ""),
                        "Areas": row.get("Areas", ""),  # Use Areas as the column name
                        "Latitude": lat,
                        "Longitude": lon,
                        "Nearest Station": row.get("Nearest Station", ""),
                        "Elevation": row.get("Elevation", 0),
                        "Land Use Classes": row.get("Land Use Classes", ""),
                        "Population": row.get("Population", 0),
                        "Road Density_m": row.get("Road Density_m", 0),
                        "Distance_to_water_m": row.get("Distance_to_water_m", 0),
                        "Soil Type": row.get("Soil Type", ""),
                        "Built_up%": row.get("Built_up%", 0),
                        "True_nearest_distance_m": row.get("True_nearest_distance_m", 0),
                        "Rainfall_mm": rain_mm,
                        "Rainfall_Intensity_mm_hr": intensity,
                        "Rainfall_Days_Count": rain_flag,
                        "Rainfall_Hours": rain_hours
                    })
                
                processed_count += 1
                logger.info(f"Processed {processed_count}/{len(df)} areas: {row['Areas']} - DONE")
            else:
                logger.warning(f"Failed to get weather data for {row['Areas']}")
                
            # Sleep to avoid API rate limits
            time.sleep(1)
        
        if results:
            # Create output dataframe
            out_df = pd.DataFrame(results)
            
            # Create a backup of the current file if it exists
            if os.path.exists(OUTPUT_CSV):
                backup_path = f"{OUTPUT_CSV}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(OUTPUT_CSV, backup_path)
                logger.info(f"Created backup of existing data file at {backup_path}")
            
            # Save the new data
            out_df.to_csv(OUTPUT_CSV, index=False)
            logger.info(f"SUCCESS: Updated 7-day forecast saved to {OUTPUT_CSV}")
            logger.info(f"Total areas processed: {processed_count}/{len(df)}")
            return True
        else:
            logger.error("No data collected, forecast not updated")
            return False
    
    except Exception as e:
        logger.error(f"Error updating forecast data: {str(e)}")
        return False

# -------------------------------------------------
# SCHEDULER AND MAIN FUNCTIONALITY
# -------------------------------------------------
def run_scheduled_update():
    """Run the scheduled update task."""
    logger.info("Running scheduled forecast data update")
    success = update_forecast_data()
    if success:
        logger.info("Scheduled update completed successfully")
    else:
        logger.error("Scheduled update failed")
    
def run_once():
    """Run the update immediately once."""
    logger.info("Running immediate forecast data update")
    return update_forecast_data()

def setup_scheduler(update_time="00:00"):
    """Set up the scheduler to run the update at a specific time each day."""
    schedule.every().day.at(update_time).do(run_scheduled_update)
    logger.info(f"Scheduler set to run daily at {update_time}")

def main():
    """Main function to parse arguments and run the script."""
    parser = argparse.ArgumentParser(description="Update Mumbai 7-day forecast data")
    parser.add_argument("--run-once", action="store_true", help="Run the update once and exit")
    parser.add_argument("--time", default="00:00", help="Time to run daily update (format: HH:MM)")
    args = parser.parse_args()
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    
    if args.run_once:
        success = run_once()
        return 0 if success else 1
    else:
        # First run immediately
        run_once()
        
        # Then set up scheduler
        setup_scheduler(args.time)
        
        # Run the scheduler continuously
        logger.info("Starting scheduler loop. Press Ctrl+C to exit.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        
        return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
