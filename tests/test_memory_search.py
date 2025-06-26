import requests
import json
import time

# Test the ChatGPT clone memory search functionality
BASE_URL = "http://localhost:4000"

def test_memory_search():
    print("🧪 Testing Memory Search Functionality\n")
    
    # Test prompts that should match different memories
    test_prompts = [
        "Tell me about my intelligence",  # Should match "I am very smart", "I am a genius", "IQ of 145"
        "What food do I like?",          # Should match "I love pizza", "I love Italian Food"
        "Am I smart?",                   # Should match intelligence-related memories
        "What's my favorite cuisine?",   # Should match Italian food/pizza
        "Do I have a high IQ?",         # Should match IQ memory specifically
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"🔍 Test {i}: '{prompt}'")
        
        try:
            response = requests.post(f"{BASE_URL}/send_message", 
                                   json={
                                       "message": prompt,
                                       "thread_id": None,
                                       "use_memory_search": True
                                   },
                                   timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ Response: {data['response'][:100]}...")
                    
                    memory_context = data.get('memory_context', [])
                    if memory_context:
                        print(f"🧠 Memories found: {len(memory_context)}")
                        for j, mem in enumerate(memory_context[:3]):
                            print(f"   {j+1}. '{mem['memory']['content']}' (score: {mem['final_score']:.3f})")
                    else:
                        print("❌ No memories were injected!")
                else:
                    print(f"❌ API Error: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        
        print("-" * 60)
        time.sleep(1)  # Brief pause between tests

if __name__ == "__main__":
    # Wait a moment for the server to start
    print("⏳ Waiting for server to start...")
    time.sleep(3)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/check_memory_availability", timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('available'):
                print("✅ Memory system is available!")
                test_memory_search()
            else:
                print("❌ Memory system is not available")
        else:
            print(f"❌ Server not responding: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Make sure the ChatGPT server is running on http://localhost:4000") 