#!/bin/bash

# Georgia Water Quality Dashboard - Run Script

echo "🚰 Georgia Water Quality Dashboard"
echo "================================="

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

# Check if database exists
if [ ! -f "georgia_water.db" ]; then
    echo "Database not found. Setting up database..."
    python setup_database.py
else
    echo "Database found."
fi

# Run the Streamlit app
echo ""
echo "Starting Streamlit app..."
echo "Access the app at: http://localhost:8501"
echo ""
streamlit run app.py