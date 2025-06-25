#!/usr/bin/env python3

import sys
import os
import threading
import time
import requests
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
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
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
            max-width: 1600px;
            margin: 0 auto;
            padding: 10px;
            display: flex;
            flex-direction: column;
            height: 100vh;
            gap: 10px;
        }

        .main-content {
            display: grid;
            grid-template-columns: 1fr 1.2fr;
            gap: 10px;
            flex: 1;
            min-height: 0;
        }

        .header {
            display: none; /* Remove the header entirely */
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
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur);
            padding: 8px 16px;
            border-bottom: 1px solid var(--glass-border);
        }

        .chat-header h2 {
            margin: 0;
            color: var(--primary-300);
            font-size: 0.9rem;
            font-weight: 500;
            opacity: 0.8;
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
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur);
            border: 1px solid var(--primary-400);
            border-radius: 8px;
            padding: 12px 20px;
            color: var(--primary-200);
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s var(--ease-smooth);
            box-shadow: 0 2px 8px rgba(168, 85, 247, 0.2);
        }

        .send-button:hover {
            background: rgba(168, 85, 247, 0.2);
            border-color: var(--primary-300);
            color: var(--primary-100);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(168, 85, 247, 0.3);
        }

        .send-button:active {
            transform: translateY(0);
        }

        .thread-controls {
            display: flex;
            gap: 6px;
            margin-bottom: 8px;
            flex-wrap: wrap;
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            padding: 8px;
            box-shadow: var(--shadow-floating);
        }

        .new-thread-btn, .clear-thread-btn, .end-thread-btn, .memory-toggle-btn {
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur);
            border: 1px solid var(--glass-border);
            border-radius: 6px;
            padding: 6px 12px;
            color: var(--gray-200);
            font-weight: 500;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.3s var(--ease-smooth);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .new-thread-btn:hover, .clear-thread-btn:hover, .end-thread-btn:hover, .memory-toggle-btn:hover {
            background: rgba(168, 85, 247, 0.2);
            border-color: var(--primary-400);
            color: var(--primary-200);
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(168, 85, 247, 0.2);
        }

        .clear-thread-btn:hover {
            background: rgba(220, 38, 38, 0.2);
            border-color: #dc2626;
            color: #fca5a5;
        }

        .end-thread-btn:hover {
            background: rgba(5, 150, 105, 0.2);
            border-color: #059669;
            color: #6ee7b7;
        }

        .memory-toggle-btn.active {
            background: rgba(5, 150, 105, 0.3);
            border-color: #059669;
            color: #6ee7b7;
            box-shadow: 0 0 10px rgba(5, 150, 105, 0.3);
        }

        .memory-toggle-btn.disabled {
            background: rgba(75, 85, 99, 0.3);
            border-color: var(--gray-600);
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

        /* Memory Network Visualization */
        .memory-network-container {
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 12px;
            box-shadow: var(--shadow-floating);
            flex: 1;
            min-height: 400px;
            display: flex;
            flex-direction: column;
        }

        .memory-network-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            flex-shrink: 0;
        }

        .memory-network-header h3 {
            color: var(--primary-300);
            margin: 0;
            font-size: 1rem;
            font-weight: 500;
            opacity: 0.9;
        }

        .memory-network-controls {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .threshold-slider {
            background: var(--gray-700);
            border: 1px solid var(--glass-border);
            border-radius: 8px;
            padding: 5px 10px;
            color: var(--gray-200);
            font-size: 0.9rem;
        }

        .memory-network-stats {
            display: flex;
            gap: 8px;
            margin-bottom: 8px;
            font-size: 0.75rem;
            color: var(--gray-400);
            flex-shrink: 0;
        }

        .stat-item {
            background: rgba(31, 41, 55, 0.8);
            backdrop-filter: var(--glass-blur);
            padding: 6px 10px;
            border-radius: 6px;
            border: 1px solid var(--glass-border);
        }

        .stat-value {
            color: var(--primary-300);
            font-weight: 500;
        }

        #memory-network {
            flex: 1;
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            background: rgba(17, 24, 39, 0.9);
            backdrop-filter: var(--glass-blur);
            position: relative;
            overflow: hidden;
            min-height: 300px;
        }

        .network-loading {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: var(--gray-400);
            font-style: italic;
        }

        .memory-activity-indicator {
            position: absolute;
            top: 10px;
            right: 10px;
            background: var(--primary-600);
            color: white;
            padding: 5px 10px;
            border-radius: 8px;
            font-size: 0.8rem;
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .memory-activity-indicator.active {
            opacity: 1;
        }

        @media (max-width: 1024px) {
            .main-content {
                grid-template-columns: 1fr;
                grid-template-rows: 1fr 1fr;
            }
            
            .memory-network-container {
                min-height: 300px;
            }
            
            #memory-network {
                height: 240px;
            }
        }

        @media (max-width: 768px) {
            .container {
                padding: 8px;
            }
            
            .message {
                max-width: 95%;
            }
            
            .chat-input-form {
                flex-direction: column;
                gap: 8px;
            }
            
            .send-button {
                width: 100%;
            }
            
            .thread-controls {
                flex-wrap: wrap;
                justify-content: center;
            }
            
            .memory-network-stats {
                flex-wrap: wrap;
                gap: 8px;
            }
            
            .stat-item {
                font-size: 0.7rem;
                padding: 4px 8px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="thread-controls">
            <button class="new-thread-btn" onclick="newThread()">New</button>
            <button class="clear-thread-btn" onclick="clearThread()">Clear</button>
            <button class="end-thread-btn" onclick="endThread()">💾 Save</button>
            <button class="memory-toggle-btn" id="memory-toggle" onclick="toggleMemorySearch()">
                <span id="memory-toggle-text">🔍 Memories</span>
            </button>
        </div>
        
        <div class="main-content">
            <!-- Chat Section -->
            <div class="chat-container">
                <div class="chat-header">
                    <h2 id="thread-title">Conversation</h2>
                </div>
                
                <div class="chat-messages" id="chat-messages">
                    <div class="empty-state">
                        Start a conversation...
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
            
            <!-- Memory Network Section -->
            <div class="memory-network-container" id="memory-network-container">
                <div class="memory-network-header">
                    <h3>🧠 Memory Network</h3>
                    <div class="memory-network-controls">
                        <label for="threshold-slider" style="color: var(--gray-400); font-size: 0.8rem;">Threshold:</label>
                        <input type="range" id="threshold-slider" class="threshold-slider" min="0.1" max="0.8" step="0.05" value="0.35">
                        <span id="threshold-value" style="color: var(--primary-400); font-size: 0.8rem;">0.35</span>
                    </div>
                </div>
                
                <div class="memory-network-stats">
                    <div class="stat-item">
                        <span>Memories: </span><span class="stat-value" id="memory-count">0</span>
                    </div>
                    <div class="stat-item">
                        <span>Connections: </span><span class="stat-value" id="connection-count">0</span>
                    </div>
                    <div class="stat-item">
                        <span>Active: </span><span class="stat-value" id="active-memories">0</span>
                    </div>
                    <div class="stat-item">
                        <span>Last: </span><span class="stat-value" id="last-search">None</span>
                    </div>
                </div>
                
                <div id="memory-network">
                    <div class="network-loading">Loading memory network...</div>
                    <div class="memory-activity-indicator" id="activity-indicator">🔥 Memory Activity</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentThreadId = null;
        let isTyping = false;
        let memorySearchEnabled = false;
        
        // Memory Network Variables
        let memoryNetwork = null;
        let networkData = { nodes: [], edges: [] };
        let activeMemories = new Set();
        let lastActivatedMemories = [];
        let animationTimeout = null;

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
                        
                        // Animate memory activation in the network
                        const activatedMemoryIds = data.memory_context.map(ctx => ctx.memory.id);
                        animateMemoryActivation(activatedMemoryIds);
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
                        addMessage(`🧠 ${data.message || 'Conversation ended successfully!'}\\n\\n• ${memoriesText}\\n\\nThese will inform future conversations.`, 'assistant');
                    } else {
                        addMessage('🧠 Conversation ended! No new memories were extracted from this conversation.', 'assistant');
                    }
                    
                    // Refresh the memory network to show new memories
                    setTimeout(() => {
                        loadMemoryNetwork();
                    }, 1000);
                    
                    // Start a new thread
                    setTimeout(() => {
                        newThread();
                    }, 2000);
                } else {
                    addMessage(`❌ ${data.error || 'Failed to end conversation and extract memories.'}`, 'assistant');
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

        // Memory Network Functions
        function initializeMemoryNetwork() {
            const container = document.getElementById('memory-network');
            const options = {
                nodes: {
                    shape: 'dot',
                    scaling: {
                        min: 10,
                        max: 30
                    },
                    font: {
                        size: 12,
                        color: '#e5e7eb'
                    },
                    borderWidth: 2,
                    shadow: true
                },
                edges: {
                    width: 0.15,
                    color: { 
                        color: 'rgba(168,85,247,0.3)',
                        highlight: 'rgba(168,85,247,0.8)',
                        hover: 'rgba(168,85,247,0.6)'
                    },
                    smooth: {
                        type: 'continuous'
                    },
                    shadow: true
                },
                physics: {
                    enabled: true,
                    barnesHut: {
                        gravitationalConstant: -2000,
                        centralGravity: 0.3,
                        springLength: 95,
                        springConstant: 0.04,
                        damping: 0.09,
                        avoidOverlap: 0.1
                    },
                    maxVelocity: 146,
                    minVelocity: 0.1,
                    solver: 'barnesHut',
                    stabilization: {
                        enabled: true,
                        iterations: 1000,
                        updateInterval: 25
                    }
                },
                interaction: {
                    tooltipDelay: 200,
                    hideEdgesOnDrag: false,
                    hideNodesOnDrag: false
                }
            };
            
            memoryNetwork = new vis.Network(container, networkData, options);
            
            // Add hover tooltips
            memoryNetwork.on('hoverNode', function(event) {
                const nodeId = event.node;
                const node = networkData.nodes.find(n => n.id === nodeId);
                if (node) {
                    memoryNetwork.setOptions({
                        nodes: {
                            chosen: {
                                node: function(values, id, selected, hovering) {
                                    if (hovering) {
                                        values.shadow = true;
                                        values.shadowSize = 10;
                                    }
                                }
                            }
                        }
                    });
                }
            });
            
            console.log('🧠 Memory network initialized');
        }

        async function loadMemoryNetwork() {
            try {
                const threshold = parseFloat(document.getElementById('threshold-slider').value);
                const response = await fetch(`/memory-network?threshold=${threshold}`);
                const data = await response.json();
                
                // Update network data
                networkData.nodes = data.nodes.map(node => ({
                    id: node.id,
                    label: node.label.length > 30 ? node.label.substring(0, 30) + '...' : node.label,
                    title: node.label, // Full text for tooltip
                    size: Math.max(15, Math.min(40, 15 + node.score * 0.3)),
                    color: {
                        background: `rgba(168,85,247,${Math.max(0.3, Math.min(1, node.score / 100))})`,
                        border: 'rgba(168,85,247,0.8)',
                        highlight: {
                            background: 'rgba(168,85,247,0.9)',
                            border: 'rgba(168,85,247,1)'
                        }
                    },
                    score: node.score,
                    tags: node.tags || [],
                    created: node.created || ''
                }));
                
                networkData.edges = data.edges.map(edge => ({
                    from: edge.from,
                    to: edge.to,
                    value: edge.value,
                    width: Math.max(1, edge.value * 3),
                    color: {
                        color: `rgba(168,85,247,${Math.max(0.2, edge.value * 0.8)})`,
                        highlight: 'rgba(168,85,247,1)',
                        hover: 'rgba(168,85,247,0.8)'
                    },
                    title: `Similarity: ${edge.value.toFixed(3)}`
                }));
                
                // Update network
                if (memoryNetwork) {
                    memoryNetwork.setData(networkData);
                }
                
                // Update stats
                document.getElementById('memory-count').textContent = data.nodes.length;
                document.getElementById('connection-count').textContent = data.edges.length;
                document.getElementById('active-memories').textContent = activeMemories.size;
                
                console.log(`🧠 Loaded ${data.nodes.length} memories, ${data.edges.length} connections`);
                
            } catch (error) {
                console.error('Error loading memory network:', error);
            }
        }

        function animateMemoryActivation(activatedMemoryIds) {
            if (!memoryNetwork || !activatedMemoryIds.length) return;
            
            console.log('🔥 Animating memory activation:', activatedMemoryIds);
            
            // Show activity indicator
            const indicator = document.getElementById('activity-indicator');
            indicator.classList.add('active');
            setTimeout(() => indicator.classList.remove('active'), 2000);
            
            // Update last search
            document.getElementById('last-search').textContent = new Date().toLocaleTimeString();
            
            // Clear previous animation
            if (animationTimeout) {
                clearTimeout(animationTimeout);
            }
            
            // Reset all nodes to normal
            const updatedNodes = networkData.nodes.map(node => ({
                ...node,
                color: {
                    background: `rgba(168,85,247,${Math.max(0.3, Math.min(1, node.score / 100))})`,
                    border: 'rgba(168,85,247,0.8)'
                },
                borderWidth: 2
            }));
            
            // Highlight activated nodes
            const activatedNodes = new Set(activatedMemoryIds);
            updatedNodes.forEach(node => {
                if (activatedNodes.has(node.id)) {
                    node.color = {
                        background: 'rgba(255,215,0,0.9)', // Gold for activated
                        border: 'rgba(255,215,0,1)'
                    };
                    node.borderWidth = 4;
                }
            });
            
            // Update nodes
            memoryNetwork.setData({
                nodes: updatedNodes,
                edges: networkData.edges
            });
            
            // Animate synaptic propagation
            setTimeout(() => animateSynapticPropagation(activatedMemoryIds), 500);
            
            // Update active memories count
            activeMemories = new Set(activatedMemoryIds);
            document.getElementById('active-memories').textContent = activeMemories.size;
            
            // Reset animation after delay
            animationTimeout = setTimeout(() => {
                memoryNetwork.setData(networkData);
                activeMemories.clear();
                document.getElementById('active-memories').textContent = '0';
            }, 3000);
        }

        function animateSynapticPropagation(startNodeIds) {
            if (!memoryNetwork || !startNodeIds.length) return;
            
            const connectedNodes = new Set();
            const secondDegreeNodes = new Set();
            
            // Find connected nodes (first degree)
            networkData.edges.forEach(edge => {
                if (startNodeIds.includes(edge.from)) {
                    connectedNodes.add(edge.to);
                } else if (startNodeIds.includes(edge.to)) {
                    connectedNodes.add(edge.from);
                }
            });
            
            // Find second degree connections
            networkData.edges.forEach(edge => {
                if (connectedNodes.has(edge.from) && !startNodeIds.includes(edge.to)) {
                    secondDegreeNodes.add(edge.to);
                } else if (connectedNodes.has(edge.to) && !startNodeIds.includes(edge.from)) {
                    secondDegreeNodes.add(edge.from);
                }
            });
            
            // Animate first degree connections
            setTimeout(() => {
                const propagatedNodes = networkData.nodes.map(node => {
                    if (connectedNodes.has(node.id)) {
                        return {
                            ...node,
                            color: {
                                background: 'rgba(34,197,94,0.8)', // Green for propagated
                                border: 'rgba(34,197,94,1)'
                            },
                            borderWidth: 3
                        };
                    }
                    return node;
                });
                
                memoryNetwork.setData({
                    nodes: propagatedNodes,
                    edges: networkData.edges
                });
            }, 300);
            
            // Animate second degree connections
            setTimeout(() => {
                const secondDegreeUpdated = networkData.nodes.map(node => {
                    if (secondDegreeNodes.has(node.id)) {
                        return {
                            ...node,
                            color: {
                                background: 'rgba(59,130,246,0.7)', // Blue for second degree
                                border: 'rgba(59,130,246,0.9)'
                            },
                            borderWidth: 2
                        };
                    }
                    return node;
                });
                
                memoryNetwork.setData({
                    nodes: secondDegreeUpdated,
                    edges: networkData.edges
                });
            }, 800);
            
            console.log(`🔗 Propagated to ${connectedNodes.size} first-degree, ${secondDegreeNodes.size} second-degree nodes`);
        }

        // Threshold slider handler
        document.getElementById('threshold-slider').addEventListener('input', function(e) {
            const value = parseFloat(e.target.value);
            document.getElementById('threshold-value').textContent = value;
            loadMemoryNetwork(); // Reload with new threshold
        });

        // Form submit handler
        document.getElementById('chat-form').addEventListener('submit', function(e) {
            e.preventDefault();
            sendMessage();
        });

        // Initialize
        updateThreadTitle();
        
        // Initialize memory network after page load
        setTimeout(() => {
            initializeMemoryNetwork();
            loadMemoryNetwork();
            
            // Auto-refresh network every 30 seconds
            setInterval(loadMemoryNetwork, 30000);
        }, 1000);
        
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

@app.route('/memory-network')
def memory_network():
    """Get memory network data for visualization"""
    if not MEMORY_AVAILABLE or not memory_manager:
        return jsonify({'nodes': [], 'edges': []})
        
    try:
        # Get threshold from query param, default 0.35
        threshold = float(request.args.get('threshold', 0.35))
        
        # Use the comprehensive function to get connections and similarity matrix
        result = memory_manager._calculate_all_scores_and_connections(threshold)
        if result is None or result == (None, None):
            return jsonify({'nodes': [], 'edges': []})
        
        connections, sim_matrix = result
        all_mems = memory_manager._get_all_memories_flat()
        nodes = []
        edges = []

        # Build nodes
        for mem in all_mems:
            nodes.append({
                'id': mem['id'],
                'label': mem['content'],
                'score': mem.get('score', 0),
                'created': mem.get('created', ''),
                'tags': mem.get('tags', []),
                'size': 20 + min(mem.get('score', 0), 100) * 0.5,
            })

        # Build edges from the connection graph
        n = len(all_mems)
        for i in range(n):
            for j, sim in connections[i]:
                if i < j:  # Avoid duplicate edges
                    edges.append({
                        'from': all_mems[i]['id'],
                        'to': all_mems[j]['id'],
                        'value': sim,
                        'color': 'rgba(168,85,247,' + str(min(1, sim)) + ')',
                        'width': 2 + 12 * sim,
                        'type': 'semantic'
                    })

        return jsonify({'nodes': nodes, 'edges': edges})
        
    except Exception as e:
        print(f"❌ Error in memory-network route: {e}")
        return jsonify({'nodes': [], 'edges': []})

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
        
        # Extract memories with better error handling
        try:
            extracted_memories = extract_memories_from_conversation(conversation)
        except Exception as e:
            print(f"❌ Error during memory extraction: {e}")
            extracted_memories = []
        
        # Add extracted memories to the memory system using both local and API approach
        successful_adds = 0
        if extracted_memories:
            print(f"💾 Extracting {len(extracted_memories)} memories from conversation...")
            
            # First try local memory manager
            if MEMORY_AVAILABLE and memory_manager:
                for memory_text in extracted_memories:
                    try:
                        memory_manager.add_memory(memory_text, ["conversation", "auto-extracted"])
                        print(f"   ✅ Added locally: {memory_text}")
                        successful_adds += 1
                    except Exception as e:
                        print(f"   ❌ Failed to add locally: {memory_text} - {e}")
            
            # Also try to add via API to ensure both servers are synchronized
            try:
                for memory_text in extracted_memories:
                    api_response = requests.post('http://localhost:5000/memories', 
                                               json={
                                                   'content': memory_text, 
                                                   'tags': ['conversation', 'auto-extracted']
                                               }, 
                                               timeout=5)
                    if api_response.status_code == 201:
                        print(f"   🔄 Synced to API: {memory_text}")
                    else:
                        print(f"   ⚠️ API sync failed for: {memory_text}")
            except Exception as e:
                print(f"   ⚠️ API synchronization failed: {e}")
                
            # Force local reload if we have memory manager
            if MEMORY_AVAILABLE and memory_manager:
                try:
                    time.sleep(1)  # Give file operations time to complete
                    memory_manager.reload_from_disk()
                    print(f"💾 Reloaded memory manager after adding {successful_adds} memories")
                except Exception as e:
                    print(f"⚠️ Warning: Could not reload memory manager: {e}")
        
        # Clean up the thread
        if thread_id in chat_threads:
            del chat_threads[thread_id]
        
        return jsonify({
            'success': True,
            'extracted_memories': extracted_memories,
            'count': len(extracted_memories),
            'successful_adds': successful_adds,
            'message': f'Successfully extracted and saved {len(extracted_memories)} memories!'
        })
        
    except Exception as e:
        print(f"❌ Error in end_thread: {e}")
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
            temperature=0.3,
            timeout=30  # Add timeout to prevent hanging
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
        
        # Always search memories if available (try multiple sources)
        if MEMORY_AVAILABLE and memory_manager:
            try:
                print(f"\n🔍 Searching memories for: '{message}'")
                # Force a quick reload to ensure we have the latest memories
                try:
                    memory_manager.reload_from_disk()
                except:
                    pass  # Don't fail if reload fails
                search_results = memory_manager.search_memories(message, top_k=5, min_relevance=0.2)
                memory_context = search_results
                
                # If no results from local search, try API search as backup
                if not search_results:
                    try:
                        api_response = requests.get(f'http://localhost:5000/search/{message}', timeout=5)
                        if api_response.status_code == 200:
                            api_results = api_response.json()
                            if api_results:
                                print(f"   🔄 Found {len(api_results)} memories via API fallback")
                                memory_context = api_results[:5]  # Limit to 5
                    except Exception as e:
                        print(f"   ⚠️ API search fallback failed: {e}")
                
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
        # Add conversation history (excluding the current message to avoid duplication)
        for msg in conversation_history[:-1]:  # Exclude the last message (current user message)
            role = "user" if msg['sender'] == 'user' else "assistant"
            messages.append({"role": role, "content": msg['content']})
        
        # Add the current user message
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
            
            # Avoid duplicate reloads within 5 seconds (increased from 2)
            if current_time - self.last_reload_time < 5.0:
                return
            
            try:
                # Check if file actually changed (avoid reloading on same content)
                if os.path.exists(event.src_path):
                    current_size = os.path.getsize(event.src_path)
                    
                    # Skip if file is empty or being written
                    if current_size == 0:
                        return
                    
                    # Wait a bit for file write to complete
                    time.sleep(0.2)
                    
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
                        print(f"[Watcher] 📁 File locked, skipping reload")
                        return
                
                print(f"[Watcher] 📁 Detected memories.json change, reloading...")
                
                # Add delay before reloading to let file operations complete
                time.sleep(0.5)
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
    try:
        mem_json_path = os.path.join(os.path.dirname(__file__), 'memory-app', 'backend', 'data', 'memories.json')
        watcher_thread = threading.Thread(target=start_memory_file_watcher, args=(memory_manager, mem_json_path), daemon=True)
        watcher_thread.start()
        print("🔄 Memory file watcher started successfully")
    except Exception as e:
        print(f"⚠️ Warning: Could not start memory file watcher: {e}")

if __name__ == '__main__':
    print("🤖 Starting ChatGPT Clone with OpenAI API and Memory Search...")
    print("📱 Open your browser and go to: http://localhost:4000")
    print("💜 Enjoy your purple-themed chat experience!")
    if MEMORY_AVAILABLE:
        print("🧠 Memory search system is available!")
    else:
        print("⚠️  Memory search system is not available")
    app.run(debug=True, host='0.0.0.0', port=4000) 