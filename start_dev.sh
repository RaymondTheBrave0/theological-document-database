#!/bin/bash
# Development launcher for Document Database Web Application

echo "🌐 Starting Document Database Web Interface (Development Mode)"
echo "📍 URL will be: http://127.0.0.1:5000"
echo "⚠️  This is a development server (the warning is normal)"
echo "🔄 Press Ctrl+C to stop"
echo ""

# Activate the virtual environment
source document_db_env/bin/activate

# Launch in development mode
python src/web_app.py
