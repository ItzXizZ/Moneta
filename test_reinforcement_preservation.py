#!/usr/bin/env python3
"""
Test script to verify that reinforcement scores are preserved
and not overwritten by the connection-based scoring system.
"""

import requests
import json
import time

def test_reinforcement_preservation():
    """Test that reinforcement scores are preserved"""
    
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Reinforcement Score Preservation")
    print("=" * 60)
    
    # 1. Add some test memories
    test_memories = [
        "Machine learning is a subset of artificial intelligence",
        "Deep learning uses neural networks with multiple layers",
        "Natural language processing helps computers understand text",
        "Computer vision enables machines to interpret images",
        "Reinforcement learning learns through trial and error"
    ]
    
    print("📝 Adding test memories...")
    memory_ids = []
    
    for content in test_memories:
        response = requests.post(f"{base_url}/memories", json={
            "content": content,
            "tags": ["test", "ai"]
        })
        
        if response.status_code == 201:
            memory_data = response.json()
            memory_ids.append(memory_data['id'])
            print(f"  ✅ Added: {content[:40]}... (Score: {memory_data.get('score', 0):.2f})")
    
    print(f"\n📊 Added {len(memory_ids)} test memories")
    
    # 2. Get initial scores
    print("\n🔍 Getting initial scores...")
    response = requests.get(f"{base_url}/score-updates")
    if response.status_code == 200:
        data = response.json()
        initial_scores = {update['id']: update['score'] for update in data['updates']}
        print("  📈 Initial scores:")
        for mem_id, score in initial_scores.items():
            print(f"    • {mem_id}: {score:.2f}")
    
    # 3. Trigger reinforcement by searching
    print("\n🔍 Triggering reinforcement through searches...")
    search_queries = ["machine learning", "neural networks", "artificial intelligence"]
    
    for query in search_queries:
        print(f"  🔎 Searching for: '{query}'")
        response = requests.get(f"{base_url}/search/{query}")
        if response.status_code == 200:
            results = response.json()
            print(f"    📊 Found {len(results)} relevant memories")
            
            # Show top results
            for i, result in enumerate(results[:2]):
                memory = result['memory']
                print(f"      {i+1}. {memory['content'][:40]}... (Score: {memory.get('score', 0):.2f})")
        
        time.sleep(1)  # Small delay between searches
    
    # 4. Check scores after reinforcement
    print("\n📈 Checking scores after reinforcement...")
    time.sleep(2)  # Wait for reinforcement to complete
    
    response = requests.get(f"{base_url}/score-updates")
    if response.status_code == 200:
        data = response.json()
        reinforced_scores = {update['id']: update['score'] for update in data['updates']}
        print("  📊 Scores after reinforcement:")
        for mem_id, score in reinforced_scores.items():
            initial_score = initial_scores.get(mem_id, 0)
            change = score - initial_score
            print(f"    • {mem_id}: {score:.2f} (was {initial_score:.2f}, change: {change:+.2f})")
    
    # 5. Trigger network refresh (this used to overwrite scores)
    print("\n🔄 Triggering network refresh (should preserve reinforcement)...")
    response = requests.get(f"{base_url}/memory-network")
    if response.status_code == 200:
        print("  ✅ Network refresh completed")
    
    # 6. Check scores after network refresh
    print("\n📈 Checking scores after network refresh...")
    response = requests.get(f"{base_url}/score-updates")
    if response.status_code == 200:
        data = response.json()
        final_scores = {update['id']: update['score'] for update in data['updates']}
        print("  📊 Scores after network refresh:")
        
        preserved_count = 0
        for mem_id, score in final_scores.items():
            reinforced_score = reinforced_scores.get(mem_id, 0)
            if abs(score - reinforced_score) < 0.01:
                status = "✅ PRESERVED"
                preserved_count += 1
            else:
                status = f"❌ CHANGED (was {reinforced_score:.2f})"
            print(f"    • {mem_id}: {score:.2f} - {status}")
        
        print(f"\n📊 Summary: {preserved_count}/{len(final_scores)} scores preserved")
        
        if preserved_count == len(final_scores):
            print("🎉 SUCCESS: All reinforcement scores were preserved!")
        else:
            print("⚠️  WARNING: Some scores were overwritten")
    
    # 7. Test manual recalculation
    print("\n🔄 Testing manual score recalculation...")
    response = requests.post(f"{base_url}/recalculate-scores", json={'threshold': 0.35})
    if response.status_code == 200:
        print("  ✅ Manual recalculation completed")
        
        # Check scores after manual recalculation
        response = requests.get(f"{base_url}/score-updates")
        if response.status_code == 200:
            data = response.json()
            recalculated_scores = {update['id']: update['score'] for update in data['updates']}
            print("  📊 Scores after manual recalculation:")
            for mem_id, score in recalculated_scores.items():
                final_score = final_scores.get(mem_id, 0)
                change = score - final_score
                print(f"    • {mem_id}: {score:.2f} (change: {change:+.2f})")
    
    print("\n✅ Reinforcement preservation test completed!")
    print("\n💡 Key findings:")
    print("  • Reinforcement scores should be preserved during normal operations")
    print("  • Manual recalculation will reset all scores")
    print("  • Live score updates should now work properly")

if __name__ == "__main__":
    try:
        test_reinforcement_preservation()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the server.")
        print("   Make sure the MemoryOS backend is running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Error: {e}") 