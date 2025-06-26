#!/usr/bin/env python3
"""
Model Speed Comparison Tool
"""

import sys
import yaml
import time
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_model_speed(model_name):
    """Test query speed with specific model"""
    print(f"\n🧪 Testing {model_name}...")
    
    try:
        # Load config
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Override model
        config['ollama']['model'] = model_name
        
        # Import after path setup
        from src.database_manager import DatabaseManager
        from src.query_engine import QueryEngine
        
        # Initialize components
        db_manager = DatabaseManager(config)
        query_engine = QueryEngine(config, db_manager)
        
        # Test query
        test_query = "What are the key features of the document database system?"
        
        start_time = time.time()
        response = query_engine.query(test_query, use_llm=True)
        execution_time = time.time() - start_time
        
        print(f"✓ Model: {model_name}")
        print(f"✓ Execution time: {execution_time:.3f} seconds")
        print(f"✓ Response length: {len(response['llm_response'])} characters")
        print(f"✓ Search results: {len(response['search_results'])}")
        
        return execution_time, len(response['llm_response'])
        
    except Exception as e:
        print(f"❌ Error with {model_name}: {e}")
        return None, None

def main():
    """Compare model speeds"""
    print("🏃‍♂️ Model Speed Comparison")
    print("=" * 50)
    
    # Test different models
    models = [
        "llama3.2:3b",      # Fast
        "mistral:latest",   # Balanced  
        "mixtral:latest"    # High quality
    ]
    
    results = {}
    
    for model in models:
        exec_time, response_length = test_model_speed(model)
        if exec_time:
            results[model] = {
                'time': exec_time,
                'response_length': response_length
            }
    
    # Display comparison
    print("\n📊 SPEED COMPARISON RESULTS")
    print("=" * 50)
    
    if results:
        fastest_time = min(results.values(), key=lambda x: x['time'])['time']
        
        for model, data in results.items():
            speed_ratio = data['time'] / fastest_time
            print(f"\n🤖 {model}")
            print(f"   ⏱️  Time: {data['time']:.3f}s ({speed_ratio:.1f}x slower than fastest)")
            print(f"   📝 Response: {data['response_length']} characters")
            
            if data['time'] == fastest_time:
                print("   🏆 FASTEST MODEL")
    
    print("\n💡 RECOMMENDATIONS:")
    print("• llama3.2:3b - Best for speed and quick responses")
    print("• mistral:latest - Good balance of speed and quality") 
    print("• mixtral:latest - Best for complex analysis (slower)")

if __name__ == "__main__":
    main()
