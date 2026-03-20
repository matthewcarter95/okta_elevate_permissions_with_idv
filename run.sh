#!/bin/bash
# Helper script to run the application

# Activate virtual environment
source venv/bin/activate

echo "Starting Flask application..."
echo "Visit: http://localhost:5000"
echo ""

# Run the Flask application
python app.py
