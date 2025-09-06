# Mumbai Flood Risk Prediction Service

This application predicts flood risk in Mumbai areas based on weather forecast data. It uses machine learning to provide risk assessments that can help residents and authorities prepare for potential flooding events.

## Features

- **Prediction API**: Get flood risk predictions for specific areas and dates
- **Interactive UI**: Easy-to-use interface for making predictions
- **Comprehensive Data**: Covers multiple areas in Mumbai with 7-day forecasts

## How to Use

### Web Interface

1. Select an area from the dropdown menu
2. Select a forecast date
3. View the flood risk prediction and rainfall information

### API Endpoints

The service also provides API endpoints for programmatic access:

- `/predict?area={area}&date={date}` - Get a prediction for a specific area and date
- `/areas` - Get a list of all available areas
- `/dates` - Get a list of all available forecast dates

### API Documentation

Full API documentation is available at `/docs` endpoint.

## About the Model

This service uses an ensemble machine learning model trained on historical flood and rainfall data for Mumbai. The model takes into account factors such as:

- Rainfall amount
- Area characteristics
- Land use
- Soil type
- Elevation
- And other geographical features

## Data Sources

The forecast data is updated regularly and includes 7-day predictions for rainfall and other relevant weather parameters across different areas of Mumbai.

## Deployment

This application is deployed on Hugging Face Spaces.
