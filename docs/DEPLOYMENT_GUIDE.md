# MindCoach Deployment Guide

This guide covers production deployment, scaling, monitoring, and maintenance procedures for the MindCoach Personalized Learning Path Generator.

## Table of Contents

1. [Production Environment Setup](#production-environment-setup)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Platform Deployment](#cloud-platform-deployment)
4. [Database Management](#database-management)
5. [Monitoring and Logging](#monitoring-and-logging)
6. [Security Configuration](#security-configuration)
7. [Performance Optimization](#performance-optimization)
8. [Backup and Recovery](#backup-and-recovery)
9. [Scaling Strategies](#scaling-strategies)
10. [Troubleshooting](#troubleshooting)

## Production Environment Setup

### Server Requirements

#### Minimum Requirements
- **CPU**: 2 cores (4 recommended)
- **RAM**: 4GB (8GB recommended)
- **Storage**: 50GB SSD (100GB recommended)
- **Network**: 1Gbps connection
- **OS**: Ubuntu 20.04 LTS or CentOS 8

#### Recommended Production Setup
- **CPU**: 4-8 cores
- **RAM**: 16-32GB
- **Storage**: 200GB+ SSD with backup storage
- **Network**: High-speed connection with CDN
- **Load Balancer**: For high availability

### Environment Variables

Create a production environment file:

```bash
# .env.production
# Flask Configuration
SECRET_KEY=your-super-secure-secret-key-here
FLASK_ENV=production
FLASK_DEBUG=False

# xAI API Configuration
XAI_API_KEY=your-xai-api-key
GROK_API_URL=https://api.x.ai/v1

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/mindcoach_prod
# Or for SQLite: sqlite:///data/mindcoach_prod.db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Monitoring
SENTRY_DSN=your-sentry-dsn-for-error-tracking
LOG_LEVEL=INFO

# Email Configuration (for notifications)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# File Storage (if using cloud storage)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=mindcoach-user-data
AWS_REGION=us-east-1
```

### SSL Certificate Setup

#### Using Let's Encrypt (Recommended)
```bash
# Install Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal setup
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Using Custom SSL Certificate
```bash
# Copy certificates to appropriate location
sudo mkdir -p /etc/ssl/mindcoach
sudo cp your-certificate.crt /etc/ssl/mindcoach/
sudo cp your-private-key.key /etc/ssl/mindcoach/
sudo chmod 600 /etc/ssl/mindcoach/*
```## D
ocker Deployment

### Production Docker Setup

#### 1. Prepare Production Environment
```bash
# Create production directory
mkdir -p /opt/mindcoach
cd /opt/mindcoach

# Clone repository
git clone https://github.com/your-org/mindcoach.git .
git checkout main

# Set up environment
cp .env.example .env.production
# Edit .env.production with your production values
```

#### 2. Build and Deploy
```bash
# Build production images
docker-compose -f docker-compose.yml build --no-cache

# Start services
docker-compose -f docker-compose.yml up -d

# Initialize database
docker-compose exec backend python init_db.py

# Run database migrations
docker-compose exec backend python migrate.py
```

#### 3. Production Docker Compose Configuration
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    container_name: mindcoach-nginx-prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - static_files:/usr/share/nginx/html/static
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - frontend
      - backend
    networks:
      - mindcoach-network
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.frontend
      args:
        - REACT_APP_API_BASE_URL=https://api.yourdomain.com
    container_name: mindcoach-frontend-prod
    volumes:
      - static_files:/usr/share/nginx/html
    networks:
      - mindcoach-network
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.backend
    container_name: mindcoach-backend-prod
    env_file:
      - .env.production
    volumes:
      - database_data:/app/data
      - user_data:/app/users
      - logs:/app/logs
      - ./rag_docs:/app/rag_docs:ro
    depends_on:
      - redis
      - postgres
    networks:
      - mindcoach-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.celery
    env_file:
      - .env.production
    volumes:
      - database_data:/app/data
      - user_data:/app/users
      - logs:/app/logs
      - ./rag_docs:/app/rag_docs:ro
    depends_on:
      - redis
      - postgres
      - backend
    networks:
      - mindcoach-network
    restart: unless-stopped
    deploy:
      replicas: 3
    healthcheck:
      test: ["CMD", "celery", "-A", "app.celery", "inspect", "ping"]
      interval: 60s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.celery
    container_name: mindcoach-celery-beat
    env_file:
      - .env.production
    volumes:
      - database_data:/app/data
      - logs:/app/logs
    depends_on:
      - redis
      - postgres
    networks:
      - mindcoach-network
    restart: unless-stopped
    command: ["celery", "-A", "app.celery", "beat", "--loglevel=info"]
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  postgres:
    image: postgres:15-alpine
    container_name: mindcoach-postgres-prod
    environment:
      POSTGRES_DB: mindcoach_prod
      POSTGRES_USER: mindcoach_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - mindcoach-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mindcoach_user -d mindcoach_prod"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  redis:
    image: redis:7-alpine
    container_name: mindcoach-redis-prod
    command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - mindcoach-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  database_data:
    driver: local
  postgres_data:
    driver: local
  user_data:
    driver: local
  redis_data:
    driver: local
  static_files:
    driver: local
  logs:
    driver: local

networks:
  mindcoach-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

#### 4. Production Nginx Configuration
```nginx
# nginx/nginx.prod.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 2048;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    '$request_time $upstream_response_time';

    access_log /var/log/nginx/access.log main;

    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 10M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json
        application/xml
        image/svg+xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=content:10m rate=1r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/s;

    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://api.x.ai;" always;

    # Upstream servers
    upstream backend {
        least_conn;
        server backend:5000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_session_timeout 1d;
        ssl_session_cache shared:SSL:50m;
        ssl_session_tickets off;

        # Modern configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # HSTS
        add_header Strict-Transport-Security "max-age=63072000" always;

        # Frontend static files
        location / {
            root /usr/share/nginx/html;
            index index.html index.htm;
            try_files $uri $uri/ /index.html;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
                access_log off;
            }
        }

        # API routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            
            # Buffer settings
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
        }

        # Content generation endpoints (stricter rate limiting)
        location ~ ^/api/users/.*/subjects/.*/content/generate$ {
            limit_req zone=content burst=5 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Extended timeouts for content generation
            proxy_connect_timeout 300s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
        }

        # Authentication endpoints
        location ~ ^/api/(auth|users)/ {
            limit_req zone=auth burst=10 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # Block access to sensitive files
        location ~ /\. {
            deny all;
            access_log off;
            log_not_found off;
        }

        location ~ \.(env|log|ini)$ {
            deny all;
            access_log off;
            log_not_found off;
        }
    }
}
```

### Deployment Automation

#### Deployment Script
```bash
#!/bin/bash
# deploy-production.sh

set -e

# Configuration
REPO_URL="https://github.com/your-org/mindcoach.git"
DEPLOY_DIR="/opt/mindcoach"
BACKUP_DIR="/opt/mindcoach-backups"
LOG_FILE="/var/log/mindcoach-deploy.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Backup function
backup_current_deployment() {
    log "Creating backup of current deployment..."
    
    BACKUP_NAME="mindcoach-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR/$BACKUP_NAME"
    
    # Backup application code
    if [ -d "$DEPLOY_DIR" ]; then
        cp -r "$DEPLOY_DIR" "$BACKUP_DIR/$BACKUP_NAME/app"
    fi
    
    # Backup database
    docker-compose -f "$DEPLOY_DIR/docker-compose.prod.yml" exec -T postgres \
        pg_dump -U mindcoach_user mindcoach_prod > "$BACKUP_DIR/$BACKUP_NAME/database.sql"
    
    # Backup user data
    docker cp mindcoach-backend-prod:/app/users "$BACKUP_DIR/$BACKUP_NAME/users"
    
    log "Backup created: $BACKUP_DIR/$BACKUP_NAME"
}

# Health check function
health_check() {
    log "Performing health checks..."
    
    # Wait for services to start
    sleep 30
    
    # Check frontend
    if curl -f http://localhost/health > /dev/null 2>&1; then
        log "✅ Frontend health check passed"
    else
        error_exit "Frontend health check failed"
    fi
    
    # Check backend
    if curl -f http://localhost/api/health > /dev/null 2>&1; then
        log "✅ Backend health check passed"
    else
        error_exit "Backend health check failed"
    fi
    
    # Check database
    if docker-compose -f "$DEPLOY_DIR/docker-compose.prod.yml" exec -T postgres \
        pg_isready -U mindcoach_user -d mindcoach_prod > /dev/null 2>&1; then
        log "✅ Database health check passed"
    else
        error_exit "Database health check failed"
    fi
    
    log "All health checks passed"
}

# Main deployment function
deploy() {
    log "Starting MindCoach production deployment..."
    
    # Validate environment
    if [ ! -f "$DEPLOY_DIR/.env.production" ]; then
        error_exit "Production environment file not found"
    fi
    
    # Create backup
    backup_current_deployment
    
    # Update code
    log "Updating application code..."
    cd "$DEPLOY_DIR"
    git fetch origin
    git checkout main
    git pull origin main
    
    # Build new images
    log "Building Docker images..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # Stop current services
    log "Stopping current services..."
    docker-compose -f docker-compose.prod.yml down
    
    # Start new services
    log "Starting new services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Run database migrations
    log "Running database migrations..."
    docker-compose -f docker-compose.prod.yml exec -T backend python migrate.py
    
    # Perform health checks
    health_check
    
    # Clean up old images
    log "Cleaning up old Docker images..."
    docker image prune -f
    
    log "🎉 Deployment completed successfully!"
    
    # Show running services
    docker-compose -f docker-compose.prod.yml ps
}

# Rollback function
rollback() {
    log "Starting rollback process..."
    
    if [ -z "$1" ]; then
        error_exit "Please specify backup name for rollback"
    fi
    
    BACKUP_NAME="$1"
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
    
    if [ ! -d "$BACKUP_PATH" ]; then
        error_exit "Backup not found: $BACKUP_PATH"
    fi
    
    # Stop current services
    docker-compose -f "$DEPLOY_DIR/docker-compose.prod.yml" down
    
    # Restore application code
    rm -rf "$DEPLOY_DIR"
    cp -r "$BACKUP_PATH/app" "$DEPLOY_DIR"
    
    # Restore database
    docker-compose -f "$DEPLOY_DIR/docker-compose.prod.yml" up -d postgres
    sleep 10
    docker-compose -f "$DEPLOY_DIR/docker-compose.prod.yml" exec -T postgres \
        psql -U mindcoach_user -d mindcoach_prod < "$BACKUP_PATH/database.sql"
    
    # Restore user data
    docker-compose -f "$DEPLOY_DIR/docker-compose.prod.yml" up -d backend
    sleep 10
    docker cp "$BACKUP_PATH/users" mindcoach-backend-prod:/app/
    
    # Start all services
    docker-compose -f "$DEPLOY_DIR/docker-compose.prod.yml" up -d
    
    # Health check
    health_check
    
    log "Rollback completed successfully"
}

# Parse command line arguments
case "$1" in
    deploy)
        deploy
        ;;
    rollback)
        rollback "$2"
        ;;
    backup)
        backup_current_deployment
        ;;
    health)
        health_check
        ;;
    *)
        echo "Usage: $0 {deploy|rollback <backup_name>|backup|health}"
        exit 1
        ;;
esac
```

#### CI/CD Pipeline (GitHub Actions)
```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install Python dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    
    - name: Install Node.js dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Run Python tests
      run: |
        cd backend
        python -m pytest tests/ -v
    
    - name: Run JavaScript tests
      run: |
        cd frontend
        npm run test:ci
    
    - name: Run security scan
      run: |
        pip install safety bandit
        cd backend
        safety check -r requirements.txt
        bandit -r app/
        
        cd ../frontend
        npm audit --audit-level moderate

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to production server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.PRODUCTION_HOST }}
        username: ${{ secrets.PRODUCTION_USER }}
        key: ${{ secrets.PRODUCTION_SSH_KEY }}
        script: |
          cd /opt/mindcoach
          ./deploy-production.sh deploy
    
    - name: Notify deployment status
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        channel: '#deployments'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
      if: always()
```