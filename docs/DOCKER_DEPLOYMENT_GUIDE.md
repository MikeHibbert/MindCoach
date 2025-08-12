# Docker Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the MindCoach Personalized Learning Path Generator using Docker containers. The application supports multiple deployment scenarios including development, testing, production, and scaled deployments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Deployment Environments](#deployment-environments)
4. [Configuration](#configuration)
5. [Security Guidelines](#security-guidelines)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Backup and Recovery](#backup-and-recovery)
8. [Scaling](#scaling)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance](#maintenance)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+), macOS (10.15+), or Windows 10/11 with WSL2
- **CPU**: Minimum 2 cores, Recommended 4+ cores
- **Memory**: Minimum 4GB RAM, Recommended 8GB+ RAM
- **Storage**: Minimum 20GB free space, Recommended 50GB+ for production
- **Network**: Internet connection for image downloads and API access

### Required Software

1. **Docker Engine** (version 20.10+)
   ```bash
   # Ubuntu/Debian
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # Add user to docker group
   sudo usermod -aG docker $USER
   ```

2. **Docker Compose** (version 2.0+)
   ```bash
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

3. **Git** (for cloning the repository)
   ```bash
   sudo apt-get update && sudo apt-get install git
   ```

### Verification

Verify your installation:
```bash
docker --version
docker-compose --version
docker info
```

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/mindcoach.git
cd mindcoach
```

### 2. Environment Setup

Create environment file:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```bash
# Required Configuration
SECRET_KEY=your-super-secret-key-here
XAI_API_KEY=your-xai-api-key
GROK_API_URL=https://api.x.ai/v1

# Database Configuration
DATABASE_URL=postgresql://postgres:password@postgres:5432/mindcoach
POSTGRES_PASSWORD=secure-database-password

# Optional Configuration
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
LOG_LEVEL=INFO
```

### 3. Start the Application

```bash
# Development environment
docker-compose -f docker-compose.dev.yml up -d

# Production environment
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Verify Deployment

```bash
# Check container status
docker-compose ps

# Check application health
curl http://localhost/api/health
```

## Deployment Environments
#
## Development Environment

**Purpose**: Local development with hot reloading and debugging capabilities.

**Configuration**: `docker-compose.dev.yml`

**Features**:
- Hot reloading for frontend and backend
- Debug ports exposed
- Development databases with sample data
- Admin interfaces (pgAdmin, Redis Commander)
- File watchers for automatic rebuilds

**Usage**:
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop environment
docker-compose -f docker-compose.dev.yml down
```

**Access Points**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- pgAdmin: http://localhost:8081
- Redis Commander: http://localhost:8082
- Dev Tools Dashboard: http://localhost:8080

### Testing Environment

**Purpose**: Automated testing and CI/CD pipelines.

**Configuration**: `docker-compose.test.yml`

**Features**:
- Isolated test databases
- Mock services for external APIs
- Test result aggregation
- Performance and security testing

**Usage**:
```bash
# Run comprehensive tests
./scripts/run-docker-system-tests.sh comprehensive

# Run specific test types
./scripts/run-docker-system-tests.sh networking
./scripts/run-docker-system-tests.sh persistence
```

### Production Environment

**Purpose**: Production deployment with optimized performance and security.

**Configuration**: `docker-compose.prod.yml`

**Features**:
- Optimized container images
- SSL/TLS termination
- Health checks and monitoring
- Log aggregation
- Resource limits

**Usage**:
```bash
# Deploy to production
docker-compose -f docker-compose.prod.yml up -d

# Update application
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --no-deps backend frontend

# View production logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100
```

### Scaled Environment

**Purpose**: High-availability deployment with horizontal scaling.

**Configuration**: `docker-compose.scale.yml`

**Features**:
- Load balancing with HAProxy
- Multiple backend instances
- Auto-scaling capabilities
- Database connection pooling
- Distributed caching

**Usage**:
```bash
# Deploy scaled environment
docker-compose -f docker-compose.scale.yml up -d

# Scale backend services
docker-compose -f docker-compose.scale.yml up -d --scale backend=5

# Monitor scaling
docker-compose -f docker-compose.scale.yml ps
```

## Configuration

### Environment Variables

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | `your-super-secret-key-here` |
| `XAI_API_KEY` | xAI API key for Grok-3 Mini | `xai-api-key-here` |
| `GROK_API_URL` | xAI API endpoint URL | `https://api.x.ai/v1` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `secure-password` |

#### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |
| `LOG_LEVEL` | Application log level | `INFO` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://redis:6379/0` |
| `GRAFANA_PASSWORD` | Grafana admin password | `admin` |

### Volume Configuration

#### Persistent Data Volumes

```yaml
volumes:
  # Database data
  postgres-data:
    driver: local
    
  # Redis data
  redis-data:
    driver: local
    
  # Application data
  app-data:
    driver: local
    
  # User-generated content
  user-data:
    driver: local
    
  # Logs
  log-data:
    driver: local
```

#### Volume Mounting

```yaml
services:
  backend:
    volumes:
      - ./data:/app/data              # Application data
      - ./users:/app/users            # User content
      - ./logs/backend:/app/logs      # Application logs
      - ./backend:/app                # Source code (dev only)
```

### Network Configuration

#### Default Network

```yaml
networks:
  mindcoach-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

#### Service Communication

- **Frontend** → **Backend**: HTTP API calls
- **Backend** → **Database**: PostgreSQL connection
- **Backend** → **Redis**: Caching and task queue
- **Celery Workers** → **Redis**: Task processing
- **Nginx** → **Backend**: Reverse proxy

## Security Guidelines#
## Container Security

#### 1. Use Non-Root Users

```dockerfile
# Create non-root user
RUN addgroup --system --gid 1001 appgroup
RUN adduser --system --uid 1001 --gid 1001 appuser

# Switch to non-root user
USER appuser
```

#### 2. Minimize Attack Surface

```dockerfile
# Use minimal base images
FROM python:3.11-slim

# Remove unnecessary packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    required-package \
    && rm -rf /var/lib/apt/lists/*
```

#### 3. Secure File Permissions

```bash
# Set proper file permissions
chmod 600 .env
chmod 644 docker-compose.*.yml
chmod 755 scripts/*.sh
```

### Network Security

#### 1. Internal Networks

```yaml
networks:
  frontend-network:
    driver: bridge
    internal: false  # Allows external access
  backend-network:
    driver: bridge
    internal: true   # Internal only
```

#### 2. Port Exposure

```yaml
services:
  backend:
    expose:
      - "5000"  # Internal port only
    # ports:    # Don't expose directly
    #   - "5000:5000"
```

#### 3. SSL/TLS Configuration

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
}
```

### Secrets Management

#### 1. Environment Variables

```bash
# Use Docker secrets for sensitive data
echo "my-secret-password" | docker secret create db_password -

# Reference in compose file
services:
  database:
    secrets:
      - db_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
```

#### 2. External Secret Stores

```yaml
# Use external secret management
services:
  backend:
    environment:
      SECRET_KEY: ${SECRET_KEY}  # From external store
    env_file:
      - secrets.env  # Not in version control
```

### Image Security

#### 1. Vulnerability Scanning

```bash
# Scan images for vulnerabilities
docker scan mindcoach/backend:latest
docker scan mindcoach/frontend:latest

# Use security scanning in CI/CD
trivy image mindcoach/backend:latest
```

#### 2. Image Signing

```bash
# Sign images with Docker Content Trust
export DOCKER_CONTENT_TRUST=1
docker push mindcoach/backend:latest
```

## Monitoring and Logging

### Health Checks

#### Application Health Checks

```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

#### Database Health Checks

```yaml
services:
  postgres:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d mindcoach"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Logging Configuration

#### Centralized Logging

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=backend"
```

#### Log Aggregation

```yaml
# ELK Stack for log aggregation
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    
  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    
  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
```

### Monitoring Stack

#### Prometheus Configuration

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
```

#### Grafana Dashboards

```yaml
services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
```

## Backup and Recovery#
## Database Backup

#### Automated Backup Script

```bash
#!/bin/bash
# backup-database.sh

BACKUP_DIR="/backups/database"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="mindcoach_backup_${TIMESTAMP}.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
docker exec mindcoach-postgres pg_dump -U postgres mindcoach > "$BACKUP_DIR/$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_DIR/$BACKUP_FILE"

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Database backup completed: $BACKUP_FILE.gz"
```

#### Backup Scheduling

```bash
# Add to crontab for daily backups
0 2 * * * /path/to/backup-database.sh >> /var/log/backup.log 2>&1
```

### Volume Backup

#### Data Volume Backup

```bash
#!/bin/bash
# backup-volumes.sh

BACKUP_DIR="/backups/volumes"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup user data
docker run --rm -v mindcoach_user-data:/data -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/user-data_${TIMESTAMP}.tar.gz -C /data .

# Backup application data
docker run --rm -v mindcoach_app-data:/data -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/app-data_${TIMESTAMP}.tar.gz -C /data .

echo "Volume backup completed"
```

### Recovery Procedures

#### Database Recovery

```bash
#!/bin/bash
# restore-database.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

# Stop application
docker-compose -f docker-compose.prod.yml stop backend celery-worker

# Restore database
gunzip -c $BACKUP_FILE | docker exec -i mindcoach-postgres psql -U postgres -d mindcoach

# Start application
docker-compose -f docker-compose.prod.yml start backend celery-worker

echo "Database restore completed"
```

#### Volume Recovery

```bash
#!/bin/bash
# restore-volumes.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

# Stop application
docker-compose -f docker-compose.prod.yml down

# Restore volume
docker run --rm -v mindcoach_user-data:/data -v $(dirname $BACKUP_FILE):/backup \
  alpine tar xzf /backup/$(basename $BACKUP_FILE) -C /data

# Start application
docker-compose -f docker-compose.prod.yml up -d

echo "Volume restore completed"
```

### Disaster Recovery Plan

#### 1. Backup Strategy

- **Daily**: Database backups
- **Weekly**: Full volume backups
- **Monthly**: Complete system snapshots
- **Offsite**: Cloud storage replication

#### 2. Recovery Time Objectives (RTO)

- **Database**: < 15 minutes
- **Application**: < 30 minutes
- **Full System**: < 2 hours

#### 3. Recovery Point Objectives (RPO)

- **Database**: < 1 hour
- **User Data**: < 24 hours
- **Configuration**: < 1 week

## Scaling

### Horizontal Scaling

#### Backend Scaling

```bash
# Scale backend services
docker-compose -f docker-compose.scale.yml up -d --scale backend=5

# Scale Celery workers
docker-compose -f docker-compose.scale.yml up -d --scale celery-worker=8
```

#### Load Balancer Configuration

```haproxy
# HAProxy configuration
global
    daemon
    maxconn 4096

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend http_front
    bind *:80
    default_backend http_back

backend http_back
    balance roundrobin
    server backend1 backend_1:5000 check
    server backend2 backend_2:5000 check
    server backend3 backend_3:5000 check
```

### Auto-Scaling

#### Docker Swarm Auto-Scaling

```yaml
# docker-compose.swarm.yml
version: '3.8'
services:
  backend:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

#### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mindcoach-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mindcoach-backend
  template:
    metadata:
      labels:
        app: mindcoach-backend
    spec:
      containers:
      - name: backend
        image: mindcoach/backend:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: mindcoach-backend-service
spec:
  selector:
    app: mindcoach-backend
  ports:
  - port: 80
    targetPort: 5000
  type: LoadBalancer
```

### Performance Optimization

#### Database Optimization

```sql
-- PostgreSQL optimization
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
```

#### Redis Optimization

```redis
# Redis configuration
maxmemory 512mb
maxmemory-policy allkeys-lru
tcp-keepalive 60
timeout 300
```

## Troubleshooting#
## Common Issues and Solutions

#### Container Startup Issues

**Problem**: Containers fail to start
```bash
# Check container logs
docker-compose logs <service_name>

# Check container status
docker-compose ps

# Check system resources
docker system df
docker system prune
```

**Solution**: 
- Verify environment variables
- Check port conflicts
- Ensure sufficient disk space
- Review resource limits

#### Database Connection Issues

**Problem**: Application cannot connect to database
```bash
# Check database container
docker-compose exec postgres pg_isready -U postgres

# Test connection from backend
docker-compose exec backend python -c "
import psycopg2
conn = psycopg2.connect('postgresql://postgres:password@postgres:5432/mindcoach')
print('Connection successful')
"
```

**Solution**:
- Verify DATABASE_URL configuration
- Check network connectivity
- Ensure database is initialized
- Review firewall settings

#### Memory Issues

**Problem**: Containers running out of memory
```bash
# Check memory usage
docker stats

# Check container limits
docker inspect <container_name> | grep -i memory
```

**Solution**:
- Increase container memory limits
- Optimize application memory usage
- Add swap space
- Scale horizontally

#### Performance Issues

**Problem**: Slow application response
```bash
# Monitor container performance
docker stats --no-stream

# Check application logs
docker-compose logs -f backend

# Monitor database performance
docker-compose exec postgres psql -U postgres -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;
"
```

**Solution**:
- Optimize database queries
- Implement caching
- Scale services
- Review resource allocation

### Debugging Tools

#### Container Debugging

```bash
# Enter container shell
docker-compose exec backend bash

# Run commands in container
docker-compose exec backend python manage.py shell

# Copy files from container
docker cp container_name:/path/to/file ./local/path

# View container filesystem
docker-compose exec backend find /app -name "*.log"
```

#### Network Debugging

```bash
# Test network connectivity
docker-compose exec backend ping postgres
docker-compose exec backend nc -zv redis 6379

# Check network configuration
docker network ls
docker network inspect mindcoach_default
```

#### Log Analysis

```bash
# Follow logs in real-time
docker-compose logs -f --tail=100

# Search logs for errors
docker-compose logs backend | grep -i error

# Export logs for analysis
docker-compose logs --no-color > application.log
```

### Health Check Debugging

```bash
# Manual health check
curl -f http://localhost/api/health

# Check health status
docker inspect --format='{{.State.Health.Status}}' container_name

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' container_name
```

## Maintenance

### Regular Maintenance Tasks

#### Daily Tasks

```bash
#!/bin/bash
# daily-maintenance.sh

# Check container health
docker-compose ps

# Check disk usage
df -h
docker system df

# Backup database
./scripts/backup-database.sh

# Check logs for errors
docker-compose logs --since=24h | grep -i error
```

#### Weekly Tasks

```bash
#!/bin/bash
# weekly-maintenance.sh

# Update images
docker-compose pull

# Clean up unused resources
docker system prune -f

# Backup volumes
./scripts/backup-volumes.sh

# Check security updates
docker scan mindcoach/backend:latest
```

#### Monthly Tasks

```bash
#!/bin/bash
# monthly-maintenance.sh

# Full system backup
./scripts/full-backup.sh

# Update base images
docker pull python:3.11-slim
docker pull postgres:15-alpine
docker pull redis:7-alpine

# Review and rotate logs
find ./logs -name "*.log" -mtime +30 -delete

# Security audit
docker bench-security
```

### Update Procedures

#### Application Updates

```bash
#!/bin/bash
# update-application.sh

# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Update services with zero downtime
docker-compose -f docker-compose.prod.yml up -d --no-deps backend
docker-compose -f docker-compose.prod.yml up -d --no-deps frontend

# Verify update
curl -f http://localhost/api/health
```

#### Database Migrations

```bash
#!/bin/bash
# run-migrations.sh

# Backup database before migration
./scripts/backup-database.sh

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend python migrate.py

# Verify migration
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    print('Migration successful')
"
```

### Monitoring and Alerting

#### System Monitoring

```bash
#!/bin/bash
# system-monitor.sh

# Check container status
UNHEALTHY=$(docker ps --filter health=unhealthy -q | wc -l)
if [ $UNHEALTHY -gt 0 ]; then
    echo "ALERT: $UNHEALTHY unhealthy containers detected"
    # Send alert notification
fi

# Check disk usage
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "ALERT: Disk usage is ${DISK_USAGE}%"
    # Send alert notification
fi
```

#### Performance Monitoring

```bash
#!/bin/bash
# performance-monitor.sh

# Check response time
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' http://localhost/api/health)
if (( $(echo "$RESPONSE_TIME > 5.0" | bc -l) )); then
    echo "ALERT: High response time: ${RESPONSE_TIME}s"
fi

# Check memory usage
MEMORY_USAGE=$(docker stats --no-stream --format "table {{.MemPerc}}" | tail -n +2 | sort -nr | head -1 | sed 's/%//')
if (( $(echo "$MEMORY_USAGE > 80" | bc -l) )); then
    echo "ALERT: High memory usage: ${MEMORY_USAGE}%"
fi
```

## Best Practices

### Development Best Practices

1. **Use Multi-Stage Builds**: Optimize image size and security
2. **Implement Health Checks**: Ensure container reliability
3. **Use Specific Image Tags**: Avoid `latest` in production
4. **Minimize Layers**: Combine RUN commands when possible
5. **Use .dockerignore**: Exclude unnecessary files

### Production Best Practices

1. **Resource Limits**: Set appropriate CPU and memory limits
2. **Security Scanning**: Regularly scan images for vulnerabilities
3. **Backup Strategy**: Implement comprehensive backup procedures
4. **Monitoring**: Set up comprehensive monitoring and alerting
5. **Documentation**: Keep deployment documentation up-to-date

### Security Best Practices

1. **Non-Root Users**: Run containers as non-root users
2. **Secrets Management**: Use proper secrets management
3. **Network Segmentation**: Isolate services with networks
4. **Regular Updates**: Keep base images and dependencies updated
5. **Access Control**: Implement proper access controls

## Conclusion

This deployment guide provides comprehensive instructions for deploying the MindCoach application using Docker containers. Follow the guidelines and best practices outlined in this document to ensure a secure, scalable, and maintainable deployment.

For additional support or questions, please refer to the troubleshooting section or contact the development team.

---

**Last Updated**: August 2025  
**Version**: 1.0  
**Maintainer**: MindCoach Development Team