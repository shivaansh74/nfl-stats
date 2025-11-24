#!/bin/bash

# Test production setup locally

echo "🚀 Testing NFL Stats API in production mode..."
echo ""

# Check if gunicorn is installed
if ! pip show gunicorn > /dev/null 2>&1; then
    echo "📦 Installing gunicorn..."
    pip install gunicorn==21.2.0
fi

# Start the server
echo "Starting API server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

export PORT=8000
gunicorn api_server:app --bind 0.0.0.0:8000 --workers 2
