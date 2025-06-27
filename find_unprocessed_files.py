#!/usr/bin/env python3
"""
Script to find files that are truly not processed by comparing the filesystem 
with the database records.
"""

import os
import sys
import yaml
import logging
import sqlite3
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.initialize_database import initialize_database

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)

def get_processed_files_from_db(metadata_db_path):
    """Get list of processed files from the database"""
    processed_files = set()
    try:
        conn = sqlite3.connect(metadata_db_path)
        cursor = conn.cursor()
        
        # Get all file paths from the documents table
        cursor.execute("SELECT filepath FROM documents")
        rows = cursor.fetchall()
        
        for row in rows:
            file_path = row[0]
            # Normalize the path - convert to absolute path
            abs_path = os.path.abspath(file_path)
            processed_files.add(abs_path)
            
        conn.close()
        return processed_files
        
    except Exception as e:
        logging.error(f"Error reading database: {e}")
        return set()

def get_files_in_directory(directory):
    """Get all supported files in the documents directory"""
    supported_extensions = ['.txt', '.pdf', '.doc', '.docx', '.csv']
    all_files = set()
    
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if any(file_path.lower().endswith(ext) for ext in supported_extensions):
                abs_path = os.path.abspath(file_path)
                all_files.add(abs_path)
    
    return all_files

def main():
    logger = setup_logging()
    logger.info("Finding truly unprocessed files...")
    
    # Load configuration
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Initialize database to get the metadata database path
    try:
        db_manager = initialize_database(config)
        metadata_db_path = db_manager.metadata_db_path
        logger.info(f"Database initialized, metadata DB: {metadata_db_path}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)
    
    # Get processed files from database
    processed_files = get_processed_files_from_db(metadata_db_path)
    logger.info(f"Found {len(processed_files)} processed files in database")
    
    # Get all files in documents directory
    documents_dir = config['document_processing']['input_folder']
    all_files = get_files_in_directory(documents_dir)
    logger.info(f"Found {len(all_files)} total files in {documents_dir}")
    
    # Find unprocessed files
    unprocessed_files = all_files - processed_files
    
    logger.info(f"Found {len(unprocessed_files)} unprocessed files")
    
    if unprocessed_files:
        print("\nUnprocessed Files:")
        print("="*50)
        
        # Convert back to relative paths for readability
        unprocessed_relative = []
        for file_path in sorted(unprocessed_files):
            relative_path = os.path.relpath(file_path)
            unprocessed_relative.append(relative_path)
            print(relative_path)
        
        # Save to file
        output_file = './truly_unprocessed_files.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            for file_path in unprocessed_relative:
                f.write(file_path + '\n')
        
        logger.info(f"Saved list of unprocessed files to {output_file}")
        
        # Show some sample processed files for comparison
        print("\nSample of processed files (first 10):")
        print("-" * 50)
        for i, file_path in enumerate(sorted(processed_files)):
            if i >= 10:
                break
            relative_path = os.path.relpath(file_path)
            print(relative_path)
            
    else:
        print("\nAll files have been processed!")
        logger.info("No unprocessed files found - all documents are in the database")
        
        # Double check by showing some stats
        stats = db_manager.get_database_stats()
        print(f"\nDatabase stats:")
        print(f"- Document count: {stats.get('document_count', 'N/A')}")
        print(f"- Chunk count: {stats.get('chunk_count', 'N/A')}")
        print(f"- Vector count: {stats.get('vector_count', 'N/A')}")

if __name__ == "__main__":
    main()
