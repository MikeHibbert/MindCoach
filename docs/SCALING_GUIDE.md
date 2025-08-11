# Horizontal Scaling Guide

This guide covers the horizontal scaling capabilities of MindCoach, including auto-scaling, load balancing, and performance optimization.

## Overview

MindCoach supports horizontal scaling across multiple dimensions:

- **Application Servers**: Scale backend API servers based on CPU/memory usage
- **Worker Processes**: Scale Celery workers based on queue length
- **Frontend Servers**: Scale static file servers for high traffic
- **Database Connections**: Connection pooling for database scalability
- **Session Management**: Distributed sessions for stateless scaling

## Architecture

```
                    ┌─────────────────┐
                    │   Load Balancer │
                    │    (HAProxy)    │
                    └─────────┬───────┘
                              │
                    ┌─────────┴───────┐
                    │                 │
            ┌───────▼────────┐ ┌──────▼────────┐
            │  Frontend (N)  │ │  Backend (N)  │
            │   (Nginx)      │ │   (Flask)     │
            └────────────────┘ └───────┬───────┘
                                       │
                              ┌────────▼────────┐
                              │  Worker Pool    │
                              │  (Celery N)     │
                              └─────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
            ┌───────▼────────┐ ┌───────▼────────┐ ┌──────▼──────┐
            │   PostgreSQL   │ │     Redis      │ │ Monitoring  │
            │ (Connection    │ │  (Sessions &   │ │(Prometheus) │
            │   Pooling)     │ │    Cache)      │ │             │
            └────────────────┘ └────────────────┘ └─────────────┘
```

## Auto-Scaling Configuration

### Service Configuration

The auto-scaler monitors multiple services with different scaling strategies:

**Backend Services**:
```json
{
  "service_name": "backend",
  "min_replicas": 2,
  "max_replicas": 10,
  "scale_up_threshold": 80.0,
  "scale_down_threshold": 20.0,
  "scale_up_cooldown": 300,
  "scale_down_cooldown": 600,
  "metric_name": "cpu_usage"
}
```

**Worker Services**:
```json
{
  "service_name": "celery-worker",
  "min_replicas": 2,
  "max_replicas": 8,
  "scale_up_threshold": 10.0,
  "scale_down_threshold": 2.0,
  "scale_up_cooldown": 180,
  "scale_down_cooldown": 600,
  "metric_name": "queue_length"
}
```

### Scaling Metrics

1. **CPU Usage**: Average CPU utilization across containers
2. **Memory Usage**: Memory utilization percentage
3. **Request Rate**: HTTP requests per second
4. **Response Time**: Average response time
5. **Queue Length**: Number of pending tasks

### Scaling Policies

**Scale Up Conditions**:
- Metric exceeds threshold for sustained period
- Not in cooldown period
- Below maximum replica count
- Service is healthy

**Scale Down Conditions**:
- Metric below threshold for sustained period
- Not in cooldown period
- Above minimum replica count
- All instances are healthy

## Load Balancing

### HAProxy Configuration

**Load Balancing Algorithms**:
- **Round Robin**: Default for API requests
- **Source IP**: For WebSocket connections
- **Least Connections**: For long-running requests

**Health Checks**:
- HTTP health check endpoint: `/api/health`
- Check interval: 10 seconds
- Failure threshold: 3 consecutive failures
- Recovery threshold: 2 consecutive successes

**Session Persistence**:
- Cookie-based sticky sessions for stateful operations
- Redis-based session storage for stateless scaling

### Traffic Distribution

```
Frontend Traffic:
├── Static Assets (80%) → Nginx Servers
├── API Requests (15%) → Backend Servers
└── WebSocket (5%) → Backend Servers (Sticky)
```

## Database Scaling

### Connection Pooling

**PostgreSQL Configuration**:
```sql
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
```

**Connection Pool Settings**:
- Pool size: 20 connections per backend instance
- Max overflow: 10 additional connections
- Pool timeout: 30 seconds
- Pool recycle: 3600 seconds

### Query Optimization

**Indexes**:
- User ID indexes for fast user lookups
- Composite indexes for common query patterns
- Partial indexes for active records only

**Query Patterns**:
- Use prepared statements
- Implement query result caching
- Optimize N+1 query problems
- Use database-level pagination

## Session Management

### Distributed Sessions

**Redis Session Store**:
```python
# Session configuration
SESSION_TYPE = 'redis'
SESSION_REDIS = redis.from_url('redis://redis:6379/0')
SESSION_PERMANENT = False
SESSION_USE_SIGNER = True
SESSION_KEY_PREFIX = 'session:'
```

**Session Data Structure**:
```json
{
  "user_id": "user123",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T01:00:00Z",
  "data": {
    "preferences": {},
    "current_subject": "python",
    "progress": {}
  }
}
```

### Session Cleanup

**Automatic Cleanup**:
- TTL-based expiration in Redis
- Periodic cleanup of expired sessions
- User logout cleanup
- Inactive session cleanup

## Performance Testing

### Load Testing with K6

**Basic Load Test**:
```bash
# Test with 50 concurrent users for 5 minutes
./scripts/test-scaling.sh 300 50 60
```

**Scaling Test Scenarios**:
1. **Ramp Up Test**: Gradually increase load
2. **Spike Test**: Sudden traffic spikes
3. **Soak Test**: Sustained load over time
4. **Stress Test**: Beyond normal capacity

### Performance Metrics

**Application Metrics**:
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (percentage)
- Throughput (MB/second)

**System Metrics**:
- CPU utilization
- Memory usage
- Network I/O
- Disk I/O

**Database Metrics**:
- Connection count
- Query execution time
- Lock wait time
- Cache hit ratio

## Monitoring and Alerting

### Prometheus Metrics

**Custom Metrics**:
```python
# Request metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

# Application metrics
ACTIVE_USERS = Gauge('active_users_total', 'Number of active users')
QUEUE_LENGTH = Gauge('celery_queue_length', 'Celery queue length')
```

**System Metrics**:
- Container CPU and memory usage
- Network traffic
- Disk usage
- Service health status

### Grafana Dashboards

**Application Dashboard**:
- Request rate and response time
- Error rates by endpoint
- Active user count
- Queue lengths

**Infrastructure Dashboard**:
- Container resource usage
- Database performance
- Redis performance
- Load balancer statistics

### Alerting Rules

**Critical Alerts**:
- Service down (immediate)
- High error rate (>5% for 5 minutes)
- High response time (>2s p95 for 5 minutes)
- Database connection exhaustion

**Warning Alerts**:
- High CPU usage (>80% for 10 minutes)
- High memory usage (>85% for 10 minutes)
- Queue backlog (>100 tasks for 5 minutes)
- Disk space low (<20% free)

## Scaling Operations

### Manual Scaling

**Scale Up Backend**:
```bash
docker-compose -f docker-compose.scale.yml up -d --scale backend=5
```

**Scale Up Workers**:
```bash
docker-compose -f docker-compose.scale.yml up -d --scale celery-worker=6
```

**Verify Scaling**:
```bash
docker-compose -f docker-compose.scale.yml ps
curl http://localhost:8404/stats  # HAProxy stats
```

### Auto-Scaling Management

**Check Auto-Scaler Status**:
```bash
curl http://localhost:8080/status
```

**Auto-Scaler Logs**:
```bash
docker-compose -f docker-compose.scale.yml logs -f autoscaler
```

**Modify Scaling Policies**:
```bash
# Edit autoscaler-config.json
# Restart autoscaler
docker-compose -f docker-compose.scale.yml restart autoscaler
```

## Troubleshooting

### Common Scaling Issues

1. **Slow Scale Up**:
   - Check metric collection
   - Verify scaling thresholds
   - Review cooldown periods

2. **Uneven Load Distribution**:
   - Check load balancer configuration
   - Verify health checks
   - Review session stickiness

3. **Database Connection Issues**:
   - Monitor connection pool usage
   - Check connection limits
   - Review query performance

4. **Session Loss**:
   - Verify Redis connectivity
   - Check session TTL settings
   - Review session cleanup

### Debug Commands

**Check Service Health**:
```bash
# Backend health
curl http://localhost/api/health

# Database health
docker-compose -f docker-compose.scale.yml exec postgres pg_isready

# Redis health
docker-compose -f docker-compose.scale.yml exec redis redis-cli ping
```

**Monitor Resource Usage**:
```bash
# Container stats
docker stats

# System resources
htop
iotop
```

**Check Load Balancer**:
```bash
# HAProxy stats
curl http://localhost:8404/stats

# Backend connectivity
curl -H "Host: backend" http://localhost/api/health
```

## Best Practices

### Scaling Strategy

1. **Start Small**: Begin with minimum viable scaling
2. **Monitor Closely**: Watch metrics during scaling events
3. **Test Thoroughly**: Load test before production scaling
4. **Plan Capacity**: Understand peak usage patterns
5. **Automate Everything**: Reduce manual intervention

### Performance Optimization

1. **Cache Aggressively**: Use Redis for frequently accessed data
2. **Optimize Queries**: Index properly and avoid N+1 queries
3. **Compress Responses**: Enable gzip compression
4. **Use CDN**: Serve static assets from CDN
5. **Monitor Continuously**: Set up comprehensive monitoring

### Operational Excellence

1. **Document Everything**: Keep scaling procedures documented
2. **Practice Scaling**: Regular scaling drills
3. **Monitor Costs**: Track resource usage and costs
4. **Plan for Failures**: Have rollback procedures ready
5. **Learn from Incidents**: Post-mortem analysis

## Cost Optimization

### Resource Right-Sizing

- Monitor actual resource usage
- Adjust container resource limits
- Use appropriate instance types
- Implement resource quotas

### Scaling Efficiency

- Optimize scaling thresholds
- Reduce scaling frequency
- Use predictive scaling
- Implement cost-aware scaling

### Monitoring Costs

- Track resource usage trends
- Set up cost alerts
- Regular cost reviews
- Optimize for cost-performance ratio

---

This guide provides comprehensive coverage of horizontal scaling capabilities, from basic configuration to advanced optimization techniques. Regular monitoring and testing ensure optimal performance and cost efficiency.