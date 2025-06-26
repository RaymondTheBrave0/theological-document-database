#!/usr/bin/env python3
"""
Simple test for Ollama integration
"""

import sys
import yaml
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_ollama():
    """Test Ollama integration"""
    print("Testing Ollama Integration...")
    
    try:
        # Load config
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        print("✓ Configuration loaded successfully")
        
        # Import after path setup
        from src.database_manager import DatabaseManager
        from src.query_engine import QueryEngine
        
        # Initialize database manager
        db_manager = DatabaseManager(config)
        print("✓ Database manager initialized")
        
        # Initialize query engine
        query_engine = QueryEngine(config, db_manager)
        print("✓ Query engine initialized")
        
        # Test simple query without LLM first
        print("\n🔍 Testing vector search only...")
        response = query_engine.query("machine learning", use_llm=False)
        
        print(f"Search results: {len(response['search_results'])}")
        print(f"Execution time: {response['execution_time']:.3f} seconds")
        
        # Test with LLM if vector search works
        if response['search_results']:
            print("\n🔍 Testing with LLM response...")
            response_llm = query_engine.query("What is machine learning?", use_llm=True)
            
            if response_llm['llm_response']:
                print("✓ LLM response generated successfully")
                print(f"Response length: {len(response_llm['llm_response'])} characters")
            else:
                print("❌ No LLM response generated")
        
        print("\n🎉 Ollama integration test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_ollama()
