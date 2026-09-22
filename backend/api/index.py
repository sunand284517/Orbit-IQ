import sys
import os

# Ensure the backend directory is on the Python path
sys.path.insert(0, os.path.dirname(os.path.join(os.path.dirname(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the FastAPI app from main.py
from main import app
