#!/usr/bin/env python3
"""
Moneta Authentication System with Supabase Integration
Handles user registration, login, and individual memory database management.
"""

import os
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session
from supabase import create_client, Client
from typing import Optional, Dict, Any

class MonetaAuthSystem:
    """
    Authentication system for Moneta that creates individual memory databases
    for each user using Supabase row-level security.
    """
    
    def __init__(self):
        # Initialize Supabase client
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.jwt_secret = os.getenv('JWT_SECRET', secrets.token_hex(32))
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Initialize database tables
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize required database tables for user management and memories."""
        try:
            # Create users table if it doesn't exist
            self.supabase.table('users').select('id').limit(1).execute()
        except Exception:
            print("Setting up database tables...")
            # Note: In production, you'd run these SQL commands directly in Supabase
            # Here we're just checking if tables exist
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt."""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        try:
            salt, password_hash = hashed.split(':')
            return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
        except ValueError:
            return False
    
    def _generate_jwt_token(self, user_id: str, email: str) -> str:
        """Generate JWT token for authenticated user."""
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': datetime.utcnow() + timedelta(days=7),  # Token expires in 7 days
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def _verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def register_user(self, name: str, email: str, password: str) -> Dict[str, Any]:
        """
        Register a new user and create their personal memory database.
        
        Args:
            name: User's full name
            email: User's email address
            password: User's password
            
        Returns:
            Dictionary with user info and JWT token
        """
        try:
            # Check if user already exists
            existing_user = self.supabase.table('users').select('id').eq('email', email).execute()
            if existing_user.data:
                return {
                    'success': False,
                    'error': 'User with this email already exists'
                }
            
            # Hash password
            password_hash = self._hash_password(password)
            
            # Create user record
            user_data = {
                'name': name,
                'email': email,
                'password_hash': password_hash,
                'created_at': datetime.utcnow().isoformat(),
                'is_active': True
            }
            
            result = self.supabase.table('users').insert(user_data).execute()
            
            if not result.data:
                return {
                    'success': False,
                    'error': 'Failed to create user account'
                }
            
            user = result.data[0]
            user_id = user['id']
            
            # Create personal memory database for the user
            self._create_user_memory_database(user_id)
            
            # Generate JWT token
            token = self._generate_jwt_token(user_id, email)
            
            return {
                'success': True,
                'user': {
                    'id': user_id,
                    'name': name,
                    'email': email
                },
                'token': token
            }
            
        except Exception as e:
            print(f"Registration error: {e}")
            return {
                'success': False,
                'error': 'Registration failed. Please try again.'
            }
    
    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user login.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dictionary with user info and JWT token
        """
        try:
            # Get user from database
            result = self.supabase.table('users').select('*').eq('email', email).execute()
            
            if not result.data:
                return {
                    'success': False,
                    'error': 'Invalid email or password'
                }
            
            user = result.data[0]
            
            # Check if user is active
            if not user.get('is_active', True):
                return {
                    'success': False,
                    'error': 'Account is deactivated'
                }
            
            # Verify password
            if not self._verify_password(password, user['password_hash']):
                return {
                    'success': False,
                    'error': 'Invalid email or password'
                }
            
            # Update last login
            self.supabase.table('users').update({
                'last_login': datetime.utcnow().isoformat()
            }).eq('id', user['id']).execute()
            
            # Generate JWT token
            token = self._generate_jwt_token(user['id'], email)
            
            return {
                'success': True,
                'user': {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email']
                },
                'token': token
            }
            
        except Exception as e:
            print(f"Login error: {e}")
            return {
                'success': False,
                'error': 'Login failed. Please try again.'
            }
    
    def _create_user_memory_database(self, user_id: str):
        """
        Create personal memory database for user using Row Level Security.
        Each user gets their own isolated memory space.
        """
        try:
            # Create initial memory database entry for user
            memory_db_data = {
                'user_id': user_id,
                'created_at': datetime.utcnow().isoformat(),
                'memory_count': 0,
                'last_accessed': datetime.utcnow().isoformat()
            }
            
            self.supabase.table('user_memory_databases').insert(memory_db_data).execute()
            
            print(f"✅ Created personal memory database for user {user_id}")
            
        except Exception as e:
            print(f"❌ Error creating user memory database: {e}")
    
    def get_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user information from JWT token."""
        payload = self._verify_jwt_token(token)
        if not payload:
            return None
        
        try:
            result = self.supabase.table('users').select('id, name, email').eq('id', payload['user_id']).execute()
            return result.data[0] if result.data else None
        except Exception:
            return None
    
    def require_auth(self, f):
        """Decorator to require authentication for routes."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Authentication required'}), 401
            
            token = auth_header.split(' ')[1]
            user = self.get_user_from_token(token)
            
            if not user:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            # Add user to request context
            request.current_user = user
            return f(*args, **kwargs)
        
        return decorated_function

class UserMemoryManager:
    """
    Memory manager that operates on user-specific memory databases.
    Integrates with the main memory system but isolates data per user.
    """
    
    def __init__(self, auth_system: MonetaAuthSystem):
        self.auth_system = auth_system
        self.supabase = auth_system.supabase
    
    def add_memory_for_user(self, user_id: str, content: str, tags: list = None) -> Dict[str, Any]:
        """Add a memory to user's personal database."""
        try:
            memory_data = {
                'user_id': user_id,
                'content': content,
                'tags': tags or [],
                'score': 0.0,
                'created_at': datetime.utcnow().isoformat(),
                'last_accessed': datetime.utcnow().isoformat(),
                'access_count': 0
            }
            
            result = self.supabase.table('user_memories').insert(memory_data).execute()
            
            if result.data:
                # Update memory count for user
                self._update_user_memory_count(user_id)
                return {
                    'success': True,
                    'memory': result.data[0]
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to add memory'
                }
                
        except Exception as e:
            print(f"Error adding memory for user {user_id}: {e}")
            return {
                'success': False,
                'error': 'Failed to add memory'
            }
    
    def get_user_memories(self, user_id: str, limit: int = 50) -> list:
        """Get all memories for a specific user."""
        try:
            result = self.supabase.table('user_memories').select('*').eq('user_id', user_id).order('score', desc=True).limit(limit).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting memories for user {user_id}: {e}")
            return []
    
    def search_user_memories(self, user_id: str, query: str, limit: int = 10) -> list:
        """Search memories for a specific user."""
        try:
            # For now, use simple text search. In production, you'd use vector similarity
            result = self.supabase.table('user_memories').select('*').eq('user_id', user_id).ilike('content', f'%{query}%').order('score', desc=True).limit(limit).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error searching memories for user {user_id}: {e}")
            return []
    
    def _update_user_memory_count(self, user_id: str):
        """Update the memory count for a user."""
        try:
            # Get current count
            count_result = self.supabase.table('user_memories').select('id', count='exact').eq('user_id', user_id).execute()
            memory_count = count_result.count if count_result.count else 0
            
            # Update user's memory database record
            self.supabase.table('user_memory_databases').update({
                'memory_count': memory_count,
                'last_accessed': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).execute()
            
        except Exception as e:
            print(f"Error updating memory count for user {user_id}: {e}")

# Global auth system instance
auth_system = MonetaAuthSystem()
user_memory_manager = UserMemoryManager(auth_system) 