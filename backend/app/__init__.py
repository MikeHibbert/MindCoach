from flask import Flask, jsonify, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import logging
import time
from logging.handlers import RotatingFileHandler

db = SQLAlchemy()

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    
    from config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Configure CORS with security settings
    CORS(app, 
         origins=app.config['CORS_ORIGINS'],
         methods=['GET', 'POST', 'PUT', 'DELETE'],
         allow_headers=['Content-Type', 'Authorization'])
    
    # Set up logging
    setup_logging(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register performance monitoring
    register_performance_monitoring(app)
    
    # Register blueprints
    from app.api.users import users_bp
    from app.api.subjects import subjects_bp
    from app.api.surveys import surveys_bp
    from app.api.lessons import lessons_bp
    from app.api.subscriptions import subscriptions_bp
    from app.api.payment_gate import payment_gate_bp
    from app.api.health import health_bp
    from app.api.langchain_test import langchain_test_bp
    from app.api.rag_documents import rag_docs_bp
    
    app.register_blueprint(users_bp, url_prefix='/api')
    app.register_blueprint(subjects_bp, url_prefix='/api')
    app.register_blueprint(surveys_bp, url_prefix='/api')
    app.register_blueprint(lessons_bp, url_prefix='/api')
    app.register_blueprint(subscriptions_bp, url_prefix='/api')
    app.register_blueprint(payment_gate_bp, url_prefix='/api')
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(langchain_test_bp, url_prefix='/api')
    app.register_blueprint(rag_docs_bp, url_prefix='/api')
    
    # Add performance monitoring endpoint
    @app.route('/api/admin/performance')
    def get_performance_metrics():
        from app.services.performance_service import performance_monitor
        from app.services.cache_service import cache
        
        return jsonify({
            'performance_metrics': performance_monitor.get_metrics(),
            'cache_stats': cache.get_stats(),
            'database_stats': get_database_stats()
        })
    
    return app

def register_performance_monitoring(app):
    """Register performance monitoring middleware"""
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            # Log slow requests
            if duration > 1.0:
                app.logger.warning(
                    f"Slow request: {request.method} {request.path} - {duration:.2f}s"
                )
            
            # Add performance headers
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
        
        return response

def get_database_stats():
    """Get basic database statistics"""
    try:
        from app.services.performance_service import DatabaseOptimizer
        return DatabaseOptimizer.get_connection_pool_status()
    except Exception as e:
        return {'error': str(e)}

def setup_logging(app):
    """Configure application logging"""
    if app.testing:
        # Disable logging during tests to avoid file conflicts
        app.logger.setLevel(logging.CRITICAL)
        return
    
    if not app.debug:
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