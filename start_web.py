#!/usr/bin/env python3
"""
Web Application Startup Script
Start the web interface with database selection support
"""

import os
import sys
import argparse

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database_config import add_database_args, handle_database_selection
from src.web_app import initialize_app, app, socketio

def main():
    """Main entry point with database selection"""
    parser = argparse.ArgumentParser(description='Start the Document Database Web Interface')
    
    # Add database selection arguments
    add_database_args(parser)
    
    # Add web-specific arguments
    parser.add_argument('--host', default=None, help='Host to bind to (overrides config)')
    parser.add_argument('--port', type=int, default=None, help='Port to bind to (overrides config)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Handle database selection
    requested_db_id = handle_database_selection(args)
    if requested_db_id is None and hasattr(args, 'list_databases') and args.list_databases:
        return 0  # Exit after listing databases
    
    try:
        # Initialize app with selected database
        db_id = initialize_app(requested_db_id)
        
        # Get configuration - we need to import here after initialization
        from src.web_app import config
        
        # Use command line overrides or config defaults
        host = args.host or config['web']['host']
        port = args.port or config['web']['port']
        debug = args.debug or config['web']['debug']
        
        # Suppress ALL Flask output before printing anything
        import logging
        import sys
        import os
        from contextlib import redirect_stdout, redirect_stderr
        
        # Completely disable all logging
        logging.disable(logging.CRITICAL)
        
        # Suppress all Flask-related loggers  
        for logger_name in ['werkzeug', 'flask', 'flask.app', 'socketio', 'engineio', 'urllib3']:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.CRITICAL)
            logger.disabled = True
            logger.propagate = False
        
        print(f"🌐 Web interface started: http://{host}:{port}")
        
        # Redirect both stdout and stderr to suppress ALL Flask messages
        with open(os.devnull, 'w') as devnull:
            with redirect_stdout(devnull), redirect_stderr(devnull):
                # Start the web application with all output suppressed
                socketio.run(app, host=host, port=port, debug=False, log_output=False, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n👋 Web server stopped")
        return 0
    except Exception as e:
        print(f"❌ Failed to start web application: {e}")
        print("💡 Use 'manage_databases.py list' to see available databases")
        return 1

if __name__ == '__main__':
    sys.exit(main())
