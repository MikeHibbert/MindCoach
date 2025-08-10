#!/bin/bash

# Deployment script for Personalized Learning Path Generator
# Usage: ./deploy.sh [environment]

set -e  # Exit on any error

ENVIRONMENT=${1:-production}
PROJECT_NAME="mindcoach"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🚀 Starting deployment for environment: $ENVIRONMENT"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if required tools are installed
check_dependencies() {
    log_info "Checking dependencies..."
    
    command -v node >/dev/null 2>&1 || { log_error "Node.js is required but not installed. Aborting."; exit 1; }
    command -v npm >/dev/null 2>&1 || { log_error "npm is required but not installed. Aborting."; exit 1; }
    command -v python3 >/dev/null 2>&1 || { log_error "Python 3 is required but not installed. Aborting."; exit 1; }
    command -v pip3 >/dev/null 2>&1 || { log_error "pip3 is required but not installed. Aborting."; exit 1; }
    
    log_success "All dependencies are installed"
}

# Validate environment variables
validate_environment() {
    log_info "Validating environment variables for $ENVIRONMENT..."
    
    if [ "$ENVIRONMENT" = "production" ]; then
        if [ -z "$SECRET_KEY" ]; then
            log_error "SECRET_KEY environment variable is required for production"
            exit 1
        fi
        
        if [ -z "$CORS_ORIGINS" ]; then
            log_error "CORS_ORIGINS environment variable is required for production"
            exit 1
        fi
        
        if [ -z "$DATABASE_URL" ]; then
            log_warning "DATABASE_URL not set, using default SQLite database"
        fi
    fi
    
    log_success "Environment validation passed"
}

# Build frontend
build_frontend() {
    log_info "Building frontend..."
    
    cd frontend
    
    # Install dependencies
    log_info "Installing frontend dependencies..."
    npm ci --production=false
    
    # Run tests
    log_info "Running frontend tests..."
    npm run test:run || { log_error "Frontend tests failed"; exit 1; }
    
    # Build for production
    log_info "Building frontend for production..."
    if [ "$ENVIRONMENT" = "production" ]; then
        npm run build:prod
    else
        npm run build
    fi
    
    # Verify build
    if [ ! -d "build" ]; then
        log_error "Frontend build failed - build directory not found"
        exit 1
    fi
    
    log_success "Frontend build completed"
    cd ..
}

# Setup backend
setup_backend() {
    log_info "Setting up backend..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate || source venv/Scripts/activate
    
    # Install dependencies
    log_info "Installing backend dependencies..."
    pip install -r requirements.txt
    
    # Run database migrations
    log_info "Running database migrations..."
    python migrations/add_performance_indexes.py
    
    # Run tests
    log_info "Running backend tests..."
    python -m pytest tests/ -v || { log_error "Backend tests failed"; exit 1; }
    
    log_success "Backend setup completed"
    cd ..
}

# Create production configuration
create_production_config() {
    log_info "Creating production configuration..."
    
    # Create production environment file for backend
    cat > backend/.env.production << EOF
FLASK_ENV=production
SECRET_KEY=${SECRET_KEY}
DATABASE_URL=${DATABASE_URL:-sqlite:///learning_path_prod.db}
CORS_ORIGINS=${CORS_ORIGINS}
LOG_LEVEL=INFO
EOF
    
    # Create production environment file for frontend (if not exists)
    if [ ! -f "frontend/.env.production" ]; then
        cat > frontend/.env.production << EOF
GENERATE_SOURCEMAP=false
REACT_APP_API_BASE_URL=${REACT_APP_API_BASE_URL:-https://api.mindcoach.com/api}
REACT_APP_ENVIRONMENT=production
REACT_APP_ENABLE_CACHE=true
REACT_APP_ENABLE_ANALYTICS=true
EOF
    fi
    
    log_success "Production configuration created"
}

# Create deployment package
create_deployment_package() {
    log_info "Creating deployment package..."
    
    PACKAGE_NAME="${PROJECT_NAME}_${ENVIRONMENT}_${TIMESTAMP}.tar.gz"
    
    # Create temporary directory for package
    mkdir -p dist
    
    # Copy necessary files
    tar -czf "dist/$PACKAGE_NAME" \
        --exclude='node_modules' \
        --exclude='venv' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='*.log' \
        --exclude='cypress/videos' \
        --exclude='cypress/screenshots' \
        --exclude='coverage' \
        --exclude='build/static/js/*.map' \
        --exclude='build/static/css/*.map' \
        frontend/build/ \
        backend/ \
        deploy.sh \
        docker-compose.yml \
        docker-compose.prod.yml \
        README.md \
        docs/
    
    log_success "Deployment package created: dist/$PACKAGE_NAME"
}

# Run performance optimization
optimize_performance() {
    log_info "Running performance optimizations..."
    
    # Optimize frontend build
    cd frontend
    if [ -d "build" ]; then
        # Remove source maps in production
        if [ "$ENVIRONMENT" = "production" ]; then
            find build -name "*.map" -delete
            log_info "Removed source maps from production build"
        fi
        
        # Compress static assets
        if command -v gzip >/dev/null 2>&1; then
            find build/static -name "*.js" -o -name "*.css" | while read file; do
                gzip -c "$file" > "$file.gz"
            done
            log_info "Compressed static assets"
        fi
    fi
    cd ..
    
    # Optimize backend
    cd backend
    if [ -f "venv/bin/activate" ] || [ -f "venv/Scripts/activate" ]; then
        source venv/bin/activate || source venv/Scripts/activate
        
        # Clean up Python cache
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -name "*.pyc" -delete 2>/dev/null || true
        
        log_info "Cleaned Python cache files"
    fi
    cd ..
    
    log_success "Performance optimizations completed"
}

# Health check
health_check() {
    log_info "Running health checks..."
    
    # Check if frontend build exists and has required files
    if [ ! -f "frontend/build/index.html" ]; then
        log_error "Frontend build is missing index.html"
        exit 1
    fi
    
    if [ ! -d "frontend/build/static" ]; then
        log_error "Frontend build is missing static assets"
        exit 1
    fi
    
    # Check if backend has required files
    if [ ! -f "backend/run.py" ]; then
        log_error "Backend is missing run.py"
        exit 1
    fi
    
    if [ ! -f "backend/requirements.txt" ]; then
        log_error "Backend is missing requirements.txt"
        exit 1
    fi
    
    log_success "Health checks passed"
}

# Main deployment process
main() {
    log_info "Starting deployment process..."
    
    check_dependencies
    validate_environment
    
    if [ "$ENVIRONMENT" = "production" ]; then
        create_production_config
    fi
    
    build_frontend
    setup_backend
    optimize_performance
    health_check
    create_deployment_package
    
    log_success "🎉 Deployment completed successfully!"
    log_info "Environment: $ENVIRONMENT"
    log_info "Timestamp: $TIMESTAMP"
    
    if [ -f "dist/${PROJECT_NAME}_${ENVIRONMENT}_${TIMESTAMP}.tar.gz" ]; then
        log_info "Deployment package: dist/${PROJECT_NAME}_${ENVIRONMENT}_${TIMESTAMP}.tar.gz"
    fi
    
    echo ""
    log_info "Next steps:"
    echo "1. Upload the deployment package to your server"
    echo "2. Extract the package: tar -xzf ${PROJECT_NAME}_${ENVIRONMENT}_${TIMESTAMP}.tar.gz"
    echo "3. Run the application using Docker Compose or directly"
    echo "4. Configure your web server (nginx) to serve the frontend and proxy API requests"
}

# Handle script interruption
trap 'log_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"