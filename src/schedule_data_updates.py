import schedule
import time
import subprocess
import os
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("data_scheduler")

def run_data_update():
    """Run the data update script"""
    logger.info("Running scheduled data update")
    try:
        # Get the directory of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_script = os.path.join(script_dir, "pastsevendaysData.py")
        
        # Run the script with --run-once flag
        result = subprocess.run(['python', data_script, '--run-once'], 
                               capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Data update completed successfully")
        else:
            logger.error(f"Data update failed with exit code {result.returncode}")
            logger.error(f"Error output: {result.stderr}")
            
    except Exception as e:
        logger.error(f"Error running data update: {str(e)}")

def main():
    # Run immediately on startup
    logger.info("Starting data scheduler")
    run_data_update()
    
    # Schedule to run every day at midnight
    schedule.every().day.at("00:00").do(run_data_update)
    logger.info("Scheduled daily data update at 00:00")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")

if __name__ == "__main__":
    main()
