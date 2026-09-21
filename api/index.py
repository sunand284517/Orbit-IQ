import sys
import os

# Add the backend directory to Python path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import the existing FastAPI app from backend/main.py
from main import app as backend_app

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create a wrapper app and mount the backend at /api
# This means requests to /api/observations → backend sees /observations
app = FastAPI(title="OrbitIQ API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/api", backend_app)
