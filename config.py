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
        
        # Memory search configuration (optimized for full ML version)
        self.min_relevance_threshold = 0.7  # Higher threshold for better quality with ML
        self.max_search_results = 15        # More results with powerful ML search
        self.max_injected_memories = 5      # More memories can be injected with better relevance
        
        # Initialize memory system
        self._initialize_memory_system()
    
    def _initialize_memory_system(self):
        """Initialize the memory management system (prioritizing full version)"""
        try:
            # Try to import the full memory manager with ML capabilities
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), 'memory-app', 'backend'))
            from memory_manager import MemoryManager
            
            self.memory_manager = MemoryManager()
            self.memory_available = True
            print("🚀 Full ML-powered memory system initialized successfully!")
            print("   - Semantic search with sentence-transformers")
            print("   - Advanced similarity calculations with scikit-learn")
            print("   - High-performance memory retrieval")
        except ImportError as e:
            print(f"⚠️  Full memory system not available: {e}")
            print("   Falling back to lightweight version...")
            # Fallback to lightweight memory manager
            try:
                from lightweight_memory_manager import LightweightMemoryManager
                self.memory_manager = LightweightMemoryManager()
                self.memory_available = True
                print("✅ Lightweight memory system initialized (fallback)")
            except Exception as e2:
                print(f"❌ Error initializing lightweight memory system: {e2}")
                self.memory_available = False
        except Exception as e:
            print(f"❌ Error initializing memory system: {e}")
            # Try lightweight as last resort
            try:
                from lightweight_memory_manager import LightweightMemoryManager
                self.memory_manager = LightweightMemoryManager()
                self.memory_available = True
                print("✅ Lightweight memory system initialized (last resort)")
            except Exception as e3:
                print(f"❌ All memory systems failed: {e3}")
                self.memory_available = False

# Create global config instance
config = Config() 