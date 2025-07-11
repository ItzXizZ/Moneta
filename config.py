#!/usr/bin/env python3

import os
import threading
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the Moneta application"""
    
    def __init__(self):
        # OpenAI Configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        
        # Flask Configuration
        self.debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'  # Default to False for production
        self.host = os.getenv('FLASK_HOST', '0.0.0.0')
        # Use Render's PORT environment variable if available, otherwise default to 4000
        self.port = int(os.getenv('PORT', os.getenv('FLASK_PORT', '4000')))
        
        # Memory system configuration
        self.memory_available = False
        self.memory_manager = None
        self.memory_json_path = 'memory_data.json'
        
        # Initialize memory system
        self._initialize_memory_system()
    
    def _initialize_memory_system(self):
        """Initialize the memory management system"""
        try:
            # Try to import and initialize memory manager
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), 'memory-app', 'backend'))
            from memory_manager import MemoryManager
            
            self.memory_manager = MemoryManager()
            self.memory_available = True
            print("✅ Memory system initialized successfully")
        except ImportError as e:
            print(f"⚠️  Memory system not available: {e}")
            self.memory_available = False
        except Exception as e:
            print(f"❌ Error initializing memory system: {e}")
            self.memory_available = False

# Create global config instance
config = Config() 