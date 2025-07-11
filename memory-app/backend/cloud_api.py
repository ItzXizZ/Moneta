from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
import sys

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cloud_memory_manager import CloudMemoryManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize cloud memory manager
memory_manager = CloudMemoryManager()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        if memory_manager.client:
            stats = memory_manager.get_stats()
            return jsonify({
                'status': 'healthy',
                'database_connected': True,
                'stats': stats
            })
        else:
            return jsonify({
                'status': 'unhealthy',
                'database_connected': False,
                'message': 'Supabase credentials not configured'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/memories', methods=['GET'])
def get_memories():
    """Get all memories from cloud database."""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        memories = memory_manager.get_memories(limit=limit, offset=offset)
        return jsonify(memories)
    except Exception as e:
        logger.error(f"Error getting memories: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/memories', methods=['POST'])
def add_memory():
    """Add a new memory to cloud database."""
    try:
        data = request.get_json()
        content = data.get('content')
        tags = data.get('tags', [])
        metadata = data.get('metadata', {})
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        memory = memory_manager.add_memory(content, tags, metadata)
        return jsonify(memory), 201
    except Exception as e:
        logger.error(f"Error adding memory: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/memories/<int:memory_id>', methods=['GET'])
def get_memory(memory_id):
    """Get a specific memory by ID."""
    try:
        memory = memory_manager.get_memory_by_id(memory_id)
        if memory:
            return jsonify(memory)
        else:
            return jsonify({'error': 'Memory not found'}), 404
    except Exception as e:
        logger.error(f"Error getting memory: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/memories/<int:memory_id>', methods=['DELETE'])
def delete_memory(memory_id):
    """Delete a memory from cloud database."""
    try:
        success = memory_manager.delete_memory(memory_id)
        if success:
            return jsonify({'message': 'Memory deleted successfully'})
        else:
            return jsonify({'error': 'Memory not found or could not be deleted'}), 404
    except Exception as e:
        logger.error(f"Error deleting memory: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/memories/<int:memory_id>/reinforce', methods=['POST'])
def reinforce_memory(memory_id):
    """Reinforce a memory by increasing its score."""
    try:
        data = request.get_json() or {}
        strength = data.get('strength', 1.0)
        
        memory = memory_manager.reinforce_memory(memory_id, strength)
        return jsonify(memory)
    except Exception as e:
        logger.error(f"Error reinforcing memory: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['GET'])
def search_memories():
    """Search memories by content."""
    try:
        query = request.args.get('q')
        limit = request.args.get('limit', 20, type=int)
        
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        results = memory_manager.search_memories(query, limit)
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/connections', methods=['GET'])
def get_connections():
    """Get all memory connections."""
    try:
        memory_id = request.args.get('memory_id', type=int)
        
        if memory_id:
            connections = memory_manager.get_connections(memory_id)
        else:
            connections = memory_manager.get_all_connections()
        
        return jsonify(connections)
    except Exception as e:
        logger.error(f"Error getting connections: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/connections', methods=['POST'])
def add_connection():
    """Add a connection between two memories."""
    try:
        data = request.get_json()
        source_id = data.get('source_id')
        target_id = data.get('target_id')
        strength = data.get('strength', 1.0)
        
        if not source_id or not target_id:
            return jsonify({'error': 'source_id and target_id are required'}), 400
        
        connection = memory_manager.add_connection(source_id, target_id, strength)
        return jsonify(connection), 201
    except Exception as e:
        logger.error(f"Error adding connection: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/migrate', methods=['POST'])
def migrate_from_json():
    """Migrate memories from JSON file to cloud database."""
    try:
        data = request.get_json()
        json_file_path = data.get('json_file_path')
        
        if not json_file_path:
            return jsonify({'error': 'json_file_path is required'}), 400
        
        if not os.path.exists(json_file_path):
            return jsonify({'error': 'JSON file not found'}), 404
        
        migrated_count = memory_manager.migrate_from_json(json_file_path)
        return jsonify({
            'message': f'Successfully migrated {migrated_count} memories',
            'migrated_count': migrated_count
        })
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/export', methods=['POST'])
def export_to_json():
    """Export all memories from cloud database to JSON file."""
    try:
        data = request.get_json()
        file_path = data.get('file_path', 'exported_memories.json')
        
        success = memory_manager.export_to_json(file_path)
        if success:
            return jsonify({
                'message': f'Successfully exported memories to {file_path}',
                'file_path': file_path
            })
        else:
            return jsonify({'error': 'Failed to export memories'}), 500
    except Exception as e:
        logger.error(f"Error during export: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get database statistics."""
    try:
        stats = memory_manager.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/setup', methods=['GET'])
def setup_instructions():
    """Get setup instructions for Supabase."""
    return jsonify({
        'message': 'Supabase Setup Instructions',
        'steps': [
            '1. Go to https://supabase.com and create a free account',
            '2. Create a new project',
            '3. Go to Settings > API to get your project URL and anon key',
            '4. Set environment variables:',
            '   - SUPABASE_URL: Your project URL',
            '   - SUPABASE_ANON_KEY: Your anon/public key',
            '5. Run the SQL schema in your Supabase SQL editor',
            '6. Restart the application'
        ],
        'schema_url': '/schema'
    })

@app.route('/new-memories', methods=['GET'])
def get_new_memories():
    """Get new memories (placeholder for real-time updates)."""
    # For now, just return empty array since this is for polling
    return jsonify({'memories': []})

@app.route('/memory-network', methods=['GET'])
def get_memory_network():
    """Get memory network data for visualization."""
    try:
        threshold = request.args.get('threshold', 0.35, type=float)
        
        # Get all memories
        memories = memory_manager.get_memories(limit=1000)
        
        # Create nodes for the network
        nodes = []
        edges = []
        
        for memory in memories:
            nodes.append({
                'id': memory['id'],
                'label': memory['content'][:50] + ('...' if len(memory['content']) > 50 else ''),
                'title': memory['content'],
                'score': memory['score']
            })
        
        # For now, return basic network without connections
        # You can enhance this later with actual similarity calculations
        return jsonify({
            'nodes': nodes,
            'edges': edges
        })
        
    except Exception as e:
        logger.error(f"Error getting memory network: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/schema', methods=['GET'])
def get_schema():
    """Get the SQL schema for creating tables."""
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
    return jsonify({
        'schema': schema,
        'instructions': 'Run this SQL in your Supabase SQL editor to create the required tables.'
    })

if __name__ == '__main__':
    # Check if Supabase credentials are configured
    if not memory_manager.client:
        print("⚠️  Supabase credentials not configured!")
        print("Please set the following environment variables:")
        print("  - SUPABASE_URL: Your Supabase project URL")
        print("  - SUPABASE_ANON_KEY: Your Supabase anon/public key")
        print("\nOr visit /setup for detailed instructions.")
        print("\nStarting server anyway for setup endpoints...")
    
    app.run(debug=True, host='0.0.0.0', port=5001) 