import json
from datetime import datetime
import uuid
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

class MemoryManager:
    def __init__(self, db_path='data/memories.json'):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(base_dir, db_path)
        self.memories = self._load_memories()
        
        # Initialize TF-IDF for the default method
        self.vectorizer = TfidfVectorizer()
        
        # Lazy-load the SentenceTransformer model and search index
        self.st_model = None
        self.search_embeddings = None
        self.search_index_map = []
        
        self._build_search_index() # Initial build

    def _lazy_load_st_model(self):
        if self.st_model is None:
            print("Loading SentenceTransformer model... (one-time operation)")
            self.st_model = SentenceTransformer('all-mpnet-base-v2')
            print("Model loaded.")

    def _build_search_index(self):
        """Builds embeddings for all memories for fast semantic search."""
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

    def _load_memories(self):
        if not os.path.exists(self.db_path) or os.path.getsize(self.db_path) == 0:
            default_memories = {"memories": []}
            self._save_memories_data(default_memories)
            return default_memories
        
        with open(self.db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Legacy data migration, can be removed in the future
        if "user_memories" in data:
            all_mems = []
            for category, mem_list in data["user_memories"].items():
                for mem in mem_list:
                    all_mems.append({
                        "id": mem.get("id", f"mem_{uuid.uuid4()}"),
                        "content": mem["content"],
                        "score": mem.get("weight", 5) * 20,
                        "tags": mem.get("tags", []),
                        "created": mem.get("created", datetime.now().strftime("%Y-%m-%d"))
                    })
            data = {"memories": all_mems}
            self._save_memories_data(data)
        
        return data

    def _save_memories_data(self, data):
        """Save memories data with file locking to prevent corruption."""
        import tempfile
        import shutil
        import time
        try:
            import fcntl
        except ImportError:
            fcntl = None  # Windows doesn't have fcntl
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Lock file path
        lock_path = self.db_path + '.lock'
        temp_path = self.db_path + '.tmp'
        backup_path = self.db_path + '.backup'
        
        # Try to acquire lock with retries
        max_retries = 10
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                # Try to create lock file (atomic operation)
                with open(lock_path, 'x') as lock_file:
                    lock_file.write(f"locked_by_pid_{os.getpid()}")
                break
            except FileExistsError:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                    continue
                else:
                    # Force remove stale lock if too old
                    try:
                        if os.path.exists(lock_path):
                            lock_age = time.time() - os.path.getmtime(lock_path)
                            if lock_age > 5:  # 5 seconds
                                os.remove(lock_path)
                                print("[MemoryManager] Removed stale lock file")
                                continue
                    except:
                        pass
                    raise Exception("Could not acquire file lock after retries")
        
        try:
            # Create backup of existing file
            if os.path.exists(self.db_path) and os.path.getsize(self.db_path) > 0:
                shutil.copy2(self.db_path, backup_path)
            
            # Write to temporary file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()  # Ensure data is written to disk
                os.fsync(f.fileno())  # Force write to disk
            
            # Verify the temporary file is valid JSON
            with open(temp_path, 'r', encoding='utf-8') as f:
                json.load(f)  # This will raise an exception if JSON is invalid
            
            # Atomic move to replace the original file
            if os.name == 'nt':  # Windows
                # On Windows, try multiple times due to file locking issues
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        if os.path.exists(self.db_path):
                            os.remove(self.db_path)
                        shutil.move(temp_path, self.db_path)
                        break
                    except (OSError, PermissionError) as e:
                        if attempt < max_attempts - 1:
                            time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                            continue
                        else:
                            raise e
            else:  # Unix/Linux
                shutil.move(temp_path, self.db_path)
                
            # Small delay to prevent rapid file system events
            time.sleep(0.02)
            
        except Exception as e:
            # Clean up temp file if something went wrong
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            
            # Restore from backup if available
            if os.path.exists(backup_path):
                try:
                    shutil.copy2(backup_path, self.db_path)
                    print(f"[MemoryManager] Restored from backup due to save error: {e}")
                except:
                    pass
            
            raise e
        finally:
            # Release lock
            try:
                if os.path.exists(lock_path):
                    os.remove(lock_path)
            except:
                pass
                
            # Clean up backup file (keep only one backup)
            if os.path.exists(backup_path):
                try:
                    os.remove(backup_path)
                except:
                    pass

    def _save_memories(self):
        self._save_memories_data(self.memories)

    def _get_all_memories_flat(self):
        # Return flat list of all memories
        return self.memories.get('memories', []).copy()

    def _update_scores_tfidf(self, new_content):
        all_mems = self._get_all_memories_flat()
        if len(all_mems) == 0:
            return
        contents = [mem['content'] for mem in all_mems] + [new_content]
        try:
            tfidf_matrix = self.vectorizer.fit_transform(contents)
            similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]
            for i, memory in enumerate(all_mems):
                if similarities[i] > 0.1:
                    memory['score'] += similarities[i] * 10
        except ValueError:
            pass # Vocabulary is empty

    def _update_scores_transformer(self, new_content):
        self._lazy_load_st_model()
        all_mems = self._get_all_memories_flat()
        if len(all_mems) == 0:
            return
        
        memory_texts = [mem['content'] for mem in all_mems]
        memory_embeddings = self.st_model.encode(memory_texts)
        new_embedding = self.st_model.encode([new_content])
        
        similarities = np.dot(memory_embeddings, new_embedding.T).flatten()
        
        for i, similarity in enumerate(similarities):
            if similarity > 0.6:
                memory_to_update = all_mems[i]
                score_increase = similarity * 30
                memory_to_update['score'] = float(memory_to_update['score']) + float(score_increase)
    
    def _calculate_all_scores_and_connections(self, sim_threshold=0.35, preserve_reinforcement=True):
        """
        Comprehensive function that calculates all scores and connections.
        Uses much more accurate similarity thresholds and quality filtering.
        
        Args:
            sim_threshold: Minimum similarity for connections (default 0.35)
                         - 0.35-0.5: Weak but meaningful connection
                         - 0.5-0.7: Moderate connection  
                         - 0.7-0.85: Strong connection
                         - 0.85+: Very strong connection
            preserve_reinforcement: If True, preserves existing reinforcement scores
        """
        if self.search_embeddings is None:
            self._build_search_index()
        
        all_mems = self._get_all_memories_flat()
        n = len(all_mems)
        if n == 0 or self.search_embeddings is None:
            return None, None
        
        # 1. Calculate similarity matrix using proper cosine similarity
        # Normalize embeddings to ensure cosine similarity is in [0,1] range
        normalized_embeddings = normalize(self.search_embeddings, norm='l2')
        sim_matrix = normalized_embeddings @ normalized_embeddings.T
        
        # 2. Build connection graph with much stricter thresholds
        connections = [[] for _ in range(n)]
        for i in range(n):
            for j in range(i+1, n):
                sim = float(sim_matrix[i, j])
                
                # Apply stricter similarity filtering
                if sim >= sim_threshold:
                    # Additional quality check: avoid connecting very short/generic texts
                    mem_i_words = len(all_mems[i]['content'].split())
                    mem_j_words = len(all_mems[j]['content'].split())
                    
                    # Require higher similarity for short texts (they can be misleadingly similar)
                    min_words = min(mem_i_words, mem_j_words)
                    if min_words <= 3:
                        # For very short texts, require much higher similarity
                        required_sim = max(sim_threshold + 0.15, 0.6)
                    elif min_words <= 5:
                        # For short texts, require moderately higher similarity  
                        required_sim = sim_threshold + 0.1
                    else:
                        required_sim = sim_threshold
                    
                    if sim >= required_sim:
                        connections[i].append((j, sim))
                        connections[j].append((i, sim))
        
        # 3. Calculate scores with weighted importance
        for i, mem in enumerate(all_mems):
            # Store existing reinforcement score if preserving
            existing_score = mem.get('score', 0) if preserve_reinforcement else 0
            
            # Calculate base score from connections
            base_score = 0.0
            connection_count = len(connections[i])
            
            # Base score from connections
            for neighbor, sim in connections[i]:
                # Weight stronger connections more heavily
                if sim >= 0.7:
                    weight = 3.0  # Strong connections
                elif sim >= 0.5:
                    weight = 2.0  # Moderate connections
                else:
                    weight = 1.0  # Weak connections
                base_score += sim * weight
            
            # Bonus for being a hub (connected to many relevant memories)
            if connection_count >= 3:
                base_score += connection_count * 0.1
            
            # Content quality bonus (longer, more detailed memories)
            word_count = len(mem['content'].split())
            if word_count >= 10:
                base_score += 0.2
            elif word_count >= 5:
                base_score += 0.1
            
            # Combine base score with existing reinforcement
            if preserve_reinforcement:
                # Keep the higher of base score or existing score, but add some base score
                final_score = max(existing_score, base_score * 0.5) + base_score * 0.3
            else:
                final_score = base_score
                
            mem['score'] = round(final_score, 2)
        
        # Only save if we're not preserving reinforcement (to avoid overwriting)
        if not preserve_reinforcement:
            self._save_memories()
        return connections, sim_matrix

    def _recalculate_scores_by_connections(self, sim_threshold=0.35, preserve_reinforcement=True):
        """Legacy wrapper - now calls the comprehensive function."""
        return self._calculate_all_scores_and_connections(sim_threshold, preserve_reinforcement)

    def _update_scores_on_add(self, new_content, method='tfidf'):
        """Legacy wrapper - now just recalculates everything."""
        # Rebuild search index to include new memory
        self._build_search_index()
        # Recalculate all scores, preserving reinforcement
        self._calculate_all_scores_and_connections(sim_threshold=0.35, preserve_reinforcement=True)

    def add_memory(self, content, tags=None, method='tfidf'):
        new_memory = {
            "id": f"mem_{uuid.uuid4()}",
            "content": content,
            "score": 0,  # Will be recalculated
            "tags": tags if tags is not None else [],
            "created": datetime.now().strftime("%Y-%m-%d")
        }
        # Always add to root level - no hierarchy
        self.memories['memories'].append(new_memory)
        self._save_memories()
        self._build_search_index()
        self._recalculate_scores_by_connections(preserve_reinforcement=True)  # Preserve existing reinforcement
        return new_memory

    def search_memories(self, query, top_k=10, min_relevance=0.2):
        """Search like AI models do for web results with dynamic memory reinforcement"""
        if self.search_embeddings is None or not self.search_index_map:
            print("Search index is empty. Returning all memories.")
            return self.get_all_memories().get('memories', [])

        # 1. Semantic similarity search
        query_embedding = self.st_model.encode([query])
        similarities = np.dot(self.search_embeddings, query_embedding.T).flatten()
        
        # 2. Combine semantic similarity with memory importance
        scored_memories = []
        recalled_memories = []  # Track which memories were recalled
        
        for i, similarity in enumerate(similarities):
            # DEBUG: Log all similarities for debugging
            memory = self.search_index_map[i]
            print(f"DEBUG: Memory '{memory['content'][:30]}...' similarity: {similarity:.3f}, min_relevance: {min_relevance}")
            
            if similarity > min_relevance:
                # Hybrid score: semantic relevance + memory importance
                final_score = (float(similarity) * 0.7) + (memory.get('score', 0) / 100 * 0.3)
                
                scored_memories.append({
                    'memory': memory,
                    'relevance_score': float(similarity),
                    'importance_score': memory.get('score', 0),
                    'final_score': final_score
                })
                
                # Track recalled memories for reinforcement
                recalled_memories.append((memory['id'], float(similarity)))
                print(f"DEBUG: ✅ INCLUDED - Score {similarity:.3f} > threshold {min_relevance}")
            else:
                print(f"DEBUG: ❌ FILTERED OUT - Score {similarity:.3f} <= threshold {min_relevance}")
        
        # 3. Sort and get top results
        top_results = sorted(scored_memories, key=lambda x: x['final_score'], reverse=True)[:top_k]
        
        # 4. Reinforce recalled memories (only the top results that were actually returned)
        if top_results:
            top_recalled = [(result['memory']['id'], result['relevance_score']) for result in top_results]
            self._reinforce_recalled_memories(top_recalled)
        
        return top_results

    def _reinforce_recalled_memories(self, recalled_memories):
        """
        Reinforce memories that were recalled by:
        1. Adding relevance score to the recalled memory's score
        2. Adding 30% to immediate neighbors (connected memories)
        3. Adding 30% of that (9%) to neighbors of neighbors
        4. Adding 30% of that (2.7%) to third-degree neighbors
        """
        if not recalled_memories:
            return
            
        print(f"🧠 Reinforcing {len(recalled_memories)} recalled memories...")
        
        # Get current connection graph (preserve reinforcement scores)
        result = self._calculate_all_scores_and_connections(sim_threshold=0.35, preserve_reinforcement=True)
        if result is None or result == (None, None):
            print("❌ No connection graph available for reinforcement")
            return
            
        connections, sim_matrix = result
        all_mems = self._get_all_memories_flat()
        
        # Create memory ID to index mapping
        id_to_index = {mem['id']: i for i, mem in enumerate(all_mems)}
        
        # Track all reinforcements to apply at once
        reinforcements = {}  # memory_id -> total_reinforcement
        
        for memory_id, relevance_score in recalled_memories:
            if memory_id not in id_to_index:
                continue
                
            memory_index = id_to_index[memory_id]
            # Limit base reinforcement to between 0 and 1
            base_reinforcement = min(1.0, max(0.0, relevance_score))
            
            print(f"   📈 Reinforcing '{all_mems[memory_index]['content'][:30]}...' (+{base_reinforcement:.2f})")
            
            # 1. Reinforce the recalled memory itself (100%)
            if memory_id not in reinforcements:
                reinforcements[memory_id] = 0
            reinforcements[memory_id] += base_reinforcement
            
            # 2. Reinforce immediate neighbors (30%)
            neighbor_reinforcement = base_reinforcement * 0.3
            visited_neighbors = set()
            
            for neighbor_idx, similarity in connections[memory_index]:
                neighbor_id = all_mems[neighbor_idx]['id']
                if neighbor_id not in reinforcements:
                    reinforcements[neighbor_id] = 0
                reinforcements[neighbor_id] += neighbor_reinforcement
                visited_neighbors.add(neighbor_idx)
            
            # 3. Reinforce neighbors of neighbors (9% = 30% of 30%)
            second_degree_reinforcement = neighbor_reinforcement * 0.3
            visited_second_degree = set()
            
            for neighbor_idx in visited_neighbors:
                for second_neighbor_idx, similarity in connections[neighbor_idx]:
                    if second_neighbor_idx != memory_index and second_neighbor_idx not in visited_neighbors:
                        second_neighbor_id = all_mems[second_neighbor_idx]['id']
                        if second_neighbor_id not in reinforcements:
                            reinforcements[second_neighbor_id] = 0
                        reinforcements[second_neighbor_id] += second_degree_reinforcement
                        visited_second_degree.add(second_neighbor_idx)
            
            # 4. Reinforce third-degree neighbors (2.7% = 30% of 9%)
            third_degree_reinforcement = second_degree_reinforcement * 0.3
            
            for second_neighbor_idx in visited_second_degree:
                for third_neighbor_idx, similarity in connections[second_neighbor_idx]:
                    if (third_neighbor_idx != memory_index and 
                        third_neighbor_idx not in visited_neighbors and 
                        third_neighbor_idx not in visited_second_degree):
                        third_neighbor_id = all_mems[third_neighbor_idx]['id']
                        if third_neighbor_id not in reinforcements:
                            reinforcements[third_neighbor_id] = 0
                        reinforcements[third_neighbor_id] += third_degree_reinforcement
        
        # Apply all reinforcements
        total_reinforced = 0
        for memory in all_mems:
            if memory['id'] in reinforcements:
                old_score = memory.get('score', 0)
                reinforcement = reinforcements[memory['id']]
                memory['score'] = round(old_score + reinforcement, 2)
                total_reinforced += 1
        
        print(f"   ✅ Applied reinforcements to {total_reinforced} memories")
        
        # Save the updated memories to persist reinforcement scores
        self._save_memories()
        
        # Rebuild search index with new scores
        self._build_search_index()

    def get_all_memories(self):
        """Get all memories as a flat list, sorted by score."""
        # Get all memories flat and sort by score (don't recalculate to preserve reinforcement)
        all_memories = self._get_all_memories_flat()
        sorted_memories = sorted(all_memories, key=lambda x: x.get('score', 0), reverse=True)
        
        # Update the in-memory structure but don't save (to avoid overwriting)
        self.memories['memories'] = sorted_memories
        return self.memories

    def get_top_memories(self, limit=10):
        all_memories = self._get_all_memories_flat()
        return sorted(all_memories, key=lambda x: x.get('score', 0), reverse=True)[:limit]

    def get_memory_by_id(self, memory_id):
        for memory in self.memories['memories']:
            if memory['id'] == memory_id:
                return memory
        return None

    def boost_memory(self, memory_id, boost_factor=1.2):
        for memory in self.memories['memories']:
            if memory['id'] == memory_id:
                memory['score'] = memory.get('score', 0) * boost_factor
                self._save_memories()
                return memory
        return None

    def export_for_llm(self, context_limit=2000):
        """Export top memories in LLM-friendly format"""
        memories = self.get_top_memories(limit=100) # Get a larger pool to select from
        
        # This function might need updating depending on the desired LLM format
        # For now, it provides a simple JSON structure of top memories.
        
        exported_memories = []
        total_chars = 0
        
        for mem in memories:
            mem_str = json.dumps(mem)
            if total_chars + len(mem_str) > context_limit:
                break
            exported_memories.append(mem)
            total_chars += len(mem_str)
        
        total_score = sum(m.get('score', 0) for m in exported_memories)

        return {
            "user_context": {
                "memories": exported_memories,
                "total_score": total_score
            }
        }

    def delete_memory(self, memory_id):
        # Find and delete memory from flat list
        for i, memory in enumerate(self.memories['memories']):
            if memory['id'] == memory_id:
                del self.memories['memories'][i]
                self._save_memories()
                self._build_search_index()
                # Recalculate scores but preserve reinforcement for remaining memories
                self._recalculate_scores_by_connections(preserve_reinforcement=True)
                return True
        return False
    AVAILABLE_MODELS = [
        'all-mpnet-base-v2'
    ]

    def set_model(self, model_name):
        if model_name not in self.AVAILABLE_MODELS:
            raise ValueError('Model not supported')
        if self.st_model is None or self.st_model_name != model_name:
            print(f"Loading model: {model_name}")
            self.st_model = SentenceTransformer(model_name)
            self.st_model_name = model_name
            self._build_search_index()
            self._recalculate_scores_by_connections(sim_threshold=0.35)

    def get_available_models(self):
        return self.AVAILABLE_MODELS

    def get_current_model(self):
        return getattr(self, 'st_model_name', 'all-mpnet-base-v2')

    def _get_last_update_time(self):
        """Get the timestamp of the last score update"""
        try:
            if os.path.exists(self.db_path):
                return os.path.getmtime(self.db_path)
            return 0
        except:
            return 0

    def recalculate_all_scores(self, sim_threshold=0.35):
        """
        Manually recalculate all scores from scratch (use sparingly).
        This will overwrite any existing reinforcement scores.
        """
        print("🔄 Manually recalculating all scores from scratch...")
        result = self._calculate_all_scores_and_connections(sim_threshold, preserve_reinforcement=False)
        self._save_memories()
        print("✅ Score recalculation complete")
        return result

    def save_current_scores(self):
        """
        Save current scores to JSON file to make them persistent.
        This preserves all current reinforcement and connection scores.
        """
        print("💾 Saving current scores to JSON...")
        self._save_memories()
        print("✅ Current scores saved to memories.json")
        return True

    def reload_from_disk(self):
        """Reload memories and search index from disk with error handling."""
        # Check for lock file first
        lock_path = self.db_path + '.lock'
        if os.path.exists(lock_path):
            print("[MemoryManager] File is locked, skipping reload")
            return
            
        try:
            # Check if file exists and is not empty
            if not os.path.exists(self.db_path):
                print("[MemoryManager] Warning: memories.json not found, creating default")
                self.memories = {"memories": []}
                self._save_memories()
                self._build_search_index()
                return
                
            # Check file size to avoid reading empty/corrupted files
            file_size = os.path.getsize(self.db_path)
            if file_size == 0:
                print("[MemoryManager] Warning: memories.json is empty, skipping reload")
                return
            elif file_size < 10:  # Too small to be valid JSON
                print(f"[MemoryManager] Warning: memories.json too small ({file_size} bytes), skipping reload")
                return
                
            # Try to load with retries for file locking
            import time
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Small delay to ensure file write is complete
                    time.sleep(0.05 * (attempt + 1))
                    
                    # Attempt to load the file
                    with open(self.db_path, 'r', encoding='utf-8') as f:
                        file_content = f.read().strip()
                        if not file_content:
                            print("[MemoryManager] Warning: memories.json content is empty, skipping reload")
                            return
                        
                        # Parse JSON
                        data = json.loads(file_content)
                        
                        # Validate structure
                        if not isinstance(data, dict) or 'memories' not in data:
                            print("[MemoryManager] Warning: Invalid memories.json structure, skipping reload")
                            return
                        
                        # Update memories and rebuild index
                        self.memories = data
                        self._build_search_index()
                        print("[MemoryManager] ✅ Reloaded memories and rebuilt search index from disk.")
                        return
                        
                except (IOError, OSError) as io_error:
                    if attempt < max_retries - 1:
                        print(f"[MemoryManager] File locked (attempt {attempt + 1}), retrying...")
                        continue
                    else:
                        raise io_error
            
        except (json.JSONDecodeError, IOError, OSError) as e:
            print(f"[MemoryManager] ⚠️ Error reloading from disk: {e}")
            print("[MemoryManager] Keeping current memory state to avoid data loss")
            
            # Try to restore from backup if available
            backup_path = self.db_path + '.backup'
            if os.path.exists(backup_path):
                try:
                    import shutil
                    shutil.copy2(backup_path, self.db_path)
                    print("[MemoryManager] Restored from backup file")
                except Exception as backup_error:
                    print(f"[MemoryManager] Failed to restore from backup: {backup_error}")
            
            # Keep the current state instead of crashing

