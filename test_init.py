#!/usr/bin/env python3
"""
Test script for database initialization
"""

import sys
import os
import yaml
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_database_init():
    """Test database initialization"""
    print("Testing Database Initialization...")
    
    try:
        # Load config
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        print("✓ Configuration loaded successfully")
        
        # Import after path setup
        from src.initialize_database import initialize_database
        
        # Initialize database
        db_manager = initialize_database(config)
        
        print("✓ Database manager initialized")
        
        # Get stats
        stats = db_manager.get_database_stats()
        
        print("✓ Database stats retrieved:")
        print(f"  - Documents: {stats['document_count']}")
        print(f"  - Chunks: {stats['chunk_count']}")
        print(f"  - Vectors: {stats['vector_count']}")
        print(f"  - Total file size: {stats['total_file_size']} bytes")
        
        print("\n🎉 Database initialization test passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_database_init()
