from flask import Flask, render_template_string, request, jsonify
import json
import datetime
import uuid
import sys
import os
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add the memory-app backend to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'memory-app', 'backend'))

# Import MemoryManager
try:
    from memory_manager import MemoryManager
    memory_manager = MemoryManager()
    MEMORY_AVAILABLE = True
except ImportError as e:
    print(f"Warning: MemoryManager not available: {e}")
    memory_manager = None
    MEMORY_AVAILABLE = False

app = Flask(__name__)

# In-memory storage for chat threads and messages
chat_threads = {}

# Simple HTML template for testing
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Memory Test Chat</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: white; }
        .chat-container { max-width: 800px; margin: 0 auto; }
        .message { margin: 10px 0; padding: 10px; border-radius: 8px; }
        .user { background: #333; text-align: right; }
        .assistant { background: #444; }
        .memory-context { background: #2a2a2a; border-left: 3px solid #6b46c1; padding: 10px; margin: 10px 0; }
        .memory-item { margin: 5px 0; font-size: 0.9em; }
        #chat-input { width: 100%; padding: 10px; margin: 10px 0; }
        button { padding: 10px 20px; background: #6b46c1; color: white; border: none; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="chat-container">
        <h1>🧠 Memory Test Chat</h1>
        <div id="messages"></div>
        <input type="text" id="chat-input" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
        <button onclick="sendMessage()">Send</button>
    </div>

    <script>
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        async function sendMessage() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            if (!message) return;

            addMessage(message, 'user');
            input.value = '';

            try {
                const response = await fetch('/send_message', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });

                const data = await response.json();
                if (data.success) {
                    addMessageWithMemories(data.response, 'assistant', data.memory_context);
                }
            } catch (error) {
                addMessage('Error: ' + error.message, 'assistant');
            }
        }

        function addMessage(content, sender) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            messageDiv.innerHTML = `<p>${content}</p>`;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function addMessageWithMemories(content, sender, memoryContext) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            let html = `<p>${content}</p>`;
            if (memoryContext && memoryContext.length > 0) {
                html += '<div class="memory-context"><strong>🧠 Memories Used:</strong>';
                memoryContext.forEach(mem => {
                    html += `<div class="memory-item">• "${mem.memory.content}" (relevance: ${mem.relevance_score.toFixed(3)})</div>`;
                });
                html += '</div>';
            }
            
            messageDiv.innerHTML = html;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Message cannot be empty'})
        
        # Generate AI response with memory context
        ai_response, memory_context = generate_response_with_memory(message)
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'memory_context': memory_context
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def generate_response_with_memory(message):
    """Generate a mock AI response with memory context"""
    memory_context = []
    
    # Always search memories if available
    if MEMORY_AVAILABLE and memory_manager:
        try:
            print(f"\n🔍 Searching memories for: '{message}'")
            search_results = memory_manager.search_memories(message, top_k=3, min_relevance=0.2)
            memory_context = search_results
            
            print(f"📊 Found {len(search_results)} relevant memories:")
            for i, result in enumerate(search_results):
                print(f"  {i+1}. '{result['memory']['content']}' (relevance: {result['relevance_score']:.3f})")
                
        except Exception as e:
            print(f"❌ Memory search error: {e}")
            memory_context = []
    
    # Generate a mock response based on memories found
    if memory_context:
        relevant_memories = [mem['memory']['content'] for mem in memory_context[:3]]
        response = f"Based on what I know about you: {', '.join(relevant_memories)}. "
        
        # Add context-aware responses
        if any('smart' in mem.lower() or 'genius' in mem.lower() or 'iq' in mem.lower() for mem in relevant_memories):
            response += "You seem to be quite intelligent!"
        elif any('pizza' in mem.lower() or 'italian' in mem.lower() for mem in relevant_memories):
            response += "You have great taste in food!"
        else:
            response += "That's interesting to know about you."
    else:
        response = f"I don't have specific memories related to '{message}', but I'm here to help!"
    
    return response, memory_context

if __name__ == '__main__':
    print("🧠 Starting Memory Test Chat...")
    print("📱 Open your browser and go to: http://localhost:5001")
    if MEMORY_AVAILABLE:
        print("✅ Memory search system is available!")
    else:
        print("❌ Memory search system is not available")
    app.run(debug=True, host='0.0.0.0', port=5001) 