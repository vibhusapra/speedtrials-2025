#!/bin/bash

# Georgia Water Quality Dashboard - Run All Services

echo "🚰 Georgia Water Quality Dashboard - Full Stack"
echo "============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
pip install fastapi uvicorn

# Check if database exists
if [ ! -f "georgia_water.db" ]; then
    echo "Database not found. Setting up database..."
    python setup_database.py
else
    echo "Database found."
fi

# Start API server in background
echo ""
echo "Starting API server on http://localhost:8000..."
uvicorn api:app --reload --port 8000 &
API_PID=$!

# Give API time to start
sleep 2

# Run the Streamlit app
echo ""
echo "Starting Streamlit app on http://localhost:8501..."
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo ""
streamlit run app.py

# Clean up API server when Streamlit exits
kill $API_PID