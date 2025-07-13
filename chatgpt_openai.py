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

# Session memory queue for real-time updates
session_new_memories = []
session_new_memories_lock = threading.Lock()

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

# Track processed request IDs to prevent duplicates
processed_requests = set()
import time
last_cleanup = time.time()

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
            min-height: 400px;
            max-height: calc(100vh - 200px);
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
            margin-top: 10px;
            font-size: 0.85rem;
            color: var(--primary-200);
            overflow: hidden;
            transition: all 0.3s var(--ease-smooth);
        }

        .memory-context-header {
            padding: 10px 15px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--primary-600);
            transition: all 0.3s var(--ease-smooth);
        }

        .memory-context-header:hover {
            background: rgba(168, 85, 247, 0.1);
        }

        .memory-context h4 {
            margin: 0;
            color: var(--primary-300);
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .memory-context-toggle {
            color: var(--primary-400);
            font-size: 0.8rem;
            transition: transform 0.3s var(--ease-smooth);
        }

        .memory-context-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s var(--ease-smooth);
        }

        .memory-context-content.expanded {
            max-height: 300px;
            padding: 10px;
        }

        .memory-item {
            background: rgba(168, 85, 247, 0.1);
            border-left: 3px solid var(--primary-500);
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 4px;
            font-size: 0.8rem;
            line-height: 1.4;
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
            flex-shrink: 0;
            position: sticky;
            bottom: 0;
            z-index: 100;
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
            padding: 20px;
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
            margin-bottom: 15px;
            flex-shrink: 0;
        }

        .memory-network-header h3 {
            color: var(--primary-300);
            margin: 0;
            font-size: 1.2rem;
            font-weight: 500;
        }

        .threshold-controls {
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
            gap: 10px;
            margin-bottom: 15px;
            font-size: 0.85rem;
            color: var(--gray-400);
            flex-wrap: wrap;
        }

        .stat-item {
            background: rgba(31, 41, 55, 0.8);
            backdrop-filter: var(--glass-blur);
            padding: 8px 12px;
            border-radius: 8px;
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
            background: radial-gradient(ellipse at center, rgba(10, 10, 10, 0.98) 0%, rgba(17, 24, 39, 0.95) 60%, rgba(5, 5, 5, 0.99) 100%);
            backdrop-filter: var(--glass-blur);
            position: relative;
            overflow: hidden;
            height: 100%;
            width: 100%;
            min-height: 300px;
            box-shadow: 
                inset 0 0 50px rgba(168, 85, 247, 0.1),
                0 0 30px rgba(168, 85, 247, 0.15);
        }

        #memory-network::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                radial-gradient(circle at 20% 20%, rgba(255, 215, 0, 0.02) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(168, 85, 247, 0.03) 0%, transparent 50%),
                radial-gradient(circle at 40% 70%, rgba(255, 215, 0, 0.01) 0%, transparent 30%);
            pointer-events: none;
            z-index: 1;
        }

        .memory-activity-indicator {
            position: absolute;
            top: 15px;
            right: 15px;
            background: linear-gradient(45deg, #ffd700, #ffed4e);
            color: #46096b;
            padding: 8px 12px;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
            opacity: 0;
            transition: all 0.4s ease;
            border: 2px solid rgba(255, 215, 0, 0.6);
            box-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
            z-index: 10;
        }

        .memory-activity-indicator.active {
            opacity: 1;
            animation: neuralPulse 1.5s ease-in-out infinite;
        }

        @keyframes neuralPulse {
            0%, 100% { 
                transform: scale(1); 
                box-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
            }
            50% { 
                transform: scale(1.05); 
                box-shadow: 0 0 25px rgba(255, 215, 0, 0.8);
            }
        }

        .network-loading {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: var(--gray-400);
            font-style: italic;
            z-index: 2;
            display: none;
        }

        .persistent-node-glow {
            transition: all 0.3s ease-out;
            animation: gentle-pulse 3s ease-in-out infinite;
        }

        @keyframes gentle-pulse {
            0%, 100% { 
                transform: scale(1); 
                opacity: var(--glow-opacity, 0.6); 
            }
            50% { 
                transform: scale(1.4); 
                opacity: calc(var(--glow-opacity, 1) * 1.8); 
            }
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
                    <div class="chat-input-form" id="chat-form">
                        <textarea 
                            class="chat-input" 
                            id="chat-input" 
                            placeholder="Type your message here..."
                            rows="1"
                            onkeydown="handleKeyDown(event)"
                        ></textarea>
                        <button type="button" class="send-button" onclick="console.log('🔥 BUTTON CLICKED - calling sendMessage()'); sendMessage()">Send</button>
                    </div>
                </div>
            </div>
            
            <!-- Memory Network Section -->
            <div class="memory-network-container" id="memory-network-container">
                <div class="memory-network-header">
                    <h3>Neural Memory Network</h3>
                    <div class="threshold-controls">
                        <label for="threshold-slider" style="color: var(--gray-400); font-size: 0.9rem;">Threshold:</label>
                        <input type="range" id="threshold-slider" class="threshold-slider" min="0.1" max="0.8" step="0.05" value="0.35">
                        <span id="threshold-value" style="color: var(--primary-400); font-size: 0.9rem;">0.35</span>
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
        let sendingMessage = false; // Additional flag to prevent duplicates
        
        // Memory Network Variables
        let memoryNetwork = null;
        let networkData = { nodes: [], edges: [] };
        let activeMemories = new Set();
        let currentThreshold = 0.35;
        
        // Advanced Signal Trail System for Neural-like Visualization
        let signalTrails = [];
        let sparkleSystem = [];
        let trailAnimationActive = false;
        let nodeGlowLevels = {}; // Track accumulating glow for each node
        let activeSignals = 0;

        // Auto-resize textarea
        const textarea = document.getElementById('chat-input');
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 150) + 'px';
        });

        // Handle Enter key (Send on Enter, new line on Shift+Enter)
        function handleKeyDown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                console.log('🔥 ENTER KEY PRESSED - calling sendMessage()');
                event.preventDefault();
                event.stopPropagation();
                sendMessage();
                return false;
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
            console.log('🔥 === SENDMESSAGE FUNCTION CALLED ===');
            console.log('🔥 Call stack:', new Error().stack);
            
            const input = document.getElementById('chat-input');
            const sendButton = document.querySelector('.send-button');
            const message = input.value.trim();
            
            console.log('🔥 Current state - message:', !!message, 'isTyping:', isTyping, 'sendingMessage:', sendingMessage);
            
            if (!message || isTyping || sendingMessage) {
                console.log('🔥 ❌ sendMessage BLOCKED - message:', !!message, 'isTyping:', isTyping, 'sendingMessage:', sendingMessage);
                return;
            }
            
            // Set both flags immediately to prevent duplicate calls
            isTyping = true;
            sendingMessage = true;
            
            // Disable input and button completely
            input.disabled = true;
            sendButton.disabled = true;
            sendButton.style.opacity = '0.5';
            sendButton.style.cursor = 'not-allowed';
            
            console.log('🔥 ✅ sendMessage PROCEEDING - UI disabled, flags set');
            
            // Generate unique request ID
            const requestId = 'req_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            console.log('🔥 📝 Request ID generated:', requestId);
            
            // Clear input
            input.value = '';
            input.style.height = 'auto';
            
            // Add user message to chat
            console.log('🔥 📤 Adding user message to chat');
            addMessage(message, 'user');
            
            // Show typing indicator
            console.log('🔥 ⏳ Showing typing indicator');
            showTypingIndicator();
            showSearchingMemories();
            
            try {
                console.log('🔥 🌐 Making fetch request to /send_message');
                const response = await fetch('/send_message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        thread_id: currentThreadId,
                        use_memory_search: memorySearchEnabled,
                        request_id: requestId
                    })
                });
                
                console.log('🔥 📨 Response received - Status:', response.status);
                const data = await response.json();
                console.log('🔥 📋 Response data:', data);
                
                if (data.success) {
                    console.log('🔥 ✅ SUCCESS - Processing successful response');
                    currentThreadId = data.thread_id;
                    updateThreadTitle();
                    
                    // Add AI response with memory context if available
                    if (data.memory_context && data.memory_context.length > 0) {
                        console.log('🔥 🧠 Adding response with memory context');
                        addMessageWithMemoriesInjected(data.response, 'assistant', data.memory_context);
                        
                        // Extract memory IDs and trigger neural animation
                        const activatedMemoryIds = data.memory_context.map(ctx => ctx.memory.id);
                        console.log('🔥 🌟 Triggering memory animation for recalled memories:', activatedMemoryIds);
                        
                        // Delay animation slightly to let the message render first and ensure network is ready
                        setTimeout(() => {
                            // Double-check that memory network is ready
                            if (memoryNetwork && networkData.nodes.length > 0) {
                        animateMemoryActivation(activatedMemoryIds);
                    } else {
                                console.log('🔥 ⚠️ Memory network not ready yet, retrying in 1 second...');
                                setTimeout(() => {
                                    if (memoryNetwork && networkData.nodes.length > 0) {
                                        animateMemoryActivation(activatedMemoryIds);
                                    } else {
                                        console.log('🔥 ❌ Memory network still not ready, skipping animation');
                                    }
                                }, 1000);
                            }
                        }, 200);
                    } else {
                        console.log('🔥 💬 Adding simple response (no memories recalled)');
                        addMessage(data.response, 'assistant');
                    }
                } else if (response.status === 409) {
                    // Duplicate request - silently ignore
                    console.log('🔥 🔕 Duplicate request blocked by server - IGNORING');
                } else {
                    console.log('🔥 ❌ ERROR - Adding error message');
                    addMessageWithMemoriesInjected('Sorry, I encountered an error. Please try again.', 'assistant', []);
                }
            } catch (error) {
                console.log('🔥 💥 CATCH BLOCK - Network error:', error);
                addMessageWithMemoriesInjected('Sorry, I encountered an error. Please try again.', 'assistant', []);
            } finally {
                console.log('🔥 🧹 FINALLY BLOCK - Cleaning up');
                hideTypingIndicator();
                hideSearchingMemories();
                
                // Re-enable input and button
                input.disabled = false;
                sendButton.disabled = false;
                sendButton.style.opacity = '1';
                sendButton.style.cursor = 'pointer';
                
                // Reset the flags
                isTyping = false;
                sendingMessage = false;
                
                console.log('🔥 ✅ UI re-enabled, flags reset - SENDMESSAGE COMPLETE');
                console.log('🔥 === END SENDMESSAGE ===');
            }
        }

        // Add message to chat
        function addMessage(content, sender) {
            console.log('🔥 💬 addMessage called - sender:', sender, 'content:', content.substring(0, 50) + '...');
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
            console.log('🔥 ✅ Message added to DOM');
        }

        // Add message with memories injected info
        function addMessageWithMemoriesInjected(content, sender, memoryContext) {
            console.log('🔥 🧠 addMessageWithMemoriesInjected called - sender:', sender, 'content:', content.substring(0, 50) + '...', 'memories:', memoryContext?.length || 0);
            const messagesContainer = document.getElementById('chat-messages');
            const emptyState = messagesContainer.querySelector('.empty-state');
            
            if (emptyState) {
                emptyState.remove();
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            
            // Build memories injected HTML with collapsible design
            const memoryId = 'memory-' + Date.now();
            let memoriesHtml = '<div class="memory-context">';
            memoriesHtml += `<div class="memory-context-header" onclick="toggleMemoryContext('${memoryId}')">`;
            memoriesHtml += '<h4>🧠 Memories Injected <span class="memory-count">(' + (memoryContext ? memoryContext.length : 0) + ')</span></h4>';
            memoriesHtml += '<span class="memory-context-toggle" id="toggle-' + memoryId + '">▼ Click to view</span>';
            memoriesHtml += '</div>';
            memoriesHtml += `<div class="memory-context-content" id="${memoryId}">`;
            if (memoryContext && memoryContext.length > 0) {
                memoryContext.forEach(memory => {
                    memoriesHtml += `<div class="memory-item">${memory.memory.content}<span class="memory-score">(Score: ${memory.relevance_score.toFixed(2)})</span></div>`;
                });
            } else {
                memoriesHtml += '<div class="memory-item">No relevant memories were injected for this prompt.</div>';
            }
            memoriesHtml += '</div></div>';
            
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
            console.log('🔧 DEBUG: === SAVE MEMORIES BUTTON CLICKED ===');
            console.log('🔧 DEBUG: Current thread ID:', currentThreadId);
            console.log('🔧 DEBUG: Messages in chat:', document.querySelectorAll('.message').length);
            
            if (!currentThreadId) {
                console.log('🔧 DEBUG: No active thread to save memories from');
                addMessage('❌ No active conversation to save memories from.', 'assistant');
                return;
            }

            // No confirmation needed - just save memories

            console.log('🔧 DEBUG: Starting memory extraction process...');
            console.log('🔧 DEBUG: Memory network function available:', typeof loadMemoryNetwork !== 'undefined');
            
            try {
                showTypingIndicator();
                addMessage('🧠 Analyzing conversation and extracting memories...', 'assistant');
                console.log('🔧 DEBUG: Added progress message to chat');
                
                console.log('🔧 DEBUG: Making POST request to /end_thread');
                console.log('🔧 DEBUG: Request payload:', { thread_id: currentThreadId });
                
                const response = await fetch('/end_thread', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        thread_id: currentThreadId
                    })
                });

                console.log('🔧 DEBUG: Response received - Status:', response.status);
                console.log('🔧 DEBUG: Response OK:', response.ok);
                
                const data = await response.json();
                console.log('🔧 DEBUG: Response data:', data);
                console.log('🔧 DEBUG: Success:', data.success);
                console.log('🔧 DEBUG: Extracted memories count:', data.extracted_memories?.length || 0);
                console.log('🔧 DEBUG: Successful adds to memory system:', data.successful_adds || 0);

                if (data.success) {
                    console.log('🔧 DEBUG: ✅ Memory extraction successful!');
                    
                    // DON'T clear the thread - keep it active so user can continue
                    // const oldThreadId = currentThreadId;
                    // currentThreadId = null;  // REMOVED - keep thread active
                    console.log('🔧 DEBUG: Thread preserved - ID still:', currentThreadId);
                    
                    // Show extracted memories with detailed feedback
                    if (data.extracted_memories && data.extracted_memories.length > 0) {
                        const memoriesText = data.extracted_memories.join('\\n• ');
                        addMessage(`✅ Memory extraction completed successfully!\\n\\n📚 Extracted ${data.extracted_memories.length} memories:\\n• ${memoriesText}\\n\\n🔄 Successfully added ${data.successful_adds || data.extracted_memories.length} memories to the system\\n\\n💡 You can continue this chat or click "New Chat" to start fresh.`, 'assistant');
                        console.log('🔧 DEBUG: Added detailed success message with memory list');
                        
                        // Create temporary local nodes immediately for instant feedback
                        console.log('🔧 DEBUG: Creating temporary local nodes for extracted memories...');
                        data.extracted_memories.forEach((memoryText, index) => {
                            const tempMemory = {
                                id: 'temp_' + Date.now() + '_' + index,
                                content: memoryText,
                                score: 1.0,
                                tags: ['conversation', 'auto-extracted', 'temp'],
                                created: new Date().toISOString()
                            };
                            
                            console.log('🔧 DEBUG: Creating temp node:', tempMemory);
                            
                            // Add to memory network if available
                            if (typeof addMemoryToNetworkRealtime === 'function') {
                                addMemoryToNetworkRealtime(tempMemory);
                                console.log('🔧 DEBUG: Added temp memory to network:', tempMemory.id);
                            } else {
                                console.log('🔧 DEBUG: addMemoryToNetworkRealtime not available');
                            }
                        });
                        
                        // Show success notification
                        if (typeof showNewMemoryNotification === 'function') {
                            showNewMemoryNotification(`Added ${data.extracted_memories.length} new memories to network`);
                        }
                    } else {
                        addMessage('✅ Memory extraction completed!\\n\\n📚 No new personal information was found to remember from this conversation.\\n\\n💡 You can continue this chat or click "New Chat" to start fresh.', 'assistant');
                        console.log('🔧 DEBUG: Added success message - no new memories found');
                    }
                    
                    // DON'T auto-clear the chat - user decides when to start new
                    console.log('🔧 DEBUG: Chat preserved - user can continue or manually start new');
                    
                } else {
                    console.log('🔧 DEBUG: ❌ Memory extraction failed');
                    console.log('🔧 DEBUG: Error details:', data.error);
                    addMessage(`❌ Memory extraction failed: ${data.error || 'Unknown error occurred'}\\n\\nPlease check the console for more details.`, 'assistant');
                }
            } catch (error) {
                console.error('🔧 DEBUG: 💥 Exception in endThread:', error);
                console.error('🔧 DEBUG: Exception type:', error.name);
                console.error('🔧 DEBUG: Exception message:', error.message);
                console.error('🔧 DEBUG: Exception stack:', error.stack);
                addMessage('❌ Error during memory extraction. Please check the browser console for details and try again.', 'assistant');
            } finally {
                console.log('🔧 DEBUG: 🧹 Cleanup - hiding typing indicator');
                hideTypingIndicator();
                console.log('🔧 DEBUG: === SAVE MEMORIES PROCESS COMPLETE ===');
            }
        }

        // Toggle memory context visibility
        function toggleMemoryContext(memoryId) {
            const content = document.getElementById(memoryId);
            const toggle = document.getElementById('toggle-' + memoryId);
            
            if (content.classList.contains('expanded')) {
                content.classList.remove('expanded');
                toggle.textContent = '▼ Click to view';
                toggle.style.transform = 'rotate(0deg)';
            } else {
                content.classList.add('expanded');
                toggle.textContent = '▲ Click to hide';
                toggle.style.transform = 'rotate(180deg)';
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
            
            // Clear any loading text first
            container.innerHTML = '<div class="memory-activity-indicator" id="activity-indicator">🔥 Memory Activity</div>';
            
            const options = {
                nodes: {
                    shape: 'dot',
                    scaling: {
                        min: 20,
                        max: 55
                    },
                    font: {
                        size: 11,
                        color: '#ffffff',
                        face: '-apple-system, SF Pro Display, SF Pro Text, Helvetica Neue, Helvetica, Arial, sans-serif',
                        strokeWidth: 0,
                        strokeColor: 'transparent',
                        align: 'center',
                        vadjust: 0,
                        multi: false,
                        bold: {
                            face: '-apple-system, SF Pro Display, SF Pro Text, Helvetica Neue, Helvetica, Arial, sans-serif',
                            size: 11,
                            color: '#ffffff'
                        }
                    },
                    borderWidth: 1,
                    borderWidthSelected: 2,
                    shadow: {
                        enabled: true,
                        color: 'rgba(17,24,39,0.6)',
                        size: 12,
                        x: 0,
                        y: 3
                    },
                    margin: {
                        top: 12,
                        right: 12,
                        bottom: 12,
                        left: 12
                    },
                    chosen: {
                        node: function(values, id, selected, hovering) {
                            if (hovering) {
                                values.shadowSize = 12;
                                values.shadowColor = 'rgba(168,85,247,0.6)';
                                values.borderWidth = 2;
                            }
                        }
                    }
                },
                edges: {
                    width: 1.5,
                    color: { 
                        color: 'rgba(168,85,247,0.15)',
                        highlight: 'rgba(255,215,0,0.9)',
                        hover: 'rgba(255,215,0,0.7)'
                    },
                    smooth: {
                        type: 'curvedCW',
                        roundness: 0.2,
                        forceDirection: 'none'
                    },
                    shadow: {
                        enabled: true,
                        color: 'rgba(17,24,39,0.3)',
                        size: 6,
                        x: 0,
                        y: 2
                    },
                    length: 200,
                    scaling: {
                        min: 1,
                        max: 6
                    },
                    selectionWidth: 2,
                    hoverWidth: 2
                },
                physics: {
                    enabled: true,
                    barnesHut: {
                        gravitationalConstant: -1200,
                        centralGravity: 0.15,
                        springLength: 150,
                        springConstant: 0.02,
                        damping: 0.12,
                        avoidOverlap: 0.2
                    },
                    maxVelocity: 100,
                    minVelocity: 0.1,
                    solver: 'barnesHut',
                    stabilization: {
                        enabled: true,
                        iterations: 1500,
                        updateInterval: 35,
                        fit: true
                    },
                    adaptiveTimestep: false,
                    timestep: 0.3
                },
                interaction: {
                    hover: true,
                    tooltipDelay: 150,
                    zoomView: true,
                    dragView: true,
                    dragNodes: true,
                    selectConnectedEdges: false,
                    hoverConnectedEdges: false,
                    keyboard: {
                        enabled: true,
                        speed: { x: 10, y: 10, zoom: 0.02 },
                        bindToWindow: false
                    },
                    multiselect: false,
                    navigationButtons: false,
                    zoomSpeed: 1.0
                },
                layout: {
                    improvedLayout: true,
                    clusterThreshold: 150,
                    hierarchical: false,
                    randomSeed: 2
                }
            };
            
            memoryNetwork = new vis.Network(container, networkData, options);
            
            // Add click interaction
            memoryNetwork.on('click', function(params) {
                if (params.nodes.length > 0) {
                    const nodeId = params.nodes[0];
                const node = networkData.nodes.find(n => n.id === nodeId);
                if (node) {
                        alert(`Memory: ${node.content}\nScore: ${node.score}`);
                    }
                }
            });

            // Improve dragging responsiveness
            memoryNetwork.on('dragStart', function(params) {
                // Temporarily increase physics responsiveness during drag
                    memoryNetwork.setOptions({
                    physics: {
                        barnesHut: {
                            springConstant: 0.04,
                            damping: 0.2,
                            centralGravity: 0.1
                        },
                        maxVelocity: 150
                    }
                });
            });

            let dragUpdateThrottle = null;
            
            memoryNetwork.on('dragging', function(params) {
                // Throttle glow updates during drag for better performance
                if (params.nodes.length > 0 && !dragUpdateThrottle) {
                    dragUpdateThrottle = requestAnimationFrame(() => {
                        const nodeId = params.nodes[0];
                        if (nodeGlowLevels[nodeId] > 0.01) {
                            updateNodeGlow(nodeId);
                        }
                        dragUpdateThrottle = null;
                    }); // Use requestAnimationFrame for smooth 60fps
                }
            });

            memoryNetwork.on('dragEnd', function(params) {
                // Restore normal physics after drag
                setTimeout(() => {
                    memoryNetwork.setOptions({
                        physics: {
                            barnesHut: {
                                springConstant: 0.02,
                                damping: 0.12,
                                centralGravity: 0.15
                            },
                            maxVelocity: 100
                        }
                    });
                }, 100);
            });

            let stabilizationThrottle = null;
            
            // Update all node glow positions when the network is stabilizing/moving (throttled)
            memoryNetwork.on('stabilizationProgress', () => {
                if (!stabilizationThrottle) {
                    stabilizationThrottle = requestAnimationFrame(() => {
                        for (const nodeId in nodeGlowLevels) {
                            if (nodeGlowLevels[nodeId] > 0.01) {
                                updateNodeGlow(nodeId);
                            }
                        }
                        stabilizationThrottle = null;
                    }); // Use requestAnimationFrame for smooth updates
                }
            });
            
            console.log('🧠 Memory network initialized');
        }

        async function loadMemoryNetwork() {
            try {
                const threshold = parseFloat(document.getElementById('threshold-slider').value);
                const response = await fetch(`/memory-network?threshold=${threshold}`);
                const data = await response.json();
                
                // Initialize node glow levels
                data.nodes.forEach(node => {
                    nodeGlowLevels[node.id] = 0;
                });
                
                // Create nodes with elegant Apple-style design
                networkData.nodes = data.nodes.map(node => {
                    const intensity = Math.max(0.7, Math.min(1, node.score / 100));
                    const size = Math.max(30, Math.min(65, 30 + node.score * 0.45));
                    
                    return {
                    id: node.id,
                        label: node.label.length > 25 ? node.label.substring(0, 25) + '…' : node.label,
                    title: node.label, // Full text for tooltip
                        size: size,
                    color: {
                            background: `rgba(35,4,55,${intensity})`,
                            border: `rgba(255,255,255,${Math.min(0.4, intensity * 0.5)})`,
                        highlight: {
                                background: `rgba(70,9,107,${intensity})`,
                                border: 'rgba(255,255,255,0.8)'
                            },
                            hover: {
                                background: `rgba(50,6,80,${intensity})`,
                                border: 'rgba(255,255,255,0.6)'
                            }
                        },
                        font: {
                            size: Math.max(10, Math.min(12, 8 + size * 0.08)),
                            color: '#ffffff',
                            face: '-apple-system, SF Pro Display, SF Pro Text, Helvetica Neue, Helvetica, Arial, sans-serif',
                            strokeWidth: 0,
                            strokeColor: 'transparent'
                        },
                    score: node.score,
                    tags: node.tags || [],
                        content: node.label,
                    created: node.created || ''
                    };
                });
                
                networkData.edges = data.edges.map(edge => ({
                    from: edge.from,
                    to: edge.to,
                    value: edge.value,
                    width: Math.max(1, edge.value * 6),
                    color: {
                        color: `rgba(168,85,247,${Math.max(0.2, edge.value * 0.8)})`,
                        highlight: 'rgba(255,215,0,1)',
                        hover: 'rgba(255,215,0,0.8)'
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
                console.log('🧠 📊 Available node IDs:', data.nodes.map(n => n.id));
                
                // Start glow decay system
                startGlowDecay();
                
            } catch (error) {
                console.error('Error loading memory network:', error);
            }
        }

        function animateMemoryActivation(activatedMemoryIds) {
            if (!memoryNetwork || !activatedMemoryIds.length) {
                console.log('🔥 ❌ Cannot animate - missing network or no memory IDs');
                return;
            }
            
            console.log('🔥 🌟 STARTING MEMORY ACTIVATION ANIMATION');
            console.log('🔥 📝 Activating memory IDs:', activatedMemoryIds);
            
            // Verify these nodes exist in our network
            const existingNodeIds = networkData.nodes.map(node => node.id);
            const validMemoryIds = activatedMemoryIds.filter(id => existingNodeIds.includes(id));
            const invalidMemoryIds = activatedMemoryIds.filter(id => !existingNodeIds.includes(id));
            
            if (invalidMemoryIds.length > 0) {
                console.log('🔥 ⚠️ Some memory IDs not found in network:', invalidMemoryIds);
            }
            
            if (validMemoryIds.length === 0) {
                console.log('🔥 ❌ No valid memory IDs found in current network');
                return;
            }
            
            console.log('🔥 ✅ Valid memory IDs for animation:', validMemoryIds);
            
            // Show activity indicator
            const indicator = document.getElementById('activity-indicator');
            if (indicator) {
                indicator.classList.add('active');
                setTimeout(() => {
                    if (indicator) {
                        indicator.classList.remove('active');
                    }
                }, 4000);
            }
            
            // Update last search time
            const lastSearchElement = document.getElementById('last-search');
            if (lastSearchElement) {
                lastSearchElement.textContent = new Date().toLocaleTimeString();
            }
            
            // Start the signal animation with valid IDs only
            setTimeout(() => {
                console.log('🔥 🚀 Starting neural propagation effect...');
                createNeuralPropagationEffect(validMemoryIds);
            }, 100); // Reduced delay for more immediate response
            
            // Update active memories count
            activeMemories = new Set(validMemoryIds);
            const activeMemoriesElement = document.getElementById('active-memories');
            if (activeMemoriesElement) {
                activeMemoriesElement.textContent = activeMemories.size;
            }
            
            // Clear active memories after animation completes
            setTimeout(() => {
                activeMemories.clear();
                const activeMemoriesElement = document.getElementById('active-memories');
                if (activeMemoriesElement) {
                    activeMemoriesElement.textContent = '0';
                }
            }, 5000);
        }

        function createNeuralPropagationEffect(activatedMemoryIds) {
            console.log('🔥 ⚡ Creating neural propagation effect for:', activatedMemoryIds);
            
            // Reset global visited nodes for new simulation
            globalVisitedNodes.clear();
            
            // Add immediate effects to activated nodes
            activatedMemoryIds.forEach((startNodeId, index) => {
                console.log(`🔥 💫 Activating node ${index + 1}/${activatedMemoryIds.length}: ${startNodeId}`);
                
                // Give initial activated nodes immediate glow, pulse, and vibration
                addNodeGlow(startNodeId, 1.0);
                createNodePulse(startNodeId, 1.0);
                createNodeVibration(startNodeId, 1.0);
            });
            
            // Start signal propagation from each activated node with slight delay for visual effect
            activatedMemoryIds.forEach((startNodeId, index) => {
                setTimeout(() => {
                    console.log(`🔥 🌊 Starting propagation from node: ${startNodeId}`);
                    propagateSignalFromNode(startNodeId, 0, new Set(), 1.0);
                }, index * 150); // Stagger the start of each propagation
            });
        }

        // Global visited tracking to prevent infinite loops
        let globalVisitedNodes = new Set();
        
        async function propagateSignalFromNode(currentNodeId, hopCount, visitedNodes, signalStrength) {
            // Stop if we've reached max hops, signal is too weak, or node already visited globally
            if (hopCount >= 5 || signalStrength < 0.15 || globalVisitedNodes.has(currentNodeId)) {
                return;
            }
            
            // Add current node to both local and global visited sets
            const newVisited = new Set(visitedNodes);
            newVisited.add(currentNodeId);
            globalVisitedNodes.add(currentNodeId);
            
            // Add glow to current node
            addNodeGlow(currentNodeId, signalStrength);
            
            // Find all connected neighbors
            const neighbors = getConnectedNeighbors(currentNodeId);
            
            // Filter out already visited neighbors (check global visited)
            const unvisitedNeighbors = neighbors.filter(neighborId => !globalVisitedNodes.has(neighborId));
            
            if (unvisitedNeighbors.length === 0) {
                return; // No more neighbors to visit
            }
            
            // Propagate to each neighbor with staggered timing
            const propagationPromises = unvisitedNeighbors.map((neighborId, index) => {
                return new Promise(resolve => {
                    setTimeout(async () => {
                        const newStrength = signalStrength * 0.85; // Less signal degradation
                        
                        // Animate signal to neighbor with hop count for fading trails
                        await animateSignalToNeighbor(currentNodeId, neighborId, newStrength, `hop-${hopCount}-${index}`, hopCount);
                        
                        // Continue propagation from neighbor after shorter delay
                        setTimeout(() => {
                            propagateSignalFromNode(neighborId, hopCount + 1, newVisited, newStrength);
                            resolve();
                        }, 50); // Even shorter delay between hops
                    }, index * 75); // Even faster staggering
                });
            });
            
            await Promise.all(propagationPromises);
        }

        function getConnectedNeighbors(nodeId) {
            const neighbors = [];
            networkData.edges.forEach(edge => {
                if (edge.from === nodeId) {
                    neighbors.push(edge.to);
                } else if (edge.to === nodeId) {
                    neighbors.push(edge.from);
                }
            });
            return neighbors;
        }





        async function animateSignalToNeighbor(fromId, toId, strength, signalId, hopCount = 0) {
            return new Promise(resolve => {
                activeSignals++;
                
                // Calculate fading strength based on hop count (50% fainter each hop)
                const fadedStrength = strength * Math.pow(0.8, hopCount);
                
                const particle = createSignalParticle(fadedStrength, signalId);
            const container = document.getElementById('memory-network');
                const containerRect = container.getBoundingClientRect();
                
                const animationDuration = 100; // Much faster signal travel
                const startTime = Date.now();
                const trail = [];
                
                const animate = () => {
                    const elapsed = Date.now() - startTime;
                    const progress = Math.min(elapsed / animationDuration, 1);
                    
                    const positions = memoryNetwork.getPositions([fromId, toId]);
                    const fromPos = memoryNetwork.canvasToDOM(positions[fromId]);
                    const toPos = memoryNetwork.canvasToDOM(positions[toId]);
                    
                    const eased = easeInOutCubic(progress);
                    
                    // Create curved path similar to vis.js edges
                    const { currentX, currentY } = getCurvedPathPosition(fromPos, toPos, eased, fromId, toId);
                    
                    particle.style.left = (containerRect.left + currentX) + 'px';
                    particle.style.top = (containerRect.top + currentY) + 'px';
                    
                    // Create continuous trail effect
                    trail.push({ x: currentX, y: currentY, time: elapsed });
                    
                    // Keep trail length manageable
                    if (trail.length > 15) {
                        trail.shift();
                    }
                    
                    // Draw continuous trail with faded strength
                    if (trail.length > 1) {
                        drawContinuousTrail(trail, fadedStrength, containerRect, signalId);
                    }
                    
                    // Dynamic scaling and opacity using faded strength
                    const scale = fadedStrength * (1 + Math.sin(progress * Math.PI * 2) * 0.2);
                    particle.style.transform = `translate(-50%, -50%) scale(${scale})`;
                    particle.style.opacity = Math.max(0.2, fadedStrength * (Math.sin(progress * Math.PI) * 0.7 + 0.3));
                    
                    if (progress < 1) {
                        requestAnimationFrame(animate);
                    } else {
                        // Signal reaches destination with faded strength
                        addNodeGlow(toId, fadedStrength);
                        createNodePulse(toId, fadedStrength);
                        createNodeVibration(toId, fadedStrength);
                        
                        particle.style.transition = 'all 0.4s ease-out';
                        particle.style.opacity = '0';
                        particle.style.transform = 'translate(-50%, -50%) scale(0)';
                        
                        setTimeout(() => {
                            particle.remove();
                            // Clean up trail for this signal
                            const trailElement = document.querySelector(`.continuous-trail-${signalId}`);
                            if (trailElement) {
                                trailElement.style.transition = 'opacity 0.3s ease-out';
                                trailElement.style.opacity = '0';
                                setTimeout(() => trailElement.remove(), 300);
                            }
                            activeSignals--;
                            resolve();
                        }, 400);
                    }
                };
                
                requestAnimationFrame(animate);
            });
        }

        function createSignalParticle(strength, signalId) {
            const particle = document.createElement('div');
            const size = Math.max(16, 32 * strength); // Larger particles
            const intensity = Math.max(0.7, strength); // Higher minimum intensity
            
            particle.className = `signal-particle-${signalId}`;
            particle.style.position = 'fixed';
            particle.style.width = size + 'px';
            particle.style.height = size + 'px';
            particle.style.borderRadius = '50%';
            particle.style.background = `radial-gradient(circle, rgba(255, 255, 255, ${intensity}) 0%, rgba(255, 215, 0, ${intensity * 0.9}) 30%, rgba(255, 152, 0, ${intensity * 0.7}) 100%)`;
            particle.style.boxShadow = `0 0 ${size * 2}px rgba(255, 215, 0, ${intensity}), 0 0 ${size * 4}px rgba(255, 152, 0, ${intensity * 0.8}), 0 0 ${size * 6}px rgba(255, 215, 0, ${intensity * 0.4})`;
            particle.style.zIndex = '995';
            particle.style.pointerEvents = 'none';
            particle.style.transform = 'translate(-50%, -50%)';
            document.body.appendChild(particle);
            return particle;
        }

        function drawContinuousTrail(trail, strength, containerRect, signalId = 'default') {
            // Remove any existing trail for this specific signal
            const existingTrail = document.querySelector(`.continuous-trail-${signalId}`);
            if (existingTrail) {
                existingTrail.remove();
            }
            
            // Create SVG for smooth trail
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.className = `continuous-trail continuous-trail-${signalId}`;
            svg.style.position = 'fixed';
            svg.style.top = '0';
            svg.style.left = '0';
            svg.style.width = '100vw';
            svg.style.height = '100vh';
            svg.style.pointerEvents = 'none';
            svg.style.zIndex = '990';
            document.body.appendChild(svg);
            
            // Create path for trail
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            
            // Build path data
            let pathData = '';
            trail.forEach((point, index) => {
                const x = containerRect.left + point.x;
                const y = containerRect.top + point.y;
                
                if (index === 0) {
                    pathData += `M ${x} ${y}`;
                } else {
                    pathData += ` L ${x} ${y}`;
                }
            });
            
            path.setAttribute('d', pathData);
            path.setAttribute('stroke', `rgba(255, 215, 0, ${strength * 0.8})`);
            path.setAttribute('stroke-width', Math.max(3, strength * 6));
            path.setAttribute('fill', 'none');
            path.setAttribute('stroke-linecap', 'round');
            path.setAttribute('stroke-linejoin', 'round');
            path.style.filter = `drop-shadow(0 0 ${strength * 8}px rgba(255, 215, 0, ${strength * 0.6}))`;
            
            // Add gradient effect
            const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
            const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
            gradient.setAttribute('id', 'trailGradient');
            gradient.setAttribute('gradientUnits', 'userSpaceOnUse');
            
            const stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stop1.setAttribute('offset', '0%');
            stop1.setAttribute('stop-color', `rgba(255, 215, 0, 0)`);
            
            const stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stop2.setAttribute('offset', '70%');
            stop2.setAttribute('stop-color', `rgba(255, 215, 0, ${strength * 0.6})`);
            
            const stop3 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stop3.setAttribute('offset', '100%');
            stop3.setAttribute('stop-color', `rgba(255, 255, 255, ${strength})`);
            
            gradient.appendChild(stop1);
            gradient.appendChild(stop2);
            gradient.appendChild(stop3);
            defs.appendChild(gradient);
            svg.appendChild(defs);
            
            path.setAttribute('stroke', 'url(#trailGradient)');
            svg.appendChild(path);
            
            // Auto-remove trail after animation (optimized)
            setTimeout(() => {
                if (svg.parentNode) {
                    svg.remove(); // Direct removal for better performance
                }
            }, 150); // Shorter timeout for faster cleanup
        }

        function addNodeGlow(nodeId, strength) {
            // Set glow strength (don't accumulate, just set to current strength)
            nodeGlowLevels[nodeId] = Math.min(1.0, strength);
            updateNodeGlow(nodeId);
            createNodePulse(nodeId, strength);
            
            // Restart decay interval if not already running
            if (!glowDecayInterval) {
                startGlowDecay();
            }
        }

        function updateNodeGlow(nodeId) {
            const glowLevel = nodeGlowLevels[nodeId];
            if (glowLevel <= 0.01) {
                const existingGlow = document.getElementById(`node-glow-${nodeId}`);
                if (existingGlow) existingGlow.remove();
                    return;
                }
                
            // Cache DOM queries for better performance
            let glow = document.getElementById(`node-glow-${nodeId}`);
            
            if (!glow) {
                glow = document.createElement('div');
                glow.id = `node-glow-${nodeId}`;
                glow.className = 'persistent-node-glow';
                glow.style.position = 'fixed';
                glow.style.borderRadius = '50%';
                glow.style.pointerEvents = 'none';
                glow.style.zIndex = '992';
                glow.style.transition = 'opacity 0.3s ease-out'; // Keep opacity transition for smooth appearance
                glow.style.animation = 'gentle-pulse 2s ease-in-out infinite';
                document.body.appendChild(glow);
            }

            // Get positions only once
            const positions = memoryNetwork.getPositions([nodeId]);
            const nodePos = memoryNetwork.canvasToDOM(positions[nodeId]);
            const container = document.getElementById('memory-network');
            const containerRect = container.getBoundingClientRect();
            
            const size = Math.max(60, 120 * glowLevel);
            
            // Batch style updates using transform for better performance
            const x = containerRect.left + nodePos.x - size/2;
            const y = containerRect.top + nodePos.y - size/2;
            
            glow.style.transform = `translate(${x}px, ${y}px)`;
            glow.style.width = size + 'px';
            glow.style.height = size + 'px';
            glow.style.background = `radial-gradient(circle, rgba(168,85,247,${Math.floor(glowLevel * 120).toString(16).padStart(2, '0')}) 0%, rgba(168,85,247,${Math.floor(glowLevel * 60).toString(16).padStart(2, '0')}) 40%, transparent 70%)`;
            glow.style.opacity = Math.min(0.8, glowLevel * 1.1);
            glow.style.filter = `blur(${Math.max(2, 6 * glowLevel)}px)`;
            glow.style.setProperty('--glow-opacity', glowLevel.toString());
        }

        function createNodePulse(nodeId, strength) {
            const positions = memoryNetwork.getPositions([nodeId]);
            const nodePos = memoryNetwork.canvasToDOM(positions[nodeId]);
            const container = document.getElementById('memory-network');
            const containerRect = container.getBoundingClientRect();
            
            for (let i = 0; i < Math.ceil(strength * 2); i++) {
                setTimeout(() => {
                    const pulse = document.createElement('div');
                    const size = 80 * strength;
                    
                    pulse.style.position = 'fixed';
                    pulse.style.left = (containerRect.left + nodePos.x - size/2) + 'px';
                    pulse.style.top = (containerRect.top + nodePos.y - size/2) + 'px';
                    pulse.style.width = size + 'px';
                    pulse.style.height = size + 'px';
                    pulse.style.borderRadius = '50%';
                    pulse.style.border = '3px solid rgba(168,85,247,0.8)';
                    pulse.style.pointerEvents = 'none';
                    pulse.style.zIndex = '993';
                    pulse.style.opacity = strength;
                    document.body.appendChild(pulse);

                    pulse.style.transition = 'all 0.8s ease-out';
                    pulse.style.transform = 'scale(2.5)';
                    pulse.style.opacity = '0';

                    setTimeout(() => pulse.remove(), 800);
                }, i * 150);
            }
        }

        function createNodeVibration(nodeId, strength) {
            const positions = memoryNetwork.getPositions([nodeId]);
            const nodePos = memoryNetwork.canvasToDOM(positions[nodeId]);
            const container = document.getElementById('memory-network');
            const containerRect = container.getBoundingClientRect();
            
            // Create vibration effect overlay
            const vibration = document.createElement('div');
            const size = Math.max(40, 60 * strength);
            
            vibration.style.position = 'fixed';
            vibration.style.left = (containerRect.left + nodePos.x - size/2) + 'px';
            vibration.style.top = (containerRect.top + nodePos.y - size/2) + 'px';
            vibration.style.width = size + 'px';
            vibration.style.height = size + 'px';
            vibration.style.borderRadius = '50%';
            vibration.style.background = `radial-gradient(circle, rgba(255,255,255,${strength * 0.8}) 0%, rgba(255,215,0,${strength * 0.6}) 50%, transparent 100%)`;
            vibration.style.pointerEvents = 'none';
            vibration.style.zIndex = '994';
            vibration.style.opacity = Math.min(0.9, strength * 1.2);
            document.body.appendChild(vibration);

            // Create intense vibration animation
            const vibrationIntensity = Math.max(2, strength * 8);
            const vibrationDuration = Math.max(200, strength * 400);
            const vibrationSteps = 12;
            
            let step = 0;
            const vibrateInterval = setInterval(() => {
                if (step >= vibrationSteps) {
                    clearInterval(vibrateInterval);
                    vibration.style.transition = 'all 0.2s ease-out';
                    vibration.style.opacity = '0';
                    vibration.style.transform = 'scale(0.5)';
                    setTimeout(() => vibration.remove(), 200);
                    return;
                }
                
                // Random shake in all directions
                const offsetX = (Math.random() - 0.5) * vibrationIntensity;
                const offsetY = (Math.random() - 0.5) * vibrationIntensity;
                const scale = 1 + (Math.random() - 0.5) * 0.3 * strength;
                
                vibration.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scale})`;
                
                step++;
            }, vibrationDuration / vibrationSteps);
        }

        let glowDecayInterval = null;
        
        function startGlowDecay() {
            // Clear any existing interval
            if (glowDecayInterval) {
                clearInterval(glowDecayInterval);
            }
            
            glowDecayInterval = setInterval(() => {
                let hasActiveGlows = false;
                
                for (const nodeId in nodeGlowLevels) {
                    if (nodeGlowLevels[nodeId] > 0.001) {
                        nodeGlowLevels[nodeId] *= 0.3; // Very fast decay
                        updateNodeGlow(nodeId);
                        hasActiveGlows = true;
                    } else if (nodeGlowLevels[nodeId] > 0) {
                        nodeGlowLevels[nodeId] = 0;
                        const existingGlow = document.getElementById(`node-glow-${nodeId}`);
                        if (existingGlow) {
                            existingGlow.style.transition = 'opacity 0.2s ease-out';
                            existingGlow.style.opacity = '0';
                            setTimeout(() => existingGlow.remove(), 200);
                        }
                    }
                }
                
                // Stop the interval if no active glows to save performance
                if (!hasActiveGlows) {
                    clearInterval(glowDecayInterval);
                    glowDecayInterval = null;
                }
            }, 100); // Reduced frequency for better performance
        }

        function easeInOutCubic(t) {
            return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
        }

        function getCurvedPathPosition(fromPos, toPos, progress, fromId, toId) {
            // Find the actual edge between these nodes
            const edge = networkData.edges.find(e => 
                (e.from === fromId && e.to === toId) || 
                (e.from === toId && e.to === fromId)
            );
            
            if (!edge) {
                // If no edge found, use straight line
                const currentX = fromPos.x + (toPos.x - fromPos.x) * progress;
                const currentY = fromPos.y + (toPos.y - fromPos.y) * progress;
                return { currentX, currentY };
            }
            
            // Calculate distance and direction
            const dx = toPos.x - fromPos.x;
            const dy = toPos.y - fromPos.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            // Use the global edge configuration (curvedCW with roundness 0.25)
            // For curvedCW (clockwise), the curve goes to the right when traveling from->to
            let curveDirection = -1; // Flip to opposite direction
            
            // Determine if we're going from->to or to->from to maintain consistent curve direction
            const isReversed = edge.from === toId;
            if (isReversed) {
                curveDirection = 1; // Reverse for opposite direction
            }
            
            // Use the roundness value from global configuration (0.25 for curvedCW)
            const roundness = 0.25;
            const curveOffset = distance * roundness * curveDirection;
            
            // Calculate perpendicular vector (rotated 90 degrees)
            const perpX = -dy / distance;
            const perpY = dx / distance;
            
            // Calculate control point for quadratic bezier curve
            const midX = (fromPos.x + toPos.x) / 2 + perpX * curveOffset;
            const midY = (fromPos.y + toPos.y) / 2 + perpY * curveOffset;
            
            // Quadratic bezier curve calculation
            const t = progress;
            const currentX = (1 - t) * (1 - t) * fromPos.x + 
                           2 * (1 - t) * t * midX + 
                           t * t * toPos.x;
            const currentY = (1 - t) * (1 - t) * fromPos.y + 
                           2 * (1 - t) * t * midY + 
                           t * t * toPos.y;
            
            return { currentX, currentY };
        }

        // Threshold slider handler
        document.getElementById('threshold-slider').addEventListener('input', function(e) {
            currentThreshold = parseFloat(e.target.value);
            document.getElementById('threshold-value').textContent = currentThreshold.toFixed(2);
            loadMemoryNetwork(); // Reload with new threshold
        });

        // No form submit handler needed anymore since we removed the form

        // Initialize
        updateThreadTitle();
        
        // Initialize memory network after page load
        setTimeout(() => {
            initializeMemoryNetwork();
                loadMemoryNetwork();
    
    console.log('🎉 Memory Network initialized! Auto-refresh disabled by default for persistent node positions.');
    console.log('💡 Use the refresh button or enable auto-refresh if needed.');
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

@app.route('/new-memories')
def get_new_memories():
    """Get and clear the queue of new memories for real-time network updates"""
    print("🔧 DEBUG: ========== /new-memories endpoint called ==========")
    
    with session_new_memories_lock:
        print(f"🔧 DEBUG: Session queue contains {len(session_new_memories)} memories before copy")
        if session_new_memories:
            print(f"🔧 DEBUG: Session queue contents: {[m.get('content', '')[:50] + '...' for m in session_new_memories]}")
        
        new_memories = session_new_memories.copy()
        session_new_memories.clear()
        
        print(f"🔧 DEBUG: Returning {len(new_memories)} memories to frontend")
        print(f"🔧 DEBUG: Session queue cleared, now contains {len(session_new_memories)} memories")
    
    response_data = {
        'memories': new_memories,
        'count': len(new_memories)
    }
    
    print(f"🔧 DEBUG: /new-memories response: {response_data}")
    print("🔧 DEBUG: ========== /new-memories endpoint complete ==========")
    
    return jsonify(response_data)

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
    global processed_requests, last_cleanup
    
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        thread_id = data.get('thread_id')
        use_memory_search = data.get('use_memory_search', False)
        request_id = data.get('request_id')
        
        # Clean up old request IDs every 5 minutes
        current_time = time.time()
        if current_time - last_cleanup > 300:  # 5 minutes
            processed_requests.clear()
            last_cleanup = current_time
            print("🧹 Cleaned up old request IDs")
        
        # Check for duplicate request
        if request_id and request_id in processed_requests:
            print(f"⚠️ Duplicate request detected: {request_id}")
            return jsonify({'success': False, 'error': 'Duplicate request detected'}), 409
        
        # Add request ID to processed set
        if request_id:
            processed_requests.add(request_id)
            print(f"✅ Processing request: {request_id}")
        
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
        print("🔧 DEBUG: === /end_thread endpoint called ===")
        
        data = request.get_json()
        thread_id = data.get('thread_id')
        
        print(f"🔧 DEBUG: Request data: {data}")
        print(f"🔧 DEBUG: Extracted thread_id: {thread_id}")
        print(f"🔧 DEBUG: Available threads: {list(chat_threads.keys())}")
        
        if not thread_id or thread_id not in chat_threads:
            print(f"🔧 DEBUG: Thread not found - thread_id: {thread_id}, exists: {thread_id in chat_threads if thread_id else False}")
            return jsonify({'success': False, 'error': 'Thread not found'})
        
        conversation = chat_threads[thread_id]
        print(f"🔧 DEBUG: Found conversation with {len(conversation)} messages")
        
        # Log conversation preview for debugging
        for i, msg in enumerate(conversation[:3]):
            print(f"🔧 DEBUG: Message {i+1}: {msg['sender']} - {msg['content'][:50]}...")
        
        if len(conversation) > 3:
            print(f"🔧 DEBUG: ... and {len(conversation) - 3} more messages")
        
        # Extract memories with better error handling
        try:
            print("🔧 DEBUG: Calling extract_memories_from_conversation...")
            extracted_memories = extract_memories_from_conversation(conversation)
            print(f"🔧 DEBUG: Memory extraction returned {len(extracted_memories)} memories")
        except Exception as e:
            print(f"❌ Error during memory extraction: {e}")
            print(f"🔧 DEBUG: Memory extraction exception: {type(e).__name__}: {e}")
            extracted_memories = []
        
        # Add extracted memories to the memory system using both local and API approach
        successful_adds = 0
        if extracted_memories:
            print(f"💾 Extracting {len(extracted_memories)} memories from conversation...")
            print(f"🔧 DEBUG: MEMORY_AVAILABLE: {MEMORY_AVAILABLE}, memory_manager: {memory_manager}")
            
            # First try local memory manager
            if MEMORY_AVAILABLE and memory_manager:
                for memory_text in extracted_memories:
                    try:
                        print(f"🔧 DEBUG: Adding memory: {memory_text[:50]}...")
                        new_memory = memory_manager.add_memory(memory_text, ["conversation", "auto-extracted"])
                        print(f"🔧 DEBUG: New memory object: {new_memory}")
                        print(f"   ✅ Added locally: {memory_text}")
                        successful_adds += 1
                        
                        # Add new memory to session queue for real-time network update
                        if new_memory:
                            memory_data = {
                                'id': new_memory['id'],
                                'content': new_memory['content'],
                                'score': new_memory.get('score', 0),
                                'tags': new_memory.get('tags', []),
                                'created': new_memory.get('created', '')
                            }
                            print(f"🔧 DEBUG: ========== ADDING TO SESSION QUEUE ==========")
                            print(f"🔧 DEBUG: Memory data prepared: {memory_data}")
                            print(f"🔧 DEBUG: Current session queue size before add: {len(session_new_memories)}")
                            
                            with session_new_memories_lock:
                                session_new_memories.append(memory_data)
                                queue_size_after = len(session_new_memories)
                                print(f"🔧 DEBUG: Session queue size after add: {queue_size_after}")
                                print(f"🔧 DEBUG: Session queue contents: {[m.get('content', '')[:30] + '...' for m in session_new_memories]}")
                            
                            print(f"🌐 ✅ Queued new memory for network: {memory_data['id']}")
                            print(f"🔧 DEBUG: ========== SESSION QUEUE ADD COMPLETE ==========")
                        else:
                            print(f"🔧 DEBUG: ❌ new_memory is None/empty - cannot add to session queue!")
                            print(f"🔧 DEBUG: new_memory object: {new_memory}")
                    except Exception as e:
                        print(f"   ❌ Failed to add locally: {memory_text} - {e}")
                        print(f"🔧 DEBUG: Exception details: {type(e).__name__}: {e}")
            else:
                print(f"🔧 DEBUG: Memory system not available - MEMORY_AVAILABLE: {MEMORY_AVAILABLE}, memory_manager: {memory_manager}")
            
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
        
        # DON'T clean up the thread - keep it active so user can continue chatting
        # if thread_id in chat_threads:
        #     del chat_threads[thread_id]
        #     print(f"🔧 DEBUG: Cleaned up thread {thread_id}")
        print(f"🔧 DEBUG: Thread {thread_id} preserved for continued conversation")
        
        print(f"🔧 DEBUG: Preparing response - extracted: {len(extracted_memories)}, successful_adds: {successful_adds}")
        
        return jsonify({
            'success': True,
            'extracted_memories': extracted_memories,
            'count': len(extracted_memories),
            'successful_adds': successful_adds,
            'message': f'Successfully extracted and saved {len(extracted_memories)} memories!'
        })
        
    except Exception as e:
        print(f"❌ Error in end_thread: {e}")
        print(f"🔧 DEBUG: Exception type: {type(e).__name__}")
        print(f"🔧 DEBUG: Exception details: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def extract_memories_from_conversation(conversation):
    """
    Extract up to 5 meaningful memories from a conversation using OpenAI
    """
    print(f"🔧 DEBUG: extract_memories_from_conversation called with {len(conversation) if conversation else 0} messages")
    
    if not conversation or len(conversation) < 2:
        print("🔧 DEBUG: Conversation too short, returning empty list")
        return []
    
    # Build conversation text
    conversation_text = ""
    for msg in conversation:
        role = "User" if msg['sender'] == 'user' else "Assistant"
        conversation_text += f"{role}: {msg['content']}\n"
    
    print(f"🔧 DEBUG: Built conversation text, length: {len(conversation_text)}")
    
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

        print("🔧 DEBUG: Calling OpenAI API for memory extraction...")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": extraction_prompt}],
            max_tokens=300,
            temperature=0.3,
            timeout=30  # Add timeout to prevent hanging
        )
        
        result = response.choices[0].message.content.strip()
        print(f"🔧 DEBUG: OpenAI response: {result}")
        
        if result == "NONE" or not result:
            print("🔧 DEBUG: No memories extracted (NONE or empty result)")
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
                print(f"🔧 DEBUG: Parsed memory: {line}")
        
        print(f"🔧 DEBUG: Extracted {len(memories)} memories total")
        return memories[:5]  # Limit to 5 memories
        
    except Exception as e:
        print(f"❌ Error extracting memories: {e}")
        print(f"🔧 DEBUG: Exception type: {type(e).__name__}")
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
                print(f"🔧 DEBUG: Using min_relevance=0.35 threshold")
                # Force a quick reload to ensure we have the latest memories
                try:
                    memory_manager.reload_from_disk()
                except:
                    pass  # Don't fail if reload fails
                search_results = memory_manager.search_memories(message, top_k=10, min_relevance=0.1)  # Get more results with lower threshold
                # Apply STRICT relevance filtering - only relevance_score >= 0.35
                strict_filtered_results = [r for r in search_results if r.get('relevance_score', 0) >= 0.35]
                print(f"🔧 DEBUG: Raw search returned {len(search_results)} results, strict filter kept {len(strict_filtered_results)}")
                memory_context = strict_filtered_results[:5]  # Take top 5 after strict filtering
                search_results = memory_context  # Update search_results to use filtered ones
                
                # If no results from strict local search, try API search as backup with STRICT filtering
                if not search_results:
                    try:
                        api_response = requests.get(f'http://localhost:5000/search/{message}', timeout=5)
                        if api_response.status_code == 200:
                            api_results = api_response.json()
                            if api_results:
                                # Apply STRICT relevance filtering to API results - ONLY relevance_score >= 0.35
                                filtered_api_results = []
                                for result in api_results:
                                    if isinstance(result, dict):
                                        relevance_score = result.get('relevance_score', 0)  # Only check relevance_score
                                        if relevance_score >= 0.35:
                                            filtered_api_results.append(result)
                                        print(f"   API result: '{result.get('memory', {}).get('content', 'N/A')[:30]}...' relevance: {relevance_score:.3f} {'✅' if relevance_score >= 0.35 else '❌'}")
                                
                                if filtered_api_results:
                                    print(f"   🔄 Found {len(filtered_api_results)} STRICT filtered memories via API fallback (from {len(api_results)} total)")
                                    memory_context = filtered_api_results[:5]  # Limit to 5
                                    search_results = memory_context
                                else:
                                    print(f"   🔄 API returned {len(api_results)} memories but NONE met STRICT 0.35 relevance threshold")
                    except Exception as e:
                        print(f"   ⚠️ API search fallback failed: {e}")
                
                print(f"📊 Found {len(search_results)} STRICT filtered memories (relevance >= 0.35):")
                for i, result in enumerate(search_results):
                    print(f"  {i+1}. '{result['memory']['content']}' (relevance: {result['relevance_score']:.3f}, final: {result['final_score']:.3f})")
                    # All should be >= 0.35 now
                    if result['relevance_score'] < 0.35:
                        print(f"       🚨 BUG: This memory passed strict filter but score {result['relevance_score']:.3f} < 0.35!")
                
                if search_results:
                    # All results should already be filtered to relevance_score >= 0.35
                    filtered_results = search_results  # No additional filtering needed
                    
                    if filtered_results:
                        memory_text = "USER MEMORIES (for context):\n"
                        print(f"🔧 DEBUG: About to inject {len(filtered_results[:3])} memories:")
                        for result in filtered_results[:3]:  # Use top 3
                            print(f"   - '{result['memory']['content']}' (relevance: {result['relevance_score']:.3f})")
                            memory_text += f"- {result['memory']['content']} (relevance: {result['relevance_score']:.2f})\n"
                            debug_memories.append(result['memory']['content'])
                        memory_text += "\nUse these memories to personalize your response when relevant."
                        messages[0]["content"] += memory_text
                        print(f"💡 Injected {len(debug_memories)} memories into prompt")
                    else:
                        print("❌ No memories met the 0.35 relevance threshold after filtering")
                else:
                    print("❌ No memories met the 0.35 relevance threshold")
                    
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