#!/bin/bash

# Production startup script for MindCoach
# This script starts the application in production mode

set -e

echo "🚀 Starting MindCoach in production mode..."

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is available
if command -v docker >/dev/null 2>&1 && command -v docker-compose >/dev/null 2>&1; then
    log_info "Docker detected, using containerized deployment"
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        log_warning ".env file not found, creating from template..."
        cat > .env << EOF
# Production environment variables
SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=https://mindcoach.com,https://www.mindcoach.com
DATABASE_URL=sqlite:///data/learning_path_prod.db
REACT_APP_API_BASE_URL=https://api.mindcoach.com/api

# Optional monitoring
GRAFANA_PASSWORD=admin123
EOF
        log_info "Created .env file with default values. Please review and update as needed."
    fi
    
    # Create necessary directories
    mkdir -p data users logs/nginx logs/backend logs/celery
    
    # Start services
    log_info "Starting services with Docker Compose..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 10
    
    # Health check
    log_info "Performing health check..."
    if curl -f http://localhost/api/health >/dev/null 2>&1; then
        log_success "✅ Application is running and healthy!"
        log_info "Frontend: http://localhost"
        log_info "API: http://localhost/api"
        log_info "Health check: http://localhost/api/health"
    else
        log_error "❌ Health check failed"
        log_info "Checking service logs..."
        docker-compose -f docker-compose.prod.yml logs --tail=20
        exit 1
    fi
    
else
    log_info "Docker not available, using direct deployment"
    
    # Check if virtual environment exists
    if [ ! -d "backend/venv" ]; then
        log_error "Virtual environment not found. Please run deployment script first."
        exit 1
    fi
    
    # Check if frontend build exists
    if [ ! -d "frontend/build" ]; then
        log_error "Frontend build not found. Please run deployment script first."
        exit 1
    fi
    
    # Start backend
    log_info "Starting backend server..."
    cd backend
    source venv/bin/activate || source venv/Scripts/activate
    
    # Set production environment
    export FLASK_ENV=production
    export SECRET_KEY=${SECRET_KEY:-$(openssl rand -hex 32)}
    export CORS_ORIGINS=${CORS_ORIGINS:-"http://localhost:3000"}
    
    # Start with gunicorn
    if command -v gunicorn >/dev/null 2>&1; then
        log_info "Starting with Gunicorn..."
        gunicorn --bind 0.0.0.0:5000 --workers 4 --worker-class gevent --daemon --pid gunicorn.pid run:app
    else
        log_warning "Gunicorn not found, starting with Flask development server (not recommended for production)"
        python run.py &
        echo $! > flask.pid
    fi
    
    cd ..
    
    # Start frontend server
    log_info "Starting frontend server..."
    cd frontend
    
    if command -v serve >/dev/null 2>&1; then
        log_info "Starting with serve..."
        serve -s build -l 3000 &
        echo $! > serve.pid
    else
        log_warning "serve not found, please install: npm install -g serve"
        log_info "You can manually serve the build directory with any static file server"
    fi
    
    cd ..
    
    # Health check
    sleep 5
    log_info "Performing health check..."
    if curl -f http://localhost:5000/api/health >/dev/null 2>&1; then
        log_success "✅ Backend is running and healthy!"
        log_info "Backend API: http://localhost:5000/api"
        log_info "Frontend: http://localhost:3000"
        log_info "Health check: http://localhost:5000/api/health"
    else
        log_error "❌ Backend health check failed"
        exit 1
    fi
fi

log_success "🎉 MindCoach is now running in production mode!"

echo ""
log_info "Useful commands:"
echo "  - View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  - Stop services: docker-compose -f docker-compose.prod.yml down"
echo "  - Restart services: docker-compose -f docker-compose.prod.yml restart"
echo "  - Scale workers: docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=3"
echo ""
log_info "Monitoring:"
echo "  - Application health: http://localhost/api/health"
echo "  - Detailed health: http://localhost/api/health/detailed"
echo "  - Performance metrics: http://localhost/api/admin/performance"