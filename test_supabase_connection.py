#!/usr/bin/env python3
"""
Simple test script to verify Supabase connection
"""

import os
import sys

# Add the backend directory to the path
sys.path.append('memory-app/backend')

def test_connection():
    """Test the Supabase connection."""
    print("🔍 Testing Supabase connection...")
    
    # Your credentials
    supabase_url = "https://pquleppdqequfjwlcmbn.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxdWxlcHBkcWVxdWZqd2xjbWJuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEzOTE2NTMsImV4cCI6MjA2Njk2NzY1M30.39JM1SBx5boaUAxu6fEl3BCclR5KYWCtSbpnrBfwmBQ"
    
    try:
        from cloud_memory_manager import CloudMemoryManager
        memory_manager = CloudMemoryManager(supabase_url, supabase_key)
        
        if memory_manager.client:
            print("✅ Connection successful!")
            
            # Test a simple operation
            try:
                memories = memory_manager.get_memories(limit=1)
                print(f"✅ Database query successful! Found {len(memories)} memories")
                return True
            except Exception as e:
                print(f"⚠️  Connection works but database tables may not exist: {e}")
                print("You need to create the database tables first.")
                return False
        else:
            print("❌ Connection failed!")
            return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def create_env_file():
    """Create .env file with the credentials."""
    env_content = """# Supabase Configuration
SUPABASE_URL=https://pquleppdqequfjwlcmbn.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxdWxlcHBkcWVxdWZqd2xjbWJuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEzOTE2NTMsImV4cCI6MjA2Njk2NzY1M30.39JM1SBx5boaUAxu6fEl3BCclR5KYWCtSbpnrBfwmBQ

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=1
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file with your credentials")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def main():
    """Main test function."""
    print("=" * 60)
    print("🔧 Supabase Connection Test")
    print("=" * 60)
    print()
    
    # Test connection
    if test_connection():
        print()
        print("🎉 Connection test passed!")
        
        # Create .env file
        if create_env_file():
            print()
            print("Next steps:")
            print("1. Create the database tables in your Supabase dashboard")
            print("2. Run the migration script: python migrate_to_cloud.py")
            print("3. Start the cloud API: python memory-app/backend/cloud_api.py")
        else:
            print("❌ Failed to create .env file")
    else:
        print()
        print("❌ Connection test failed!")
        print("Please check your Supabase credentials and try again.")

if __name__ == "__main__":
    main() 