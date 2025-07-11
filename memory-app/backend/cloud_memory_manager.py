import os
import json
import time
import numpy as np
from typing import List, Dict, Optional, Tuple
from supabase import create_client, Client
from datetime import datetime
import logging
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloudMemoryManager:
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """
        Initialize the cloud memory manager with Supabase connection.
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anon/public key
        """
        # Use hardcoded credentials
        self.supabase_url = supabase_url or "https://pquleppdqequfjwlcmbn.supabase.co"
        self.supabase_key = supabase_key or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxdWxlcHBkcWVxdWZqd2xjbWJuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEzOTE2NTMsImV4cCI6MjA2Njk2NzY1M30.39JM1SBx5boaUAxu6fEl3BCclR5KYWCtSbpnrBfwmBQ"
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")
            logger.info("You can get these from your Supabase project dashboard.")
            self.client = None
        else:
            self.client = create_client(self.supabase_url, self.supabase_key)
            self._ensure_tables_exist()
        
        # Initialize semantic search components for compatibility
        self.st_model = None
        self.search_embeddings = None
        self.search_index_map = []
        
        # Initialize search index
        self._build_search_index()
    
    def _lazy_load_st_model(self):
        """Lazy load the sentence transformer model."""
        if self.st_model is None:
            print("Loading SentenceTransformer model... (one-time operation)")
            self.st_model = SentenceTransformer('all-mpnet-base-v2')
            print("Model loaded.")
    
    def _build_search_index(self):
        """Build search index for semantic search compatibility."""
        if not self.client:
            return
        
        try:
            self._lazy_load_st_model()
            all_memories = self._get_all_memories_flat()
            
            if not all_memories:
                self.search_embeddings = None
                self.search_index_map = []
                return
            
            print("Building search index...")
            memory_texts = [mem['content'] for mem in all_memories]
            self.search_embeddings = self.st_model.encode(memory_texts)
            self.search_index_map = all_memories
            print("Search index built.")
        except Exception as e:
            logger.error(f"Error building search index: {e}")
            self.search_embeddings = None
            self.search_index_map = []
    
    def _get_all_memories_flat(self) -> List[Dict]:
        """Get all memories as a flat list (compatibility method)."""
        if not self.client:
            return []
        
        try:
            memories = self.get_memories(limit=1000)  # Get a large number
            return memories
        except Exception as e:
            logger.error(f"Error getting all memories: {e}")
            return []
    
    def reload_from_disk(self):
        """Reload memories from database (compatibility method)."""
        # For cloud database, we just rebuild the search index
        self._build_search_index()
    
    def get_all_memories(self) -> Dict:
        """Get all memories in the format expected by the existing interface."""
        memories = self._get_all_memories_flat()
        return {"memories": memories}

    def _ensure_tables_exist(self):
        """Ensure the required database tables exist."""
        try:
            # Create memories table if it doesn't exist
            self.client.table('memories').select('id').limit(1).execute()
            logger.info("Memories table exists and is accessible")
        except Exception as e:
            logger.error(f"Error accessing memories table: {e}")
            logger.info("Please create the memories table in your Supabase dashboard with the following SQL:")
            self._print_table_schema()
    
    def _print_table_schema(self):
        """Print the SQL schema for creating the required tables."""
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
        print("=== SUPABASE TABLE SCHEMA ===")
        print(schema)
        print("=== END SCHEMA ===")
    
    def add_memory(self, content: str, tags: List[str] = None, metadata: Dict = None) -> Dict:
        """Add a new memory to the cloud database."""
        if not self.client:
            raise Exception("Supabase client not initialized. Please set up credentials.")
        
        try:
            memory_data = {
                'content': content,
                'score': 1.0,
                'reinforcement_count': 0,
                'tags': tags or [],
                'metadata': metadata or {}
            }
            
            result = self.client.table('memories').insert(memory_data).execute()
            
            if result.data:
                memory = result.data[0]
                # Convert to format expected by existing interface
                memory['id'] = str(memory['id'])  # Convert to string for compatibility
                memory['created'] = memory.get('timestamp', datetime.now().isoformat())
                logger.info(f"Added memory with ID: {memory['id']}")
                
                # Rebuild search index to include new memory
                self._build_search_index()
                
                return memory
            else:
                raise Exception("Failed to add memory")
                
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            raise
    
    def get_memories(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get memories from the cloud database."""
        if not self.client:
            raise Exception("Supabase client not initialized. Please set up credentials.")
        
        try:
            result = self.client.table('memories')\
                .select('*')\
                .order('score', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            memories = result.data or []
            
            # Convert to format expected by existing interface
            for memory in memories:
                memory['id'] = str(memory['id'])  # Convert to string for compatibility
                memory['created'] = memory.get('timestamp', datetime.now().isoformat())
            
            return memories
            
        except Exception as e:
            logger.error(f"Error getting memories: {e}")
            return []
    
    def search_memories(self, query: str, top_k: int = 10, min_relevance: float = 0.2) -> List[Dict]:
        """Search memories with semantic similarity (compatibility method)."""
        if not self.client:
            return []
        
        try:
            # Use semantic search if available
            if self.search_embeddings is not None and self.search_index_map:
                self._lazy_load_st_model()
                
                # Get query embedding
                query_embedding = self.st_model.encode([query])
                similarities = np.dot(self.search_embeddings, query_embedding.T).flatten()
                
                # Create scored results
                scored_memories = []
                for i, similarity in enumerate(similarities):
                    if similarity > min_relevance:
                        memory = self.search_index_map[i]
                        scored_memories.append({
                            'memory': memory,
                            'relevance_score': float(similarity),
                            'importance_score': memory.get('score', 0),
                            'final_score': float(similarity) * 0.7 + (memory.get('score', 0) / 100) * 0.3
                        })
                
                # Sort and return top results
                return sorted(scored_memories, key=lambda x: x['final_score'], reverse=True)[:top_k]
            else:
                # Fallback to simple text search
                return self._fallback_search_with_format(query, top_k, min_relevance)
                
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return self._fallback_search_with_format(query, top_k, min_relevance)
    
    def _fallback_search_with_format(self, query: str, limit: int, min_relevance: float) -> List[Dict]:
        """Fallback search with proper formatting."""
        try:
            memories = self._fallback_search(query, limit)
            
            # Format results like semantic search
            formatted_results = []
            for memory in memories:
                formatted_results.append({
                    'memory': memory,
                    'relevance_score': 0.5,  # Default relevance for fallback
                    'importance_score': memory.get('score', 0),
                    'final_score': 0.5 * 0.7 + (memory.get('score', 0) / 100) * 0.3
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in fallback search: {e}")
            return []

    def _fallback_search(self, query: str, limit: int) -> List[Dict]:
        """Fallback search using LIKE operator."""
        try:
            result = self.client.table('memories')\
                .select('*')\
                .ilike('content', f'%{query}%')\
                .order('score', desc=True)\
                .limit(limit)\
                .execute()
            
            memories = result.data or []
            
            # Convert to format expected by existing interface
            for memory in memories:
                memory['id'] = str(memory['id'])  # Convert to string for compatibility
                memory['created'] = memory.get('timestamp', datetime.now().isoformat())
            
            return memories
            
        except Exception as e:
            logger.error(f"Error in fallback search: {e}")
            return []
    
    def _calculate_all_scores_and_connections(self, sim_threshold: float = 0.35, preserve_reinforcement: bool = True) -> Tuple[List, np.ndarray]:
        """Calculate connections and similarity matrix for compatibility."""
        if not self.client or self.search_embeddings is None:
            return None, None
        
        try:
            all_mems = self._get_all_memories_flat()
            n = len(all_mems)
            if n == 0:
                return None, None
            
            # Calculate similarity matrix
            normalized_embeddings = normalize(self.search_embeddings, norm='l2')
            sim_matrix = normalized_embeddings @ normalized_embeddings.T
            
            # Build connection graph
            connections = [[] for _ in range(n)]
            for i in range(n):
                for j in range(i+1, n):
                    sim = float(sim_matrix[i, j])
                    if sim >= sim_threshold:
                        connections[i].append((j, sim))
                        connections[j].append((i, sim))
            
            return connections, sim_matrix
            
        except Exception as e:
            logger.error(f"Error calculating connections: {e}")
            return None, None

    def reinforce_memory(self, memory_id: int, reinforcement_strength: float = 1.0) -> Dict:
        """Reinforce a memory by increasing its score."""
        if not self.client:
            raise Exception("Supabase client not initialized. Please set up credentials.")
        
        try:
            # Get current memory
            result = self.client.table('memories')\
                .select('*')\
                .eq('id', memory_id)\
                .single()\
                .execute()
            
            if not result.data:
                raise Exception(f"Memory with ID {memory_id} not found")
            
            memory = result.data
            current_score = memory['score']
            current_reinforcement_count = memory['reinforcement_count']
            
            # Calculate new score
            new_score = current_score + reinforcement_strength
            new_reinforcement_count = current_reinforcement_count + 1
            
            # Update memory
            update_data = {
                'score': new_score,
                'reinforcement_count': new_reinforcement_count,
                'last_reinforced': datetime.now().isoformat()
            }
            
            result = self.client.table('memories')\
                .update(update_data)\
                .eq('id', memory_id)\
                .execute()
            
            if result.data:
                logger.info(f"Reinforced memory {memory_id}: score {current_score} -> {new_score}")
                memory = result.data[0]
                memory['id'] = str(memory['id'])  # Convert to string for compatibility
                memory['created'] = memory.get('timestamp', datetime.now().isoformat())
                
                # Rebuild search index to reflect updated scores
                self._build_search_index()
                
                return memory
            else:
                raise Exception("Failed to reinforce memory")
                
        except Exception as e:
            logger.error(f"Error reinforcing memory: {e}")
            raise

    def get_memory_by_id(self, memory_id: int) -> Optional[Dict]:
        """Get a specific memory by ID."""
        if not self.client:
            return None
        
        try:
            result = self.client.table('memories')\
                .select('*')\
                .eq('id', memory_id)\
                .single()\
                .execute()
            
            if result.data:
                memory = result.data
                memory['id'] = str(memory['id'])  # Convert to string for compatibility
                memory['created'] = memory.get('timestamp', datetime.now().isoformat())
                return memory
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting memory by ID: {e}")
            return None

    def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory from cloud database."""
        if not self.client:
            return False
        
        try:
            result = self.client.table('memories')\
                .delete()\
                .eq('id', memory_id)\
                .execute()
            
            if result.data is not None:  # Supabase returns empty list for successful deletes
                logger.info(f"Deleted memory with ID: {memory_id}")
                
                # Rebuild search index to remove deleted memory
                self._build_search_index()
                
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False

    def add_connection(self, source_id: int, target_id: int, strength: float = 1.0) -> Dict:
        """Add a connection between two memories."""
        if not self.client:
            raise Exception("Supabase client not initialized. Please set up credentials.")
        
        try:
            connection_data = {
                'source_memory_id': source_id,
                'target_memory_id': target_id,
                'strength': strength
            }
            
            result = self.client.table('memory_connections')\
                .insert(connection_data)\
                .execute()
            
            if result.data:
                return result.data[0]
            else:
                raise Exception("Failed to add connection")
                
        except Exception as e:
            logger.error(f"Error adding connection: {e}")
            raise

    def get_connections(self, memory_id: int) -> List[Dict]:
        """Get all connections for a specific memory."""
        if not self.client:
            return []
        
        try:
            result = self.client.table('memory_connections')\
                .select('*')\
                .or_(f'source_memory_id.eq.{memory_id},target_memory_id.eq.{memory_id}')\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting connections: {e}")
            return []

    def get_all_connections(self) -> List[Dict]:
        """Get all memory connections."""
        if not self.client:
            return []
        
        try:
            result = self.client.table('memory_connections')\
                .select('*')\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting all connections: {e}")
            return []

    def migrate_from_json(self, json_file_path: str) -> int:
        """Migrate memories from JSON file to cloud database."""
        if not self.client:
            raise Exception("Supabase client not initialized. Please set up credentials.")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            memories = data.get('memories', [])
            migrated_count = 0
            
            for memory in memories:
                try:
                    memory_data = {
                        'content': memory['content'],
                        'score': memory.get('score', 1.0),
                        'reinforcement_count': memory.get('reinforcement_count', 0),
                        'tags': memory.get('tags', []),
                        'metadata': memory.get('metadata', {})
                    }
                    
                    result = self.client.table('memories').insert(memory_data).execute()
                    
                    if result.data:
                        migrated_count += 1
                        logger.info(f"Migrated memory: {memory['content'][:50]}...")
                        
                except Exception as e:
                    logger.error(f"Error migrating memory: {e}")
                    continue
            
            logger.info(f"Migration completed: {migrated_count} memories migrated")
            
            # Rebuild search index with migrated memories
            self._build_search_index()
            
            return migrated_count
            
        except Exception as e:
            logger.error(f"Error during migration: {e}")
            raise

    def export_to_json(self, file_path: str) -> bool:
        """Export all memories from cloud database to JSON file."""
        if not self.client:
            return False
        
        try:
            memories = self.get_memories(limit=10000)  # Get all memories
            
            export_data = {
                'memories': memories,
                'exported_at': datetime.now().isoformat(),
                'total_count': len(memories)
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(memories)} memories to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return False

    def get_stats(self) -> Dict:
        """Get statistics about the memory database."""
        if not self.client:
            return {'error': 'Database not connected'}
        
        try:
            # Get memory count
            memories_result = self.client.table('memories')\
                .select('id', count='exact')\
                .execute()
            
            memory_count = memories_result.count if memories_result.count is not None else 0
            
            # Get connection count
            connections_result = self.client.table('memory_connections')\
                .select('id', count='exact')\
                .execute()
            
            connection_count = connections_result.count if connections_result.count is not None else 0
            
            # Get average score
            avg_score = 0
            if memory_count > 0:
                memories = self.get_memories(limit=1000)
                if memories:
                    avg_score = sum(m.get('score', 0) for m in memories) / len(memories)
            
            return {
                'total_memories': memory_count,
                'total_connections': connection_count,
                'average_score': round(avg_score, 2),
                'database_type': 'cloud',
                'status': 'connected'
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'error': str(e)}

    def get_new_memories(self, since_timestamp: str = None) -> List[Dict]:
        """Get new memories since a specific timestamp."""
        if not self.client:
            return []
        
        try:
            query = self.client.table('memories').select('*').order('timestamp', desc=True)
            
            if since_timestamp:
                query = query.gte('timestamp', since_timestamp)
            
            result = query.limit(100).execute()
            
            memories = result.data or []
            
            # Convert to format expected by existing interface
            for memory in memories:
                memory['id'] = str(memory['id'])  # Convert to string for compatibility
                memory['created'] = memory.get('timestamp', datetime.now().isoformat())
            
            return memories
            
        except Exception as e:
            logger.error(f"Error getting new memories: {e}")
            return [] 