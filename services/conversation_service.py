#!/usr/bin/env python3

import datetime
import uuid
import time
import requests
import os
import json
from config import config
from services.openai_service import openai_service

class ConversationService:
    """Service for managing conversations and threads"""
    
    CHAT_HISTORY_FILE = os.path.join(os.path.dirname(__file__), '../chat_history.json')
    
    def __init__(self):
        # In-memory storage for chat threads and messages
        self.chat_threads = {}
        
        # Track processed request IDs to prevent duplicates
        self.processed_requests = set()
        self.last_cleanup = time.time()
        self.load_history_from_disk()
    
    def save_history_to_disk(self):
        try:
            with open(self.CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.chat_threads, f, indent=2)
        except Exception as e:
            print(f'⚠️ Failed to save chat history: {e}')

    def load_history_from_disk(self):
        try:
            if os.path.exists(self.CHAT_HISTORY_FILE):
                with open(self.CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.chat_threads = json.load(f)
        except Exception as e:
            print(f'⚠️ Failed to load chat history: {e}')
    
    def cleanup_old_requests(self):
        """Clean up old request IDs every 5 minutes"""
        current_time = time.time()
        if current_time - self.last_cleanup > 300:  # 5 minutes
            self.processed_requests.clear()
            self.last_cleanup = current_time
            print("🧹 Cleaned up old request IDs")
    
    def is_duplicate_request(self, request_id):
        """Check if this is a duplicate request"""
        if not request_id:
            return False
        
        if request_id in self.processed_requests:
            print(f"⚠️ Duplicate request detected: {request_id}")
            return True
        
        self.processed_requests.add(request_id)
        print(f"✅ Processing request: {request_id}")
        return False
    
    def create_or_get_thread(self, thread_id=None):
        """Create a new thread or get existing one"""
        if not thread_id:
            thread_id = str(uuid.uuid4())
            self.chat_threads[thread_id] = []
        
        if thread_id not in self.chat_threads:
            self.chat_threads[thread_id] = []
        
        return thread_id
    
    def create_new_thread(self):
        """Create a new empty thread and return its ID"""
        thread_id = str(uuid.uuid4())
        self.chat_threads[thread_id] = []
        self.save_history_to_disk()
        return thread_id
    
    def add_message_to_thread(self, thread_id, content, sender):
        """Add a message to a thread"""
        timestamp = datetime.datetime.now().isoformat()
        message = {
            'id': str(uuid.uuid4()),
            'content': content,
            'sender': sender,
            'timestamp': timestamp
        }
        
        if thread_id not in self.chat_threads:
            self.chat_threads[thread_id] = []
        
        self.chat_threads[thread_id].append(message)
        self.save_history_to_disk()
        return message
    
    def get_thread_messages(self, thread_id):
        """Get all messages from a thread"""
        return self.chat_threads.get(thread_id, [])
    
    def process_message(self, message, thread_id, request_id=None):
        """Process a user message and generate AI response"""
        # Clean up old requests
        self.cleanup_old_requests()
        
        # Check for duplicate request
        if self.is_duplicate_request(request_id):
            return None, None, None, "Duplicate request detected"
        
        if not message.strip():
            return None, None, None, "Message cannot be empty"
        
        # Create or get thread
        thread_id = self.create_or_get_thread(thread_id)
        
        # Add user message to thread
        user_message = self.add_message_to_thread(thread_id, message, 'user')
        
        # Generate AI response using OpenAI API with memory context
        ai_response, memory_context = openai_service.generate_response_with_memory(
            message, 
            self.chat_threads[thread_id]
        )
        
        # Add AI response to thread
        ai_message = self.add_message_to_thread(thread_id, ai_response, 'assistant')
        
        return thread_id, ai_response, memory_context, None
    
    def end_thread_and_extract_memories(self, thread_id):
        """Extract memories from a conversation thread when it ends"""
        print(f"🔧 DEBUG: end_thread_and_extract_memories called for thread: {thread_id}")
        
        if not thread_id or thread_id not in self.chat_threads:
            print(f"🔧 DEBUG: Thread not found - thread_id: {thread_id}, exists: {thread_id in self.chat_threads if thread_id else False}")
            return False, [], "Thread not found"
        
        conversation = self.chat_threads[thread_id]
        print(f"🔧 DEBUG: Found conversation with {len(conversation)} messages")
        
        # Extract memories with error handling
        try:
            print("🔧 DEBUG: Calling extract_memories_from_conversation...")
            extracted_memories = openai_service.extract_memories_from_conversation(conversation)
            print(f"🔧 DEBUG: Memory extraction completed, got {len(extracted_memories)} memories")
        except Exception as e:
            print(f"❌ Error during memory extraction: {e}")
            print(f"🔧 DEBUG: Memory extraction exception: {type(e).__name__}: {e}")
            extracted_memories = []
        
        # Add extracted memories to the memory system
        successful_adds = 0
        if extracted_memories:
            print(f"💾 Extracting {len(extracted_memories)} memories from conversation...")
            print(f"🔧 DEBUG: Memory manager available: {config.memory_available}")
            print(f"🔧 DEBUG: Memory manager object: {config.memory_manager}")
            
            # Try local memory manager first
            if config.memory_available and config.memory_manager:
                for memory_text in extracted_memories:
                    try:
                        print(f"🔧 DEBUG: Adding memory: {memory_text[:50]}...")
                        new_memory = config.memory_manager.add_memory(memory_text, ["conversation", "auto-extracted"])
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
                            print(f"🔧 DEBUG: Memory data prepared: {memory_data}")
                            
                            with config.session_new_memories_lock:
                                config.session_new_memories.append(memory_data)
                                print(f"🔧 DEBUG: Session queue size after add: {len(config.session_new_memories)}")
                            
                            print(f"🌐 Queued new memory for network: {memory_data['id']}")
                        else:
                            print(f"🔧 DEBUG: new_memory is None/empty!")
                    except Exception as e:
                        print(f"   ❌ Failed to add locally: {memory_text} - {e}")
                        print(f"🔧 DEBUG: Exception details: {type(e).__name__}: {e}")
            else:
                print(f"🔧 DEBUG: Memory system not available - config.memory_available: {config.memory_available}, config.memory_manager: {config.memory_manager}")
            
            # Also try to add via API to ensure synchronization
            try:
                for memory_text in extracted_memories:
                    api_response = requests.post(
                        'http://localhost:5000/memories', 
                        json={
                            'content': memory_text, 
                            'tags': ['conversation', 'auto-extracted']
                        }, 
                        timeout=5
                    )
                    if api_response.status_code == 201:
                        print(f"   🔄 Synced to API: {memory_text}")
                    else:
                        print(f"   ⚠️ API sync failed for: {memory_text}")
            except Exception as e:
                print(f"   ⚠️ API synchronization failed: {e}")
            
            # Force local reload if we have memory manager
            if config.memory_available and config.memory_manager:
                try:
                    time.sleep(1)  # Give file operations time to complete
                    config.memory_manager.reload_from_disk()
                    print(f"💾 Reloaded memory manager after adding {successful_adds} memories")
                except Exception as e:
                    print(f"⚠️ Warning: Could not reload memory manager: {e}")
        
        # DON'T clean up the thread - keep it active so user can continue chatting
        # if thread_id in self.chat_threads:
        #     del self.chat_threads[thread_id]
        print(f"🔧 DEBUG: Thread {thread_id} preserved for continued conversation")
        
        return True, extracted_memories, f'Successfully extracted and saved {len(extracted_memories)} memories!'
    
    def clear_thread(self, thread_id):
        """Clear a specific thread"""
        if thread_id in self.chat_threads:
            del self.chat_threads[thread_id]
            self.save_history_to_disk()
            return True
        return False

# Global service instance
conversation_service = ConversationService() 