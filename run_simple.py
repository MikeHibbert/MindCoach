#!/usr/bin/env python3
"""
Simple Flask application runner for development
Bypasses complex database initialization for quick startup
"""

from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

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