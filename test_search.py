#!/usr/bin/env python3
"""
Test script for search functionality
"""

import sys
import yaml
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_search():
    """Test search functionality"""
    print("Testing Search Functionality...")
    
    try:
        # Load config
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        print("✓ Configuration loaded successfully")
        
        # Import after path setup
        from src.database_manager import DatabaseManager
        
        # Initialize database manager
        db_manager = DatabaseManager(config)
        
        print("✓ Database manager initialized")
        
        # Test queries
        test_queries = [
            "machine learning python",
            "database optimization",
            "employee salary data",
            "vector database configuration"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Searching for: '{query}'")
            results = db_manager.search_similar_documents(query, top_k=3)
            
            if results:
                for i, result in enumerate(results):
                    similarity = result['similarity']
                    filename = result['metadata']['filename']
                    content_preview = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
                    
                    print(f"  {i+1}. {filename} (similarity: {similarity:.3f})")
                    print(f"     Preview: {content_preview}")
            else:
                print("  No results found")
        
        print("\n🎉 Search functionality test passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_search()
