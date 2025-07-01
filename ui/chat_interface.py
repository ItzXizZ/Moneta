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
            overflow: visible;
            display: flex;
            flex-direction: row;
        }

        .thread-sidebar {
            width: 250px;
            min-width: 12px;
            max-width: 220px;
            height: 100vh;
            background: rgba(255,255,255,0.10);
            backdrop-filter: blur(18px);
            border-right: 1.5px solid rgba(255,255,255,0.18);
            box-shadow: 2px 0 24px 0 rgba(168,85,247,0.08);
            display: flex;
            flex-direction: column;
            align-items: stretch;
            padding: 60px 0 18px 0;
            z-index: 1100;
            transition: transform 0.3s cubic-bezier(0.4,0,0.2,1);
            position: relative;
        }
        .thread-sidebar.hidden {
            transform: translateX(-100%);
        }

        .thread-list {
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
            padding: 0 8px;
            margin-top: 60px;
        }

        .thread-list-item {
            min-width: 140px;
            max-width: 200px;
            background: rgba(168,85,247,0.10);
            border: 1px solid rgba(168,85,247,0.18);
            border-radius: 20px;
            color: #fff;
            padding: 10px 16px 10px 12px;
            margin-bottom: 8px;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4,0,0.2,1);
            box-shadow: 0 2px 8px rgba(168,85,247,0.06);
            user-select: none;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: space-between;
            min-height: 40px;
        }
        .thread-list-item.active, .thread-list-item:hover {
            background: rgba(168,85,247,0.18);
            border-color: rgba(168,85,247,0.32);
            color: #fff;
            transform: scale(1.04);
        }
        
        .thread-list-item .thread-title {
            flex: 1;
            text-align: left;
            padding-right: 16px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .thread-delete-btn {
            background: rgba(239, 68, 68, 0.18);
            border: none;
            border-radius: 50%;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 1.2rem;
            color: #ef4444;
            transition: all 0.2s cubic-bezier(0.4,0,0.2,1);
            margin-left: 12px;
            opacity: 0.7;
            outline: none;
        }
        
        .thread-list-item:hover .thread-delete-btn {
            opacity: 1;
            background: rgba(239, 68, 68, 0.28);
            color: #fff;
            box-shadow: 0 2px 8px rgba(239,68,68,0.12);
        }
        
        .thread-delete-btn:hover, .thread-delete-btn:focus {
            background: #ef4444;
            color: #fff;
            opacity: 1;
            transform: scale(1.12);
            box-shadow: 0 4px 16px rgba(239,68,68,0.18);
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
            left: 250px;
            bottom: 20px;
            width: 500px;
            height: calc(100vh - 40px);
            display: flex;
            flex-direction: column;
            background: transparent;
            border: none;
            border-radius: 0;
            overflow: hidden;
            box-shadow: none;
            pointer-events: auto;
            z-index: 1000;
            transition: left 0.3s cubic-bezier(0.4,0,0.2,1), width 0.3s cubic-bezier(0.4,0,0.2,1);
            margin-right: 12px;
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
            overflow-x: hidden;
            padding: 10px;
            height: calc(100vh - 160px);
            scroll-behavior: smooth;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: thin;
            scrollbar-color: rgba(255, 255, 255, 0.2) transparent;
        }

        .message {
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            padding: 20px 24px;
            max-width: 85%;
            position: relative;
            transition: all 0.4s var(--ease-smooth);
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.3),
                0 0 0 1px rgba(255, 255, 255, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.2),
                0 4px 16px rgba(168, 85, 247, 0.1);
            overflow: hidden;
            margin: 15px 0;
            opacity: 0;
            transform: scale(0.8) translateY(20px);
            animation: messagePopIn 0.3s ease-out forwards;
            width: fit-content;
        }

        @keyframes messagePopIn {
            0% {
                opacity: 0;
                transform: scale(0.8) translateY(20px);
            }
            100% {
                opacity: 1;
                transform: scale(1) translateY(0);
            }
        }

        .message::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 50%, transparent 100%);
            pointer-events: none;
            border-radius: 20px;
        }

        .message:hover {
            transform: translateY(-2px) scale(1.02);
            box-shadow: 
                0 12px 48px rgba(0, 0, 0, 0.4),
                0 0 0 1px rgba(255, 255, 255, 0.25),
                inset 0 1px 0 rgba(255, 255, 255, 0.3),
                0 8px 32px rgba(168, 85, 247, 0.2);
            border-color: rgba(255, 255, 255, 0.3);
            backdrop-filter: blur(24px);
        }

        .message.user {
            float: right;
            clear: both;
            background: linear-gradient(135deg, rgba(168, 85, 247, 0.15), rgba(147, 51, 234, 0.1));
            backdrop-filter: blur(20px);
            border-color: rgba(168, 85, 247, 0.3);
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.3),
                0 0 0 1px rgba(168, 85, 247, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.25),
                0 4px 20px rgba(168, 85, 247, 0.15);
            animation: messagePopIn 0.2s ease-out forwards;
        }

        .message.user::before {
            background: linear-gradient(135deg, rgba(168, 85, 247, 0.1) 0%, rgba(168, 85, 247, 0.05) 50%, transparent 100%);
        }

        .message.user:hover {
            box-shadow: 
                0 12px 48px rgba(0, 0, 0, 0.4),
                0 0 0 1px rgba(168, 85, 247, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.35),
                0 8px 40px rgba(168, 85, 247, 0.3);
            border-color: rgba(168, 85, 247, 0.5);
        }

        .message.assistant {
            float: left;
            clear: both;
            background: rgba(255, 255, 255, 0.08);
            animation: messagePopIn 0.3s ease-out forwards;
            animation-delay: 0.1s;
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
            background: rgba(168, 85, 247, 0.08);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(168, 85, 247, 0.2);
            border-radius: 16px;
            margin-top: 12px;
            font-size: 0.85rem;
            color: var(--primary-200);
            overflow: hidden;
            transition: all 0.3s var(--ease-smooth);
            box-shadow: 
                0 4px 16px rgba(168, 85, 247, 0.1),
                0 0 0 1px rgba(168, 85, 247, 0.05),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }

        .memories-injected-header {
            padding: 12px 16px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(168, 85, 247, 0.15);
            transition: all 0.3s var(--ease-smooth);
            backdrop-filter: blur(20px);
        }

        .memories-injected-header:hover {
            background: rgba(168, 85, 247, 0.08);
            border-bottom-color: rgba(168, 85, 247, 0.25);
        }

        .memories-injected-header h4 {
            margin: 0;
            color: var(--primary-300);
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .memories-injected-toggle {
            color: var(--primary-400);
            font-size: 0.8rem;
            transition: transform 0.3s var(--ease-smooth);
        }

        .memories-injected-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s var(--ease-smooth);
        }

        .memories-injected-content.expanded {
            max-height: 300px;
            padding: 10px;
        }

        .memories-injected-item {
            background: rgba(168, 85, 247, 0.06);
            backdrop-filter: blur(16px);
            border-left: 3px solid rgba(168, 85, 247, 0.4);
            border-radius: 8px;
            padding: 10px 14px;
            margin: 8px 0;
            font-size: 0.8rem;
            line-height: 1.4;
            box-shadow: 
                0 2px 8px rgba(168, 85, 247, 0.05),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
            transition: all 0.3s var(--ease-smooth);
        }

        .memories-injected-item:hover {
            background: rgba(168, 85, 247, 0.1);
            border-left-color: rgba(168, 85, 247, 0.6);
            transform: translateX(2px);
        }

        .memories-injected-score {
            color: var(--primary-400);
            font-weight: 600;
            margin-left: 8px;
        }

        .chat-input-container {
            padding: 5px 16px 10px 0;
            border-top: none;
            background: transparent;
            backdrop-filter: none;
            width:92%
            margin-top: auto;
            flex-shrink: 0;
            position: sticky;
            bottom: 0;
            z-index: 100;
        }

        .chat-input-form {
            display: flex;
            gap: 12px;
            padding-right: 16px;
            justify-content: center;
        }

        .chat-input {
            width: 75%;
            flex: none;
            max-width: 420px;
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
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
                0 4px 16px rgba(0, 0, 0, 0.2),
                0 0 0 1px rgba(255, 255, 255, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.2),
                inset 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .chat-input::placeholder {
            color: rgba(255, 255, 255, 0.4);
        }

        .chat-input:focus {
            outline: none;
            border-color: rgba(168, 85, 247, 0.4);
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.3),
                0 0 0 2px rgba(168, 85, 247, 0.2),
                0 0 0 1px rgba(168, 85, 247, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.25),
                inset 0 2px 8px rgba(0, 0, 0, 0.15);
            background: rgba(255, 255, 255, 0.12);
            transform: translateY(-1px) scale(1.01);
            backdrop-filter: blur(24px);
        }

        .send-button {
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            padding: 18px 20px;
            color: rgba(255, 255, 255, 0.9);
            font-size: 0.8rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.4s var(--ease-smooth);
            box-shadow: 
                0 4px 16px rgba(0, 0, 0, 0.2),
                0 0 0 1px rgba(255, 255, 255, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.2);
            position: relative;
            overflow: hidden;
            white-space: nowrap;
            max-width: 8vw;
            min-width: 70px;
            flex-shrink: 0;
        }

        .send-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(168, 85, 247, 0.1) 0%, rgba(168, 85, 247, 0.05) 50%, transparent 100%);
            opacity: 0;
            transition: opacity 0.4s var(--ease-smooth);
            pointer-events: none;
            border-radius: 20px;
        }

        .send-button:hover {
            background: rgba(168, 85, 247, 0.12);
            border-color: rgba(168, 85, 247, 0.3);
            color: rgba(255, 255, 255, 1);
            transform: translateY(-2px) scale(1.02);
            box-shadow: 
                0 8px 32px rgba(168, 85, 247, 0.3),
                0 0 0 1px rgba(168, 85, 247, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.25);
            backdrop-filter: blur(24px);
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
            gap: 12px;
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

        .new-thread-btn, .end-thread-btn {
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 16px;
            padding: 10px 18px;
            color: rgba(255, 255, 255, 0.9);
            font-weight: 500;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.4s var(--ease-smooth);
            box-shadow: 
                0 4px 16px rgba(0, 0, 0, 0.2),
                0 0 0 1px rgba(255, 255, 255, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.2);
            position: relative;
            overflow: hidden;
            white-space: nowrap;
            max-width: 7vw;
            min-width: 70px;
        }

        .new-thread-btn::before, .end-thread-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 50%, transparent 100%);
            opacity: 0;
            transition: opacity 0.4s var(--ease-smooth);
            pointer-events: none;
            border-radius: 16px;
        }

        .new-thread-btn:hover, .end-thread-btn:hover {
            background: rgba(255, 255, 255, 0.12);
            border-color: rgba(255, 255, 255, 0.3);
            color: rgba(255, 255, 255, 1);
            transform: translateY(-2px) scale(1.02);
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.3),
                0 0 0 1px rgba(255, 255, 255, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.25);
            backdrop-filter: blur(24px);
        }

        .new-thread-btn:hover::before, .end-thread-btn:hover::before {
            opacity: 1;
        }

        .new-thread-btn:hover {
            box-shadow: 
                0 8px 24px rgba(168, 85, 247, 0.3),
                0 0 0 1px rgba(168, 85, 247, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.2);
        }

        .empty-state {
            text-align: center;
            color: var(--gray-400);
            font-style: italic;
            padding: 40px;
            clear: both;
            width: 100%;
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
                min-height: 0;
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
            
            .new-thread-btn, .end-thread-btn {
                max-width: none;
                min-width: 80px;
                padding: 8px 12px;
                font-size: 0.75rem;
            }
            
            .chat-messages {
                min-height: 0;
                max-height: calc(100vh - 180px);
            }
            
            .message {
                max-width: 95%;
            }
            
            .chat-input-form {
                flex-direction: row;
                gap: 8px;
            }
            
            .send-button {
                max-width: none;
                min-width: 60px;
                padding: 18px 16px;
            }
        }

        .chat-messages::after {
            content: "";
            display: table;
            clear: both;
        }

        .sidebar-toggle-btn {
            position: fixed;
            top: 24px;
            left: 18px;
            z-index: 1200;
            width: 36px;
            height: 36px;
            background: rgba(255,255,255,0.13);
            border: 1.5px solid rgba(255,255,255,0.18);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(168,85,247,0.10);
            transition: background 0.2s, box-shadow 0.2s;
        }
        .sidebar-toggle-btn:hover {
            background: rgba(168,85,247,0.18);
            box-shadow: 0 4px 16px rgba(168,85,247,0.18);
        }
        .sidebar-toggle-btn .bar {
            width: 20px;
            height: 3px;
            background: #fff;
            margin: 2.5px 0;
            border-radius: 2px;
            transition: all 0.3s;
        }

        .container.sidebar-hidden .chat-container {
            left: 8px !important;
            margin-right: 12px;
            /* width: 100vw !important; */
            transition: left 0.3s cubic-bezier(0.4,0,0.2,1);
        }
        .chat-container {
            transition: left 0.3s cubic-bezier(0.4,0,0.2,1), width 0.3s cubic-bezier(0.4,0,0.2,1);
        }

        /* If your icon is in a container, e.g. .sidebar-icon, add: */
        .sidebar-icon {
            margin-bottom: 24px;
        }

        .thread-list-item:first-child {
            margin-top: 10px;
        }

        .sidebar-controls {
            position: absolute;
            left: 0;
            right: 0;
            bottom: 18px;
            display: flex;
            gap: 12px;
            justify-content: center;
            padding: 0 12px;
            z-index: 1201;
        }
        .thread-sidebar.hidden .sidebar-controls {
            display: none;
        }
    </style>
</head>
<body>
    <div class="sidebar-toggle-btn" id="sidebar-toggle-btn" onclick="toggleSidebar()">
        <div class="bar"></div>
        <div class="bar"></div>
        <div class="bar"></div>
    </div>
    <div class="container">
        <div class="thread-sidebar" id="thread-sidebar">
            <!-- Thread list will be populated here -->
            <div class="sidebar-controls">
                <button class="new-thread-btn" onclick="newThread()">New</button>
                <button class="end-thread-btn" onclick="endThread()">💾 Save</button>
            </div>
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