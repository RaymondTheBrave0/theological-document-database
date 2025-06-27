#!/bin/bash
# Development launcher for Document Database Web Application

echo "Starting Document Database Web Interface (Development Mode)"

# The pyenv virtual environment will activate automatically via .python-version file
# No need to manually activate - pyenv handles this automatically

# Launch in development mode and filter out Flask startup messages
python src/web_app.py 2>&1 | grep -v "Serving Flask app" | grep -v "Debug mode:"
