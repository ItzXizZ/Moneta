#!/usr/bin/env python3
"""
Complete MemoryOS Cloud System Startup
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path
import threading

def start_backend():
    """Start the cloud API backend."""
    print("🚀 Starting MemoryOS Cloud API Backend...")
    
    # Set credentials
    os.environ['SUPABASE_URL'] = "https://pquleppdqequfjwlcmbn.supabase.co"
    os.environ['SUPABASE_ANON_KEY'] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxdWxlcHBkcWVxdWZqd2xjbWJuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEzOTE2NTMsImV4cCI6MjA2Njk2NzY1M30.39JM1SBx5boaUAxu6fEl3BCclR5KYWCtSbpnrBfwmBQ"
    
    # Change to backend directory
    backend_dir = Path("memory-app/backend")
    original_dir = os.getcwd()
    
    try:
        os.chdir(backend_dir)
        # Use shell=True for Windows PowerShell compatibility
        subprocess.run([sys.executable, "cloud_api.py"], shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Backend failed: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Backend shutting down...")
    finally:
        os.chdir(original_dir)

def start_frontend():
    """Start a simple HTTP server for the frontend."""
    print("🌐 Starting Frontend Server...")
    
    frontend_dir = Path("memory-app/frontend")
    original_dir = os.getcwd()
    
    try:
        if frontend_dir.exists():
            os.chdir(frontend_dir)
            # Start a simple HTTP server on port 8000
            subprocess.run([sys.executable, "-m", "http.server", "8000"], check=True)
        else:
            print(f"❌ Frontend directory not found: {frontend_dir}")
            print("Current directory:", os.getcwd())
            print("Available directories:", [d.name for d in Path(".").iterdir() if d.is_dir()])
    except subprocess.CalledProcessError as e:
        print(f"❌ Frontend failed: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Frontend shutting down...")
    finally:
        os.chdir(original_dir)

def test_connection():
    """Test the database connection."""
    print("🔍 Testing database connection...")
    
    try:
        sys.path.append('memory-app/backend')
        from cloud_memory_manager import CloudMemoryManager
        
        memory_manager = CloudMemoryManager()
        if memory_manager.client:
            stats = memory_manager.get_stats()
            print(f"✅ Connected! Found {stats.get('total_memories', 0)} memories")
            return True
        else:
            print("❌ Connection failed")
            return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def main():
    """Main function to start the complete system."""
    print("=" * 60)
    print("🧠 MemoryOS Cloud System - Complete Startup")
    print("=" * 60)
    
    # Test connection first
    if not test_connection():
        print("❌ Database connection failed. Exiting...")
        return False
    
    print("\n🎉 Database connection successful!")
    print("📊 Your memories are ready!")
    print("\n🚀 Starting both backend and frontend...")
    print("📝 Backend API: http://localhost:5001")
    print("🌐 Frontend UI: http://localhost:8000")
    print("\n💡 The frontend will automatically open in your browser!")
    print("⚡ Press Ctrl+C to stop both servers\n")
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # Give backend time to start
    time.sleep(3)
    
    # Open browser
    try:
        webbrowser.open('http://localhost:8000')
    except:
        print("Could not open browser automatically. Go to http://localhost:8000")
    
    # Start frontend (this will block until Ctrl+C)
    try:
        start_frontend()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down complete system...")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 