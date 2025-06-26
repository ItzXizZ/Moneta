import requests
import json
import time

# Test the ChatGPT integration with dynamic memory reinforcement
BASE_URL = "http://localhost:4000"

def test_chatgpt_reinforcement():
    print("🤖 Testing ChatGPT + Dynamic Memory Reinforcement\n")
    
    # Test queries that should reinforce different memory clusters
    test_scenarios = [
        {
            "queries": [
                "Tell me about my intelligence",
                "Am I smart?", 
                "What's my IQ?",
                "Am I a genius?"
            ],
            "category": "Intelligence",
            "expected_reinforcement": ["smart", "genius", "IQ"]
        },
        {
            "queries": [
                "What food do I like?",
                "Do I like pizza?",
                "What's my favorite cuisine?",
                "Tell me about Italian food"
            ],
            "category": "Food Preferences", 
            "expected_reinforcement": ["pizza", "Italian"]
        }
    ]
    
    print("⏳ Waiting for server to start...")
    time.sleep(5)
    
    # Check server availability
    try:
        response = requests.get(f"{BASE_URL}/check_memory_availability", timeout=10)
        if response.status_code != 200:
            print("❌ Server not available")
            return
        print("✅ Server is running!")
    except:
        print("❌ Cannot connect to server")
        return
    
    for scenario in test_scenarios:
        print(f"\n📂 Testing {scenario['category']} Queries")
        print("=" * 50)
        
        for i, query in enumerate(scenario['queries'], 1):
            print(f"\n🔍 Query {i}: '{query}'")
            
            try:
                response = requests.post(f"{BASE_URL}/send_message",
                                       json={
                                           "message": query,
                                           "thread_id": None,
                                           "use_memory_search": True
                                       },
                                       timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        ai_response = data['response']
                        memory_context = data.get('memory_context', [])
                        
                        print(f"✅ AI Response: {ai_response[:80]}...")
                        print(f"🧠 Memories used: {len(memory_context)}")
                        
                        if memory_context:
                            for j, mem in enumerate(memory_context, 1):
                                content = mem['memory']['content']
                                relevance = mem['relevance_score']
                                score = mem['memory']['score']
                                print(f"   {j}. '{content}' (relevance: {relevance:.3f}, score: {score:.2f})")
                        
                        print("   💪 This query will reinforce these memories!")
                    else:
                        print(f"❌ Error: {data.get('error')}")
                else:
                    print(f"❌ HTTP Error: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Request failed: {e}")
            
            time.sleep(2)  # Pause between requests
    
    print("\n🎯 Reinforcement Test Summary:")
    print("- Each query reinforces the recalled memories")
    print("- Related memories (neighbors) also get reinforced at 30%")
    print("- Frequently used memories will have higher scores over time")
    print("- The system learns which memories are most important!")

if __name__ == "__main__":
    print("🧠 ChatGPT + Dynamic Memory Reinforcement Test")
    print("=" * 60)
    test_chatgpt_reinforcement()
    print("\n🏁 Test completed!") 