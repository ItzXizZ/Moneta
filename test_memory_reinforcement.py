import sys
import os
import time

# Add the memory-app backend to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'memory-app', 'backend'))

# Import MemoryManager
from memory_manager import MemoryManager

def test_memory_reinforcement():
    print("🧪 Testing Dynamic Memory Reinforcement System\n")
    
    # Initialize memory manager
    memory_manager = MemoryManager()
    
    # Test query that should consistently find the same memories
    test_query = "Am I smart?"
    
    print("📋 Initial memory scores:")
    all_memories = memory_manager.get_all_memories()
    for i, mem in enumerate(all_memories['memories'], 1):
        print(f"  {i}. '{mem['content']}' (score: {mem['score']})")
    print()
    
    # Perform multiple searches to see reinforcement in action
    num_searches = 5
    
    for search_round in range(1, num_searches + 1):
        print(f"🔍 Search Round {search_round}: '{test_query}'")
        
        # Search memories (this will trigger reinforcement)
        search_results = memory_manager.search_memories(test_query, top_k=3, min_relevance=0.2)
        
        if search_results:
            print(f"   Found {len(search_results)} memories:")
            for j, result in enumerate(search_results, 1):
                content = result['memory']['content']
                relevance = result['relevance_score']
                score = result['memory']['score']
                print(f"      {j}. '{content}' (relevance: {relevance:.3f}, score: {score})")
        else:
            print("   No memories found!")
        
        # Show updated scores after reinforcement
        print("   📊 Updated scores after reinforcement:")
        updated_memories = memory_manager.get_all_memories()
        for mem in updated_memories['memories']:
            if any(mem['id'] == result['memory']['id'] for result in search_results):
                print(f"      → '{mem['content']}': {mem['score']}")
        
        print("-" * 70)
        time.sleep(1)  # Brief pause between searches
    
    # Final comparison
    print("📈 Final Score Comparison:")
    print("Memory Content | Initial → Final | Change")
    print("-" * 50)
    
    final_memories = memory_manager.get_all_memories()
    initial_scores = {mem['content']: mem['score'] for mem in all_memories['memories']}
    
    for mem in final_memories['memories']:
        content = mem['content']
        initial_score = initial_scores.get(content, 0)
        final_score = mem['score']
        change = final_score - initial_score
        
        if change > 0:
            print(f"'{content[:30]}...' | {initial_score:.2f} → {final_score:.2f} | +{change:.2f} ⬆️")
        else:
            print(f"'{content[:30]}...' | {initial_score:.2f} → {final_score:.2f} | {change:.2f}")
    
    print("\n🎯 Key Observations:")
    print("1. Memories that were recalled multiple times should have higher scores")
    print("2. Connected memories should also get reinforced (network effect)")
    print("3. The most relevant memories should show the biggest score increases")

def test_different_queries():
    print("\n🔄 Testing Different Query Types for Reinforcement Patterns\n")
    
    memory_manager = MemoryManager()
    
    # Different types of queries
    test_queries = [
        ("intelligence", ["Am I smart?", "What's my IQ?", "Tell me about my intelligence"]),
        ("food", ["What food do I like?", "pizza", "What's my favorite cuisine?"]),
    ]
    
    for category, queries in test_queries:
        print(f"📂 Testing {category.upper()} queries:")
        
        for query in queries:
            print(f"   🔍 '{query}'")
            results = memory_manager.search_memories(query, top_k=2, min_relevance=0.2)
            for result in results:
                print(f"      → '{result['memory']['content']}' (score: {result['memory']['score']:.2f})")
        
        print()

if __name__ == "__main__":
    print("🧠 Dynamic Memory Reinforcement Test Suite")
    print("=" * 60)
    
    test_memory_reinforcement()
    test_different_queries()
    
    print("\n🏁 Reinforcement testing completed!")
    print("💡 The system now learns which memories are most important based on usage!") 