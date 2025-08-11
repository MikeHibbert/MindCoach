#!/bin/bash

# Production deployment script
# Usage: ./scripts/deploy-production.sh [version]

set -e

VERSION=${1:-latest}
DEPLOYMENT_ID=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/mindcoach/backups"
DEPLOY_DIR="/opt/mindcoach/production"

echo "🚀 Starting production deployment..."
echo "Version: $VERSION"
echo "Deployment ID: $DEPLOYMENT_ID"

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

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check if running as root or with sudo
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root or with sudo"
        exit 1
    fi
    
    # Check disk space
    AVAILABLE_SPACE=$(df /opt | awk 'NR==2 {print $4}')
    REQUIRED_SPACE=5000000  # 5GB in KB
    
    if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
        log_error "Insufficient disk space. Required: 5GB, Available: $(($AVAILABLE_SPACE/1024/1024))GB"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi
    
    # Check if required environment variables are set
    if [ -z "$SECRET_KEY" ]; then
        log_error "SECRET_KEY environment variable is required"
        exit 1
    fi
    
    log_success "Pre-deployment checks passed"
}

# Create backup
create_backup() {
    log_info "Creating backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup database
    if [ -f "$DEPLOY_DIR/data/learning_path_prod.db" ]; then
        cp "$DEPLOY_DIR/data/learning_path_prod.db" "$BACKUP_DIR/db_backup_$DEPLOYMENT_ID.db"
        log_info "Database backup created"
    fi
    
    # Backup user data
    if [ -d "$DEPLOY_DIR/users" ]; then
        tar -czf "$BACKUP_DIR/users_backup_$DEPLOYMENT_ID.tar.gz" -C "$DEPLOY_DIR" users/
        log_info "User data backup created"
    fi
    
    # Backup configuration
    if [ -f "$DEPLOY_DIR/.env" ]; then
        cp "$DEPLOY_DIR/.env" "$BACKUP_DIR/env_backup_$DEPLOYMENT_ID"
        log_info "Configuration backup created"
    fi
    
    log_success "Backup completed: $BACKUP_DIR"
}

# Pull new images
pull_images() {
    log_info "Pulling new container images..."
    
    # Pull images
    docker pull "ghcr.io/mindcoach/frontend:$VERSION"
    docker pull "ghcr.io/mindcoach/backend:$VERSION"
    
    # Verify images
    if ! docker image inspect "ghcr.io/mindcoach/frontend:$VERSION" >/dev/null 2>&1; then
        log_error "Frontend image not found: ghcr.io/mindcoach/frontend:$VERSION"
        exit 1
    fi
    
    if ! docker image inspect "ghcr.io/mindcoach/backend:$VERSION" >/dev/null 2>&1; then
        log_error "Backend image not found: ghcr.io/mindcoach/backend:$VERSION"
        exit 1
    fi
    
    log_success "Images pulled successfully"
}

# Update configuration
update_configuration() {
    log_info "Updating configuration..."
    
    cd "$DEPLOY_DIR"
    
    # Update docker-compose.yml with new image versions
    sed -i "s|ghcr.io/mindcoach/frontend:.*|ghcr.io/mindcoach/frontend:$VERSION|g" docker-compose.prod.yml
    sed -i "s|ghcr.io/mindcoach/backend:.*|ghcr.io/mindcoach/backend:$VERSION|g" docker-compose.prod.yml
    
    # Update deployment metadata
    cat > deployment-info.json << EOF
{
  "deployment_id": "$DEPLOYMENT_ID",
  "version": "$VERSION",
  "deployed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "deployed_by": "$(whoami)",
  "images": {
    "frontend": "ghcr.io/mindcoach/frontend:$VERSION",
    "backend": "ghcr.io/mindcoach/backend:$VERSION"
  }
}
EOF
    
    log_success "Configuration updated"
}

# Blue-green deployment
blue_green_deploy() {
    log_info "Starting blue-green deployment..."
    
    cd "$DEPLOY_DIR"
    
    # Scale up new instances (green)
    log_info "Scaling up new instances..."
    docker-compose -f docker-compose.prod.yml up -d --scale backend=2 --scale celery-worker=2 --no-recreate
    
    # Wait for new instances to be healthy
    log_info "Waiting for new instances to be healthy..."
    sleep 60
    
    # Health check on new instances
    for i in {1..5}; do
        if curl -f http://localhost/api/health >/dev/null 2>&1; then
            log_success "Health check passed"
            break
        else
            log_warning "Health check failed, attempt $i/5"
            if [ $i -eq 5 ]; then
                log_error "Health check failed after 5 attempts"
                rollback_deployment
                exit 1
            fi
            sleep 30
        fi
    done
    
    # Switch traffic to new instances (remove old ones)
    log_info "Switching traffic to new instances..."
    docker-compose -f docker-compose.prod.yml up -d --remove-orphans
    
    # Final health check
    sleep 30
    if ! curl -f http://localhost/api/health >/dev/null 2>&1; then
        log_error "Final health check failed"
        rollback_deployment
        exit 1
    fi
    
    log_success "Blue-green deployment completed"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    cd "$DEPLOY_DIR"
    
    # Run migrations in backend container
    docker-compose -f docker-compose.prod.yml exec -T backend python migrations/add_performance_indexes.py
    
    if [ $? -eq 0 ]; then
        log_success "Database migrations completed"
    else
        log_warning "Database migrations failed or not needed"
    fi
}

# Cleanup old images
cleanup_old_images() {
    log_info "Cleaning up old images..."
    
    # Remove dangling images
    docker image prune -f
    
    # Remove old versions (keep last 3)
    docker images --format "table {{.Repository}}:{{.Tag}}" | grep "ghcr.io/mindcoach" | tail -n +4 | while read image; do
        docker rmi "$image" 2>/dev/null || true
    done
    
    log_success "Old images cleaned up"
}

# Rollback deployment
rollback_deployment() {
    log_error "Rolling back deployment..."
    
    cd "$DEPLOY_DIR"
    
    # Restore from backup
    if [ -f "$BACKUP_DIR/db_backup_$DEPLOYMENT_ID.db" ]; then
        cp "$BACKUP_DIR/db_backup_$DEPLOYMENT_ID.db" "$DEPLOY_DIR/data/learning_path_prod.db"
        log_info "Database restored from backup"
    fi
    
    if [ -f "$BACKUP_DIR/users_backup_$DEPLOYMENT_ID.tar.gz" ]; then
        tar -xzf "$BACKUP_DIR/users_backup_$DEPLOYMENT_ID.tar.gz" -C "$DEPLOY_DIR"
        log_info "User data restored from backup"
    fi
    
    # Restart with previous configuration
    docker-compose -f docker-compose.prod.yml down
    docker-compose -f docker-compose.prod.yml up -d
    
    log_warning "Rollback completed"
}

# Post-deployment verification
post_deployment_verification() {
    log_info "Running post-deployment verification..."
    
    # Health checks
    if ! curl -f http://localhost/api/health >/dev/null 2>&1; then
        log_error "Application health check failed"
        return 1
    fi
    
    # Database connectivity
    cd "$DEPLOY_DIR"
    if ! docker-compose -f docker-compose.prod.yml exec -T backend python -c "from app import db; db.engine.execute('SELECT 1')"; then
        log_error "Database connectivity check failed"
        return 1
    fi
    
    # Redis connectivity
    if ! docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping | grep -q PONG; then
        log_error "Redis connectivity check failed"
        return 1
    fi
    
    # API endpoints
    if ! curl -f http://localhost/api/subjects >/dev/null 2>&1; then
        log_error "API endpoints check failed"
        return 1
    fi
    
    log_success "Post-deployment verification passed"
}

# Send notifications
send_notifications() {
    log_info "Sending deployment notifications..."
    
    # Slack notification (if webhook URL is set)
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚀 MindCoach production deployment completed successfully!\n\nVersion: $VERSION\nDeployment ID: $DEPLOYMENT_ID\nTime: $(date)\"}" \
            "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || log_warning "Slack notification failed"
    fi
    
    # Email notification (if configured)
    if command -v mail >/dev/null 2>&1 && [ -n "$NOTIFICATION_EMAIL" ]; then
        echo "MindCoach production deployment completed successfully.

Version: $VERSION
Deployment ID: $DEPLOYMENT_ID
Time: $(date)
Status: SUCCESS" | mail -s "MindCoach Deployment Success" "$NOTIFICATION_EMAIL" || log_warning "Email notification failed"
    fi
    
    log_success "Notifications sent"
}

# Main deployment process
main() {
    log_info "Starting production deployment process..."
    
    pre_deployment_checks
    create_backup
    pull_images
    update_configuration
    blue_green_deploy
    run_migrations
    post_deployment_verification
    cleanup_old_images
    send_notifications
    
    log_success "🎉 Production deployment completed successfully!"
    log_info "Version: $VERSION"
    log_info "Deployment ID: $DEPLOYMENT_ID"
    log_info "Application URL: http://localhost"
    log_info "API Health: http://localhost/api/health"
}

# Handle script interruption
trap 'log_error "Deployment interrupted"; rollback_deployment; exit 1' INT TERM

# Run main function
main "$@"