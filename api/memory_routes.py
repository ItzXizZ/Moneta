#!/usr/bin/env python3

from flask import request, jsonify
from config import config
from services.memory_search_service import memory_search_service

def register_memory_routes(app):
    """Register all memory-related routes with the Flask app"""
    
    @app.route('/check_memory_availability')
    def check_memory_availability():
        """Check if the memory system is available"""
        return jsonify({'available': config.memory_available})
    
    @app.route('/new-memories')
    def get_new_memories():
        """Get and clear the queue of new memories for real-time network updates"""
        print(f"🔧 DEBUG: /new-memories endpoint called")
        
        with config.session_new_memories_lock:
            print(f"🔧 DEBUG: Session queue size before copy: {len(config.session_new_memories)}")
            new_memories = config.session_new_memories.copy()
            config.session_new_memories.clear()
            print(f"🔧 DEBUG: Session queue size after clear: {len(config.session_new_memories)}")
        
        print(f"🔧 DEBUG: Returning {len(new_memories)} new memories")
        if new_memories:
            for i, memory in enumerate(new_memories):
                print(f"🔧 DEBUG: Memory {i+1}: {memory.get('content', 'N/A')[:30]}...")
        
        return jsonify({
            'memories': new_memories,
            'count': len(new_memories)
        })
    
    @app.route('/memory-network')
    def memory_network():
        """Get memory network data for visualization"""
        try:
            # Get threshold from query param, default 0.35
            threshold = float(request.args.get('threshold', config.min_relevance_threshold))
            
            # Get network data from memory search service
            network_data = memory_search_service.get_memory_network_data(threshold)
            
            return jsonify(network_data)
            
        except Exception as e:
            print(f"❌ Error in memory-network route: {e}")
            return jsonify({'nodes': [], 'edges': []}) 