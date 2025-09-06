import os
import time
import datetime
import json
import requests
import socket
import threading
from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

# Create FastAPI app for health monitoring
app = FastAPI(
    title="Flood Prediction Health Monitor",
    description="Monitoring service for the Flood Prediction API"
)

# Configuration
API_URL = "http://localhost:8082"  # Main API URL updated to port 8082
HEALTH_PORT = 8081  # Health monitoring port
CHECK_INTERVAL = 60  # Check API health every 60 seconds

# Store health check history
health_history = []
MAX_HISTORY_ITEMS = 100  # Keep last 100 health checks

# Track health monitor uptime
START_TIME = time.time()

# Models
class ServiceStatus(BaseModel):
    service: str
    status: str
    last_check: str
    uptime: float
    endpoint_status: Dict[str, bool]
    response_times: Dict[str, float]

class HealthCheckResult(BaseModel):
    timestamp: str
    monitor_uptime: float
    services: List[ServiceStatus]
    system_info: Dict[str, Any]

# Background health check thread
def run_health_checks():
    """Background thread to periodically check API health"""
    while True:
        try:
            check_api_health()
        except Exception as e:
            print(f"Error in health check: {str(e)}")
        
        time.sleep(CHECK_INTERVAL)

def check_api_health():
    """Perform health check on the main API and store results"""
    timestamp = datetime.datetime.now().isoformat()
    
    # Initialize status object
    status = {
        "service": "flood-prediction-api",
        "status": "unknown",
        "last_check": timestamp,
        "uptime": 0,
        "endpoint_status": {},
        "response_times": {}
    }
    
    # Check main endpoints
    endpoints = ["/ping", "/health", "/areas", "/dates", "/predict?area=Colaba"]
    all_healthy = True
    
    for endpoint in endpoints:
        try:
            start_time = time.time()
            response = requests.get(f"{API_URL}{endpoint}", timeout=5)
            response_time = time.time() - start_time
            
            is_healthy = response.status_code == 200
            status["endpoint_status"][endpoint] = is_healthy
            status["response_times"][endpoint] = response_time
            
            if not is_healthy:
                all_healthy = False
            
            # If this is the health endpoint, extract uptime
            if endpoint == "/health" and is_healthy:
                health_data = response.json()
                status["uptime"] = health_data.get("uptime", 0)
        
        except requests.exceptions.RequestException:
            status["endpoint_status"][endpoint] = False
            status["response_times"][endpoint] = -1
            all_healthy = False
    
    # Set overall status
    status["status"] = "healthy" if all_healthy else "unhealthy"
    
    # Store in history, removing oldest if needed
    health_history.append(status)
    if len(health_history) > MAX_HISTORY_ITEMS:
        health_history.pop(0)

@app.get("/")
async def get_monitor_status():
    """Get current status of the monitoring service"""
    return {
        "service": "flood-prediction-health-monitor",
        "status": "running", 
        "uptime": time.time() - START_TIME,
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.get("/status", response_model=HealthCheckResult)
async def get_service_status():
    """Get detailed status of all monitored services"""
    if not health_history:
        # If no health checks yet, do one now
        try:
            check_api_health()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
    
    # Get system info
    system_info = {
        "hostname": socket.gethostname(),
        "monitor_port": HEALTH_PORT,
        "checks_performed": len(health_history)
    }
    
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "monitor_uptime": time.time() - START_TIME,
        "services": health_history,
        "system_info": system_info
    }

@app.get("/history")
async def get_health_history():
    """Get history of health checks"""
    return {
        "history": health_history,
        "count": len(health_history)
    }

def start_background_thread():
    """Start the background health check thread"""
    thread = threading.Thread(target=run_health_checks, daemon=True)
    thread.start()

if __name__ == "__main__":
    # Start background health check thread
    start_background_thread()
    
    # Run the health monitoring service
    print(f"Starting Health Monitoring Service on port {HEALTH_PORT}...")
    print(f"Access health monitor at: http://localhost:{HEALTH_PORT}/status")
    print(f"Main API being monitored at: {API_URL}")
    uvicorn.run(app, host="0.0.0.0", port=HEALTH_PORT)
