from flask import Flask, request, jsonify, send_from_directory
from memory_manager import MemoryManager
from flask_cors import CORS
import os
import threading

app = Flask(__name__, static_folder='../frontend')
CORS(app)  # This will enable CORS for all routes
mm = MemoryManager()

# Session memory queue for real-time updates
session_new_memories = []
session_new_memories_lock = threading.Lock()

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    # This serves script.js, style.css, etc.
    return send_from_directory(app.static_folder, path)

@app.route('/memories', methods=['GET', 'POST'])
def handle_memories():
    if request.method == 'POST':
        data = request.json
        content = data.get('content')
        if not content:
            return jsonify({"error": "Content is required"}), 400
        
        tags = data.get('tags', [])
        method = data.get('method', 'tfidf') # Default to 'tfidf'
        
        new_mem = mm.add_memory(content, tags, method)
        
        # Add new memory to session queue for real-time network update
        if new_mem:
            memory_data = {
                'id': new_mem['id'],
                'content': new_mem['content'],
                'score': new_mem.get('score', 0),
                'tags': new_mem.get('tags', []),
                'created': new_mem.get('created', '')
            }
            with session_new_memories_lock:
                session_new_memories.append(memory_data)
            print(f"🌐 Queued new memory for network: {memory_data['id']}")
        
        return jsonify(new_mem), 201
    else: # GET
        return jsonify(mm.get_all_memories())

@app.route('/search/<string:query>')
def search(query):
    # An empty query will now return all memories, sorted by score
    results = mm.search_memories(query if query != ' ' else '')
    return jsonify(results)

@app.route('/models', methods=['GET'])
def get_models():
    return jsonify({
        'available': mm.get_available_models(),
        'current': mm.get_current_model()
    })

@app.route('/models', methods=['POST'])
def set_model():
    data = request.json
    model_name = data.get('model')
    try:
        mm.set_model(model_name)
        return jsonify({'success': True, 'current': mm.get_current_model()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/new-memories')
def get_new_memories():
    """Get and clear the queue of new memories for real-time network updates"""
    with session_new_memories_lock:
        new_memories = session_new_memories.copy()
        session_new_memories.clear()
    
    return jsonify({
        'memories': new_memories,
        'count': len(new_memories)
    })

@app.route('/memory-network')
def memory_network():
    # Get threshold from query param, default 0.35
    try:
        threshold = float(request.args.get('threshold', 0.35))
    except Exception:
        threshold = 0.35
    
    # Use the comprehensive function to get connections and similarity matrix
    result = mm._calculate_all_scores_and_connections(threshold)
    if result is None or result == (None, None):
        return jsonify({'nodes': [], 'edges': []})
    
    connections, sim_matrix = result
    all_mems = mm._get_all_memories_flat()
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
            'size': 20 + min(mem.get('score', 0), 100) * 0.5,  # Node size by score
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
                    'width': 2 + 12 * sim,  # Match frontend scaling
                    'type': 'semantic'
                })

    return jsonify({'nodes': nodes, 'edges': edges})

@app.route('/memories/<string:memory_id>', methods=['DELETE'])
def delete_memory(memory_id):
    success = mm.delete_memory(memory_id)
    if success:
        return jsonify({'success': True}), 200
    return jsonify({'error': 'Memory not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
