# app.py - Gunicorn entry point for Render deployment
from dotenv import load_dotenv
load_dotenv()

import sys
import os

# Add src directory to Python path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the Flask app from src/main.py
from main import app

# Configure for Render deployment
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
