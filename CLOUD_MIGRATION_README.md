# MemoryOS Cloud Migration Guide

## 🚀 Why Migrate to Cloud?

The JSON-based memory system was becoming complex with file overwriting issues and state management problems. A cloud database provides:

- **Reliability**: No more file corruption or overwriting issues
- **Scalability**: Handle thousands of memories efficiently
- **Real-time**: Live updates across multiple sessions
- **Backup**: Automatic cloud backups
- **Performance**: Fast queries and indexing
- **Simplicity**: Clean API without file management complexity

## 📋 Migration Overview

This guide will help you transition from the JSON-based system to **Supabase** (PostgreSQL cloud database).

### What's Included

1. **Cloud Memory Manager** (`cloud_memory_manager.py`) - Handles all database operations
2. **Cloud API** (`cloud_api.py`) - REST API for the cloud database
3. **Migration Script** (`migrate_to_cloud.py`) - Moves your existing data
4. **Setup Script** (`setup_cloud.py`) - Configures Supabase connection

## 🛠️ Step-by-Step Migration

### Step 1: Set Up Supabase

1. **Create Supabase Account**
   - Go to [https://supabase.com](https://supabase.com)
   - Sign up for a free account
   - Create a new project

2. **Get Your Credentials**
   - Go to Settings > API in your project
   - Copy your **Project URL** and **anon/public key**


Project URL: https://pquleppdqequfjwlcmbn.supabase.co
Anon Public API Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxdWxlcHBkcWVxdWZqd2xjbWJuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEzOTE2NTMsImV4cCI6MjA2Njk2NzY1M30.39JM1SBx5boaUAxu6fEl3BCclR5KYWCtSbpnrBfwmBQ

3. **Create Database Tables**
   - Go to SQL Editor in your Supabase dashboard
   - Run the following SQL:

```sql
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
```

### Step 2: Run Setup Script

```bash
python setup_cloud.py
```

This script will:
- Install required dependencies
- Prompt for your Supabase credentials
- Test the connection
- Create a `.env` file with your credentials

### Step 3: Migrate Your Data

```bash
python migrate_to_cloud.py
```

This script will:
- Find your existing JSON memory files
- Preview what will be migrated
- Create a backup of your original data
- Migrate all memories to the cloud database

### Step 4: Start Cloud API

```bash
python memory-app/backend/cloud_api.py
```

The cloud API runs on port 5001 and provides all the same functionality as the JSON-based system.

## 🔄 API Endpoints

The cloud API provides these endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Check database connection |
| `/memories` | GET | Get all memories |
| `/memories` | POST | Add new memory |
| `/memories/<id>` | GET | Get specific memory |
| `/memories/<id>` | DELETE | Delete memory |
| `/memories/<id>/reinforce` | POST | Reinforce memory |
| `/search?q=<query>` | GET | Search memories |
| `/connections` | GET | Get memory connections |
| `/connections` | POST | Add connection |
| `/stats` | GET | Get database statistics |
| `/migrate` | POST | Migrate from JSON |
| `/export` | POST | Export to JSON |

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```env
SUPABASE_URL=your-project-url
SUPABASE_ANON_KEY=your-anon-key
FLASK_ENV=development
FLASK_DEBUG=1
```

### Frontend Updates

Update your frontend to use the cloud API:

```javascript
// Old JSON-based API
const API_BASE = 'http://localhost:5000';

// New Cloud API
const API_BASE = 'http://localhost:5001';
```

## 📊 Benefits of Cloud Database

### Performance
- **Fast Queries**: PostgreSQL with proper indexing
- **Full-text Search**: Built-in search capabilities
- **Pagination**: Efficient memory loading

### Reliability
- **No File Corruption**: Database transactions ensure data integrity
- **Automatic Backups**: Supabase handles backups
- **Concurrent Access**: Multiple users can access simultaneously

### Features
- **Real-time Updates**: Live score updates without polling
- **Complex Queries**: Advanced filtering and sorting
- **Scalability**: Handle thousands of memories
- **Relationships**: Proper foreign key relationships

## 🔍 Monitoring and Debugging

### Health Check
```bash
curl http://localhost:5001/health
```

### Database Stats
```bash
curl http://localhost:5001/stats
```

### View Logs
The API provides detailed logging for debugging:
- Memory operations
- Search queries
- Error handling
- Performance metrics

## 🚨 Troubleshooting

### Connection Issues
- Verify your Supabase credentials
- Check if tables exist in your database
- Ensure your project is active

### Migration Problems
- Check the backup file created during migration
- Verify JSON file format
- Check database permissions

### Performance Issues
- Monitor database query performance
- Check Supabase usage limits
- Optimize queries if needed

## 🔄 Rollback Plan

If you need to rollback:

1. **Keep Your Backup**: The migration script creates a backup
2. **Export from Cloud**: Use `/export` endpoint to get JSON
3. **Restore Original**: Copy backup back to original location
4. **Switch Back**: Use the original JSON-based API

## 📈 Next Steps

After migration:

1. **Test Thoroughly**: Verify all functionality works
2. **Update Documentation**: Update any references to JSON files
3. **Monitor Performance**: Watch for any issues
4. **Optimize**: Fine-tune queries and indexes as needed

## 🆘 Support

If you encounter issues:

1. Check the logs in the console
2. Verify Supabase dashboard for errors
3. Test individual API endpoints
4. Check the health endpoint for status

## 🎉 Migration Complete!

Once you've completed the migration:

- Your memories are safely stored in the cloud
- No more file overwriting issues
- Better performance and reliability
- Real-time updates and live scores
- Automatic backups and data integrity

The cloud-based system is much more robust and will scale with your needs! 