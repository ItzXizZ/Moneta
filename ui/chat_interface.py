#!/usr/bin/env python3

# Chat Interface HTML Template with embedded CSS and JavaScript
CHAT_INTERFACE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatGPT Clone</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        /* Modern Glass Morphism Palette */
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
            
            /* Enhanced Glass Morphism Variables */
            --glass-bg: rgba(255, 255, 255, 0.08);
            --glass-bg-strong: rgba(255, 255, 255, 0.12);
            --glass-bg-subtle: rgba(255, 255, 255, 0.04);
            --glass-border: rgba(255, 255, 255, 0.15);
            --glass-border-strong: rgba(255, 255, 255, 0.25);
            --glass-blur: blur(24px);
            --glass-blur-strong: blur(32px);
            
            --glow-primary: 0 0 32px rgba(168, 85, 247, 0.25);
            --glow-secondary: 0 0 64px rgba(168, 85, 247, 0.12);
            --shadow-glass: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.05);
            --shadow-floating: 0 20px 40px -12px rgba(0, 0, 0, 0.4);
            
            --ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
            --ease-smooth: cubic-bezier(0.4, 0, 0.2, 1);
            --ease-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        * {
            box-sizing: border-box;
        }

        body {
            background: 
                radial-gradient(ellipse at center, rgba(10, 10, 10, 0.98) 0%, rgba(17, 24, 39, 0.95) 60%, rgba(5, 5, 5, 0.99) 100%),
                radial-gradient(circle at 20% 20%, rgba(255, 215, 0, 0.02) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(168, 85, 247, 0.03) 0%, transparent 50%),
                radial-gradient(circle at 40% 70%, rgba(255, 215, 0, 0.01) 0%, transparent 30%),
                radial-gradient(circle at 60% 30%, rgba(168, 85, 247, 0.02) 0%, transparent 40%);
            background-attachment: fixed;
            color: var(--gray-100);
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
            font-weight: 400;
            line-height: 1.5;
            margin: 0;
            padding: 0;
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }

        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                radial-gradient(circle at 10% 90%, rgba(168, 85, 247, 0.015) 0%, transparent 40%),
                radial-gradient(circle at 90% 10%, rgba(255, 215, 0, 0.01) 0%, transparent 30%);
            pointer-events: none;
            z-index: -1;
        }

        /* Modern Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
            background: var(--glass-bg-strong);
            border-radius: 4px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: var(--glass-blur);
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.15);
            border-color: rgba(255, 255, 255, 0.2);
        }

        .container {
            position: relative;
            width: 100vw;
            height: 100vh;
            padding: 0;
            margin: 0;
            overflow: hidden;
        }

        .main-content {
            position: relative;
            width: 100%;
            height: 100%;
            display: flex;
            pointer-events: none;
        }

        .chat-container {
            position: fixed;
            top: 20px;
            left: 20px;
            bottom: 20px;
            width: 600px;
            height: calc(100vh - 40px);
            display: flex;
            flex-direction: column;
            background: transparent;
            border: none;
            border-radius: 0;
            overflow: visible;
            box-shadow: none;
            pointer-events: auto;
            z-index: 1000;
        }

        .chat-header {
            background: transparent;
            backdrop-filter: none;
            padding: 0 0 10px 0;
            border-bottom: none;
            position: relative;
            text-align: center;
            flex-shrink: 0;
        }

        .chat-header h2 {
            margin: 0;
            color: rgba(255, 255, 255, 0.5);
            font-size: 0.875rem;
            font-weight: 400;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            position: relative;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
            display: flex;
            flex-direction: column;
            gap: 15px;
            min-height: calc(100vh - 180px);
        }

        .message {
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 20px;
            max-width: 85%;
            position: relative;
            transition: all 0.4s var(--ease-smooth);
            box-shadow: 
                0 12px 40px rgba(0, 0, 0, 0.4),
                0 0 0 1px rgba(255, 255, 255, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.15),
                0 0 20px rgba(168, 85, 247, 0.08);
            overflow: hidden;
            margin: 10px 0;
        }

        .message::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, transparent 50%);
            pointer-events: none;
            border-radius: 16px;
        }

        .message:hover {
            transform: translateY(-4px) scale(1.01);
            box-shadow: 
                0 20px 60px rgba(0, 0, 0, 0.5),
                0 0 0 1px rgba(255, 255, 255, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.2),
                0 0 40px rgba(168, 85, 247, 0.15);
            border-color: var(--glass-border-strong);
        }

        .message.user {
            align-self: flex-end;
            background: linear-gradient(135deg, rgba(168, 85, 247, 0.2), rgba(147, 51, 234, 0.15));
            border-color: rgba(168, 85, 247, 0.4);
            box-shadow: 
                0 12px 40px rgba(0, 0, 0, 0.4),
                0 0 0 1px rgba(168, 85, 247, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.2),
                0 0 30px rgba(168, 85, 247, 0.2);
        }

        .message.user::before {
            background: linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, transparent 50%);
        }

        .message.user:hover {
            box-shadow: 
                0 20px 60px rgba(0, 0, 0, 0.5),
                0 0 0 1px rgba(168, 85, 247, 0.5),
                inset 0 1px 0 rgba(255, 255, 255, 0.25),
                0 0 50px rgba(168, 85, 247, 0.4);
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

        .chat-input-container {
            padding: 10px 0;
            border-top: none;
            background: transparent;
            backdrop-filter: none;
            margin-top: auto;
        }

        .chat-input-form {
            display: flex;
            gap: 12px;
        }

        .chat-input {
            flex: 1;
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 18px 24px;
            color: rgba(255, 255, 255, 0.95);
            font-size: 1rem;
            transition: all 0.4s var(--ease-smooth);
            resize: none;
            min-height: 60px;
            max-height: 150px;
            font-family: inherit;
            line-height: 1.5;
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.4),
                0 0 0 1px rgba(255, 255, 255, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.15),
                inset 0 2px 8px rgba(0, 0, 0, 0.15),
                0 0 20px rgba(168, 85, 247, 0.08);
        }

        .chat-input::placeholder {
            color: rgba(255, 255, 255, 0.4);
        }

        .chat-input:focus {
            outline: none;
            border-color: var(--glass-border-strong);
            box-shadow: 
                0 12px 48px rgba(0, 0, 0, 0.5),
                0 0 0 3px rgba(168, 85, 247, 0.2),
                0 0 0 1px rgba(168, 85, 247, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.2),
                inset 0 2px 8px rgba(0, 0, 0, 0.2),
                0 0 40px rgba(168, 85, 247, 0.25);
            background: var(--glass-bg-strong);
            transform: translateY(-2px) scale(1.01);
        }

        .send-button {
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur-strong);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 18px 28px;
            color: rgba(255, 255, 255, 0.9);
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.4s var(--ease-smooth);
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.4),
                0 0 0 1px rgba(255, 255, 255, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.15),
                0 0 20px rgba(168, 85, 247, 0.1);
            position: relative;
            overflow: hidden;
            white-space: nowrap;
        }

        .send-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(168, 85, 247, 0.1) 0%, transparent 50%);
            opacity: 0;
            transition: opacity 0.4s var(--ease-smooth);
            pointer-events: none;
        }

        .send-button:hover {
            background: var(--glass-bg-strong);
            border-color: var(--glass-border-strong);
            color: rgba(255, 255, 255, 1);
            transform: translateY(-4px) scale(1.02);
            box-shadow: 
                0 16px 48px rgba(168, 85, 247, 0.4),
                0 0 0 1px rgba(168, 85, 247, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.25),
                0 0 40px rgba(168, 85, 247, 0.3);
        }

        .send-button:hover::before {
            opacity: 1;
        }

        .send-button:active {
            transform: translateY(-1px);
        }

        .thread-controls {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            background: transparent;
            border: none;
            border-radius: 0;
            padding: 0;
            box-shadow: none;
            justify-content: center;
            pointer-events: auto;
            z-index: 1000;
        }

        .new-thread-btn, .clear-thread-btn, .end-thread-btn, .memory-toggle-btn {
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur-strong);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            padding: 12px 20px;
            color: rgba(255, 255, 255, 0.9);
            font-weight: 500;
            font-size: 0.875rem;
            cursor: pointer;
            transition: all 0.4s var(--ease-smooth);
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.4),
                0 0 0 1px rgba(255, 255, 255, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.15),
                0 0 20px rgba(168, 85, 247, 0.1);
            position: relative;
            overflow: hidden;
            white-space: nowrap;
        }

        .new-thread-btn::before, .clear-thread-btn::before, .end-thread-btn::before, .memory-toggle-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
            opacity: 0;
            transition: opacity 0.4s var(--ease-smooth);
            pointer-events: none;
        }

        .new-thread-btn:hover, .clear-thread-btn:hover, .end-thread-btn:hover, .memory-toggle-btn:hover {
            background: var(--glass-bg-strong);
            border-color: var(--glass-border-strong);
            color: rgba(255, 255, 255, 1);
            transform: translateY(-4px) scale(1.02);
            box-shadow: 
                0 16px 48px rgba(0, 0, 0, 0.5),
                0 0 0 1px rgba(255, 255, 255, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.25),
                0 0 40px rgba(168, 85, 247, 0.3);
        }

        .new-thread-btn:hover::before, .clear-thread-btn:hover::before, .end-thread-btn:hover::before, .memory-toggle-btn:hover::before {
            opacity: 1;
        }

        .new-thread-btn:hover {
            box-shadow: 
                0 8px 24px rgba(168, 85, 247, 0.3),
                0 0 0 1px rgba(168, 85, 247, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.2);
        }

        .clear-thread-btn:hover {
            box-shadow: 
                0 8px 24px rgba(239, 68, 68, 0.3),
                0 0 0 1px rgba(239, 68, 68, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.2);
            color: #fca5a5;
        }

        .end-thread-btn:hover {
            box-shadow: 
                0 8px 24px rgba(34, 197, 94, 0.3),
                0 0 0 1px rgba(34, 197, 94, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.2);
            color: #86efac;
        }

        .memory-toggle-btn.active {
            background: var(--glass-bg-strong);
            border-color: rgba(34, 197, 94, 0.4);
            color: #86efac;
            box-shadow: 
                0 4px 16px rgba(34, 197, 94, 0.2),
                0 0 0 1px rgba(34, 197, 94, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.15);
        }

        .memory-toggle-btn.disabled {
            background: var(--glass-bg-subtle);
            border-color: rgba(255, 255, 255, 0.1);
            cursor: not-allowed;
            opacity: 0.5;
            color: rgba(255, 255, 255, 0.4);
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

        @media (max-width: 1200px) {
            .chat-container {
                width: 500px;
            }
        }

        @media (max-width: 1024px) {
            .chat-container {
                width: 450px;
                left: 10px;
                top: 10px;
                bottom: 10px;
                height: calc(100vh - 20px);
            }
            
            .thread-controls {
                top: 10px;
                gap: 12px;
            }
            
            .chat-messages {
                min-height: calc(100vh - 160px);
            }
        }

        @media (max-width: 768px) {
            .chat-container {
                width: calc(100vw - 20px);
                left: 10px;
                right: 10px;
                top: 80px;
                bottom: 10px;
                height: calc(100vh - 90px);
            }
            
            .thread-controls {
                top: 10px;
                left: 10px;
                right: 10px;
                transform: none;
                flex-wrap: wrap;
                justify-content: center;
                gap: 8px;
            }
            
            .chat-messages {
                min-height: calc(100vh - 200px);
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
                <span id="memory-toggle-text">✅ Memory Search ALWAYS ON</span>
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
                        <button type="button" class="send-button" onclick="sendMessage()">Send</button>
                    </div>
                </div>
            </div>
            
            <!-- Memory Network Section -->
            <div id="memory-network-container">
                <!-- This will be populated by the memory network UI component -->
            </div>
        </div>
    </div>
</body>
</html>
''' 