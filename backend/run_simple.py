#!/usr/bin/env python3
"""
Simple Flask application runner for development
Bypasses complex database initialization for quick startup
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
    },
    {
        'id': 'nodejs',
        'name': 'Node.js Backend',
        'description': 'Server-side development with Node.js',
        'icon': '🟢',
        'color': 'bg-green-100',
        'locked': False
    },
    {
        'id': 'sql',
        'name': 'SQL Database',
        'description': 'Database design and SQL queries',
        'icon': '🗄️',
        'color': 'bg-purple-100',
        'locked': True  # This one requires subscription
    }
]

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'MindCoach API is running',
        'version': '1.0.0'
    })

@app.route('/api/subjects')
def get_subjects():
    """Get available subjects"""
    user_id = request.args.get('user_id') if 'request' in globals() else None
    
    return jsonify({
        'subjects': SUBJECTS_DATA,
        'total_count': len(SUBJECTS_DATA)
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
        'subject': {
            'id': subject_id,
            'name': subject['name'],
            'selected_at': 'now'
        }
    })

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user"""
    from flask import request
    data = request.get_json() or {}
    
    return jsonify({
        'message': 'User created successfully',
        'user': {
            'user_id': data.get('user_id', 'demo-user'),
            'email': data.get('email', 'demo@example.com')
        }
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

@app.route('/api/users/<user_id>/subjects/custom', methods=['POST'])
def create_custom_subject_for_user(user_id):
    """Create a custom subject for a user"""
    from flask import request
    import uuid
    import time
    
    data = request.get_json() or {}
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({
            'error': {
                'code': 'MISSING_REQUIRED_FIELD',
                'message': 'Subject name is required'
            }
        }), 400
    
    # Check if user has enough tokens (simplified check)
    tokens_required = data.get('tokensRequired', 50)
    user_tokens = USER_TOKENS.get(user_id, 150)  # Get from in-memory storage
    
    if user_tokens < tokens_required:
        return jsonify({
            'error': {
                'code': 'INSUFFICIENT_TOKENS',
                'message': f'Insufficient tokens. Required: {tokens_required}, Available: {user_tokens}'
            }
        }), 402
    
    # Create custom subject
    subject_id = f"custom_{int(time.time())}"
    custom_subject = {
        'id': subject_id,
        'name': data['name'],
        'description': data.get('description', f"Learn {data['name']} programming"),
        'icon': '🎯',  # Custom subject icon
        'color': 'bg-purple-100',
        'locked': False,  # User paid with tokens
        'custom': True,
        'created_by': user_id,
        'difficulty': data.get('difficulty', 'beginner'),
        'estimated_lessons': data.get('estimatedLessons', 10),
        'tokens_spent': tokens_required,
        'created_at': time.time()
    }
    
    # Deduct tokens from user's balance
    USER_TOKENS[user_id] = user_tokens - tokens_required
    
    # In a real app, you would:
    # 1. Save the custom subject to database
    # 2. Trigger AI content generation pipeline
    # 3. Create the subject directory structure
    
    return jsonify({
        'message': f'Custom subject "{data["name"]}" created successfully',
        'subject': custom_subject,
        'tokens_remaining': user_tokens - tokens_required,
        'content_generation_status': 'queued'
    })

if __name__ == '__main__':
    # Import request here to avoid circular imports
    from flask import request
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'
    
    print(f"Starting MindCoach API server on port {port}")
    print(f"Debug mode: {debug}")
    print(f"Health check: http://localhost:{port}/api/health")
    print(f"Subjects API: http://localhost:{port}/api/subjects")
    
    app.run(host='0.0.0.0', port=port, debug=debug)