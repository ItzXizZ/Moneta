import sys
import os

# Add the memory-app backend to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'memory-app', 'backend'))

# Import MemoryManager
from memory_manager import MemoryManager

def test_memory_search_direct():
    print("🧪 Testing Memory Search Directly\n")
    
    # Initialize memory manager
    memory_manager = MemoryManager()
    
    # Test prompts that should match different memories
    test_prompts = [
        "Tell me about my intelligence",  # Should match "I am very smart", "I am a genius", "IQ of 145"
        "What food do I like?",          # Should match "I love pizza", "I love Italian Food"
        "Am I smart?",                   # Should match intelligence-related memories
        "What's my favorite cuisine?",   # Should match Italian food/pizza
        "Do I have a high IQ?",         # Should match IQ memory specifically
        "pizza",                        # Direct match
        "genius",                       # Direct match
    ]
    
    print("📋 Available memories:")
    all_memories = memory_manager.get_all_memories()
    for i, mem in enumerate(all_memories['memories'], 1):
        print(f"  {i}. '{mem['content']}' (score: {mem['score']})")
    print()
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"🔍 Test {i}: '{prompt}'")
        
        try:
            # Search memories with lower threshold for testing
            search_results = memory_manager.search_memories(prompt, top_k=5, min_relevance=0.1)
            
            if search_results:
                print(f"✅ Found {len(search_results)} relevant memories:")
                for j, result in enumerate(search_results, 1):
                    print(f"   {j}. '{result['memory']['content']}'")
                    print(f"      Relevance: {result['relevance_score']:.3f}, Final: {result['final_score']:.3f}")
            else:
                print("❌ No memories found!")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 60)

if __name__ == "__main__":
    test_memory_search_direct() 