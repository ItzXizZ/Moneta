#!/usr/bin/env python3

from config import config
from services.memory_search_service import memory_search_service

class OpenAIService:
    """Service for OpenAI API interactions"""
    
    def __init__(self):
        self.client = config.openai_client
    
    def generate_response_with_memory(self, message, conversation_history):
        """Generate AI response using OpenAI API with memory context"""
        # Check if OpenAI client is available
        if not self.client:
            return "I apologize, but I encountered an error: OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file.", []
        
        try:
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant. Use the following user memories to answer as personally and specifically as possible. If relevant, reference these memories directly in your answer. If no memories are relevant, answer as best you can.\n\n"}
            ]
            
            # Search for relevant memories
            memory_context = memory_search_service.search_memories_with_strict_filtering(message)
            
            # Inject memories into system prompt if found
            if memory_context:
                memory_text = memory_search_service.format_memories_for_injection(memory_context)
                messages[0]["content"] += memory_text
            
            # Add conversation history (excluding the current message to avoid duplication)
            for msg in conversation_history[:-1]:  # Exclude the last message (current user message)
                role = "user" if msg['sender'] == 'user' else "assistant"
                messages.append({"role": role, "content": msg['content']})
            
            # Add the current user message
            messages.append({"role": "user", "content": message})
            
            # Generate response
            response = self.client.chat.completions.create(
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
    
    def extract_memories_from_conversation(self, conversation):
        """Extract up to 5 meaningful memories from a conversation using OpenAI"""
        print(f"🔧 DEBUG: extract_memories_from_conversation called with {len(conversation) if conversation else 0} messages")
        
        # Check if OpenAI client is available
        if not self.client:
            print("🔧 DEBUG: OpenAI client not available, cannot extract memories")
            return []
        
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
            
            response = self.client.chat.completions.create(
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

# Global service instance
openai_service = OpenAIService() 