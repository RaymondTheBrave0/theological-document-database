#!/usr/bin/env python3
"""
Process New Documents
Processes new documents added to the document database and rebuilds indexes.
This script handles adding new files to your document database with full preprocessing,
embedding generation, and indexing.
"""

import os
import sys
import yaml
import logging
import argparse
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.initialize_database import initialize_database
from src.document_processor import DocumentProcessor
from src.theological_indexer import TheologicalIndexer
from src.scripture_indexer import ScriptureIndexer

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/document_processing.log'),
            logging.StreamHandler()
        ]
    )

def clear_existing_data(db_manager):
    """Clear existing document data and indexes"""
    try:
        import sqlite3
        
        # Clear vector database - get all IDs first
        try:
            all_data = db_manager.collection.get()
            if all_data['ids']:
                db_manager.collection.delete(ids=all_data['ids'])
                logging.info(f"Cleared {len(all_data['ids'])} vectors from vector database")
        except Exception as ve:
            logging.warning(f"Vector database might be empty: {ve}")
        
        # Clear metadata database
        conn = sqlite3.connect(db_manager.metadata_db_path)
        cursor = conn.cursor()
        
        # Clear tables
        cursor.execute("DELETE FROM document_chunks")
        cursor.execute("DELETE FROM documents")
        cursor.execute("DELETE FROM theological_concept_index")
        cursor.execute("DELETE FROM scripture_index")
        cursor.execute("DELETE FROM query_history")
        
        conn.commit()
        conn.close()
        
        logging.info("Cleared existing data successfully")
        return True
        
    except Exception as e:
        logging.error(f"Failed to clear existing data: {e}")
        return False

def main():
    """Main function to process new documents with preprocessing"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process new documents with preprocessing')
    parser.add_argument('--clear', action='store_true', 
                       help='Clear existing data and process all documents from scratch')
    parser.add_argument('--force', action='store_true',
                       help='Force processing without confirmation')
    args = parser.parse_args()
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting document processing with preprocessing...")
    start_time = datetime.now()
    
    try:
        # Load configuration
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Initialize database manager
        db_manager = initialize_database(config)
        
        # Handle clearing existing data
        should_clear = args.clear
        if not args.force and not should_clear:
            response = input("Do you want to clear existing data and process all documents from scratch? (y/N): ")
            should_clear = response.lower() in ['y', 'yes']
        
        if should_clear:
            logger.info("Clearing existing data...")
            if not clear_existing_data(db_manager):
                logger.error("Failed to clear existing data. Exiting.")
                return 1
        
        # Initialize document processor with preprocessing
        doc_processor = DocumentProcessor(config, db_manager)
        logger.info("Document processor initialized with preprocessing enabled")
        
        # Process documents directory
        documents_dir = config['document_processing']['input_folder']
        logger.info(f"Processing documents from: {documents_dir}")
        
        # Get initial stats
        initial_stats = db_manager.get_database_stats()
        logger.info(f"Initial stats - Documents: {initial_stats['document_count']}, Chunks: {initial_stats['chunk_count']}")
        
        # Process all documents
        doc_processor.process_directory(documents_dir)
        
        # Get final stats
        final_stats = db_manager.get_database_stats()
        logger.info(f"Final stats - Documents: {final_stats['document_count']}, Chunks: {final_stats['chunk_count']}")
        
        # Rebuild theological concept index
        logger.info("Rebuilding theological concept index...")
        theological_indexer = TheologicalIndexer(db_manager.metadata_db_path)
        theological_success = theological_indexer.rebuild_index_for_all_documents()
        
        if theological_success:
            # Get theological stats
            theological_stats = theological_indexer.get_concept_statistics()
            logger.info(f"Theological index rebuilt - Total concepts: {theological_stats.get('total_entries', 0)}, "
                       f"Unique concepts: {theological_stats.get('unique_concepts', 0)}")
        else:
            logger.warning("Theological index rebuild failed")
        
        # Rebuild scripture reference index
        logger.info("Rebuilding scripture reference index...")
        scripture_indexer = ScriptureIndexer(db_manager.metadata_db_path)
        scripture_success = scripture_indexer.rebuild_scripture_index_for_all_documents()
        
        if scripture_success:
            # Get scripture stats
            scripture_stats = scripture_indexer.get_scripture_statistics()
            logger.info(f"Scripture index rebuilt - Total references: {scripture_stats.get('total_references', 0)}, "
                       f"Unique references: {scripture_stats.get('unique_references', 0)}")
        else:
            logger.warning("Scripture index rebuild failed")
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Document processing completed in {duration}")
        
        # Show summary
        print("\n" + "="*60)
        print("DOCUMENT PROCESSING SUMMARY")
        print("="*60)
        print(f"Documents processed: {final_stats['document_count']}")
        print(f"Text chunks created: {final_stats['chunk_count']}")
        print(f"Vector embeddings: {final_stats['vector_count']}")
        
        if theological_success:
            print(f"Theological concepts indexed: {theological_stats.get('total_entries', 0)}")
            print(f"Unique theological concepts: {theological_stats.get('unique_concepts', 0)}")
        
        if scripture_success:
            print(f"Scripture references indexed: {scripture_stats.get('total_references', 0)}")
            print(f"Unique scripture references: {scripture_stats.get('unique_references', 0)}")
        
        print(f"Total processing time: {duration}")
        print("\nAll documents have been processed with full preprocessing and indexing!")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to process documents: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
