# Flood Prediction Service

This project is a flood risk prediction service for Mumbai areas. It includes both a web interface (using Gradio) and a REST API (using FastAPI) to predict flood risk based on weather forecast data. The service automatically updates its weather data daily.

## Project Structure

```
flood-prediction-service
├── src
│   ├── app.py                   # Gradio web interface for flood risk prediction
│   ├── api.py                   # FastAPI REST API for flood risk prediction
│   ├── pastsevendaysData.py     # Script to fetch and update past 7 days weather data
│   ├── schedule_data_updates.py # Script to schedule automatic data updates daily
│   ├── models                   # ML models for flood prediction
│   │   ├── ensemble_model.joblib
│   │   ├── scaler.joblib
│   │   └── target_encoder.joblib
│   └── data                     # Data files for the project
│       ├── final_flood_classification data.csv
│       ├── mumbai_regions_7day_forecast.csv
│       └── mumbai_static_areas_unique.csv
├── Dockerfile                   # For containerizing the application
├── client_example.py            # Example client to demonstrate API usage
├── requirements.txt             # Project dependencies
└── README.md                    # Project documentation
```

## Features

- **Flood Risk Prediction**: Predicts flood risk for Mumbai areas based on rainfall and other factors
- **Multiple Interfaces**: 
  - Web UI using Gradio
  - REST API using FastAPI
- **Automatic Data Updates**: Daily fetches past 7 days of weather data to keep predictions current
- **Containerization**: Docker support for easy deployment

## Setup Instructions

1. **Set Up Environment**: Ensure you have Python 3.8+ and pip installed. Create a virtual environment and activate it.

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

2. **Install Dependencies**: Install the necessary packages:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Web Interface**: Start the Gradio web interface:

   ```bash
   python src/app.py
   ```

   The web interface will be available at http://localhost:7860

4. **Run the API Service**: Start the FastAPI REST API:

   ```bash
   python src/api.py
   ```

   The API will be available at http://localhost:8082 with documentation at http://localhost:8082/docs

5. **Update Weather Data**: To manually update the weather data:

   ```bash
   python src/pastsevendaysData.py --run-once
   ```

6. **Schedule Automatic Updates**: To set up daily automatic data updates:

   ```bash
   python src/schedule_data_updates.py
   ```

7. **Docker Deployment**: To use Docker:

   ```bash
   docker build -t flood-prediction-service .
   docker run -p 8080:8080 flood-prediction-service
   ```

## API Usage

The API provides the following endpoints:

- `GET /predict?area={area_name}&date={optional_date}`: Get flood risk prediction for an area
- `GET /areas`: Get list of all available areas
- `GET /dates`: Get list of all available dates
- `GET /health`: Get comprehensive health status of the API
- `GET /ping`: Simple ping endpoint for basic health checks

Example usage with the provided client:

```bash
python client_example.py
```

## Health Monitoring

The system includes health monitoring at two levels:

1. **API Health Endpoints**: The main API includes `/health` and `/ping` endpoints to check its status
2. **Dedicated Health Monitor**: A separate service running on port 8081 that continuously monitors the API

To run the health monitor:

```bash
python src/health_monitor.py
```

The health monitor provides these endpoints:

- `GET /status`: Get detailed status of the API and endpoints
- `GET /history`: View historical health check results
- `GET /`: Basic health monitor information

Health checks include:
- API availability and response times
- Data and model status
- Memory and resource usage
- Uptime statistics

## Automatic Data Updates

The system automatically fetches past 7 days of weather data using the Open-Meteo API. The data update can be:

1. Run manually using `python src/pastsevendaysData.py --run-once`
2. Scheduled to run daily using `python src/schedule_data_updates.py`

## License

This project is licensed under the MIT License - see the LICENSE file for details.