"""
Database Configuration Manager
Handles multi-database system with database ID routing
"""

import os
import yaml
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Manages configuration for multiple theological databases"""
    
    def __init__(self, registry_file="database_registry.yaml", base_config_file="config.yaml"):
        self.registry_file = registry_file
        self.base_config_file = base_config_file
        self.registry = self.load_registry()
        self.base_config = self.load_base_config()
    
    def load_registry(self) -> Dict:
        """Load the database registry"""
        if not os.path.exists(self.registry_file):
            raise FileNotFoundError(f"Database registry not found: {self.registry_file}")
        
        with open(self.registry_file, 'r') as f:
            return yaml.safe_load(f)
    
    def load_base_config(self) -> Dict:
        """Load the base configuration template"""
        if not os.path.exists(self.base_config_file):
            raise FileNotFoundError(f"Base config not found: {self.base_config_file}")
        
        with open(self.base_config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def get_database_info(self, db_id: str) -> Optional[Dict]:
        """Get database information by ID"""
        return self.registry.get('databases', {}).get(str(db_id))
    
    def get_default_database_id(self) -> Optional[str]:
        """Get the default database ID"""
        default_id = self.registry.get('default_database')
        return str(default_id) if default_id else None
    
    def list_database_ids(self) -> list:
        """Get list of all database IDs"""
        return list(self.registry.get('databases', {}).keys())
    
    def validate_database_id(self, db_id: str) -> bool:
        """Check if database ID exists"""
        return str(db_id) in self.registry.get('databases', {})
    
    def generate_database_paths(self, db_id: str, db_info: Dict) -> Dict:
        """Generate all paths for a database based on configuration"""
        # Get base paths from configuration
        base_dir = self.base_config['database']['base_databases_dir']
        vector_subdir = self.base_config['database']['vector_db_subdir']
        metadata_filename = self.base_config['database']['metadata_db_filename']
        documents_subdir = self.base_config['database']['documents_subdir']
        output_subdir = self.base_config['database']['output_subdir']
        
        # Create safe folder name from database name
        safe_name = db_info['name'].lower().replace(' ', '-').replace('&', 'and')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '-_')
        
        # Generate database-specific directory
        db_dir = os.path.join(base_dir, f"{db_id}-{safe_name}")
        
        return {
            'database_dir': db_dir,
            'vector_db_path': os.path.join(db_dir, vector_subdir),
            'metadata_db_path': os.path.join(db_dir, metadata_filename),
            'document_folder': os.path.join(db_dir, documents_subdir),
            'output_folder': os.path.join(db_dir, output_subdir)
        }
    
    def get_config_for_database(self, db_id: str) -> Dict:
        """Generate complete configuration for specific database"""
        db_info = self.get_database_info(db_id)
        if not db_info:
            raise ValueError(f"Database ID {db_id} not found in registry")
        
        # Start with base configuration
        config = self.base_config.copy()
        
        # Generate dynamic paths
        paths = self.generate_database_paths(db_id, db_info)
        
        # Override database-specific paths
        config['database']['vector_db_path'] = paths['vector_db_path']
        config['database']['metadata_db_path'] = paths['metadata_db_path']
        config['document_processing']['input_folder'] = paths['document_folder']
        config['output']['default_output_folder'] = paths['output_folder']
        
        # Add database metadata
        config['database']['database_id'] = db_id
        config['database']['database_name'] = db_info['name']
        config['database']['database_description'] = db_info['description']
        config['database']['database_directory'] = paths['database_dir']
        
        # Update logging path to be database-specific
        safe_name = db_info['name'].lower().replace(' ', '-').replace('&', 'and')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '-_')
        log_dir = f"./logs/{db_id}-{safe_name}"
        os.makedirs(log_dir, exist_ok=True)
        config['logging']['file'] = f"{log_dir}/app.log"
        
        return config
    
    def resolve_database_id(self, requested_id: Optional[str] = None) -> str:
        """Resolve database ID from request, default, or error"""
        # If specific ID requested, validate it
        if requested_id:
            if self.validate_database_id(requested_id):
                return str(requested_id)
            else:
                raise ValueError(f"Invalid database ID: {requested_id}")
        
        # Use default database
        default_id = self.get_default_database_id()
        if default_id:
            return default_id
        
        # No default set
        available_ids = self.list_database_ids()
        if available_ids:
            raise ValueError(f"No default database set. Available IDs: {', '.join(available_ids)}")
        else:
            raise ValueError("No databases configured. Use manage_databases.py to add databases.")
    
    def print_database_summary(self, db_id: str):
        """Print summary of selected database"""
        db_info = self.get_database_info(db_id)
        if db_info:
            # Generate paths dynamically
            paths = self.generate_database_paths(db_id, db_info)
            
            default_marker = " [DEFAULT]" if db_id == self.get_default_database_id() else ""
            print(f"🗄️  Using Database: {db_id}{default_marker}")
            print(f"📝 Name: {db_info['name']}")
            print(f"📖 Description: {db_info['description'][:100]}{'...' if len(db_info['description']) > 100 else ''}")
            print(f"📁 Documents: {paths['document_folder']}")
            print()

def get_database_config(db_id: Optional[str] = None, 
                       registry_file: str = "database_registry.yaml",
                       base_config_file: str = "config.yaml") -> tuple[Dict, str]:
    """
    Convenience function to get database configuration
    Returns: (config_dict, resolved_db_id)
    """
    db_config = DatabaseConfig(registry_file, base_config_file)
    resolved_id = db_config.resolve_database_id(db_id)
    config = db_config.get_config_for_database(resolved_id)
    
    return config, resolved_id

def add_database_args(parser):
    """Add database selection arguments to argument parser"""
    parser.add_argument('--db-id', '--database-id', 
                       help='Database ID to use (4-digit number). Use manage_databases.py list to see available databases.')
    parser.add_argument('--list-databases', action='store_true',
                       help='List all available databases and exit')
    return parser

def handle_database_selection(args) -> Optional[str]:
    """Handle database selection from command line arguments"""
    if hasattr(args, 'list_databases') and args.list_databases:
        # List databases and exit
        try:
            db_config = DatabaseConfig()
            print("📂 Available Databases:")
            print("=" * 50)
            for db_id in db_config.list_database_ids():
                db_info = db_config.get_database_info(db_id)
                default_marker = " [DEFAULT]" if db_id == db_config.get_default_database_id() else ""
                print(f"🔹 {db_id}{default_marker}: {db_info['name']}")
                print(f"   {db_info['description'][:100]}{'...' if len(db_info['description']) > 100 else ''}")
            return None  # Signal to exit
        except Exception as e:
            print(f"❌ Error listing databases: {e}")
            return None
    
    # Return requested database ID (or None for default)
    return getattr(args, 'db_id', None)
