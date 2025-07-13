#!/usr/bin/env python3
"""
Test script for live score updates in MemoryOS
This script demonstrates how scores change in real-time and how the visualization updates.
"""

import requests
import json
import time
import random

def test_live_score_updates():
    """Test the live score update functionality"""
    
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Live Score Updates")
    print("=" * 50)
    
    # 1. Add some test memories
    test_memories = [
        "Python is a versatile programming language",
        "Machine learning uses algorithms to find patterns in data",
        "Artificial intelligence mimics human cognitive functions",
        "Data science combines statistics and programming",
        "Neural networks are inspired by biological brains",
        "Deep learning uses multiple layers of neural networks",
        "Natural language processing helps computers understand text",
        "Computer vision enables machines to interpret images",
        "Reinforcement learning learns through trial and error",
        "Big data refers to large, complex datasets"
    ]
    
    print("📝 Adding test memories...")
    memory_ids = []
    
    for i, content in enumerate(test_memories):
        response = requests.post(f"{base_url}/memories", json={
            "content": content,
            "tags": ["test", f"category_{i % 3}"]
        })
        
        if response.status_code == 201:
            memory_data = response.json()
            memory_ids.append(memory_data['id'])
            print(f"  ✅ Added: {content[:30]}... (Score: {memory_data.get('score', 0):.2f})")
        else:
            print(f"  ❌ Failed to add: {content[:30]}...")
    
    print(f"\n📊 Added {len(memory_ids)} test memories")
    
    # 2. Check initial scores
    print("\n🔍 Checking initial scores...")
    response = requests.get(f"{base_url}/score-updates")
    if response.status_code == 200:
        data = response.json()
        print(f"  📈 Found {len(data['updates'])} memories with scores:")
        for update in data['updates'][:5]:  # Show first 5
            print(f"    • {update['content'][:40]}... (Score: {update['score']:.2f})")
    
    # 3. Trigger score changes by searching (this will reinforce memories)
    print("\n🔍 Triggering score changes through searches...")
    search_queries = [
        "machine learning",
        "neural networks", 
        "data science",
        "artificial intelligence",
        "programming"
    ]
    
    for query in search_queries:
        print(f"  🔎 Searching for: '{query}'")
        response = requests.get(f"{base_url}/search/{query}")
        if response.status_code == 200:
            results = response.json()
            print(f"    📊 Found {len(results)} relevant memories")
            
            # Show top results
            for i, result in enumerate(results[:3]):
                memory = result['memory']
                print(f"      {i+1}. {memory['content'][:40]}... (Score: {memory.get('score', 0):.2f})")
        
        time.sleep(1)  # Small delay between searches
    
    # 4. Check updated scores
    print("\n📈 Checking updated scores after reinforcement...")
    time.sleep(2)  # Wait for reinforcement to complete
    
    response = requests.get(f"{base_url}/score-updates")
    if response.status_code == 200:
        data = response.json()
        print(f"  📊 Current scores for {len(data['updates'])} memories:")
        
        # Sort by score to show highest scoring memories
        sorted_updates = sorted(data['updates'], key=lambda x: x['score'], reverse=True)
        
        for i, update in enumerate(sorted_updates[:5]):
            print(f"    {i+1}. {update['content'][:40]}... (Score: {update['score']:.2f})")
    
    # 5. Demonstrate continuous monitoring
    print("\n🔄 Demonstrating continuous score monitoring...")
    print("  💡 Enable 'Live Score Updates' in the UI to see real-time changes")
    print("  📊 Scores will update every 3 seconds when enabled")
    print("  🎯 Node sizes and colors will animate smoothly")
    
    # 6. Add one more memory to trigger more changes
    print("\n➕ Adding one more memory to trigger additional score changes...")
    response = requests.post(f"{base_url}/memories", json={
        "content": "Quantum computing uses quantum mechanics for computation",
        "tags": ["test", "quantum", "computing"]
    })
    
    if response.status_code == 201:
        new_memory = response.json()
        print(f"  ✅ Added: {new_memory['content']} (Score: {new_memory.get('score', 0):.2f})")
        
        # Wait and check scores again
        time.sleep(3)
        response = requests.get(f"{base_url}/score-updates")
        if response.status_code == 200:
            data = response.json()
            print(f"  📊 Scores after adding new memory:")
            sorted_updates = sorted(data['updates'], key=lambda x: x['score'], reverse=True)
            for i, update in enumerate(sorted_updates[:3]):
                print(f"    {i+1}. {update['content'][:40]}... (Score: {update['score']:.2f})")
    
    print("\n✅ Live score update test completed!")
    print("\n🎯 To see live updates in action:")
    print("  1. Open the Memory Network visualization")
    print("  2. Click '📊 Enable Live Scores' button")
    print("  3. Watch as node sizes and colors change in real-time")
    print("  4. Try adding new memories or searching to trigger score changes")

def cleanup_test_memories():
    """Clean up test memories (optional)"""
    print("\n🧹 Cleaning up test memories...")
    
    base_url = "http://localhost:5000"
    
    # Get all memories
    response = requests.get(f"{base_url}/memories")
    if response.status_code == 200:
        data = response.json()
        memories = data.get('memories', [])
        
        # Delete memories with test tags
        deleted_count = 0
        for memory in memories:
            tags = memory.get('tags', [])
            if 'test' in tags:
                response = requests.delete(f"{base_url}/memories/{memory['id']}")
                if response.status_code == 200:
                    deleted_count += 1
                    print(f"  🗑️ Deleted: {memory['content'][:30]}...")
        
        print(f"  ✅ Deleted {deleted_count} test memories")

if __name__ == "__main__":
    try:
        test_live_score_updates()
        
        # Uncomment the next line to clean up test memories
        # cleanup_test_memories()
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the server.")
        print("   Make sure the MemoryOS backend is running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Error: {e}") 