#!/bin/bash

# Instructions:
# 1. Sign up at https://dashboard.ngrok.com/signup
# 2. Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
# 3. Replace YOUR_AUTHTOKEN_HERE with your actual token
# 4. Run: chmod +x start_ngrok.sh
# 5. Run: ./start_ngrok.sh

# Configure ngrok with your authtoken (only need to do this once)
# ngrok config add-authtoken YOUR_AUTHTOKEN_HERE

# Start ngrok tunnel for Streamlit app
echo "Starting ngrok tunnel for Streamlit app on port 8501..."
ngrok http 8501