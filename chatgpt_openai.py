#!/usr/bin/env python3

import sys
import os
from openai import OpenAI
from flask import Flask, request, jsonify, render_template_string
import datetime
import uuid
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

# Initialize OpenAI client with API key from environment
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("❌ Error: OPENAI_API_KEY not found in environment variables!")
    print("Please create a .env file with your OpenAI API key:")
    print("OPENAI_API_KEY=your_api_key_here")
    sys.exit(1)

client = OpenAI(api_key=api_key)

# In-memory storage for chat threads and messages
chat_threads = {}

# HTML template with embedded CSS
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatGPT Clone</title>
    <style>
        /* Purple Gradient Palette */
        :root {
            --primary-50: #faf5ff;
            --primary-100: #f3e8ff;
            --primary-200: #e9d5ff;
            --primary-300: #d8b4fe;
            --primary-400: #c084fc;
            --primary-500: #a855f7;
            --primary-600: #9333ea;
            --primary-700: #7c3aed;
            --primary-800: #6b21a8;
            --primary-900: #581c87;
            
            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-300: #d1d5db;
            --gray-400: #9ca3af;
            --gray-500: #6b7280;
            --gray-600: #4b5563;
            --gray-700: #374151;
            --gray-800: #1f2937;
            --gray-900: #111827;
            --gray-950: #0a0a0a;
            
            --glass-bg: rgba(31, 41, 55, 0.7);
            --glass-border: rgba(168, 85, 247, 0.2);
            --glass-blur: blur(20px);
            --glow-primary: 0 0 20px rgba(168, 85, 247, 0.3);
            --glow-secondary: 0 0 40px rgba(168, 85, 247, 0.15);
            --shadow-elevated: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            --shadow-floating: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            
            --ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
            --ease-smooth: cubic-bezier(0.4, 0, 0.2, 1);
            --ease-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        * {
            box-sizing: border-box;
        }

        body {
            background: linear-gradient(135deg, 
                var(--gray-950) 0%, 
                var(--gray-900) 25%, 
                #0f0f23 50%,
                var(--gray-900) 75%, 
                var(--gray-950) 100%);
            background-attachment: fixed;
            color: var(--gray-100);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 12px;
            height: 12px;
        }

        ::-webkit-scrollbar-track {
            background: var(--gray-900);
            border-radius: 10px;
            box-shadow: inset 0 0 6px rgba(0, 0, 0, 0.3);
        }

        ::-webkit-scrollbar-thumb {
            background: linear-gradient(45deg, var(--primary-600), var(--primary-500));
            border-radius: 10px;
            border: 2px solid var(--gray-900);
            box-shadow: 0 0 10px rgba(168, 85, 247, 0.3);
        }

        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(45deg, var(--primary-500), var(--primary-400));
            box-shadow: 0 0 15px rgba(168, 85, 247, 0.5);
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 20px;
            box-shadow: var(--shadow-floating);
        }

        .header h1 {
            color: var(--primary-400);
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
            text-shadow: 0 0 20px rgba(168, 85, 247, 0.5);
        }

        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: var(--shadow-floating);
        }

        .chat-header {
            background: linear-gradient(45deg, var(--primary-700), var(--primary-600));
            padding: 15px 20px;
            border-bottom: 1px solid var(--glass-border);
        }

        .chat-header h2 {
            margin: 0;
            color: white;
            font-size: 1.2rem;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .message {
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            padding: 15px;
            max-width: 80%;
            position: relative;
            transition: all 0.3s var(--ease-smooth);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        .message:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-floating);
            border-color: var(--primary-400);
        }

        .message.user {
            align-self: flex-end;
            background: linear-gradient(135deg, var(--primary-600), var(--primary-700));
            border-color: var(--primary-400);
        }

        .message.assistant {
            align-self: flex-start;
            background: var(--glass-bg);
        }

        .message-content {
            margin: 0;
            word-wrap: break-word;
            white-space: pre-wrap;
        }

        .message-time {
            font-size: 0.75rem;
            color: var(--gray-400);
            margin-top: 8px;
            opacity: 0.8;
        }

        .memory-context {
            background: linear-gradient(45deg, var(--primary-800), var(--primary-900));
            border: 1px solid var(--primary-600);
            border-radius: 8px;
            padding: 10px;
            margin-top: 10px;
            font-size: 0.85rem;
            color: var(--primary-200);
        }

        .memory-context h4 {
            margin: 0 0 8px 0;
            color: var(--primary-300);
            font-size: 0.9rem;
        }

        .memory-item {
            background: rgba(168, 85, 247, 0.1);
            border-left: 3px solid var(--primary-500);
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 4px;
            font-size: 0.8rem;
        }

        .memory-score {
            color: var(--primary-400);
            font-weight: 600;
            margin-left: 8px;
        }

        .chat-input-container {
            padding: 20px;
            border-top: 1px solid var(--glass-border);
            background: var(--glass-bg);
        }

        .chat-input-form {
            display: flex;
            gap: 10px;
        }

        .chat-input {
            flex: 1;
            background: var(--gray-800);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            padding: 15px;
            color: var(--gray-100);
            font-size: 1rem;
            transition: all 0.3s var(--ease-smooth);
            resize: none;
            min-height: 50px;
            max-height: 150px;
        }

        .chat-input:focus {
            outline: none;
            border-color: var(--primary-400);
            box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.25);
            background: var(--gray-700);
        }

        .send-button {
            background: linear-gradient(45deg, var(--primary-600), var(--primary-700));
            border: none;
            border-radius: 12px;
            padding: 15px 25px;
            color: white;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s var(--ease-smooth);
            box-shadow: var(--shadow-floating);
        }

        .send-button:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-elevated);
            background: linear-gradient(45deg, var(--primary-500), var(--primary-600));
        }

        .send-button:active {
            transform: translateY(0);
        }

        .thread-controls {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }

        .new-thread-btn, .clear-thread-btn, .end-thread-btn, .memory-toggle-btn {
            background: linear-gradient(45deg, var(--primary-600), var(--primary-700));
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s var(--ease-smooth);
        }

        .new-thread-btn:hover, .clear-thread-btn:hover, .end-thread-btn:hover, .memory-toggle-btn:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-floating);
        }

        .clear-thread-btn {
            background: linear-gradient(45deg, #dc2626, #b91c1c);
        }

        .end-thread-btn {
            background: linear-gradient(45deg, #059669, #047857);
        }

        .memory-toggle-btn {
            background: linear-gradient(45deg, var(--primary-500), var(--primary-600));
        }

        .memory-toggle-btn.active {
            background: linear-gradient(45deg, #059669, #047857);
            box-shadow: 0 0 15px rgba(5, 150, 105, 0.4);
        }

        .memory-toggle-btn.disabled {
            background: linear-gradient(45deg, var(--gray-600), var(--gray-700));
            cursor: not-allowed;
            opacity: 0.6;
        }

        .empty-state {
            text-align: center;
            color: var(--gray-400);
            font-style: italic;
            margin: auto;
            padding: 40px;
        }

        .typing-indicator {
            display: none;
            align-self: flex-start;
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            padding: 15px;
            color: var(--gray-400);
        }

        .typing-indicator.show {
            display: block;
        }

        .searching-memories-indicator {
            display: none;
            align-self: flex-start;
            background: var(--glass-bg);
            border: 1px solid var(--primary-400);
            border-radius: 12px;
            padding: 15px;
            color: var(--primary-400);
            margin-bottom: 10px;
        }
        .searching-memories-indicator.show {
            display: block;
        }

        .memories-injected-box {
            background: linear-gradient(45deg, var(--primary-900), var(--primary-800));
            border: 1px solid var(--primary-600);
            border-radius: 8px;
            padding: 10px;
            margin-top: 10px;
            font-size: 0.85rem;
            color: var(--primary-200);
        }
        .memories-injected-box h4 {
            margin: 0 0 8px 0;
            color: var(--primary-300);
            font-size: 0.9rem;
        }
        .memories-injected-item {
            background: rgba(168, 85, 247, 0.1);
            border-left: 3px solid var(--primary-500);
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 4px;
            font-size: 0.8rem;
        }
        .memories-injected-score {
            color: var(--primary-400);
            font-weight: 600;
            margin-left: 8px;
        }

        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .message {
                max-width: 90%;
            }
            
            .chat-input-form {
                flex-direction: column;
            }
            
            .send-button {
                width: 100%;
            }
            
            .thread-controls {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 ChatGPT Clone</h1>
        </div>
        
        <div class="thread-controls">
            <button class="new-thread-btn" onclick="newThread()">New Thread</button>
            <button class="clear-thread-btn" onclick="clearThread()">Clear Thread</button>
            <button class="end-thread-btn" onclick="endThread()">💾 End & Save Memories</button>
            <button class="memory-toggle-btn" id="memory-toggle" onclick="toggleMemorySearch()">
                <span id="memory-toggle-text">🔍 Search Memories</span>
            </button>
        </div>
        
        <div class="chat-container">
            <div class="chat-header">
                <h2 id="thread-title">New Conversation</h2>
            </div>
            
            <div class="chat-messages" id="chat-messages">
                <div class="empty-state">
                    Start a new conversation by typing a message below...
                </div>
            </div>
            
            <div class="searching-memories-indicator" id="searching-memories-indicator">
                🔎 Searching memories...
            </div>
            
            <div class="typing-indicator" id="typing-indicator">
                Assistant is typing...
            </div>
            
            <div class="chat-input-container">
                <form class="chat-input-form" id="chat-form">
                    <textarea 
                        class="chat-input" 
                        id="chat-input" 
                        placeholder="Type your message here..."
                        rows="1"
                        onkeydown="handleKeyDown(event)"
                    ></textarea>
                    <button type="submit" class="send-button">Send</button>
                </form>
            </div>
        </div>
    </div>

    <script>
        let currentThreadId = null;
        let isTyping = false;
        let memorySearchEnabled = false;

        // Auto-resize textarea
        const textarea = document.getElementById('chat-input');
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 150) + 'px';
        });

        // Handle Enter key (Send on Enter, new line on Shift+Enter)
        function handleKeyDown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        // Toggle memory search (always enabled now)
        function toggleMemorySearch() {
            // Memory search is always enabled now
            const toggleBtn = document.getElementById('memory-toggle');
            const toggleText = document.getElementById('memory-toggle-text');
            toggleBtn.classList.add('active');
            toggleText.textContent = '✅ Memory Search ALWAYS ON';
        }

        // Show/hide searching memories indicator
        function showSearchingMemories() {
            document.getElementById('searching-memories-indicator').classList.add('show');
        }
        function hideSearchingMemories() {
            document.getElementById('searching-memories-indicator').classList.remove('show');
        }

        // Send message function
        async function sendMessage() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            
            if (!message || isTyping) return;
            
            // Clear input
            input.value = '';
            input.style.height = 'auto';
            
            // Add user message to chat
            addMessage(message, 'user');
            
            // Show typing indicator
            showTypingIndicator();
            showSearchingMemories();
            
            try {
                const response = await fetch('/send_message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        thread_id: currentThreadId,
                        use_memory_search: memorySearchEnabled
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    currentThreadId = data.thread_id;
                    updateThreadTitle();
                    
                    // Add AI response with memory context if available
                    if (data.memory_context && data.memory_context.length > 0) {
                        addMessageWithMemoriesInjected(data.response, 'assistant', data.memory_context);
                    } else {
                        addMessage(data.response, 'assistant');
                    }
                } else {
                    addMessageWithMemoriesInjected('Sorry, I encountered an error. Please try again.', 'assistant', []);
                }
            } catch (error) {
                addMessageWithMemoriesInjected('Sorry, I encountered an error. Please try again.', 'assistant', []);
            } finally {
                hideTypingIndicator();
                hideSearchingMemories();
            }
        }

        // Add message to chat
        function addMessage(content, sender) {
            const messagesContainer = document.getElementById('chat-messages');
            const emptyState = messagesContainer.querySelector('.empty-state');
            
            if (emptyState) {
                emptyState.remove();
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            
            messageDiv.innerHTML = `
                <p class="message-content">${content}</p>
                <div class="message-time">${timeString}</div>
            `;
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        // Add message with memories injected info
        function addMessageWithMemoriesInjected(content, sender, memoryContext) {
            const messagesContainer = document.getElementById('chat-messages');
            const emptyState = messagesContainer.querySelector('.empty-state');
            
            if (emptyState) {
                emptyState.remove();
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            
            // Build memories injected HTML
            let memoriesHtml = '<div class="memories-injected-box">';
            memoriesHtml += '<h4>🧠 Memories Injected:</h4>';
            if (memoryContext && memoryContext.length > 0) {
                memoryContext.forEach(memory => {
                    memoriesHtml += `<div class="memories-injected-item">${memory.memory.content}<span class="memories-injected-score">(Score: ${memory.final_score.toFixed(2)})</span></div>`;
                });
            } else {
                memoriesHtml += '<div class="memories-injected-item">No relevant memories were injected for this prompt.</div>';
            }
            memoriesHtml += '</div>';
            
            messageDiv.innerHTML = `
                <p class="message-content">${content}</p>
                ${memoriesHtml}
                <div class="message-time">${timeString}</div>
            `;
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        // Show typing indicator
        function showTypingIndicator() {
            isTyping = true;
            const indicator = document.getElementById('typing-indicator');
            indicator.classList.add('show');
            indicator.scrollIntoView({ behavior: 'smooth' });
        }

        // Hide typing indicator
        function hideTypingIndicator() {
            isTyping = false;
            const indicator = document.getElementById('typing-indicator');
            indicator.classList.remove('show');
        }

        // New thread function
        async function newThread() {
            // If there's an existing conversation with messages, offer to extract memories
            if (currentThreadId) {
                const messagesContainer = document.getElementById('chat-messages');
                const messages = messagesContainer.querySelectorAll('.message');
                
                if (messages.length > 2) { // More than just empty state
                    const extractMemories = confirm('Extract memories from current conversation before starting new thread?');
                    if (extractMemories) {
                        await endThread();
                        return; // endThread() will call newThread() after extraction
                    }
                }
            }
            
            currentThreadId = null;
            const messagesContainer = document.getElementById('chat-messages');
            messagesContainer.innerHTML = '<div class="empty-state">Start a new conversation by typing a message below...</div>';
            updateThreadTitle();
        }

        // Clear thread function
        function clearThread() {
            if (confirm('Are you sure you want to clear this conversation?')) {
                newThread();
            }
        }

        // End thread and extract memories
        async function endThread() {
            if (!currentThreadId) {
                alert('No active conversation to end.');
                return;
            }

            if (!confirm('End this conversation and extract memories for future chats?')) {
                return;
            }

            try {
                showTypingIndicator();
                
                const response = await fetch('/end_thread', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        thread_id: currentThreadId
                    })
                });

                const data = await response.json();

                if (data.success) {
                    // Show extracted memories
                    if (data.extracted_memories && data.extracted_memories.length > 0) {
                        const memoriesText = data.extracted_memories.join('\\n• ');
                        addMessage(`🧠 Conversation ended! Extracted ${data.count} memories:\\n\\n• ${memoriesText}\\n\\nThese will inform future conversations.`, 'assistant');
                    } else {
                        addMessage('🧠 Conversation ended! No new memories were extracted from this conversation.', 'assistant');
                    }
                    
                    // Start a new thread
                    setTimeout(() => {
                        newThread();
                    }, 2000);
                } else {
                    addMessage('❌ Failed to end conversation and extract memories.', 'assistant');
                }
            } catch (error) {
                addMessage('❌ Error ending conversation. Please try again.', 'assistant');
            } finally {
                hideTypingIndicator();
            }
        }

        // Update thread title
        function updateThreadTitle() {
            const titleElement = document.getElementById('thread-title');
            if (currentThreadId) {
                titleElement.textContent = `Conversation ${currentThreadId.substring(0, 8)}...`;
            } else {
                titleElement.textContent = 'New Conversation';
            }
        }

        // Form submit handler
        document.getElementById('chat-form').addEventListener('submit', function(e) {
            e.preventDefault();
            sendMessage();
        });

        // Initialize
        updateThreadTitle();
        
        // Check if memory system is available
        fetch('/check_memory_availability')
            .then(response => response.json())
            .then(data => {
                if (!data.available) {
                    const toggleBtn = document.getElementById('memory-toggle');
                    toggleBtn.classList.add('disabled');
                    toggleBtn.disabled = true;
                    document.getElementById('memory-toggle-text').textContent = '❌ Memory System Unavailable';
                }
            });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/check_memory_availability')
def check_memory_availability():
    return jsonify({'available': MEMORY_AVAILABLE})

@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        thread_id = data.get('thread_id')
        use_memory_search = data.get('use_memory_search', False)
        
        if not message:
            return jsonify({'success': False, 'error': 'Message cannot be empty'})
        
        # Create new thread if none exists
        if not thread_id:
            thread_id = str(uuid.uuid4())
            chat_threads[thread_id] = []
        
        # Add user message to thread
        timestamp = datetime.datetime.now().isoformat()
        user_message = {
            'id': str(uuid.uuid4()),
            'content': message,
            'sender': 'user',
            'timestamp': timestamp
        }
        
        if thread_id not in chat_threads:
            chat_threads[thread_id] = []
        
        chat_threads[thread_id].append(user_message)
        
        # Generate AI response using OpenAI API with memory context (always search memories)
        ai_response, memory_context = generate_openai_response_with_memory(message, chat_threads[thread_id], True)
        
        # Add AI response to thread
        ai_message = {
            'id': str(uuid.uuid4()),
            'content': ai_response,
            'sender': 'assistant',
            'timestamp': datetime.datetime.now().isoformat()
        }
        chat_threads[thread_id].append(ai_message)
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'thread_id': thread_id,
            'memory_context': memory_context
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/end_thread', methods=['POST'])
def end_thread():
    """Extract memories from a conversation thread when it ends"""
    try:
        data = request.get_json()
        thread_id = data.get('thread_id')
        
        if not thread_id or thread_id not in chat_threads:
            return jsonify({'success': False, 'error': 'Thread not found'})
        
        conversation = chat_threads[thread_id]
        extracted_memories = extract_memories_from_conversation(conversation)
        
        # Add extracted memories to the memory system
        if MEMORY_AVAILABLE and memory_manager and extracted_memories:
            print(f"💾 Extracting {len(extracted_memories)} memories from conversation...")
            for memory_text in extracted_memories:
                try:
                    memory_manager.add_memory(memory_text, ["conversation", "auto-extracted"])
                    print(f"   ✅ Added: {memory_text}")
                except Exception as e:
                    print(f"   ❌ Failed to add: {memory_text} - {e}")
        
        # Clean up the thread
        del chat_threads[thread_id]
        
        return jsonify({
            'success': True,
            'extracted_memories': extracted_memories,
            'count': len(extracted_memories)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def extract_memories_from_conversation(conversation):
    """
    Extract up to 5 meaningful memories from a conversation using OpenAI
    """
    if not conversation or len(conversation) < 2:
        return []
    
    # Build conversation text
    conversation_text = ""
    for msg in conversation:
        role = "User" if msg['sender'] == 'user' else "Assistant"
        conversation_text += f"{role}: {msg['content']}\n"
    
    # Use OpenAI to extract memories
    try:
        extraction_prompt = f"""Analyze this conversation and extract up to 5 meaningful personal facts, preferences, or information about the user that should be remembered for future conversations.

Focus on:
- Personal preferences (food, hobbies, interests)
- Facts about the user (job, location, family, etc.)
- Opinions and feelings they expressed
- Goals or plans they mentioned
- Important experiences they shared

Return ONLY the extracted memories, one per line, in first person format (starting with "I").
If no meaningful personal information is found, return "NONE".

Conversation:
{conversation_text}

Extracted memories:"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": extraction_prompt}],
            max_tokens=300,
            temperature=0.3
        )
        
        result = response.choices[0].message.content.strip()
        
        if result == "NONE" or not result:
            return []
        
        # Parse the memories
        memories = []
        for line in result.split('\n'):
            line = line.strip()
            if line and not line.startswith('-') and len(line) > 10:
                # Clean up the memory text
                if line.startswith('- '):
                    line = line[2:]
                if not line.lower().startswith('i '):
                    line = f"I {line.lower()}"
                memories.append(line)
        
        return memories[:5]  # Limit to 5 memories
        
    except Exception as e:
        print(f"❌ Error extracting memories: {e}")
        return []

def generate_openai_response_with_memory(message, conversation_history, use_memory_search=True):
    """
    Generate AI response using OpenAI API with memory context (always searches)
    """
    try:
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Use the following user memories to answer as personally and specifically as possible. If relevant, reference these memories directly in your answer. If no memories are relevant, answer as best you can.\n\n"}
        ]
        memory_context = []
        debug_memories = []
        
        # Always search memories if available
        if MEMORY_AVAILABLE and memory_manager:
            try:
                print(f"\n🔍 Searching memories for: '{message}'")
                search_results = memory_manager.search_memories(message, top_k=5, min_relevance=0.2)
                memory_context = search_results
                
                print(f"📊 Found {len(search_results)} relevant memories:")
                for i, result in enumerate(search_results):
                    print(f"  {i+1}. '{result['memory']['content']}' (relevance: {result['relevance_score']:.3f}, final: {result['final_score']:.3f})")
                
                if search_results:
                    memory_text = "USER MEMORIES (for context):\n"
                    for result in search_results[:3]:  # Use top 3
                        memory_text += f"- {result['memory']['content']} (relevance: {result['relevance_score']:.2f})\n"
                        debug_memories.append(result['memory']['content'])
                    memory_text += "\nUse these memories to personalize your response when relevant."
                    messages[0]["content"] += memory_text
                    print(f"💡 Injected {len(debug_memories)} memories into prompt")
                else:
                    print("❌ No memories met the relevance threshold")
                    
            except Exception as e:
                print(f"❌ Memory search error: {e}")
                memory_context = []
        else:
            print("⚠️ Memory system not available")
        # Add conversation history
        for msg in conversation_history[-10:]:
            role = "user" if msg['sender'] == 'user' else "assistant"
            messages.append({"role": role, "content": msg['content']})
        messages.append({"role": "user", "content": message})
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response.choices[0].message.content.strip(), memory_context
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return f"I apologize, but I encountered an error: {str(e)}. Please try again.", []

def start_memory_file_watcher(memory_manager, path):
    class MemoryFileHandler(FileSystemEventHandler):
        def __init__(self):
            super().__init__()
            self.last_reload_time = 0
            self.last_file_size = 0
            self.last_file_hash = None
            
        def on_modified(self, event):
            # Only process memories.json files
            if not event.src_path.endswith('memories.json'):
                return
                
            # Skip temporary, backup, and lock files
            if event.src_path.endswith(('.tmp', '.backup', '.lock')):
                return
                
            import time
            import hashlib
            current_time = time.time()
            
            # Avoid duplicate reloads within 2 seconds
            if current_time - self.last_reload_time < 2.0:
                return
            
            try:
                # Check if file actually changed (avoid reloading on same content)
                if os.path.exists(event.src_path):
                    current_size = os.path.getsize(event.src_path)
                    
                    # Skip if file is empty or being written
                    if current_size == 0:
                        return
                    
                    # Calculate file hash to detect actual content changes
                    try:
                        with open(event.src_path, 'rb') as f:
                            file_hash = hashlib.md5(f.read()).hexdigest()
                        
                        # Skip if content hasn't actually changed
                        if file_hash == self.last_file_hash:
                            return
                            
                        self.last_file_hash = file_hash
                        self.last_file_size = current_size
                    except (IOError, OSError):
                        # File might be locked, skip this reload
                        return
                
                print(f"[Watcher] 📁 Detected memories.json change, reloading...")
                memory_manager.reload_from_disk()
                self.last_reload_time = current_time
                
            except Exception as e:
                print(f"[Watcher] ❌ Error during reload: {e}")
                    
    observer = Observer()
    handler = MemoryFileHandler()
    observer.schedule(handler, path=os.path.dirname(path), recursive=False)
    observer.daemon = True
    observer.start()
    print(f"[Watcher] 👀 Watching {path} for changes...")

# Start the file watcher in a background thread if memory_manager is available
if MEMORY_AVAILABLE and memory_manager:
    mem_json_path = os.path.join(os.path.dirname(__file__), 'memory-app', 'backend', 'data', 'memories.json')
    threading.Thread(target=start_memory_file_watcher, args=(memory_manager, mem_json_path), daemon=True).start()

if __name__ == '__main__':
    print("🤖 Starting ChatGPT Clone with OpenAI API and Memory Search...")
    print("📱 Open your browser and go to: http://localhost:4000")
    print("💜 Enjoy your purple-themed chat experience!")
    if MEMORY_AVAILABLE:
        print("🧠 Memory search system is available!")
    else:
        print("⚠️  Memory search system is not available")
    app.run(debug=True, host='0.0.0.0', port=4000) 