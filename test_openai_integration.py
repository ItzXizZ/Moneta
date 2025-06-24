import requests
import json
import time

# Test the OpenAI ChatGPT integration with memory search
BASE_URL = "http://localhost:4000"

def test_openai_memory_integration():
    print("🤖 Testing OpenAI ChatGPT + Memory Integration\n")
    
    # Test cases that should trigger memory searches and get intelligent responses
    test_cases = [
        {
            "prompt": "What do you know about my intelligence?",
            "expected_memories": ["smart", "genius", "IQ"],
            "description": "Should find intelligence memories and provide personalized response"
        },
        {
            "prompt": "What are my food preferences?", 
            "expected_memories": ["pizza", "Italian"],
            "description": "Should find food memories and mention preferences"
        },
        {
            "prompt": "Tell me something about myself",
            "expected_memories": [],  # Should find some memories
            "description": "General query should find relevant memories"
        },
        {
            "prompt": "Am I smart?",
            "expected_memories": ["smart", "genius", "IQ"],
            "description": "Direct intelligence question should get personalized answer"
        },
        {
            "prompt": "What's my IQ?",
            "expected_memories": ["145", "IQ"],
            "description": "Should specifically mention IQ of 145"
        }
    ]
    
    print("⏳ Waiting for server to start...")
    time.sleep(5)
    
    # Check if server is available
    try:
        response = requests.get(f"{BASE_URL}/check_memory_availability", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('available'):
                print("✅ Memory system is available!")
            else:
                print("❌ Memory system is not available")
                return
        else:
            print(f"❌ Server not responding: {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Test each case
    success_count = 0
    for i, test_case in enumerate(test_cases, 1):
        print(f"🔍 Test {i}: {test_case['description']}")
        print(f"   Prompt: '{test_case['prompt']}'")
        
        try:
            response = requests.post(f"{BASE_URL}/send_message", 
                                   json={
                                       "message": test_case['prompt'],
                                       "thread_id": None,
                                       "use_memory_search": True
                                   },
                                   timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    ai_response = data['response']
                    memory_context = data.get('memory_context', [])
                    
                    print(f"✅ AI Response: {ai_response[:100]}...")
                    print(f"🧠 Memories injected: {len(memory_context)}")
                    
                    if memory_context:
                        print("   Memory details:")
                        for j, mem in enumerate(memory_context[:3]):
                            content = mem['memory']['content']
                            relevance = mem['relevance_score']
                            print(f"      {j+1}. '{content}' (relevance: {relevance:.3f})")
                        
                        # Check if expected memories were found
                        if test_case['expected_memories']:
                            found_memories = [mem['memory']['content'].lower() for mem in memory_context]
                            expected_found = []
                            for expected in test_case['expected_memories']:
                                if any(expected.lower() in found.lower() for found in found_memories):
                                    expected_found.append(expected)
                            
                            if expected_found:
                                print(f"   ✅ Found expected memories: {expected_found}")
                            else:
                                print(f"   ⚠️  Expected memories not found: {test_case['expected_memories']}")
                        
                        # Check if AI response references the memories
                        response_lower = ai_response.lower()
                        memory_referenced = False
                        for mem in memory_context[:3]:
                            mem_content = mem['memory']['content'].lower()
                            # Check for key words from memory in response
                            if any(word in response_lower for word in mem_content.split() if len(word) > 3):
                                memory_referenced = True
                                break
                        
                        if memory_referenced:
                            print("   ✅ AI response appears to reference memories")
                        else:
                            print("   ⚠️  AI response may not be using memories effectively")
                        
                        success_count += 1
                    else:
                        print("   ❌ No memories were injected!")
                else:
                    print(f"   ❌ API Error: {data.get('error', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
        
        print("-" * 70)
        time.sleep(2)  # Pause between requests to avoid rate limits
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"   Successful tests: {success_count}/{len(test_cases)}")
    if success_count == len(test_cases):
        print("   🎉 All tests passed! OpenAI + Memory integration is working perfectly!")
    elif success_count > 0:
        print("   ⚠️  Some tests passed, but there may be issues to investigate.")
    else:
        print("   ❌ No tests passed. There are significant issues to fix.")

if __name__ == "__main__":
    print("🧪 OpenAI + Memory Integration Test Suite")
    print("=" * 60)
    test_openai_memory_integration()
    print("\n🏁 Test completed!") 