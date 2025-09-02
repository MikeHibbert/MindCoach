"""
Health check endpoint for monitoring and load balancer
"""
from flask import Blueprint, jsonify
from app import db
from app.services.performance_service import performance_monitor
from app.services.cache_service import cache
from sqlalchemy import text
import time
import os

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    try:
        # Check database connectivity
        db.session.execute(text('SELECT 1'))
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    # Check cache
    try:
        cache.set('health_check', 'test', 10)
        cache_test = cache.get('health_check')
        cache_status = 'healthy' if cache_test == 'test' else 'unhealthy'
    except Exception as e:
        cache_status = f'unhealthy: {str(e)}'
    
    # Check file system
    try:
        test_file = 'health_check_test.tmp'
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        fs_status = 'healthy'
    except Exception as e:
        fs_status = f'unhealthy: {str(e)}'
    
    overall_status = 'healthy' if all(
        status == 'healthy' for status in [db_status, cache_status, fs_status]
    ) else 'unhealthy'
    
    return jsonify({
        'status': overall_status,
        'timestamp': time.time(),
        'checks': {
            'database': db_status,
            'cache': cache_status,
            'filesystem': fs_status
        }
    }), 200 if overall_status == 'healthy' else 503

@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """Detailed health check with performance metrics"""
    try:
        # Basic health checks
        basic_health = health_check()
        health_data = basic_health[0].get_json()
        
        # Add performance metrics
        health_data['performance'] = performance_monitor.get_metrics()
        health_data['cache_stats'] = cache.get_stats()
        
        # Add system info
        health_data['system'] = {
            'python_version': os.sys.version,
            'platform': os.name,
            'cwd': os.getcwd(),
            'pid': os.getpid()
        }
        
        return jsonify(health_data), basic_health[1]
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        }), 500

@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """Readiness check for Kubernetes/container orchestration"""
    try:
        # Check if application is ready to serve requests
        db.session.execute(text('SELECT 1'))
        
        # Check if required directories exist
        required_dirs = ['users', 'logs']
        for dir_name in required_dirs:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)
        
        return jsonify({
            'status': 'ready',
            'timestamp': time.time()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'not_ready',
            'error': str(e),
            'timestamp': time.time()
        }), 503

@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """Liveness check for Kubernetes/container orchestration"""
    return jsonify({
        'status': 'alive',
        'timestamp': time.time()
    }), 200