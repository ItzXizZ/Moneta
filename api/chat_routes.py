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
            print("🔧 DEBUG: === /end_thread endpoint (chat_routes.py) called ===")
            
            data = request.get_json()
            thread_id = data.get('thread_id')
            
            print(f"🔧 DEBUG: Request data: {data}")
            print(f"🔧 DEBUG: Extracted thread_id: {thread_id}")
            
            print("🔧 DEBUG: Calling conversation_service.end_thread_and_extract_memories...")
            success, extracted_memories, message = conversation_service.end_thread_and_extract_memories(thread_id)
            
            print(f"🔧 DEBUG: Service response - success: {success}, memories count: {len(extracted_memories) if extracted_memories else 0}")
            print(f"🔧 DEBUG: Service message: {message}")
            
            if not success:
                print(f"🔧 DEBUG: Service failed, returning error")
                return jsonify({'success': False, 'error': message}), 400
            
            response_data = {
                'success': True,
                'extracted_memories': extracted_memories,
                'count': len(extracted_memories),
                'message': message
            }
            
            print(f"🔧 DEBUG: Returning success response: {response_data}")
            
            return jsonify(response_data)
            
        except Exception as e:
            print(f"🔧 DEBUG: Exception in /end_thread endpoint: {e}")
            print(f"🔧 DEBUG: Exception type: {type(e).__name__}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/chat_history/<thread_id>', methods=['GET'])
    def get_chat_history(thread_id):
        messages = conversation_service.get_thread_messages(thread_id)
        return jsonify({'thread_id': thread_id, 'messages': messages})

    @app.route('/chat_history/<thread_id>', methods=['DELETE'])
    def delete_chat_history(thread_id):
        """Delete a specific chat thread"""
        try:
            success = conversation_service.clear_thread(thread_id)
            if success:
                return jsonify({'success': True, 'message': 'Thread deleted successfully'})
            else:
                return jsonify({'success': False, 'error': 'Thread not found'}), 404
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/chat_history/last', methods=['GET'])
    def get_last_chat_history():
        threads = list(conversation_service.chat_threads.keys())
        if not threads:
            return jsonify({'thread_id': None, 'messages': []})
        last_thread = threads[-1]
        messages = conversation_service.get_thread_messages(last_thread)
        return jsonify({'thread_id': last_thread, 'messages': messages})

    @app.route('/chat_history/threads', methods=['GET'])
    def get_all_thread_ids():
        return jsonify({'threads': list(conversation_service.chat_threads.keys())})

    @app.route('/chat_history/new', methods=['POST'])
    def create_new_thread():
        """Create a new empty thread"""
        try:
            thread_id = conversation_service.create_new_thread()
            return jsonify({'success': True, 'thread_id': thread_id})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500 