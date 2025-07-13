# Supabase Database Setup for Moneta

This document contains the SQL commands needed to set up the Supabase database for Moneta's authentication and user-specific memory system.

## Environment Variables Required

Add these to your Render environment variables:

```bash
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
JWT_SECRET=your_random_jwt_secret_key
```

## Database Tables

### 1. Users Table

```sql
-- Create users table
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create index for faster email lookups
CREATE INDEX idx_users_email ON users(email);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see and update their own records
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);
```

### 2. User Memory Databases Table

```sql
-- Create user memory databases tracking table
CREATE TABLE user_memory_databases (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    memory_count INTEGER DEFAULT 0,
    UNIQUE(user_id)
);

-- Enable Row Level Security
ALTER TABLE user_memory_databases ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own memory database info
CREATE POLICY "Users can access own memory database" ON user_memory_databases
    FOR ALL USING (auth.uid() = user_id);
```

### 3. User Memories Table

```sql
-- Create user memories table (individual memory storage)
CREATE TABLE user_memories (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    score DECIMAL DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    embedding VECTOR(768) -- For future vector similarity search
);

-- Create indexes for better performance
CREATE INDEX idx_user_memories_user_id ON user_memories(user_id);
CREATE INDEX idx_user_memories_score ON user_memories(user_id, score DESC);
CREATE INDEX idx_user_memories_created_at ON user_memories(user_id, created_at DESC);
CREATE INDEX idx_user_memories_content_search ON user_memories USING gin(to_tsvector('english', content));

-- Enable Row Level Security
ALTER TABLE user_memories ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own memories
CREATE POLICY "Users can access own memories" ON user_memories
    FOR ALL USING (auth.uid() = user_id);
```

### 4. Memory Connections Table (Future Enhancement)

```sql
-- Create memory connections table for relationship mapping
CREATE TABLE memory_connections (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    from_memory_id UUID REFERENCES user_memories(id) ON DELETE CASCADE,
    to_memory_id UUID REFERENCES user_memories(id) ON DELETE CASCADE,
    similarity_score DECIMAL NOT NULL,
    connection_type TEXT DEFAULT 'semantic',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, from_memory_id, to_memory_id)
);

-- Create indexes
CREATE INDEX idx_memory_connections_user_id ON memory_connections(user_id);
CREATE INDEX idx_memory_connections_from_memory ON memory_connections(from_memory_id);
CREATE INDEX idx_memory_connections_similarity ON memory_connections(user_id, similarity_score DESC);

-- Enable Row Level Security
ALTER TABLE memory_connections ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own memory connections
CREATE POLICY "Users can access own memory connections" ON memory_connections
    FOR ALL USING (auth.uid() = user_id);
```

## Functions and Triggers

### 1. Update Memory Count Function

```sql
-- Function to update memory count when memories are added/removed
CREATE OR REPLACE FUNCTION update_memory_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE user_memory_databases 
        SET memory_count = memory_count + 1,
            last_accessed = NOW()
        WHERE user_id = NEW.user_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE user_memory_databases 
        SET memory_count = memory_count - 1,
            last_accessed = NOW()
        WHERE user_id = OLD.user_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER trigger_update_memory_count_insert
    AFTER INSERT ON user_memories
    FOR EACH ROW EXECUTE FUNCTION update_memory_count();

CREATE TRIGGER trigger_update_memory_count_delete
    AFTER DELETE ON user_memories
    FOR EACH ROW EXECUTE FUNCTION update_memory_count();
```

### 2. Initialize User Memory Database Function

```sql
-- Function to automatically create memory database when user registers
CREATE OR REPLACE FUNCTION initialize_user_memory_database()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_memory_databases (user_id)
    VALUES (NEW.id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER trigger_initialize_user_memory_database
    AFTER INSERT ON users
    FOR EACH ROW EXECUTE FUNCTION initialize_user_memory_database();
```

## Vector Search Setup (Optional - for advanced semantic search)

If you want to enable vector similarity search for memories:

```sql
-- Enable the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Function to search similar memories using embeddings
CREATE OR REPLACE FUNCTION search_similar_memories(
    query_embedding VECTOR(768),
    user_id_param UUID,
    similarity_threshold FLOAT DEFAULT 0.5,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    memory_id UUID,
    content TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        um.id,
        um.content,
        1 - (um.embedding <-> query_embedding) AS similarity
    FROM user_memories um
    WHERE um.user_id = user_id_param
        AND um.embedding IS NOT NULL
        AND (1 - (um.embedding <-> query_embedding)) > similarity_threshold
    ORDER BY um.embedding <-> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;
```

## Security Policies Summary

All tables use Row Level Security (RLS) to ensure:

1. **Users Table**: Users can only view and update their own profile
2. **User Memory Databases**: Users can only access their own memory database info
3. **User Memories**: Users can only CRUD their own memories
4. **Memory Connections**: Users can only access their own memory relationships

## Test Data (Optional)

```sql
-- Insert test user (for development only)
INSERT INTO users (name, email, password_hash) VALUES 
('Test User', 'test@example.com', 'hashed_password_here');

-- The trigger will automatically create the memory database entry
```

## Backup and Maintenance

### Regular Backups
```sql
-- Create a backup of user data
CREATE OR REPLACE FUNCTION backup_user_data(backup_user_id UUID)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'user', (SELECT row_to_json(u) FROM users u WHERE id = backup_user_id),
        'memories', (SELECT json_agg(row_to_json(m)) FROM user_memories m WHERE user_id = backup_user_id),
        'connections', (SELECT json_agg(row_to_json(c)) FROM memory_connections c WHERE user_id = backup_user_id)
    ) INTO result;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;
```

### Performance Monitoring
```sql
-- View to monitor memory usage per user
CREATE VIEW user_memory_stats AS
SELECT 
    u.id,
    u.name,
    u.email,
    umd.memory_count,
    umd.last_accessed,
    COALESCE(AVG(um.score), 0) as avg_memory_score
FROM users u
LEFT JOIN user_memory_databases umd ON u.id = umd.user_id
LEFT JOIN user_memories um ON u.id = um.user_id
GROUP BY u.id, u.name, u.email, umd.memory_count, umd.last_accessed;
```

## Notes

1. **Authentication**: This setup uses JWT tokens for authentication, not Supabase Auth
2. **Scalability**: Each user's memories are isolated using RLS
3. **Performance**: Indexes are optimized for common query patterns
4. **Security**: All sensitive operations require user authentication
5. **Extensibility**: Schema supports future enhancements like vector search

## Setup Checklist

- [ ] Create all tables in Supabase SQL editor
- [ ] Enable Row Level Security on all tables
- [ ] Create all policies
- [ ] Set up functions and triggers
- [ ] Add environment variables to Render
- [ ] Test authentication flow
- [ ] Verify memory isolation between users 