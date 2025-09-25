#!/bin/bash

# Mastery English - Vocabulary Learning App
# Development Server Startup Script

echo "🚀 Starting Mastery English Development Server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade requirements
echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# Run the Flask app
echo "Starting Flask development server..."
echo "The app will automatically find an available port (5001, 5002, 5003, etc.)"
echo "Press Ctrl+C to stop the server"
echo ""
python app.py