import requests
import json
import time

# Test the web-based memory injection
BASE_URL = "http://localhost:5001"

def test_web_memory():
    print("🌐 Testing Web-Based Memory Injection\n")
    
    # Test prompts that should trigger different memory searches
    test_cases = [
        {
            "prompt": "Tell me about my intelligence",
            "expected_memories": ["I am very smart", "I am a genius", "I have an IQ"],
            "description": "Should find intelligence-related memories"
        },
        {
            "prompt": "What food do I like?",
            "expected_memories": ["pizza", "Italian Food"],
            "description": "Should find food-related memories"
        },
        {
            "prompt": "Am I smart?",
            "expected_memories": ["I am very smart", "genius", "IQ"],
            "description": "Should find intelligence memories with high relevance"
        },
        {
            "prompt": "What's my favorite cuisine?",
            "expected_memories": ["Italian Food", "pizza"],
            "description": "Should find cuisine-related memories"
        },
        {
            "prompt": "Do I have a high IQ?",
            "expected_memories": ["IQ", "145"],
            "description": "Should specifically find IQ memory"
        },
        {
            "prompt": "pizza",
            "expected_memories": ["pizza"],
            "description": "Direct keyword match"
        },
        {
            "prompt": "genius",
            "expected_memories": ["genius"],
            "description": "Direct keyword match"
        },
        {
            "prompt": "weather",
            "expected_memories": [],
            "description": "Should find no relevant memories"
        }
    ]
    
    print("⏳ Waiting for server to start...")
    time.sleep(3)
    
    # Test each case
    for i, test_case in enumerate(test_cases, 1):
        print(f"🔍 Test {i}: {test_case['description']}")
        print(f"   Prompt: '{test_case['prompt']}'")
        
        try:
            response = requests.post(f"{BASE_URL}/send_message", 
                                   json={"message": test_case['prompt']},
                                   timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ Response: {data['response'][:80]}...")
                    
                    memory_context = data.get('memory_context', [])
                    print(f"🧠 Memories found: {len(memory_context)}")
                    
                    if memory_context:
                        print("   Injected memories:")
                        for j, mem in enumerate(memory_context):
                            content = mem['memory']['content']
                            relevance = mem['relevance_score']
                            print(f"      {j+1}. '{content}' (relevance: {relevance:.3f})")
                        
                        # Check if expected memories were found
                        found_memories = [mem['memory']['content'].lower() for mem in memory_context]
                        expected_found = []
                        for expected in test_case['expected_memories']:
                            if any(expected.lower() in found.lower() for found in found_memories):
                                expected_found.append(expected)
                        
                        if test_case['expected_memories']:
                            if expected_found:
                                print(f"   ✅ Found expected memories: {expected_found}")
                            else:
                                print(f"   ⚠️  Expected memories not found: {test_case['expected_memories']}")
                        else:
                            print("   ✅ Correctly found no memories for irrelevant prompt")
                    else:
                        if test_case['expected_memories']:
                            print("   ❌ No memories found, but some were expected!")
                        else:
                            print("   ✅ Correctly found no memories")
                else:
                    print(f"   ❌ API Error: {data.get('error', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
        
        print("-" * 70)
        time.sleep(0.5)

def test_server_availability():
    """Test if the server is running"""
    try:
        response = requests.get(BASE_URL, timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("🧪 Web Memory Injection Test Suite")
    print("=" * 50)
    
    if test_server_availability():
        print("✅ Server is running!")
        test_web_memory()
    else:
        print("❌ Server is not running on http://localhost:5001")
        print("Please start the server with: python chatgpt_test.py")
    
    print("\n🎉 Test completed!") 