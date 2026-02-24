#!/bin/bash

echo "🚀 Starting Universal AI Incident Detector Backend..."

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q flask flask-cors flask-socketio python-socketio requests openai

# Start the server
echo "✅ Starting Flask server on http://localhost:5001"
python3 app.py
