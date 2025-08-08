from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import logging
from logging.handlers import RotatingFileHandler

db = SQLAlchemy()

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Configuration based on environment
    if config_name == 'testing':
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///learning_path.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Initialize extensions
    db.init_app(app)
    
    # Configure CORS with security settings
    CORS(app, 
         origins=['http://localhost:3000'],  # Frontend URL
         methods=['GET', 'POST', 'PUT', 'DELETE'],
         allow_headers=['Content-Type', 'Authorization'])
    
    # Set up logging
    setup_logging(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    from app.api.users import users_bp
    from app.api.subjects import subjects_bp
    from app.api.surveys import surveys_bp
    from app.api.lessons import lessons_bp
    from app.api.subscriptions import subscriptions_bp
    from app.api.payment_gate import payment_gate_bp
    
    app.register_blueprint(users_bp, url_prefix='/api')
    app.register_blueprint(subjects_bp, url_prefix='/api')
    app.register_blueprint(surveys_bp, url_prefix='/api')
    app.register_blueprint(lessons_bp, url_prefix='/api')
    app.register_blueprint(subscriptions_bp, url_prefix='/api')
    app.register_blueprint(payment_gate_bp, url_prefix='/api')
    
    return app

def setup_logging(app):
    """Configure application logging"""
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Set up file handler with rotation
        file_handler = RotatingFileHandler('logs/learning_path.log', 
                                         maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Learning Path Generator startup')
    elif app.testing:
        # Disable logging during tests to avoid file conflicts
        app.logger.setLevel(logging.CRITICAL)

def register_error_handlers(app):
    """Register global error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': {
                'code': 'BAD_REQUEST',
                'message': 'Invalid request data',
                'details': str(error.description) if hasattr(error, 'description') else None
            }
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': {
                'code': 'UNAUTHORIZED',
                'message': 'Authentication required',
                'details': None
            }
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Access denied',
                'details': None
            }
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Resource not found',
                'details': None
            }
        }), 404
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({
            'error': {
                'code': 'PAYLOAD_TOO_LARGE',
                'message': 'Request payload too large',
                'details': 'Maximum file size is 16MB'
            }
        }), 413
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Server Error: {error}')
        return jsonify({
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An internal server error occurred',
                'details': None
            }
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f'Unhandled Exception: {error}')
        db.session.rollback()
        return jsonify({
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An unexpected error occurred',
                'details': None
            }
        }), 500