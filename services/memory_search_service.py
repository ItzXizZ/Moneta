#!/usr/bin/env python3

import requests
from config import config

class MemorySearchService:
    """Service for searching and filtering memories"""
    
    def __init__(self):
        self.memory_manager = config.memory_manager
        self.memory_available = config.memory_available
        self.min_relevance = config.min_relevance_threshold
        self.max_results = config.max_search_results
        self.max_injected = config.max_injected_memories
    
    def search_memories_with_strict_filtering(self, query):
        """
        Search memories with strict relevance filtering.
        Only returns memories with relevance_score >= min_relevance_threshold.
        """
        if not self.memory_available or not self.memory_manager:
            print("⚠️ Memory system not available")
            return []
        
        try:
            print(f"\n🔍 Searching memories for: '{query}'")
            print(f"🔧 DEBUG: Using min_relevance={self.min_relevance} threshold")
            
            # Force a quick reload to ensure we have the latest memories
            try:
                self.memory_manager.reload_from_disk()
            except:
                pass  # Don't fail if reload fails
            
            # Get more raw results with lower threshold for better filtering
            search_results = self.memory_manager.search_memories(
                query, 
                top_k=self.max_results, 
                min_relevance=0.1  # Low threshold to get more candidates
            )
            
            # Apply STRICT relevance filtering - only relevance_score >= threshold
            strict_filtered_results = [
                r for r in search_results 
                if r.get('relevance_score', 0) >= self.min_relevance
            ]
            
            print(f"🔧 DEBUG: Raw search returned {len(search_results)} results, strict filter kept {len(strict_filtered_results)}")
            
            # Take top results after strict filtering
            memory_context = strict_filtered_results[:self.max_injected]
            
            # If no results from strict local search, try API search as backup
            if not memory_context:
                memory_context = self._try_api_fallback_search(query)
            
            self._log_search_results(memory_context)
            return memory_context
            
        except Exception as e:
            print(f"❌ Memory search error: {e}")
            return []
    
    def _try_api_fallback_search(self, query):
        """Try API search as backup with STRICT filtering"""
        try:
            api_response = requests.get(f'http://localhost:5000/search/{query}', timeout=5)
            if api_response.status_code == 200:
                api_results = api_response.json()
                if api_results:
                    # Apply STRICT relevance filtering to API results
                    filtered_api_results = []
                    for result in api_results:
                        if isinstance(result, dict):
                            relevance_score = result.get('relevance_score', 0)
                            if relevance_score >= self.min_relevance:
                                filtered_api_results.append(result)
                            print(f"   API result: '{result.get('memory', {}).get('content', 'N/A')[:30]}...' relevance: {relevance_score:.3f} {'✅' if relevance_score >= self.min_relevance else '❌'}")
                    
                    if filtered_api_results:
                        print(f"   🔄 Found {len(filtered_api_results)} STRICT filtered memories via API fallback (from {len(api_results)} total)")
                        return filtered_api_results[:self.max_injected]
                    else:
                        print(f"   🔄 API returned {len(api_results)} memories but NONE met STRICT {self.min_relevance} relevance threshold")
        except Exception as e:
            print(f"   ⚠️ API search fallback failed: {e}")
        
        return []
    
    def _log_search_results(self, results):
        """Log the search results for debugging"""
        print(f"📊 Found {len(results)} STRICT filtered memories (relevance >= {self.min_relevance}):")
        for i, result in enumerate(results):
            print(f"  {i+1}. '{result['memory']['content']}' (relevance: {result['relevance_score']:.3f}, final: {result['final_score']:.3f})")
            # All should be >= threshold now
            if result['relevance_score'] < self.min_relevance:
                print(f"       🚨 BUG: This memory passed strict filter but score {result['relevance_score']:.3f} < {self.min_relevance}!")
    
    def format_memories_for_injection(self, memory_context):
        """Format memories for injection into the prompt"""
        if not memory_context:
            return ""
        
        print(f"🔧 DEBUG: About to inject {len(memory_context[:3])} memories:")
        memory_text = "USER MEMORIES (for context):\n"
        
        for result in memory_context[:3]:  # Use top 3
            print(f"   - '{result['memory']['content']}' (relevance: {result['relevance_score']:.3f})")
            memory_text += f"- {result['memory']['content']} (relevance: {result['relevance_score']:.2f})\n"
        
        memory_text += "\nUse these memories to personalize your response when relevant."
        print(f"💡 Injected {len(memory_context[:3])} memories into prompt")
        
        return memory_text
    
    def get_memory_network_data(self, threshold=None):
        """Get memory network data for visualization"""
        if not self.memory_available or not self.memory_manager:
            return {'nodes': [], 'edges': []}
        
        try:
            # Use provided threshold or default
            threshold = threshold if threshold is not None else self.min_relevance
            
            # Use the comprehensive function to get connections and similarity matrix
            result = self.memory_manager._calculate_all_scores_and_connections(threshold)
            if result is None or result == (None, None):
                return {'nodes': [], 'edges': []}
            
            connections, sim_matrix = result
            all_mems = self.memory_manager._get_all_memories_flat()
            nodes = []
            edges = []

            # Build nodes
            for mem in all_mems:
                nodes.append({
                    'id': mem['id'],
                    'label': mem['content'],
                    'score': mem.get('score', 0),
                    'created': mem.get('created', ''),
                    'tags': mem.get('tags', []),
                    'size': 20 + min(mem.get('score', 0), 100) * 0.5,
                })

            # Build edges from the connection graph
            n = len(all_mems)
            for i in range(n):
                for j, sim in connections[i]:
                    if i < j:  # Avoid duplicate edges
                        edges.append({
                            'from': all_mems[i]['id'],
                            'to': all_mems[j]['id'],
                            'value': sim,
                            'color': 'rgba(168,85,247,' + str(min(1, sim)) + ')',
                            'width': 2 + 12 * sim,
                            'type': 'semantic'
                        })

            return {'nodes': nodes, 'edges': edges}
            
        except Exception as e:
            print(f"❌ Error in memory network data: {e}")
            return {'nodes': [], 'edges': []}

# Global service instance
memory_search_service = MemorySearchService() 