import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import LabelEncoder
from rapidfuzz import process as fuzzy_process
import os
import time
import datetime
import psutil
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn

# ---------- Load ML artifacts ----------
# Use absolute paths from the src directory
current_dir = os.path.dirname(os.path.abspath(__file__))
MODEL = joblib.load(os.path.join(current_dir, "models/ensemble_model.joblib"))
SCALER = joblib.load(os.path.join(current_dir, "models/scaler.joblib"))
TARGET_ENCODER = joblib.load(os.path.join(current_dir, "models/target_encoder.joblib"))

TRAIN_CSV = os.path.join(current_dir, "data/final_flood_classification data.csv")
FORECAST_CSV = os.path.join(current_dir, "data/mumbai_regions_7day_forecast.csv")

df_train = pd.read_csv(TRAIN_CSV)
if " Population" in df_train.columns:
    df_train.rename(columns={" Population": "Population"}, inplace=True)

possible_cat_cols = ["Ward Code", "Land Use Classes", "Soil Type", "Areas"]
REQUIRED_FEATURES = list(SCALER.feature_names_in_)
cat_cols = [c for c in possible_cat_cols if c in df_train.columns and c in REQUIRED_FEATURES]
le_dict = {}
for col in cat_cols:
    le = LabelEncoder()
    series = df_train[col].astype(str).fillna("Unknown")
    if "Unknown" not in series.values:
        series = pd.concat([series, pd.Series(["Unknown"])], ignore_index=True)
    le.fit(series)
    le_dict[col] = le

medians = df_train[REQUIRED_FEATURES].select_dtypes(include=np.number).median().to_dict()

df_forecast = pd.read_csv(FORECAST_CSV)
# Handle column name differences
if 'Area' in df_forecast.columns and 'Areas' not in df_forecast.columns:
    df_forecast.rename(columns={'Area': 'Areas'}, inplace=True)

forecast_names = df_forecast['Areas'].astype(str).unique().tolist()
normalized_forecast = {name.strip().lower(): name for name in forecast_names}

# ---------- Helpers ----------
def fuzzy_match_area(user_input, limit=3):
    if not user_input:
        return []
    choices = list(normalized_forecast.keys())
    results = fuzzy_process.extract(user_input.strip().lower(), choices, limit=limit)
    return [(normalized_forecast[r[0]], r[1]) for r in results]

def _encode_categoricals(row: pd.Series) -> pd.Series:
    for col, le in le_dict.items():
        if col in row.index:
            val = "Unknown" if pd.isna(row[col]) else str(row[col])
            try:
                row[col] = le.transform([val])[0]
            except Exception:
                row[col] = le.transform(["Unknown"])[0]
    return row

def prepare_features_from_forecast(area_name, forecast_row):
    row = pd.Series({c: np.nan for c in REQUIRED_FEATURES})
    row["Areas"] = area_name
    if "Latitude" in forecast_row:
        row["Latitude"] = forecast_row.get("Latitude")
    if "Longitude" in forecast_row:
        row["Longitude"] = forecast_row.get("Longitude")
    if "Ward Code" in forecast_row and "Ward Code" in REQUIRED_FEATURES:
        row["Ward Code"] = forecast_row.get("Ward Code")
    rain_fields = ["Rainfall_mm", "Rainfall (mm)", "Rainfall", "rainfall"]
    for rf in rain_fields:
        if rf in forecast_row:
            if "Rainfall_mm" in REQUIRED_FEATURES:
                row["Rainfall_mm"] = forecast_row.get(rf)
            break
    row = _encode_categoricals(row)
    for col in REQUIRED_FEATURES:
        if pd.isna(row.get(col)):
            row[col] = medians.get(col, 0)
    return pd.DataFrame([[row.get(col, 0) for col in REQUIRED_FEATURES]], columns=REQUIRED_FEATURES)

def predict_risk_from_features(df_features):
    Xs = SCALER.transform(df_features)
    pred = MODEL.predict(Xs)
    return TARGET_ENCODER.inverse_transform(pred)[0]

# Create FastAPI app
app = FastAPI(title="Flood Prediction API", 
              description="API for predicting flood risk in Mumbai areas")

# Define response model
class PredictionResponse(BaseModel):
    area: str
    date: str
    flood_risk: str
    rainfall: float
    matched_area: Optional[str] = None
    match_score: Optional[float] = None

@app.get("/predict", response_model=PredictionResponse)
async def predict_flood_risk(area: str = Query(..., description="Area name"), 
                             date: Optional[str] = Query(None, description="Forecast date")):
    """
    Predict flood risk for a given area and date.
    If date is not provided, the latest available date will be used.
    """
    matches = fuzzy_match_area(area, limit=1)
    if not matches:
        return {"area": area, "date": date or "N/A", "flood_risk": "Unknown", 
                "rainfall": 0.0, "matched_area": None, "match_score": 0.0}
    
    matched_area, score = matches[0]
    rows = df_forecast[
        (df_forecast['Areas'].astype(str).str.strip().str.lower() == matched_area.strip().lower())
    ]
    
    if date:
        rows = rows[rows['Date'] == date]
    
    if rows.empty:
        return {"area": area, "date": date or "N/A", "flood_risk": "Unknown", 
                "rainfall": 0.0, "matched_area": matched_area, "match_score": score}
    
    forecast_row = rows.iloc[0].to_dict()
    features = prepare_features_from_forecast(matched_area, forecast_row)
    
    try:
        risk = predict_risk_from_features(features)
        rainfall = forecast_row.get('Rainfall_mm', 0.0)
        return {"area": area, "date": forecast_row['Date'], "flood_risk": risk, 
                "rainfall": rainfall, "matched_area": matched_area, "match_score": score}
    except Exception as e:
        return {"area": area, "date": forecast_row['Date'], "flood_risk": "Error", 
                "rainfall": 0.0, "matched_area": matched_area, "match_score": score}

# Add endpoint to list all available areas
@app.get("/areas")
async def get_areas():
    """Get a list of all areas for which predictions are available."""
    return {"areas": sorted(df_forecast['Areas'].unique().tolist())}

# Add endpoint to list all available dates
@app.get("/dates")
async def get_dates():
    """Get a list of all dates for which predictions are available."""
    return {"dates": sorted(df_forecast['Date'].unique().tolist())}

# Health check endpoints
class HealthResponse(BaseModel):
    status: str
    api_version: str
    timestamp: str
    uptime: float
    memory_usage: Dict[str, Any]
    model_info: Dict[str, Any]
    data_info: Dict[str, Any]

# Track when the API started
START_TIME = time.time()
API_VERSION = "1.0.0"

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to monitor API status and resource usage.
    Returns key metrics about the API service's health and resources.
    """
    # Basic status
    current_time = datetime.datetime.now().isoformat()
    uptime = time.time() - START_TIME
    
    # Memory usage
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_usage = {
            "rss_mb": memory_info.rss / (1024 * 1024),  # Convert to MB
            "vms_mb": memory_info.vms / (1024 * 1024),  # Virtual Memory Size
            "percent": process.memory_percent()
        }
    except ImportError:
        # If psutil isn't available
        memory_usage = {
            "rss_mb": "psutil not installed",
            "vms_mb": "psutil not installed",
            "percent": "psutil not installed"
        }
    
    # Data information
    data_info = {
        "forecast_file": os.path.basename(FORECAST_CSV),
        "forecast_size_kb": os.path.getsize(FORECAST_CSV) / 1024,
        "forecast_modified": datetime.datetime.fromtimestamp(
            os.path.getmtime(FORECAST_CSV)).isoformat(),
        "num_areas": len(forecast_names),
        "num_dates": len(df_forecast['Date'].unique())
    }
    
    # Model information
    model_info = {
        "model_type": "Mumbai Flood Prediction Model",
        "model_implementation": type(MODEL).__name__,
        "features": len(REQUIRED_FEATURES),
        "target_classes": len(TARGET_ENCODER.classes_)
    }
    
    return {
        "status": "healthy",
        "api_version": API_VERSION,
        "timestamp": current_time,
        "uptime": uptime,
        "memory_usage": memory_usage,
        "model_info": model_info,
        "data_info": data_info
    }

@app.get("/ping")
async def ping():
    """Simple ping endpoint for basic availability checks."""
    return {"status": "ok", "timestamp": datetime.datetime.now().isoformat()}

    # Run the FastAPI application with uvicorn on port 8080
    port = 8082  # Changed from 8080 to avoid conflicts
    print(f"Starting API server on port {port}...")
    print(f"Access the API documentation at: http://localhost:{port}/docs")
    print(f"To make predictions, use: http://localhost:{port}/predict?area=YOUR_AREA&date=YOUR_DATE")
    uvicorn.run(app, host="0.0.0.0", port=port)

