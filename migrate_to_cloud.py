#!/usr/bin/env python3
"""
Migration script to transition from JSON-based memory system to Supabase cloud database.
"""

import os
import json
import sys
import time
sys.path.append('memory-app/backend')
from cloud_memory_manager import CloudMemoryManager

def print_banner():
    """Print migration banner."""
    print("=" * 60)
    print("🔄 MemoryOS Cloud Migration Tool")
    print("=" * 60)
    print()

def check_supabase_setup():
    """Check if Supabase is properly configured."""
    print("🔍 Checking Supabase configuration...")
    
    memory_manager = CloudMemoryManager()
    
    if not memory_manager.client:
        print("❌ Supabase credentials not found!")
        print()
        print("Please set the following environment variables:")
        print("  export SUPABASE_URL='your-project-url'")
        print("  export SUPABASE_ANON_KEY='your-anon-key'")
        print()
        print("Or on Windows:")
        print("  set SUPABASE_URL=your-project-url")
        print("  set SUPABASE_ANON_KEY=your-anon-key")
        print()
        print("You can get these from your Supabase project dashboard:")
        print("  https://supabase.com/dashboard/project/[your-project]/settings/api")
        print()
        return False
    
    print("✅ Supabase credentials found!")
    return True

def setup_database_schema():
    """Help user set up the database schema."""
    print("🗄️  Database Schema Setup")
    print("-" * 30)
    print()
    print("You need to create the required tables in your Supabase database.")
    print("Follow these steps:")
    print()
    print("1. Go to your Supabase dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Run the following SQL:")
    print()
    
    schema = """
-- Create memories table
CREATE TABLE memories (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    score REAL DEFAULT 1.0,
    reinforcement_count INTEGER DEFAULT 0,
    last_reinforced TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

-- Create connections table for memory relationships
CREATE TABLE memory_connections (
    id SERIAL PRIMARY KEY,
    source_memory_id INTEGER REFERENCES memories(id) ON DELETE CASCADE,
    target_memory_id INTEGER REFERENCES memories(id) ON DELETE CASCADE,
    strength REAL DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_memory_id, target_memory_id)
);

-- Create indexes for better performance
CREATE INDEX idx_memories_score ON memories(score DESC);
CREATE INDEX idx_memories_timestamp ON memories(timestamp DESC);
CREATE INDEX idx_connections_source ON memory_connections(source_memory_id);
CREATE INDEX idx_connections_target ON memory_connections(target_memory_id);
    """
    
    print(schema)
    print()
    
    input("Press Enter after you've run the SQL schema...")

def find_json_files():
    """Find JSON memory files in the project."""
    print("📁 Looking for JSON memory files...")
    
    possible_files = [
        "memory-app/backend/data/memories.json",
        "memories.json",
        "chat_history.json"
    ]
    
    found_files = []
    
    for file_path in possible_files:
        if os.path.exists(file_path):
            found_files.append(file_path)
            print(f"✅ Found: {file_path}")
    
    if not found_files:
        print("❌ No JSON memory files found!")
        print("Please ensure your memory files are in one of these locations:")
        for file_path in possible_files:
            print(f"  - {file_path}")
        return []
    
    return found_files

def preview_migration(json_file_path):
    """Preview what will be migrated."""
    print(f"📋 Previewing migration from: {json_file_path}")
    print("-" * 50)
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            memories = data
            connections = []
        elif isinstance(data, dict):
            memories = data.get('memories', [])
            connections = data.get('connections', [])
        else:
            print("❌ Invalid JSON format")
            return False
        
        print(f"📝 Memories to migrate: {len(memories)}")
        print(f"🔗 Connections to migrate: {len(connections)}")
        print()
        
        if memories:
            print("Sample memories:")
            for i, memory in enumerate(memories[:3]):
                content = memory.get('content', '')[:100]
                score = memory.get('score', 1.0)
                print(f"  {i+1}. Score: {score} | Content: {content}...")
            
            if len(memories) > 3:
                print(f"  ... and {len(memories) - 3} more")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        return False

def perform_migration(json_file_path):
    """Perform the actual migration."""
    print(f"🚀 Starting migration from: {json_file_path}")
    print("-" * 50)
    
    memory_manager = CloudMemoryManager()
    
    try:
        migrated_count = memory_manager.migrate_from_json(json_file_path)
        
        print(f"✅ Migration completed successfully!")
        print(f"📊 Migrated {migrated_count} memories to cloud database")
        
        # Get stats
        stats = memory_manager.get_stats()
        print()
        print("📈 Database Statistics:")
        print(f"  Total memories: {stats.get('total_memories', 0)}")
        print(f"  Total connections: {stats.get('total_connections', 0)}")
        print(f"  Average score: {stats.get('average_score', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def backup_json_file(json_file_path):
    """Create a backup of the JSON file."""
    backup_path = f"{json_file_path}.backup.{int(time.time())}"
    
    try:
        import shutil
        shutil.copy2(json_file_path, backup_path)
        print(f"💾 Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"⚠️  Warning: Could not create backup: {e}")
        return None

def main():
    """Main migration function."""
    print_banner()
    
    # Check Supabase setup
    if not check_supabase_setup():
        return False
    
    # Setup database schema
    setup_database_schema()
    
    # Find JSON files
    json_files = find_json_files()
    if not json_files:
        return False
    
    # Let user choose which file to migrate
    if len(json_files) > 1:
        print("Multiple JSON files found. Choose one to migrate:")
        for i, file_path in enumerate(json_files):
            print(f"  {i+1}. {file_path}")
        
        while True:
            try:
                choice = int(input("\nEnter your choice (number): ")) - 1
                if 0 <= choice < len(json_files):
                    json_file_path = json_files[choice]
                    break
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
    else:
        json_file_path = json_files[0]
    
    # Preview migration
    if not preview_migration(json_file_path):
        return False
    
    # Confirm migration
    print()
    response = input("Do you want to proceed with the migration? (y/N): ").lower()
    if response != 'y':
        print("Migration cancelled.")
        return False
    
    # Create backup
    backup_path = backup_json_file(json_file_path)
    
    # Perform migration
    success = perform_migration(json_file_path)
    
    if success:
        print()
        print("🎉 Migration completed successfully!")
        print()
        print("Next steps:")
        print("1. Update your application to use the cloud API")
        print("2. Test the new cloud-based system")
        print("3. Keep the backup file for safety")
        if backup_path:
            print(f"   Backup location: {backup_path}")
        print()
        print("To use the cloud API, update your frontend to point to:")
        print("  http://localhost:5001 (for the cloud API)")
        print("  Instead of the old JSON-based API")
    else:
        print()
        print("❌ Migration failed. Your original data is safe.")
        if backup_path:
            print(f"Backup created at: {backup_path}")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 