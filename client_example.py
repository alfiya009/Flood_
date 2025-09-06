import requests
import json
from tabulate import tabulate

def predict_flood_risk(area, date=None):
    """
    Make a request to the flood prediction API.
    
    Args:
        area (str): The area name to get prediction for
        date (str, optional): The forecast date. If None, the API will use the latest date.
        
    Returns:
        dict: The prediction result
    """
    base_url = "http://localhost:8082"  # Updated to port 8082
    
    # Build the query parameters
    params = {"area": area}
    if date:
        params["date"] = date
    
    # Make the request
    try:
        response = requests.get(f"{base_url}/predict", params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None

def get_available_areas():
    """Get a list of all available areas."""
    base_url = "http://localhost:8082"  # Updated to port 8082
    try:
        response = requests.get(f"{base_url}/areas")
        response.raise_for_status()
        return response.json().get("areas", [])
    except requests.exceptions.RequestException as e:
        print(f"Error getting areas: {e}")
        return []

def get_available_dates():
    """Get a list of all available forecast dates."""
    base_url = "http://localhost:8082"  # Updated to port 8082
    try:
        response = requests.get(f"{base_url}/dates")
        response.raise_for_status()
        return response.json().get("dates", [])
    except requests.exceptions.RequestException as e:
        print(f"Error getting dates: {e}")
        return []

def check_api_health():
    """Get health status of the API."""
    base_url = "http://localhost:8082"  # Updated to port 8082
    try:
        response = requests.get(f"{base_url}/health")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error checking API health: {e}")
        return None

def ping_api():
    """Simple ping test to check if API is available."""
    base_url = "http://localhost:8082"  # Updated to port 8082
    try:
        response = requests.get(f"{base_url}/ping")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error pinging API: {e}")
        return None

def check_monitor_health():
    """Get health status from the monitor service."""
    monitor_url = "http://localhost:8081"
    try:
        response = requests.get(f"{monitor_url}/status")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error checking health monitor: {e}")
        return None

if __name__ == "__main__":
    print("Flood Prediction API Client Example")
    print("===================================")
    
    # Check API health
    print("\nChecking API health...")
    health_data = check_api_health()
    if health_data:
        print(f"API Status: {health_data.get('status', 'Unknown')}")
        print(f"API Version: {health_data.get('api_version', 'Unknown')}")
        print(f"API Uptime: {health_data.get('uptime', 0):.2f} seconds")
        
        # Show data info
        data_info = health_data.get('data_info', {})
        print(f"\nData Information:")
        print(f"  Forecast File: {data_info.get('forecast_file', 'Unknown')}")
        print(f"  Last Modified: {data_info.get('forecast_modified', 'Unknown')}")
        print(f"  Areas Available: {data_info.get('num_areas', 0)}")
        print(f"  Dates Available: {data_info.get('num_dates', 0)}")
    else:
        print("API health check failed! Try simple ping...")
        ping_result = ping_api()
        if ping_result:
            print(f"API Ping: {ping_result.get('status', 'Unknown')}")
            print(f"Timestamp: {ping_result.get('timestamp', 'Unknown')}")
        else:
            print("API is not responding!")
            print("Check if the API is running on port 8080.")
            exit(1)
    
    # Get available areas
    print("\nGetting available areas...")
    areas = get_available_areas()
    if areas:
        print(f"Found {len(areas)} areas. First 5: {areas[:5]}")
    else:
        print("No areas found or couldn't connect to the API server.")
        exit(1)
    
    # Get available dates
    print("\nGetting available dates...")
    dates = get_available_dates()
    if dates:
        print(f"Found {len(dates)} dates: {dates}")
    else:
        print("No dates found or couldn't connect to the API server.")
        exit(1)
    
    # Example prediction
    print("\nMaking a prediction...")
    area_to_check = areas[0]  # Use the first area
    date_to_check = dates[0]  # Use the first date
    
    prediction = predict_flood_risk(area_to_check, date_to_check)
    if prediction:
        print(f"\nPrediction for {prediction.get('area', 'unknown')} on {prediction.get('date', 'unknown')}:")
        print(f"Flood Risk: {prediction.get('flood_risk', 'unknown')}")
        print(f"Rainfall: {prediction.get('rainfall', 0)} mm")
    else:
        print("Failed to get prediction.")
    
    # Try with just an area (no date)
    print("\nMaking a prediction with just an area (no date)...")
    prediction = predict_flood_risk(area_to_check)
    if prediction:
        print(f"\nPrediction for {prediction.get('area', 'unknown')} on {prediction.get('date', 'unknown')}:")
        print(f"Flood Risk: {prediction.get('flood_risk', 'unknown')}")
        print(f"Rainfall: {prediction.get('rainfall', 0)} mm")
    else:
        print("Failed to get prediction.")
        
    # Check health monitor if available
    print("\nChecking health monitor status...")
    monitor_status = check_monitor_health()
    if monitor_status:
        print("Health monitor is running!")
        print(f"Monitor uptime: {monitor_status.get('monitor_uptime', 0):.2f} seconds")
        
        services = monitor_status.get('services', [])
        if services:
            print("\nMonitored Services Status:")
            for service in services:
                print(f"  Service: {service.get('service', 'Unknown')}")
                print(f"  Status: {service.get('status', 'Unknown')}")
                print(f"  Last Check: {service.get('last_check', 'Unknown')}")
                print(f"  Uptime: {service.get('uptime', 0):.2f} seconds")
                
                # Print endpoint status
                endpoints = service.get('endpoint_status', {})
                if endpoints:
                    print("  Endpoints:")
                    for endpoint, status in endpoints.items():
                        print(f"    {endpoint}: {'OK' if status else 'FAIL'}")
                print()
    else:
        print("Health monitor not available. It might not be running on port 8081.")
        print("Start it with: python src/health_monitor.py")
