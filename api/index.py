import sys
import os

# Add the backend directory to Python path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import the existing FastAPI app from backend/main.py
# Vercel routes /api/* to this file and the app handles paths at the root
# (e.g. /api/observations → app sees /observations)
from main import app
