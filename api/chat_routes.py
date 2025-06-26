#!/usr/bin/env python3

from flask import request, jsonify
from services.conversation_service import conversation_service

def register_chat_routes(app):
    """Register all chat-related routes with the Flask app"""
    
    @app.route('/send_message', methods=['POST'])
    def send_message():
        """Handle sending a message and generating AI response"""
        try:
            data = request.get_json()
            message = data.get('message', '').strip()
            thread_id = data.get('thread_id')
            request_id = data.get('request_id')
            
            # Process the message through conversation service
            thread_id, ai_response, memory_context, error = conversation_service.process_message(
                message, thread_id, request_id
            )
            
            if error:
                if error == "Duplicate request detected":
                    return jsonify({'success': False, 'error': error}), 409
                else:
                    return jsonify({'success': False, 'error': error}), 400
            
            return jsonify({
                'success': True,
                'response': ai_response,
                'thread_id': thread_id,
                'memory_context': memory_context
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/end_thread', methods=['POST'])
    def end_thread():
        """Extract memories from a conversation thread when it ends"""
        try:
            data = request.get_json()
            thread_id = data.get('thread_id')
            
            success, extracted_memories, message = conversation_service.end_thread_and_extract_memories(thread_id)
            
            if not success:
                return jsonify({'success': False, 'error': message}), 400
            
            return jsonify({
                'success': True,
                'extracted_memories': extracted_memories,
                'count': len(extracted_memories),
                'message': message
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500 