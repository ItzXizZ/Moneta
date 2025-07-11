#!/usr/bin/env python3
"""
Start the cloud-based MemoryOS system
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

# Set environment variables for the cloud database
os.environ['SUPABASE_URL'] = "https://pquleppdqequfjwlcmbn.supabase.co"
os.environ['SUPABASE_ANON_KEY'] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxdWxlcHBkcWVxdWZqd2xjbWJuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEzOTE2NTMsImV4cCI6MjA2Njk2NzY1M30.39JM1SBx5boaUAxu6fEl3BCclR5KYWCtSbpnrBfwmBQ"

def start_cloud_api():
    """Start the cloud API server."""
    print("🚀 Starting MemoryOS Cloud API...")
    
    # Change to the backend directory
    backend_dir = Path("memory-app/backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found!")
        return False
    
    try:
        # Start the Flask API server
        os.chdir(backend_dir)
        subprocess.run([sys.executable, "cloud_api.py"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start cloud API: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Shutting down cloud API...")
        return True

def test_connection():
    """Test if the cloud database connection works."""
    print("🔍 Testing cloud database connection...")
    
    try:
        # Add the backend directory to the path
        sys.path.append('memory-app/backend')
        from cloud_memory_manager import CloudMemoryManager
        
        # Initialize memory manager
        memory_manager = CloudMemoryManager()
        
        if not memory_manager.client:
            print("❌ Failed to initialize Supabase client")
            return False
        
        # Test getting stats
        stats = memory_manager.get_stats()
        print(f"✅ Connected to cloud database!")
        print(f"📊 Total memories: {stats.get('total_memories', 0)}")
        print(f"📊 Total connections: {stats.get('total_connections', 0)}")
        print(f"📊 Average score: {stats.get('average_score', 0):.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def main():
    """Main function to start the cloud system."""
    print("=" * 60)
    print("🌟 MemoryOS Cloud System Startup")
    print("=" * 60)
    
    # Test connection first
    if not test_connection():
        print("❌ Database connection failed. Please check your Supabase setup.")
        return False
    
    print("\n🎉 Database connection successful!")
    print("📝 Your migrated memories are ready to use!")
    print("🌐 Starting cloud API server...")
    print("💡 You can access the frontend at: http://localhost:8000")
    print("🔧 API will be available at: http://localhost:5001")
    print("\n⚡ Starting server... (Press Ctrl+C to stop)")
    
    # Start the cloud API
    return start_cloud_api()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 