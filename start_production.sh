#!/bin/bash
# Production launcher for Document Database Web Application

# Activate the virtual environment
source document_db_env/bin/activate

# Launch with Gunicorn
exec gunicorn -w 4 -b 0.0.0.0:5000 src.web_app:app --worker-class eventlet
