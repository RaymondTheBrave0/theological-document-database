# Initialization functions for the document database

import os
import logging
from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)

def initialize_database(config):
    """Initializes the vector and metadata databases using DatabaseManager."""
    try:
        # Create necessary directories
        os.makedirs(config['database']['vector_db_path'], exist_ok=True)
        os.makedirs(os.path.dirname(config['database']['metadata_db_path']), exist_ok=True)
        os.makedirs(config['output']['default_output_folder'], exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # Initialize DatabaseManager (this will create all necessary tables and connections)
        db_manager = DatabaseManager(config)
        
        # Get initial database stats
        stats = db_manager.get_database_stats()
        logger.info(f"Database initialized successfully")
        logger.info(f"Current stats: {stats['document_count']} documents, {stats['chunk_count']} chunks")
        
        return db_manager
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
