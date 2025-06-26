#!/usr/bin/env python3

import datetime
import uuid
import time
import requests
from config import config
from services.openai_service import openai_service

class ConversationService:
    """Service for managing conversations and threads"""
    
    def __init__(self):
        # In-memory storage for chat threads and messages
        self.chat_threads = {}
        
        # Track processed request IDs to prevent duplicates
        self.processed_requests = set()
        self.last_cleanup = time.time()
    
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
        if not thread_id or thread_id not in self.chat_threads:
            return False, [], "Thread not found"
        
        conversation = self.chat_threads[thread_id]
        
        # Extract memories with error handling
        try:
            extracted_memories = openai_service.extract_memories_from_conversation(conversation)
        except Exception as e:
            print(f"❌ Error during memory extraction: {e}")
            extracted_memories = []
        
        # Add extracted memories to the memory system
        successful_adds = 0
        if extracted_memories:
            print(f"💾 Extracting {len(extracted_memories)} memories from conversation...")
            
            # Try local memory manager first
            if config.memory_available and config.memory_manager:
                for memory_text in extracted_memories:
                    try:
                        config.memory_manager.add_memory(memory_text, ["conversation", "auto-extracted"])
                        print(f"   ✅ Added locally: {memory_text}")
                        successful_adds += 1
                    except Exception as e:
                        print(f"   ❌ Failed to add locally: {memory_text} - {e}")
            
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
        
        # Clean up the thread
        if thread_id in self.chat_threads:
            del self.chat_threads[thread_id]
        
        return True, extracted_memories, f'Successfully extracted and saved {len(extracted_memories)} memories!'
    
    def clear_thread(self, thread_id):
        """Clear a specific thread"""
        if thread_id in self.chat_threads:
            del self.chat_threads[thread_id]
            return True
        return False

# Global service instance
conversation_service = ConversationService() 