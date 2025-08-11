# Performance Testing Guide

This guide covers performance testing strategies, tools, and best practices for MindCoach, including load testing, scaling validation, and performance optimization.

## Overview

Performance testing ensures MindCoach can handle expected user loads while maintaining acceptable response times and system stability. Our testing strategy covers multiple aspects:

- **Load Testing**: Normal expected load
- **Stress Testing**: Beyond normal capacity
- **Spike Testing**: Sudden traffic increases
- **Volume Testing**: Large amounts of data
- **Endurance Testing**: Extended periods

## Testing Tools

### K6 Load Testing

**Primary Tool**: K6 for HTTP load testing
**Location**: `tests/performance/load-test.js`

**Features**:
- JavaScript-based test scripts
- Realistic user scenarios
- Detailed performance metrics
- CI/CD integration
- Threshold-based pass/fail criteria

### Scaling Test Suite

**Tool**: Custom scaling validation
**Location**: `scripts/test-scaling.sh`

**Features**:
- Auto-scaling validation
- Load balancer testing
- Database performance testing
- Session management validation
- Real-time metrics collection

## Test Scenarios

### 1. Basic Load Test

**Objective**: Validate normal user load handling

```javascript
// K6 Configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp up
    { duration: '5m', target: 10 },   // Stay at load
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.05'],
  },
};
```

**User Journey**:
1. Create user account
2. Select programming subject
3. Complete survey
4. Generate content
5. View lessons

### 2. Stress Test

**Objective**: Find system breaking point

```bash
# High load stress test
./scripts/test-scaling.sh 600 200 120
```

**Metrics Monitored**:
- Response time degradation
- Error rate increase
- Resource utilization
- Auto-scaling triggers

### 3. Spike Test

**Objective**: Handle sudden traffic spikes

```javascript
export const options = {
  stages: [
    { duration: '1m', target: 10 },   // Normal load
    { duration: '30s', target: 100 }, // Sudden spike
    { duration: '2m', target: 100 },  // Sustained spike
    { duration: '1m', target: 10 },   // Return to normal
  ],
};
```

### 4. Endurance Test

**Objective**: Long-term stability

```bash
# 2-hour endurance test
./scripts/test-scaling.sh 7200 50 300
```

**Focus Areas**:
- Memory leaks
- Connection pool exhaustion
- Cache performance
- Database performance degradation

## Performance Metrics

### Application Metrics

**Response Time**:
- **Target**: p95 < 500ms
- **Acceptable**: p95 < 1000ms
- **Critical**: p95 > 2000ms

**Throughput**:
- **Target**: 100 requests/second
- **Peak**: 500 requests/second
- **Burst**: 1000 requests/second

**Error Rate**:
- **Target**: < 0.1%
- **Acceptable**: < 1%
- **Critical**: > 5%

### System Metrics

**CPU Utilization**:
- **Normal**: < 70%
- **High**: 70-85%
- **Critical**: > 85%

**Memory Usage**:
- **Normal**: < 80%
- **High**: 80-90%
- **Critical**: > 90%

**Database Performance**:
- **Connection Pool**: < 80% utilization
- **Query Time**: p95 < 100ms
- **Lock Wait**: < 10ms average

## Running Performance Tests

### Prerequisites

```bash
# Install K6
# macOS
brew install k6

# Ubuntu/Debian
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# Windows
choco install k6
```

### Basic Load Test

```bash
# Start application
./scripts/dev-start.sh

# Run basic load test
k6 run tests/performance/load-test.js

# Or use Docker
docker run --rm -i --network host \
  -v $(pwd)/tests/performance:/scripts \
  loadimpact/k6:latest run /scripts/load-test.js
```

### Comprehensive Scaling Test

```bash
# Full scaling validation (5 minutes, 100 users, 60s ramp-up)
./scripts/test-scaling.sh 300 100 60

# Extended test (10 minutes, 200 users, 120s ramp-up)
./scripts/test-scaling.sh 600 200 120

# Stress test (15 minutes, 500 users, 180s ramp-up)
./scripts/test-scaling.sh 900 500 180
```

### Automated Test Suite

```bash
# Run all performance tests
./scripts/run-tests.sh performance

# Run specific test types
./scripts/run-tests.sh unit
./scripts/run-tests.sh integration
./scripts/run-tests.sh e2e
```

## Test Environment Setup

### Local Testing

```bash
# Start scaled infrastructure
docker-compose -f docker-compose.scale.yml up -d

# Verify services are ready
curl http://localhost/api/health
curl http://localhost:8404/stats  # HAProxy stats
```

### CI/CD Integration

**GitHub Actions** (`.github/workflows/ci-cd.yml`):
```yaml
- name: Performance Tests
  run: |
    docker-compose -f docker-compose.test.yml up -d
    sleep 30
    k6 run tests/performance/load-test.js --out json=results.json
    ./scripts/analyze-performance.sh results.json
```

## Performance Monitoring

### Real-Time Monitoring

**Development Dashboard**: http://localhost:8080
- Service status and health
- Real-time metrics
- Resource utilization
- Auto-scaling events

**HAProxy Stats**: http://localhost:8404/stats
- Load balancer statistics
- Backend server health
- Request distribution
- Response times

### Metrics Collection

**Prometheus Metrics**:
```bash
# Application metrics
curl http://localhost:9090/api/v1/query?query=http_requests_total

# System metrics
curl http://localhost:9090/api/v1/query?query=container_cpu_usage_seconds_total

# Custom metrics
curl http://localhost:9090/api/v1/query?query=mindcoach_active_users
```

**Application Logs**:
```bash
# Backend logs
docker-compose -f docker-compose.scale.yml logs -f backend

# Database logs
docker-compose -f docker-compose.scale.yml logs -f postgres

# Load balancer logs
docker-compose -f docker-compose.scale.yml logs -f load-balancer
```

## Performance Optimization

### Database Optimization

**Connection Pooling**:
```python
# SQLAlchemy configuration
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,
    'max_overflow': 10,
    'pool_timeout': 30,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
```

**Query Optimization**:
```sql
-- Add indexes for common queries
CREATE INDEX idx_users_user_id ON users(user_id);
CREATE INDEX idx_subscriptions_user_subject ON subscriptions(user_id, subject);
CREATE INDEX idx_survey_results_user_subject ON survey_results(user_id, subject);
```

### Application Optimization

**Caching Strategy**:
```python
# Redis caching
@cache.memoize(timeout=300)
def get_user_subjects(user_id):
    return db.session.query(Subscription).filter_by(user_id=user_id).all()
```

**Async Processing**:
```python
# Celery background tasks
@celery.task
def generate_content_async(user_id, subject):
    # Long-running content generation
    pass
```

### Frontend Optimization

**Code Splitting**:
```javascript
// Lazy loading components
const LessonViewer = lazy(() => import('./components/LessonViewer'));
const Survey = lazy(() => import('./components/Survey'));
```

**Asset Optimization**:
```javascript
// Webpack optimization
module.exports = {
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
      },
    },
  },
};
```

## Performance Baselines

### Response Time Baselines

| Endpoint | p50 | p95 | p99 |
|----------|-----|-----|-----|
| GET /api/health | 5ms | 10ms | 20ms |
| POST /api/users | 50ms | 100ms | 200ms |
| GET /api/subjects | 20ms | 50ms | 100ms |
| POST /api/surveys/submit | 100ms | 300ms | 500ms |
| POST /api/content/generate | 200ms | 500ms | 1000ms |
| GET /api/lessons/{id} | 30ms | 80ms | 150ms |

### Throughput Baselines

| Scenario | Target RPS | Peak RPS | Notes |
|----------|------------|----------|-------|
| Health checks | 1000 | 5000 | Lightweight endpoint |
| User registration | 50 | 200 | Database writes |
| Subject selection | 100 | 500 | Read-heavy |
| Survey submission | 20 | 100 | Complex processing |
| Content generation | 5 | 20 | AI-intensive |
| Lesson viewing | 200 | 1000 | Cached content |

### Resource Utilization Baselines

| Resource | Normal | High Load | Critical |
|----------|--------|-----------|----------|
| Backend CPU | 30% | 70% | 85% |
| Backend Memory | 40% | 75% | 90% |
| Database CPU | 20% | 60% | 80% |
| Database Memory | 50% | 80% | 95% |
| Redis Memory | 30% | 70% | 85% |

## Troubleshooting Performance Issues

### Common Performance Problems

**High Response Times**:
1. Check database query performance
2. Verify connection pool utilization
3. Review cache hit rates
4. Analyze slow query logs

**High Error Rates**:
1. Check application logs for exceptions
2. Verify database connectivity
3. Review load balancer health checks
4. Analyze timeout configurations

**Resource Exhaustion**:
1. Monitor memory usage and leaks
2. Check connection pool limits
3. Review cache memory usage
4. Analyze garbage collection patterns

### Performance Debugging

**Database Performance**:
```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check connection usage
SELECT count(*) as connections, state 
FROM pg_stat_activity 
GROUP BY state;
```

**Application Performance**:
```python
# Profile Python code
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# Your code here
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative').print_stats(10)
```

**Load Balancer Analysis**:
```bash
# HAProxy statistics
curl -s http://localhost:8404/stats | grep backend

# Connection analysis
netstat -an | grep :80 | wc -l
```

## Continuous Performance Testing

### Automated Performance Monitoring

**Scheduled Tests**:
```yaml
# GitHub Actions scheduled performance tests
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  performance-test:
    runs-on: ubuntu-latest
    steps:
      - name: Run Performance Tests
        run: |
          ./scripts/test-scaling.sh 300 50 60
          ./scripts/analyze-results.sh
```

**Performance Regression Detection**:
```bash
# Compare performance results
./scripts/compare-performance.sh baseline.json current.json

# Alert on regression
if [ $REGRESSION_DETECTED -eq 1 ]; then
  echo "Performance regression detected!"
  exit 1
fi
```

### Performance Metrics Dashboard

**Grafana Dashboard**:
- Response time trends
- Throughput metrics
- Error rate monitoring
- Resource utilization
- Auto-scaling events

**Alerting Rules**:
```yaml
# Prometheus alerting rules
groups:
  - name: performance
    rules:
      - alert: HighResponseTime
        expr: http_request_duration_seconds{quantile="0.95"} > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High response time detected
```

## Best Practices

### Test Design

1. **Realistic Scenarios**: Model actual user behavior
2. **Gradual Load Increase**: Ramp up load gradually
3. **Baseline Establishment**: Establish performance baselines
4. **Regular Testing**: Run tests regularly, not just before releases
5. **Environment Consistency**: Use consistent test environments

### Performance Optimization

1. **Measure First**: Always measure before optimizing
2. **Focus on Bottlenecks**: Identify and fix the biggest bottlenecks
3. **Cache Strategically**: Cache frequently accessed data
4. **Optimize Queries**: Use proper indexing and query optimization
5. **Monitor Continuously**: Continuous performance monitoring

### Scaling Strategy

1. **Horizontal Scaling**: Scale out rather than up when possible
2. **Stateless Design**: Design for stateless scaling
3. **Load Distribution**: Distribute load evenly across instances
4. **Auto-Scaling**: Implement intelligent auto-scaling
5. **Capacity Planning**: Plan for peak loads and growth

---

This performance testing guide provides comprehensive coverage of testing strategies, tools, and optimization techniques for MindCoach. Regular performance testing ensures the platform can handle growth and maintain excellent user experience under load.