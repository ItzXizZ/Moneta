#!/usr/bin/env python3
"""
Setup script for MemoryOS Cloud Database
"""

import os
import sys

def print_banner():
    """Print setup banner."""
    print("=" * 60)
    print("☁️  MemoryOS Cloud Database Setup")
    print("=" * 60)
    print()

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "memory-app/requirements_cloud.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def get_supabase_credentials():
    """Get Supabase credentials from user."""
    print("🔑 Supabase Credentials Setup")
    print("-" * 30)
    print()
    print("You need to get your Supabase credentials:")
    print("1. Go to https://supabase.com and create a free account")
    print("2. Create a new project")
    print("3. Go to Settings > API")
    print("4. Copy your Project URL and anon/public key")
    print()
    
    url = input("Enter your Supabase Project URL: ").strip()
    key = input("Enter your Supabase anon/public key: ").strip()
    
    if not url or not key:
        print("❌ Both URL and key are required!")
        return None, None
    
    return url, key

def create_env_file(url, key):
    """Create .env file with Supabase credentials."""
    env_content = f"""# Supabase Configuration
SUPABASE_URL={url}
SUPABASE_ANON_KEY={key}

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

def test_connection(url, key):
    """Test the Supabase connection."""
    print("🔍 Testing Supabase connection...")
    
    try:
        import sys
        sys.path.append('memory-app/backend')
        from cloud_memory_manager import CloudMemoryManager
        memory_manager = CloudMemoryManager(url, key)
        
        if memory_manager.client:
            print("✅ Connection successful!")
            return True
        else:
            print("❌ Connection failed!")
            return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def print_next_steps():
    """Print next steps for the user."""
    print()
    print("🎉 Setup completed successfully!")
    print()
    print("Next steps:")
    print("1. Run the migration script to move your data:")
    print("   python migrate_to_cloud.py")
    print()
    print("2. Start the cloud API server:")
    print("   python memory-app/backend/cloud_api.py")
    print()
    print("3. Update your frontend to use the cloud API:")
    print("   Change API endpoints from JSON-based to cloud-based")
    print()
    print("4. Test the new system!")
    print()

def main():
    """Main setup function."""
    print_banner()
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Get Supabase credentials
    url, key = get_supabase_credentials()
    if not url or not key:
        return False
    
    # Test connection
    if not test_connection(url, key):
        print("❌ Please check your credentials and try again.")
        return False
    
    # Create .env file
    if not create_env_file(url, key):
        return False
    
    # Print next steps
    print_next_steps()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 