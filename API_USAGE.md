# Flood Prediction API Usage Guide

## How to Access the API

The Flood Prediction API is running as a backend service on your machine. Here's how to access it:

### API Documentation

Access the interactive API documentation at:
```
http://localhost:8080/docs
```

This provides a user-friendly interface to test all API endpoints.

### Making Predictions

To get flood risk predictions, use the `/predict` endpoint:
```
http://localhost:8080/predict?area=YOUR_AREA&date=YOUR_DATE
```

Example:
```
http://localhost:8080/predict?area=Colaba Causeway&date=2025-08-29
```

The date parameter is optional. If not provided, the API will use the latest available date.

### Available Areas

To get a list of all areas that can be predicted:
```
http://localhost:8080/areas
```

### Available Dates

To get a list of all dates for which forecast data is available:
```
http://localhost:8080/dates
```

## Important Note

When accessing the API from your browser or applications, always use `localhost` or `127.0.0.1`, not `0.0.0.0`. 

The server is configured to listen on all network interfaces (0.0.0.0), but when accessing it from the same machine, you need to use localhost.

## Using the API in Code

Here's an example of how to use the API from Python:

```python
import requests

# Make a prediction
response = requests.get("http://localhost:8080/predict", 
                        params={"area": "Colaba Causeway", "date": "2025-08-29"})
prediction = response.json()
print(f"Flood risk: {prediction['flood_risk']}")
print(f"Rainfall: {prediction['rainfall']} mm")

# Get all available areas
response = requests.get("http://localhost:8080/areas")
areas = response.json()["areas"]
print(f"Available areas: {areas}")

# Get all available dates
response = requests.get("http://localhost:8080/dates")
dates = response.json()["dates"]
print(f"Available dates: {dates}")
```

## Running the API Server

To start the API server:

```
python src/api.py
```

The server will start on port 8080.
