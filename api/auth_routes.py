#!/usr/bin/env python3
"""
Authentication API Routes for Moneta
Handles user registration, login, and authenticated memory operations.
"""

from flask import Blueprint, request, jsonify, render_template
from auth_system import auth_system, user_memory_manager

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def landing_page():
    """Serve the landing page."""
    return render_template('landing.html')

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validation
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        if not password or len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Register user
        result = auth_system.register_user(name, email, password)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Account created successfully',
                'user': result['user'],
                'token': result['token']
            }), 201
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate user login."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validation
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        # Authenticate user
        result = auth_system.login_user(email, password)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': result['user'],
                'token': result['token']
            }), 200
        else:
            return jsonify({'error': result['error']}), 401
            
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/api/auth/verify', methods=['GET'])
@auth_system.require_auth
def verify_token():
    """Verify JWT token and return user info."""
    return jsonify({
        'success': True,
        'user': request.current_user
    }), 200

@auth_bp.route('/api/auth/logout', methods=['POST'])
@auth_system.require_auth
def logout():
    """Logout user (client-side token removal)."""
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200

# Memory Management Routes (User-specific)

@auth_bp.route('/api/memories', methods=['GET'])
@auth_system.require_auth
def get_user_memories():
    """Get all memories for the authenticated user."""
    try:
        user_id = request.current_user['id']
        limit = request.args.get('limit', 50, type=int)
        
        memories = user_memory_manager.get_user_memories(user_id, limit)
        
        return jsonify({
            'success': True,
            'memories': memories,
            'count': len(memories)
        }), 200
        
    except Exception as e:
        print(f"Error getting user memories: {e}")
        return jsonify({'error': 'Failed to retrieve memories'}), 500

@auth_bp.route('/api/memories', methods=['POST'])
@auth_system.require_auth
def add_user_memory():
    """Add a new memory for the authenticated user."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        content = data.get('content', '').strip()
        tags = data.get('tags', [])
        
        if not content:
            return jsonify({'error': 'Memory content is required'}), 400
        
        user_id = request.current_user['id']
        
        result = user_memory_manager.add_memory_for_user(user_id, content, tags)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Memory added successfully',
                'memory': result['memory']
            }), 201
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        print(f"Error adding user memory: {e}")
        return jsonify({'error': 'Failed to add memory'}), 500

@auth_bp.route('/api/memories/search', methods=['GET'])
@auth_system.require_auth
def search_user_memories():
    """Search memories for the authenticated user."""
    try:
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 10, type=int)
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        user_id = request.current_user['id']
        
        memories = user_memory_manager.search_user_memories(user_id, query, limit)
        
        return jsonify({
            'success': True,
            'query': query,
            'memories': memories,
            'count': len(memories)
        }), 200
        
    except Exception as e:
        print(f"Error searching user memories: {e}")
        return jsonify({'error': 'Failed to search memories'}), 500

@auth_bp.route('/api/user/profile', methods=['GET'])
@auth_system.require_auth
def get_user_profile():
    """Get user profile information."""
    try:
        user_id = request.current_user['id']
        
        # Get user's memory statistics
        memories = user_memory_manager.get_user_memories(user_id, 1000)  # Get all for stats
        
        profile_data = {
            'user': request.current_user,
            'stats': {
                'total_memories': len(memories),
                'average_score': sum(m.get('score', 0) for m in memories) / len(memories) if memories else 0,
                'most_recent_memory': max(memories, key=lambda x: x['created_at'])['created_at'] if memories else None
            }
        }
        
        return jsonify({
            'success': True,
            'profile': profile_data
        }), 200
        
    except Exception as e:
        print(f"Error getting user profile: {e}")
        return jsonify({'error': 'Failed to get profile'}), 500

def register_auth_routes(app):
    """Register authentication routes with the Flask app."""
    app.register_blueprint(auth_bp) 