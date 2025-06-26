#!/usr/bin/env python3
"""
Scripture Index Rebuilder
Rebuilds the scripture reference index for all documents in the database
"""

import os
import sys
import logging
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scripture_indexer import ScriptureIndexer

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/scripture_rebuild.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main function to rebuild scripture index"""
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting scripture index rebuild...")
    start_time = datetime.now()
    
    try:
        # Initialize scripture indexer
        indexer = ScriptureIndexer('data/metadata.db')
        
        # Get statistics before rebuild
        logger.info("Getting statistics before rebuild...")
        stats_before = indexer.get_scripture_statistics()
        logger.info(f"Before rebuild - Total references: {stats_before.get('total_references', 0)}, "
                   f"Unique references: {stats_before.get('unique_references', 0)}")
        
        # Rebuild the index
        success = indexer.rebuild_scripture_index_for_all_documents()
        
        if success:
            logger.info("Scripture index rebuild completed successfully!")
            
            # Get statistics after rebuild
            stats_after = indexer.get_scripture_statistics()
            logger.info(f"After rebuild - Total references: {stats_after.get('total_references', 0)}, "
                       f"Unique references: {stats_after.get('unique_references', 0)}")
            
            # Show top scripture references
            if stats_after.get('top_scriptures'):
                logger.info("Top scripture references:")
                for i, ref_data in enumerate(stats_after['top_scriptures'][:10], 1):
                    logger.info(f"  {i}. {ref_data['reference']} - {ref_data['document_count']} documents")
        else:
            logger.error("Scripture index rebuild failed!")
            return 1
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Scripture index rebuild completed in {duration}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to rebuild scripture index: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
