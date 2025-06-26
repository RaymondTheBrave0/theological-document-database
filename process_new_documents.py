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
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/document_processing.log'),
            logging.StreamHandler()
        ]
    )

def get_new_documents_for_indexing(db_manager, documents_dir):
    """Get the current maximum document ID to track new additions"""
    try:
        import sqlite3
        conn = sqlite3.connect(db_manager.metadata_db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(id) FROM documents")
        result = cursor.fetchone()
        max_id = result[0] if result[0] is not None else 0
        
        conn.close()
        return max_id
        
    except Exception as e:
        logging.error(f"Failed to get current document IDs: {e}")
        return 0

def get_newly_added_documents(db_manager, previous_max_id):
    """Get documents that were added after the previous maximum ID"""
    try:
        import sqlite3
        conn = sqlite3.connect(db_manager.metadata_db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, filename, filepath FROM documents WHERE id > ? ORDER BY id",
            (previous_max_id,)
        )
        new_documents = cursor.fetchall()
        
        conn.close()
        
        return [{
            'document_id': doc[0],
            'filename': doc[1],
            'filepath': doc[2]
        } for doc in new_documents]
        
    except Exception as e:
        logging.error(f"Failed to get newly added documents: {e}")
        return []

def index_specific_documents(indexer, documents, index_type):
    """Index specific documents using the appropriate indexer"""
    logger = logging.getLogger(__name__)
    success_count = 0
    
    try:
        import sqlite3
        conn = sqlite3.connect(indexer.metadata_db_path)
        cursor = conn.cursor()
        
        for doc in documents:
            try:
                doc_id = doc['document_id']
                filename = doc['filename']
                
                # Get document content from chunks
                cursor.execute(
                    "SELECT chunk_text FROM document_chunks WHERE document_id = ? ORDER BY chunk_index",
                    (doc_id,)
                )
                chunks = cursor.fetchall()
                
                if chunks:
                    # Combine all chunks into full document content
                    content = '\n'.join(chunk[0] for chunk in chunks if chunk[0])
                    
                    # Index the document based on type
                    if index_type == "theological":
                        success = indexer.index_document(doc_id, content, filename)
                    elif index_type == "scripture":
                        success = indexer.index_document_scriptures(doc_id, content, filename)
                    else:
                        logger.error(f"Unknown index type: {index_type}")
                        success = False
                    
                    if success:
                        success_count += 1
                    else:
                        logger.warning(f"Failed to index {filename} for {index_type}")
                else:
                    logger.warning(f"No chunks found for document: {filename}")
                    
            except Exception as e:
                logger.error(f"Failed to index document {doc.get('filename', 'unknown')}: {e}")
        
        conn.close()
        
        # Silent success
        return success_count == len(documents)
        
    except Exception as e:
        logger.error(f"Failed to index documents for {index_type}: {e}")
        return False

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
            if not clear_existing_data(db_manager):
                logger.error("Failed to clear existing data. Exiting.")
                return 1
        
        # Initialize document processor with preprocessing
        doc_processor = DocumentProcessor(config, db_manager)
        
        # Process documents directory
        documents_dir = config['document_processing']['input_folder']
        
        # Get initial stats
        initial_stats = db_manager.get_database_stats()
        
        # Get list of new documents to process
        new_document_ids = get_new_documents_for_indexing(db_manager, documents_dir)
        
        # Process all documents
        doc_processor.process_directory(documents_dir)
        
        # Get final stats
        final_stats = db_manager.get_database_stats()
        
        # Get the actual newly added documents after processing
        newly_added_documents = get_newly_added_documents(db_manager, new_document_ids)
        
        # Only index newly processed documents (not all documents)
        theological_success = True
        scripture_success = True
        theological_stats = {}
        scripture_stats = {}
        
        if newly_added_documents:
            # Initialize indexers
            theological_indexer = TheologicalIndexer(db_manager.metadata_db_path)
            scripture_indexer = ScriptureIndexer(db_manager.metadata_db_path)
            
            # Index only the newly processed documents
            theological_success = index_specific_documents(theological_indexer, newly_added_documents, "theological")
            scripture_success = index_specific_documents(scripture_indexer, newly_added_documents, "scripture")
            
            if theological_success:
                # Get theological stats
                theological_stats = theological_indexer.get_concept_statistics()
            else:
                logger.warning("Theological indexing of new documents failed")
            
            if scripture_success:
                # Get scripture stats
                scripture_stats = scripture_indexer.get_scripture_statistics()
            else:
                logger.warning("Scripture indexing of new documents failed")
        else:
            print("No new documents to index")
        
        end_time = datetime.now()
        duration = end_time - start_time
        
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
