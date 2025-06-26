#!/usr/bin/env python3
"""
Build Theological Concept Index
Script to create theological concept indexes for existing documents
"""

import sys
import os
import logging
import time
import yaml
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from theological_indexer import TheologicalIndexer

def load_config():
    """Load configuration from YAML file"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('theological_indexing.log')
        ]
    )

def main():
    """Main function to build theological concept index"""
    print("Building Theological Concept Index")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        config = load_config()
        metadata_db_path = config['database']['metadata_db_path']
        
        # Check if metadata database exists
        if not os.path.exists(metadata_db_path):
            print(f"Error: Metadata database not found at {metadata_db_path}")
            print("Please run the document processing pipeline first.")
            return 1
        
        # Initialize theological indexer
        print("Initializing theological indexer...")
        indexer = TheologicalIndexer(metadata_db_path)
        
        # Get initial statistics
        print("\nInitial index state:")
        stats = indexer.get_concept_statistics()
        print(f"  Total entries: {stats.get('total_entries', 0)}")
        print(f"  Unique concepts: {stats.get('unique_concepts', 0)}")
        
        # Ask user for confirmation
        response = input("\nProceed with rebuilding the theological concept index? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Index building cancelled.")
            return 0
        
        # Rebuild index
        print("\nRebuilding theological concept index...")
        start_time = time.time()
        
        success = indexer.rebuild_index_for_all_documents()
        
        end_time = time.time()
        duration = end_time - start_time
        
        if success:
            print(f"\n✓ Index rebuilt successfully in {duration:.2f} seconds")
        else:
            print(f"\n✗ Index rebuild completed with some errors in {duration:.2f} seconds")
            print("Check the log file for details: theological_indexing.log")
        
        # Show final statistics
        print("\nFinal index state:")
        final_stats = indexer.get_concept_statistics()
        print(f"  Total entries: {final_stats.get('total_entries', 0)}")
        print(f"  Unique concepts: {final_stats.get('unique_concepts', 0)}")
        
        # Show top concepts
        if final_stats.get('top_concepts'):
            print("\nTop theological concepts found:")
            for i, concept_info in enumerate(final_stats['top_concepts'][:10], 1):
                print(f"  {i:2d}. {concept_info['concept']:15} "
                      f"({concept_info['document_count']} docs, "
                      f"{concept_info['total_frequency']} occurrences)")
        
        print(f"\nTheological concept index is ready!")
        print("You can now use concept-based queries for faster document retrieval.")
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Failed to build theological index: {e}")
        print(f"\nError: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
