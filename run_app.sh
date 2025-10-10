#!/bin/bash
# GeoScout Launch Script

# Load environment variables from .env.local (with your actual API key)
if [ -f ../.env.local ]; then
    export $(cat ../.env.local | grep -v '^#' | xargs)
elif [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
else
    echo "Error: No .env.local or .env file found"
    echo "Copy .env.example to .env.local and add your API key"
    exit 1
fi

# Set Python path to include geoscout directory
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Launch Streamlit
cd ui
streamlit run app.py
