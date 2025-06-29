#!/usr/bin/env python3
"""
Web Application Startup Script
Start the web interface with interactive database selection
"""

import os
import sys
import argparse

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database_config import DatabaseConfig
from src.web_app import initialize_app, app, socketio

def show_database_menu():
    """Display interactive database selection menu"""
    try:
        db_config = DatabaseConfig()
        databases = db_config.registry.get('databases', {})
        default_db_id = db_config.get_default_database_id()
        
        if not databases:
            print("❌ No databases found in registry.")
            print("💡 Use 'manage_databases.py add' to create databases")
            return None
        
        print("\n🗄️  Available Databases:")
        print("=" * 60)
        
        # Display databases with numbering
        db_list = list(databases.keys())
        for i, db_id in enumerate(db_list, 1):
            db_info = databases[db_id]
            default_marker = " [DEFAULT]" if db_id == default_db_id else ""
            print(f"{i:2}. {db_id}{default_marker}: {db_info['name']}")
            print(f"    📖 {db_info['description'][:80]}{'...' if len(db_info['description']) > 80 else ''}")
            print()
        
        print(f"{len(db_list) + 1:2}. Use default database ({default_db_id}: {databases[default_db_id]['name']})")
        print(f"{len(db_list) + 2:2}. Exit")
        print("=" * 60)
        
        while True:
            try:
                choice = input(f"Select database (1-{len(db_list) + 2}): ").strip()
                
                if not choice:
                    continue
                    
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(db_list):
                    selected_db_id = db_list[choice_num - 1]
                    print(f"✅ Selected: {selected_db_id} - {databases[selected_db_id]['name']}")
                    return selected_db_id
                elif choice_num == len(db_list) + 1:
                    print(f"✅ Using default database: {default_db_id} - {databases[default_db_id]['name']}")
                    return default_db_id
                elif choice_num == len(db_list) + 2:
                    print("👋 Goodbye!")
                    return None
                else:
                    print(f"❌ Invalid choice. Please enter a number between 1 and {len(db_list) + 2}")
                    
            except ValueError:
                print("❌ Invalid input. Please enter a number.")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return None
                
    except Exception as e:
        print(f"❌ Error loading databases: {e}")
        return None

def main():
    """Main entry point with interactive database selection"""
    parser = argparse.ArgumentParser(description='Start the Document Database Web Interface')
    
    # Add database selection arguments (keeping for backward compatibility)
    parser.add_argument('--db-id', '--database-id', 
                       help='Database ID to use (4-digit number). If not specified, interactive menu will be shown.')
    parser.add_argument('--list-databases', action='store_true',
                       help='List all available databases and exit')
    
    # Add web-specific arguments
    parser.add_argument('--host', default=None, help='Host to bind to (overrides config)')
    parser.add_argument('--port', type=int, default=None, help='Port to bind to (overrides config)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Handle list databases option
    if args.list_databases:
        try:
            db_config = DatabaseConfig()
            print("📂 Available Databases:")
            print("=" * 50)
            for db_id in db_config.list_database_ids():
                db_info = db_config.get_database_info(db_id)
                default_marker = " [DEFAULT]" if db_id == db_config.get_default_database_id() else ""
                print(f"🔹 {db_id}{default_marker}: {db_info['name']}")
                print(f"   {db_info['description'][:100]}{'...' if len(db_info['description']) > 100 else ''}")
            return 0
        except Exception as e:
            print(f"❌ Error listing databases: {e}")
            return 1
    
    # Determine database ID
    if args.db_id:
        # Use command line specified database
        requested_db_id = args.db_id
        print(f"🎯 Using database ID from command line: {requested_db_id}")
    else:
        # Show interactive menu
        requested_db_id = show_database_menu()
        if requested_db_id is None:
            return 0  # User chose to exit
    
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
