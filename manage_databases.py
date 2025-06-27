#!/usr/bin/env python3
"""
Database Registry Management Utility
Manage multiple theological databases with IDs, names, and descriptions.
"""

import os
import sys
import yaml
import argparse
from datetime import datetime
from pathlib import Path

class DatabaseManager:
    def __init__(self, registry_file="database_registry.yaml"):
        self.registry_file = registry_file
        self.registry = self.load_registry()
    
    def load_registry(self):
        """Load the database registry from file"""
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Create default registry structure
            return {
                'databases': {},
                'default_database': None,
                'registry_version': '1.0',
                'last_updated': datetime.now().isoformat()
            }
    
    def save_registry(self):
        """Save the registry to file"""
        self.registry['last_updated'] = datetime.now().isoformat()
        with open(self.registry_file, 'w') as f:
            yaml.dump(self.registry, f, default_flow_style=False, sort_keys=False)
        print(f"✅ Registry saved to {self.registry_file}")
    
    def list_databases(self):
        """List all registered databases"""
        if not self.registry['databases']:
            print("📂 No databases registered yet.")
            return
        
        print("📂 Registered Databases:")
        print("=" * 80)
        
        for db_id, db_info in self.registry['databases'].items():
            default_marker = " [DEFAULT]" if str(db_id) == str(self.registry.get('default_database', '')) else ""
            print(f"🔹 ID: {db_id}{default_marker}")
            print(f"   Name: {db_info['name']}")
            print(f"   Description: {db_info['description'][:100]}{'...' if len(db_info['description']) > 100 else ''}")
            print(f"   Created: {db_info.get('created_date', 'Unknown')}")
            print()
    
    def add_database(self, db_id, name, description, set_default=False):
        """Add a new database to the registry"""
        # Validate ID
        try:
            db_id_int = int(db_id)
            if db_id_int < 1000 or db_id_int > 9999:
                print("❌ Database ID must be between 1000 and 9999")
                return False
        except ValueError:
            print("❌ Database ID must be a 4-digit number")
            return False
        
        # Check if ID already exists
        if str(db_id) in self.registry['databases']:
            print(f"❌ Database ID {db_id} already exists")
            return False
        
        # Validate name length
        if len(name) > 30:
            print("❌ Database name must be 30 characters or less")
            return False
        
        # Create safe folder name from the name
        safe_name = name.lower().replace(' ', '-').replace('&', 'and')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '-_')
        
        # Add database to registry (no hard-coded paths)
        self.registry['databases'][str(db_id)] = {
            'name': name,
            'description': description,
            'created_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Set as default if requested or if it's the first database
        if set_default or not self.registry['databases'] or len(self.registry['databases']) == 1:
            self.registry['default_database'] = int(db_id)
        
        print(f"✅ Added database {db_id}: {name}")
        return True
    
    def edit_database(self, db_id, name=None, description=None, set_default=None):
        """Edit an existing database"""
        if str(db_id) not in self.registry['databases']:
            print(f"❌ Database ID {db_id} not found")
            return False
        
        db_info = self.registry['databases'][str(db_id)]
        
        if name is not None:
            if len(name) > 30:
                print("❌ Database name must be 30 characters or less")
                return False
            db_info['name'] = name
            print(f"✅ Updated name to: {name}")
        
        if description is not None:
            db_info['description'] = description
            print(f"✅ Updated description")
        
        if set_default is not None and set_default:
            self.registry['default_database'] = int(db_id)
            print(f"✅ Set {db_id} as default database")
        
        return True
    
    def remove_database(self, db_id, confirm=False):
        """Remove a database from registry"""
        if str(db_id) not in self.registry['databases']:
            print(f"❌ Database ID {db_id} not found")
            return False
        
        db_info = self.registry['databases'][str(db_id)]
        
        if not confirm:
            print(f"⚠️  This will remove database {db_id}: {db_info['name']}")
            print("⚠️  This only removes the registry entry - actual files will remain")
            response = input("Are you sure? (y/N): ")
            if response.lower() not in ['y', 'yes']:
                print("❌ Cancelled")
                return False
        
        # Remove from registry
        del self.registry['databases'][str(db_id)]
        
        # Update default if necessary
        if self.registry.get('default_database') == int(db_id):
            if self.registry['databases']:
                # Set first available as default
                self.registry['default_database'] = int(list(self.registry['databases'].keys())[0])
                print(f"✅ Default database changed to {self.registry['default_database']}")
            else:
                self.registry['default_database'] = None
                print("✅ No default database (no databases remaining)")
        
        print(f"✅ Removed database {db_id}")
        return True
    
    def create_directories(self, db_id):
        """Create the directory structure for a database using dynamic paths"""
        if str(db_id) not in self.registry['databases']:
            print(f"❌ Database ID {db_id} not found")
            return False
        
        # Import database config to generate paths dynamically
        try:
            from src.database_config import DatabaseConfig
            db_config = DatabaseConfig()
            config = db_config.get_config_for_database(db_id)
            
            directories = [
                config['database']['vector_db_path'],
                os.path.dirname(config['database']['metadata_db_path']),
                config['document_processing']['input_folder'],
                config['output']['default_output_folder']
            ]
            
            for directory in directories:
                Path(directory).mkdir(parents=True, exist_ok=True)
                print(f"📁 Created: {directory}")
            
            print(f"✅ Directory structure created for database {db_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating directories: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Manage theological document databases')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all databases')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new database')
    add_parser.add_argument('id', help='4-digit database ID (1000-9999)')
    add_parser.add_argument('name', help='Database name (max 30 chars)')
    add_parser.add_argument('description', help='Database description')
    add_parser.add_argument('--default', action='store_true', help='Set as default database')
    
    # Edit command
    edit_parser = subparsers.add_parser('edit', help='Edit existing database')
    edit_parser.add_argument('id', help='Database ID to edit')
    edit_parser.add_argument('--name', help='New name')
    edit_parser.add_argument('--description', help='New description')
    edit_parser.add_argument('--default', action='store_true', help='Set as default database')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a database')
    remove_parser.add_argument('id', help='Database ID to remove')
    remove_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    
    # Create directories command
    create_parser = subparsers.add_parser('create-dirs', help='Create directory structure for database')
    create_parser.add_argument('id', help='Database ID')
    
    # Interactive mode
    interactive_parser = subparsers.add_parser('interactive', help='Interactive management mode')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = DatabaseManager()
    
    if args.command == 'list':
        manager.list_databases()
    
    elif args.command == 'add':
        if manager.add_database(args.id, args.name, args.description, args.default):
            manager.save_registry()
    
    elif args.command == 'edit':
        if manager.edit_database(args.id, args.name, args.description, args.default):
            manager.save_registry()
    
    elif args.command == 'remove':
        if manager.remove_database(args.id, args.force):
            manager.save_registry()
    
    elif args.command == 'create-dirs':
        manager.create_directories(args.id)
    
    elif args.command == 'interactive':
        interactive_mode(manager)

def interactive_mode(manager):
    """Interactive mode for managing databases"""
    print("🗄️  Interactive Database Management")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. List databases")
        print("2. Add database")
        print("3. Edit database")
        print("4. Remove database")
        print("5. Create directories")
        print("6. Save and exit")
        print("7. Exit without saving")
        
        choice = input("\nEnter choice (1-7): ").strip()
        
        if choice == '1':
            manager.list_databases()
        
        elif choice == '2':
            print("\n➕ Add New Database")
            db_id = input("Database ID (4 digits): ").strip()
            name = input("Name (max 30 chars): ").strip()
            description = input("Description: ").strip()
            set_default = input("Set as default? (y/N): ").lower() in ['y', 'yes']
            
            manager.add_database(db_id, name, description, set_default)
        
        elif choice == '3':
            print("\n✏️  Edit Database")
            manager.list_databases()
            db_id = input("Database ID to edit: ").strip()
            print("Leave blank to keep current value:")
            name = input("New name: ").strip() or None
            description = input("New description: ").strip() or None
            set_default = input("Set as default? (y/N): ").lower() in ['y', 'yes']
            
            manager.edit_database(db_id, name, description, set_default)
        
        elif choice == '4':
            print("\n🗑️  Remove Database")
            manager.list_databases()
            db_id = input("Database ID to remove: ").strip()
            manager.remove_database(db_id)
        
        elif choice == '5':
            print("\n📁 Create Directories")
            manager.list_databases()
            db_id = input("Database ID: ").strip()
            manager.create_directories(db_id)
        
        elif choice == '6':
            manager.save_registry()
            print("👋 Goodbye!")
            break
        
        elif choice == '7':
            print("👋 Goodbye! (Changes not saved)")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == '__main__':
    main()
