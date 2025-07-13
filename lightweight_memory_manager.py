#!/usr/bin/env python3
"""
DEPRECATED: Lightweight Memory Manager (Fallback Only)

⚠️  This is a lightweight fallback version used only when ML dependencies are unavailable.
    The full-featured memory manager (memory-app/backend/memory_manager.py) is preferred
    and provides much more advanced capabilities:
    
    - Semantic search with sentence-transformers
    - Advanced reinforcement learning
    - Multi-degree connection graphs
    - Sophisticated scoring algorithms
    - Dynamic memory reinforcement
    
    This lightweight version provides basic memory functionality using simple text matching.
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

class LightweightMemoryManager:
    """
    ⚠️  DEPRECATED: A lightweight memory manager that provides basic memory functionality
    without requiring heavy ML libraries. This is only used as a fallback when the full
    ML-powered memory manager is not available.
    """
    
    def __init__(self, memory_file='memory_data.json'):
        self.memory_file = memory_file
        self.memories = []
        self.load_memories()
    
    def load_memories(self):
        """Load memories from JSON file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.memories = json.load(f)
                print(f"✅ Loaded {len(self.memories)} memories")
            else:
                self.memories = []
                print("📝 No existing memories found, starting fresh")
        except Exception as e:
            print(f"⚠️  Error loading memories: {e}")
            self.memories = []
    
    def save_memories(self):
        """Save memories to JSON file"""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memories, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved {len(self.memories)} memories")
        except Exception as e:
            print(f"❌ Error saving memories: {e}")
    
    def add_memory(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """Add a new memory"""
        memory_id = f"mem_{len(self.memories)}_{int(datetime.now().timestamp())}"
        
        memory = {
            'id': memory_id,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {},
            'access_count': 0
        }
        
        self.memories.append(memory)
        self.save_memories()
        
        print(f"🧠 Added memory: {memory_id}")
        return memory_id
    
    def search_memories(self, query: str, top_k: int = 5, min_relevance: float = 0.1) -> List[Dict[str, Any]]:
        """
        Search memories using simple text matching (no ML required).
        This is a lightweight alternative to semantic search.
        """
        if not query.strip():
            return []
        
        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))
        
        scored_memories = []
        
        for memory in self.memories:
            content_lower = memory['content'].lower()
            content_words = set(re.findall(r'\w+', content_lower))
            
            # Simple scoring based on word overlap
            common_words = query_words.intersection(content_words)
            score = len(common_words) / len(query_words) if query_words else 0
            
            # Boost score for exact phrase matches
            if query_lower in content_lower:
                score += 0.5
            
            # Boost score for partial matches
            for word in query_words:
                if word in content_lower:
                    score += 0.1
            
            if score > 0:
                memory_copy = memory.copy()
                memory_copy['score'] = score
                scored_memories.append(memory_copy)
        
        # Sort by score (highest first) and return top results
        scored_memories.sort(key=lambda x: x['score'], reverse=True)
        
        # Filter by minimum relevance
        filtered_memories = [m for m in scored_memories if m['score'] >= min_relevance]
        
        # Update access count for returned memories
        for memory in filtered_memories[:top_k]:
            self._update_access_count(memory['id'])
        
        # Return results in the expected format
        results = []
        for memory in filtered_memories[:top_k]:
            results.append({
                'memory': memory,
                'relevance_score': memory['score'],
                'final_score': memory['score']
            })
        
        return results
    
    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific memory by ID"""
        for memory in self.memories:
            if memory['id'] == memory_id:
                self._update_access_count(memory_id)
                return memory
        return None
    
    def _update_access_count(self, memory_id: str):
        """Update access count for a memory"""
        for memory in self.memories:
            if memory['id'] == memory_id:
                memory['access_count'] = memory.get('access_count', 0) + 1
                break
    
    def get_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent memories"""
        sorted_memories = sorted(self.memories, 
                               key=lambda x: x['timestamp'], 
                               reverse=True)
        return sorted_memories[:limit]
    
    def get_popular_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most accessed memories"""
        sorted_memories = sorted(self.memories, 
                               key=lambda x: x.get('access_count', 0), 
                               reverse=True)
        return sorted_memories[:limit]
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory"""
        for i, memory in enumerate(self.memories):
            if memory['id'] == memory_id:
                del self.memories[i]
                self.save_memories()
                print(f"🗑️  Deleted memory: {memory_id}")
                return True
        return False
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        if not self.memories:
            return {
                'total_memories': 0,
                'total_access_count': 0,
                'average_access_count': 0
            }
        
        total_access = sum(m.get('access_count', 0) for m in self.memories)
        
        return {
            'total_memories': len(self.memories),
            'total_access_count': total_access,
            'average_access_count': total_access / len(self.memories) if self.memories else 0
        }
    
    def reload_from_disk(self):
        """Reload memories from disk (for compatibility)"""
        self.load_memories()
    
    def _get_all_memories_flat(self) -> List[Dict[str, Any]]:
        """Get all memories in flat format (for compatibility)"""
        return self.memories
    
    def _calculate_all_scores_and_connections(self, threshold: float = 0.3):
        """Calculate memory connections (simplified for lightweight version)"""
        # For the lightweight version, we'll return minimal connections
        # This is a simplified version that doesn't do complex similarity calculations
        connections = []
        sim_matrix = []
        
        n = len(self.memories)
        for i in range(n):
            row_connections = []
            sim_row = []
            
            for j in range(n):
                if i != j:
                    # Simple similarity based on common words
                    content_i = self.memories[i]['content'].lower()
                    content_j = self.memories[j]['content'].lower()
                    
                    words_i = set(content_i.split())
                    words_j = set(content_j.split())
                    
                    if words_i and words_j:
                        similarity = len(words_i.intersection(words_j)) / len(words_i.union(words_j))
                    else:
                        similarity = 0
                    
                    sim_row.append(similarity)
                    
                    if similarity >= threshold:
                        row_connections.append((j, similarity))
                else:
                    sim_row.append(1.0)  # Self-similarity
            
            connections.append(row_connections)
            sim_matrix.append(sim_row)
        
        return connections, sim_matrix

# Alias for compatibility
MemoryManager = LightweightMemoryManager 