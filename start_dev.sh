#!/bin/bash
# Development launcher for Document Database Web Application

echo "This is a development server (the warning is normal)"
echo "Press Ctrl+C to stop"

# The pyenv virtual environment will activate automatically via .python-version file
# No need to manually activate - pyenv handles this automatically

# Launch in development mode and filter out only Flask startup messages
python src/web_app.py 2>&1 | grep -v "Serving Flask app" | grep -v "Debug mode:" | grep -v "WARNING: This is a development server"
