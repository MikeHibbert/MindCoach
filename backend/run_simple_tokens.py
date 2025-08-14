#!/usr/bin/env python3
"""
Simple Flask application with token management for testing
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Simple in-memory token storage for development
USER_TOKENS = {}

# Simple subjects data for development
SUBJECTS_DATA = [
    {
        'id': 'python',
        'name': 'Python Programming',
        'description': 'Learn Python from basics to advanced concepts',
        'icon': '🐍',
        'color': 'bg-blue-100',
        'locked': False
    },
    {
        'id': 'javascript',
        'name': 'JavaScript Development',
        'description': 'Master JavaScript for web development',
        'icon': '⚡',
        'color': 'bg-yellow-100',
        'locked': False
    },
    {
        'id': 'react',
        'name': 'React Framework',
        'description': 'Build modern web applications with React',
        'icon': '⚛️',
        'color': 'bg-cyan-100',
        'locked': False
    }
]

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'MindCoach API is running with token management',
        'version': '1.0.0'
    })

@app.route('/api/test')
def test_endpoint():
    """Test endpoint to verify server is running new code"""
    return jsonify({
        'message': 'New server is running!',
        'endpoints': [
            '/api/health',
            '/api/subjects',
            '/api/users/<user_id>/tokens',
            '/api/users/<user_id>/tokens/topup'
        ]
    })

@app.route('/api/subjects')
def get_subjects():
    """Get available subjects"""
    return jsonify({
        'subjects': SUBJECTS_DATA,
        'total_count': len(SUBJECTS_DATA)
    })

@app.route('/api/users/<user_id>/tokens')
def get_user_tokens(user_id):
    """Get user's token balance"""
    # Get tokens from in-memory storage, default to 150 for new users
    tokens = USER_TOKENS.get(user_id, 150)
    return jsonify({
        'user_id': user_id,
        'tokens': tokens,
        'last_updated': '2024-01-01T00:00:00Z'
    })

@app.route('/api/users/<user_id>/tokens/topup', methods=['POST'])
def topup_user_tokens(user_id):
    """Top up user's token balance"""
    data = request.get_json()
    
    if not data or 'amount' not in data:
        return jsonify({
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'Amount is required'
            }
        }), 400
    
    amount = data['amount']
    
    if not isinstance(amount, int) or amount <= 0:
        return jsonify({
            'error': {
                'code': 'INVALID_AMOUNT',
                'message': 'Amount must be a positive integer'
            }
        }), 400
    
    # Get current balance
    current_tokens = USER_TOKENS.get(user_id, 150)
    
    # Add tokens
    new_balance = current_tokens + amount
    USER_TOKENS[user_id] = new_balance
    
    return jsonify({
        'message': f'Successfully added {amount} tokens',
        'user_id': user_id,
        'previous_balance': current_tokens,
        'tokens_added': amount,
        'new_balance': new_balance,
        'last_updated': '2024-01-01T00:00:00Z'
    })

@app.route('/api/users/<user_id>/subjects/<subject_id>/select', methods=['POST'])
def select_subject(user_id, subject_id):
    """Select a subject for learning"""
    # Find the subject
    subject = next((s for s in SUBJECTS_DATA if s['id'] == subject_id), None)
    
    if not subject:
        return jsonify({
            'error': {
                'code': 'SUBJECT_NOT_FOUND',
                'message': 'Subject not found'
            }
        }), 404
    
    if subject['locked']:
        return jsonify({
            'error': {
                'code': 'SUBSCRIPTION_REQUIRED',
                'message': f'Subscription required for {subject["name"]}'
            }
        }), 402
    
    return jsonify({
        'message': f'Successfully selected {subject["name"]}',
        'subject': subject,
        'user_id': user_id
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'
    
    print(f"Starting MindCoach API server with token management on port {port}")
    print(f"Debug mode: {debug}")
    print(f"Health check: http://localhost:{port}/api/health")
    print(f"Subjects API: http://localhost:{port}/api/subjects")
    print(f"Token API: http://localhost:{port}/api/users/test_user/tokens")
    print(f"Token Topup: POST http://localhost:{port}/api/users/test_user/tokens/topup")
    
    app.run(host='0.0.0.0', port=port, debug=debug)