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
        
        print(f"🌐 Starting web interface for database {db_id}")
        print("   Access your document database at:")
        
        # Get configuration - we need to import here after initialization
        from src.web_app import config
        
        # Use command line overrides or config defaults
        host = args.host or config['web']['host']
        port = args.port or config['web']['port']
        debug = args.debug or config['web']['debug']
        
        print(f"   → http://{host}:{port}")
        print("\n🔍 Features available:")
        print("   • Document search with AI responses")
        print("   • Query history")
        print("   • Auto-save results")
        print("   • Real-time interface")
        print("\n💡 Use Ctrl+C to stop the server")
        print("="*50)
        
        # Suppress Flask startup messages
        import logging
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.ERROR)
        werkzeug_logger.disabled = True
        
        flask_logger = logging.getLogger('flask')
        flask_logger.setLevel(logging.ERROR)
        flask_logger.disabled = True
        
        # Start the web application
        socketio.run(app, host=host, port=port, debug=debug, log_output=False)
        
    except KeyboardInterrupt:
        print("\n👋 Web server stopped")
        return 0
    except Exception as e:
        print(f"❌ Failed to start web application: {e}")
        print("💡 Use 'manage_databases.py list' to see available databases")
        return 1

if __name__ == '__main__':
    sys.exit(main())
