# Docker Container Troubleshooting Guide

## Overview

This guide provides detailed troubleshooting procedures for common Docker container issues in the MindCoach application. Use this guide to diagnose and resolve deployment problems quickly.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Container Issues](#container-issues)
3. [Network Issues](#network-issues)
4. [Storage Issues](#storage-issues)
5. [Performance Issues](#performance-issues)
6. [Security Issues](#security-issues)
7. [Application-Specific Issues](#application-specific-issues)
8. [Emergency Procedures](#emergency-procedures)

## Quick Diagnostics

### System Health Check

```bash
#!/bin/bash
# quick-health-check.sh

echo "=== Docker System Health Check ==="

# Check Docker daemon
echo "1. Docker Daemon Status:"
docker info > /dev/null 2>&1 && echo "✓ Docker daemon running" || echo "✗ Docker daemon not running"

# Check container status
echo -e "\n2. Container Status:"
docker-compose ps

# Check resource usage
echo -e "\n3. Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Check disk usage
echo -e "\n4. Disk Usage:"
docker system df

# Check network connectivity
echo -e "\n5. Network Connectivity:"
curl -s -o /dev/null -w "API Health: %{http_code} (Response time: %{time_total}s)\n" http://localhost/api/health

echo -e "\n=== Health Check Complete ==="
```

### Log Analysis

```bash
#!/bin/bash
# analyze-logs.sh

SERVICE=${1:-all}
HOURS=${2:-1}

echo "=== Log Analysis for $SERVICE (last $HOURS hours) ==="

if [ "$SERVICE" = "all" ]; then
    # Analyze all services
    for service in backend frontend postgres redis celery-worker; do
        echo -e "\n--- $service logs ---"
        docker-compose logs --since="${HOURS}h" $service 2>/dev/null | tail -20
    done
else
    # Analyze specific service
    docker-compose logs --since="${HOURS}h" $SERVICE
fi

# Look for common error patterns
echo -e "\n=== Error Summary ==="
docker-compose logs --since="${HOURS}h" 2>/dev/null | grep -i "error\|exception\|failed\|timeout" | tail -10
```

## Container Issues

### Container Won't Start

#### Symptoms
- Container exits immediately
- Container status shows "Exited (1)"
- Application not accessible

#### Diagnosis
```bash
# Check container logs
docker-compose logs <service_name>

# Check container exit code
docker-compose ps

# Inspect container configuration
docker inspect <container_name>

# Check resource availability
docker system df
free -h
```

#### Common Causes and Solutions

**1. Port Conflicts**
```bash
# Check port usage
netstat -tulpn | grep <port_number>
lsof -i :<port_number>

# Solution: Change port mapping or stop conflicting service
docker-compose down
# Edit docker-compose.yml to use different ports
docker-compose up -d
```

**2. Environment Variable Issues**
```bash
# Check environment variables
docker-compose config

# Validate .env file
cat .env | grep -v '^#' | grep -v '^$'

# Solution: Fix environment variables
cp .env.example .env
# Edit .env with correct values
```

**3. Volume Mount Issues**
```bash
# Check volume mounts
docker inspect <container_name> | grep -A 10 "Mounts"

# Check directory permissions
ls -la ./data ./users ./logs

# Solution: Fix permissions
sudo chown -R $USER:$USER ./data ./users ./logs
chmod -R 755 ./data ./users ./logs
```

### Container Keeps Restarting

#### Symptoms
- Container status shows "Restarting"
- High CPU usage from Docker daemon
- Application intermittently accessible

#### Diagnosis
```bash
# Check restart count
docker-compose ps

# Monitor container behavior
docker-compose logs -f <service_name>

# Check health check status
docker inspect --format='{{.State.Health.Status}}' <container_name>
```

#### Solutions

**1. Fix Health Check Issues**
```bash
# Test health check manually
docker-compose exec <service_name> curl -f http://localhost:5000/api/health

# Disable health check temporarily
# In docker-compose.yml:
# healthcheck:
#   disable: true
```

**2. Increase Resource Limits**
```yaml
# In docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

**3. Fix Application Errors**
```bash
# Check application logs for errors
docker-compose logs backend | grep -i "error\|exception"

# Check database connectivity
docker-compose exec backend python -c "
import psycopg2
conn = psycopg2.connect('postgresql://postgres:password@postgres:5432/mindcoach')
print('Database connection successful')
"
```

### Container Performance Issues

#### Symptoms
- Slow response times
- High CPU/memory usage
- Timeouts

#### Diagnosis
```bash
# Monitor real-time performance
docker stats

# Check container resource limits
docker inspect <container_name> | grep -A 10 "Resources"

# Profile application performance
docker-compose exec backend python -m cProfile -s cumulative app.py
```

#### Solutions

**1. Optimize Resource Allocation**
```yaml
# Increase container resources
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

**2. Implement Caching**
```python
# Add Redis caching
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@cache.memoize(timeout=300)
def expensive_function():
    # Cached function
    pass
```

## Network Issues### 
Service Communication Issues

#### Symptoms
- Services cannot communicate with each other
- Connection refused errors
- DNS resolution failures

#### Diagnosis
```bash
# Check network configuration
docker network ls
docker network inspect <network_name>

# Test connectivity between containers
docker-compose exec backend ping postgres
docker-compose exec backend nc -zv redis 6379

# Check service discovery
docker-compose exec backend nslookup postgres
```

#### Solutions

**1. Fix Network Configuration**
```yaml
# Ensure services are on the same network
networks:
  mindcoach-network:
    driver: bridge

services:
  backend:
    networks:
      - mindcoach-network
  postgres:
    networks:
      - mindcoach-network
```

**2. Use Service Names for Communication**
```python
# Use service name instead of localhost
DATABASE_URL = "postgresql://postgres:password@postgres:5432/mindcoach"
REDIS_URL = "redis://redis:6379/0"
```

**3. Check Port Exposure**
```yaml
services:
  postgres:
    expose:
      - "5432"  # Internal port
    # Don't expose externally unless needed
```

### External Access Issues

#### Symptoms
- Cannot access application from browser
- Connection timeouts from external clients
- Load balancer not working

#### Diagnosis
```bash
# Check port bindings
docker-compose ps
netstat -tulpn | grep docker

# Test external connectivity
curl -v http://localhost/api/health
telnet localhost 80

# Check firewall rules
sudo ufw status
sudo iptables -L
```

#### Solutions

**1. Fix Port Mapping**
```yaml
services:
  nginx:
    ports:
      - "80:80"    # HTTP
      - "443:443"  # HTTPS
```

**2. Configure Firewall**
```bash
# Allow HTTP/HTTPS traffic
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload
```

**3. Check Load Balancer Configuration**
```haproxy
# HAProxy configuration
frontend http_front
    bind *:80
    default_backend http_back

backend http_back
    balance roundrobin
    option httpchk GET /api/health
    server backend1 backend_1:5000 check
    server backend2 backend_2:5000 check
```

## Storage Issues

### Volume Mount Problems

#### Symptoms
- Data not persisting
- Permission denied errors
- Files not accessible

#### Diagnosis
```bash
# Check volume mounts
docker inspect <container_name> | grep -A 20 "Mounts"

# Check volume status
docker volume ls
docker volume inspect <volume_name>

# Check file permissions
docker-compose exec <service_name> ls -la /app/data
```

#### Solutions

**1. Fix Volume Configuration**
```yaml
services:
  backend:
    volumes:
      - ./data:/app/data:rw  # Read-write access
      - user-data:/app/users
      
volumes:
  user-data:
    driver: local
```

**2. Fix Permissions**
```bash
# Fix host directory permissions
sudo chown -R $USER:$USER ./data ./users
chmod -R 755 ./data ./users

# Fix container permissions
docker-compose exec backend chown -R appuser:appgroup /app/data
```

### Disk Space Issues

#### Symptoms
- "No space left on device" errors
- Container fails to write files
- Database corruption

#### Diagnosis
```bash
# Check disk usage
df -h
docker system df

# Check Docker space usage
docker system df -v

# Find large files
find /var/lib/docker -size +100M -type f
```

#### Solutions

**1. Clean Up Docker Resources**
```bash
# Remove unused containers, networks, images
docker system prune -a -f

# Remove unused volumes
docker volume prune -f

# Remove specific images
docker rmi $(docker images -q --filter "dangling=true")
```

**2. Implement Log Rotation**
```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**3. Move Docker Root Directory**
```bash
# Stop Docker daemon
sudo systemctl stop docker

# Edit Docker daemon configuration
sudo nano /etc/docker/daemon.json
{
  "data-root": "/new/docker/location"
}

# Move existing data
sudo mv /var/lib/docker /new/docker/location

# Start Docker daemon
sudo systemctl start docker
```

## Performance Issues

### High CPU Usage

#### Symptoms
- System becomes unresponsive
- High load average
- Slow application response

#### Diagnosis
```bash
# Monitor CPU usage
top -p $(docker inspect --format='{{.State.Pid}}' <container_name>)
docker stats --no-stream

# Profile application
docker-compose exec backend python -m cProfile -s cumulative run.py
```

#### Solutions

**1. Optimize Application Code**
```python
# Use connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

**2. Implement Caching**
```python
# Cache expensive operations
@cache.memoize(timeout=300)
def get_user_lessons(user_id):
    # Expensive database query
    return query_result
```

**3. Scale Horizontally**
```bash
# Scale backend services
docker-compose -f docker-compose.scale.yml up -d --scale backend=3
```

### Memory Issues

#### Symptoms
- Out of memory errors
- Container killed by OOM killer
- Swap usage high

#### Diagnosis
```bash
# Check memory usage
free -h
docker stats --no-stream

# Check container memory limits
docker inspect <container_name> | grep -i memory

# Monitor memory leaks
docker-compose exec backend python -c "
import psutil
import time
process = psutil.Process()
for i in range(10):
    print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')
    time.sleep(1)
"
```

#### Solutions

**1. Increase Memory Limits**
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
```

**2. Optimize Memory Usage**
```python
# Use generators instead of lists
def process_large_dataset():
    for item in large_dataset:
        yield process_item(item)

# Close database connections
@app.teardown_appcontext
def close_db(error):
    db.session.close()
```

**3. Implement Memory Monitoring**
```python
import psutil

def check_memory_usage():
    memory_percent = psutil.virtual_memory().percent
    if memory_percent > 80:
        logger.warning(f"High memory usage: {memory_percent}%")
```

## Application-Specific Issues

### Database Connection Issues

#### Symptoms
- "Connection refused" errors
- "Too many connections" errors
- Slow database queries

#### Diagnosis
```bash
# Test database connectivity
docker-compose exec postgres pg_isready -U postgres

# Check active connections
docker-compose exec postgres psql -U postgres -c "
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE state = 'active';
"

# Check slow queries
docker-compose exec postgres psql -U postgres -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;
"
```

#### Solutions

**1. Configure Connection Pooling**
```python
# SQLAlchemy connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

**2. Optimize Database Configuration**
```postgresql
# postgresql.conf
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
```

### Redis Connection Issues

#### Symptoms
- Cache misses
- Connection timeouts
- Memory errors

#### Diagnosis
```bash
# Test Redis connectivity
docker-compose exec redis redis-cli ping

# Check Redis memory usage
docker-compose exec redis redis-cli info memory

# Monitor Redis operations
docker-compose exec redis redis-cli monitor
```

#### Solutions

**1. Configure Redis Properly**
```redis
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
timeout 300
tcp-keepalive 60
```

**2. Implement Connection Pooling**
```python
import redis.connection

pool = redis.ConnectionPool(
    host='redis',
    port=6379,
    db=0,
    max_connections=20
)
redis_client = redis.Redis(connection_pool=pool)
```

### Celery Task Issues

#### Symptoms
- Tasks not processing
- Worker crashes
- Task timeouts

#### Diagnosis
```bash
# Check Celery worker status
docker-compose exec celery-worker celery -A app.celery inspect active

# Monitor task queue
docker-compose exec celery-worker celery -A app.celery inspect reserved

# Check worker logs
docker-compose logs celery-worker
```

#### Solutions

**1. Configure Celery Properly**
```python
# celery_config.py
CELERY_TASK_SOFT_TIME_LIMIT = 300
CELERY_TASK_TIME_LIMIT = 600
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True
```

**2. Scale Workers**
```bash
# Scale Celery workers
docker-compose -f docker-compose.scale.yml up -d --scale celery-worker=4
```

## Emergency Procedures

### Complete System Recovery

```bash
#!/bin/bash
# emergency-recovery.sh

echo "=== Emergency System Recovery ==="

# Stop all services
echo "1. Stopping all services..."
docker-compose -f docker-compose.prod.yml down

# Clean up resources
echo "2. Cleaning up resources..."
docker system prune -a -f
docker volume prune -f

# Restore from backup
echo "3. Restoring from backup..."
./scripts/restore-database.sh /backups/latest-backup.sql.gz
./scripts/restore-volumes.sh /backups/latest-volumes.tar.gz

# Start services
echo "4. Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Verify recovery
echo "5. Verifying recovery..."
sleep 30
curl -f http://localhost/api/health && echo "✓ Recovery successful" || echo "✗ Recovery failed"
```

### Rollback Procedure

```bash
#!/bin/bash
# rollback.sh

VERSION=${1:-previous}

echo "=== Rolling back to $VERSION ==="

# Stop current services
docker-compose -f docker-compose.prod.yml down

# Pull previous version
docker pull mindcoach/backend:$VERSION
docker pull mindcoach/frontend:$VERSION

# Update compose file to use previous version
sed -i "s/:latest/:$VERSION/g" docker-compose.prod.yml

# Start services with previous version
docker-compose -f docker-compose.prod.yml up -d

# Verify rollback
sleep 30
curl -f http://localhost/api/health && echo "✓ Rollback successful" || echo "✗ Rollback failed"
```

### Data Recovery

```bash
#!/bin/bash
# data-recovery.sh

BACKUP_DATE=${1:-$(date -d "yesterday" +%Y%m%d)}

echo "=== Data Recovery for $BACKUP_DATE ==="

# Stop application
docker-compose -f docker-compose.prod.yml stop backend celery-worker

# Restore database
gunzip -c /backups/database/mindcoach_backup_${BACKUP_DATE}_*.sql.gz | \
  docker exec -i mindcoach-postgres psql -U postgres -d mindcoach

# Restore volumes
tar xzf /backups/volumes/user-data_${BACKUP_DATE}_*.tar.gz -C /var/lib/docker/volumes/mindcoach_user-data/_data/

# Start application
docker-compose -f docker-compose.prod.yml start backend celery-worker

echo "✓ Data recovery completed"
```

## Prevention and Monitoring

### Automated Health Monitoring

```bash
#!/bin/bash
# health-monitor.sh

# Run every 5 minutes via cron
# */5 * * * * /path/to/health-monitor.sh

ALERT_EMAIL="admin@mindcoach.com"
LOG_FILE="/var/log/mindcoach-health.log"

# Check container health
UNHEALTHY=$(docker ps --filter health=unhealthy -q | wc -l)
if [ $UNHEALTHY -gt 0 ]; then
    echo "$(date): ALERT - $UNHEALTHY unhealthy containers" >> $LOG_FILE
    echo "Unhealthy containers detected" | mail -s "MindCoach Health Alert" $ALERT_EMAIL
fi

# Check API health
if ! curl -f -s http://localhost/api/health > /dev/null; then
    echo "$(date): ALERT - API health check failed" >> $LOG_FILE
    echo "API health check failed" | mail -s "MindCoach API Alert" $ALERT_EMAIL
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 85 ]; then
    echo "$(date): ALERT - Disk usage at ${DISK_USAGE}%" >> $LOG_FILE
    echo "High disk usage: ${DISK_USAGE}%" | mail -s "MindCoach Disk Alert" $ALERT_EMAIL
fi
```

### Log Monitoring

```bash
#!/bin/bash
# log-monitor.sh

# Monitor for error patterns
tail -f /var/log/mindcoach/*.log | while read line; do
    if echo "$line" | grep -qi "error\|exception\|failed"; then
        echo "$(date): ERROR DETECTED - $line" >> /var/log/mindcoach-alerts.log
        # Send alert if needed
    fi
done
```

---

This troubleshooting guide provides comprehensive solutions for common Docker container issues. Keep this guide updated as new issues are discovered and resolved.