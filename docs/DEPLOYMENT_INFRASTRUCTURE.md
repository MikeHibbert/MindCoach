# Deployment and Scaling Infrastructure

This document describes the comprehensive deployment and scaling infrastructure implemented for MindCoach, including CI/CD pipelines, horizontal scaling capabilities, and development environment setup.

## Overview

The infrastructure supports:
- **Production Deployment**: Automated CI/CD with blue-green deployment
- **Horizontal Scaling**: Auto-scaling based on metrics with load balancing
- **Development Environment**: Containerized development with hot reloading
- **Monitoring & Observability**: Comprehensive metrics and logging
- **Security**: Automated security scanning and best practices

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Development   │    │    Staging      │    │   Production    │
│   Environment   │    │   Environment   │    │   Environment   │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Hot Reloading │    │ • Auto Deploy   │    │ • Blue-Green    │
│ • Debug Support │    │ • Integration   │    │ • Auto-Scaling  │
│ • Mock Services │    │ • Testing       │    │ • Load Balancer │
│ • Dev Dashboard │    │ • Validation    │    │ • Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   CI/CD Pipeline │
                    │                 │
                    │ • GitHub Actions│
                    │ • Automated Tests│
                    │ • Security Scans │
                    │ • Container Build│
                    │ • Registry Push  │
                    └─────────────────┘
```

## Components

### 1. CI/CD Pipeline

**Location**: `.github/workflows/ci-cd.yml`

**Features**:
- Automated testing (unit, integration, E2E)
- Security vulnerability scanning
- Multi-platform container builds
- Automated deployment to staging/production
- Rollback capabilities

**Workflow**:
1. **Test Stage**: Run all test suites
2. **Security Stage**: Vulnerability scanning
3. **Build Stage**: Create container images
4. **Deploy Stage**: Deploy to environments
5. **Notify Stage**: Send deployment notifications

### 2. Container Registry

**Scripts**: `scripts/setup-registry.sh`, `scripts/build-images.sh`

**Supported Registries**:
- GitHub Container Registry (ghcr.io)
- Docker Hub
- AWS ECR
- Private registries

**Features**:
- Multi-platform builds (AMD64, ARM64)
- Automated tagging and versioning
- Security scanning integration
- Image optimization

### 3. Horizontal Scaling

**Configuration**: `docker-compose.scale.yml`

**Components**:
- **Load Balancer**: HAProxy with health checks
- **Auto-Scaler**: Metrics-based scaling service
- **Session Management**: Redis-based distributed sessions
- **Database Pooling**: Optimized PostgreSQL configuration

**Scaling Metrics**:
- CPU usage
- Memory usage
- Request rate
- Queue length
- Response time

### 4. Development Environment

**Configuration**: `docker-compose.dev.yml`

**Features**:
- Hot reloading for frontend and backend
- Remote debugging support
- Development dashboard
- Database and Redis admin interfaces
- Mock API services
- File watching and auto-rebuilds

## Quick Start

### Production Deployment

1. **Setup Container Registry**:
   ```bash
   ./scripts/setup-registry.sh github
   ```

2. **Build and Push Images**:
   ```bash
   ./scripts/build-images.sh v1.0.0
   ```

3. **Deploy to Production**:
   ```bash
   ./scripts/deploy-production.sh v1.0.0
   ```

### Development Environment

1. **Setup Development Environment**:
   ```bash
   ./scripts/setup-dev.sh
   ```

2. **Start Development Services**:
   ```bash
   ./scripts/dev-start.sh
   ```

3. **Access Services**:
   - Frontend: http://localhost:3000
   - Backend: http://localhost:5000
   - Dev Dashboard: http://localhost:8080

### Scaling Testing

1. **Test Horizontal Scaling**:
   ```bash
   ./scripts/test-scaling.sh 300 100 60
   ```

2. **Run Load Tests**:
   ```bash
   ./scripts/run-tests.sh performance
   ```

## Configuration

### Environment Variables

**Production** (`.env`):
```bash
SECRET_KEY=your-production-secret
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
CORS_ORIGINS=https://yourdomain.com
```

**Development** (`.env.dev`):
```bash
SECRET_KEY=dev-secret-key
DATABASE_URL=postgresql://postgres:devpassword@postgres-dev:5432/mindcoach_dev
REDIS_URL=redis://redis-dev:6379/0
CORS_ORIGINS=http://localhost:3000
```

### Scaling Configuration

**Auto-Scaler Config** (`autoscaler-config.json`):
```json
{
  "service_name": "backend",
  "min_replicas": 2,
  "max_replicas": 10,
  "scale_up_threshold": 80.0,
  "scale_down_threshold": 20.0,
  "scale_up_cooldown": 300,
  "scale_down_cooldown": 600
}
```

## Monitoring

### Development Dashboard

**URL**: http://localhost:8080

**Features**:
- Real-time service status
- Performance metrics
- Log viewing
- File change monitoring
- Service management

### Production Monitoring

**Components**:
- Prometheus for metrics collection
- Grafana for visualization
- HAProxy stats dashboard
- Application health checks

**Metrics**:
- Request rate and response time
- Error rates and status codes
- Resource utilization (CPU, memory)
- Database performance
- Queue lengths

## Security

### Automated Security Scanning

- **Container Images**: Trivy vulnerability scanning
- **Dependencies**: npm audit and pip safety checks
- **Code Quality**: Static analysis with security rules
- **Secrets**: Automated secret detection

### Security Best Practices

- Minimal container images
- Non-root user execution
- Network segmentation
- Encrypted communications
- Regular security updates

## Deployment Strategies

### Blue-Green Deployment

1. Deploy new version alongside current (green)
2. Run health checks on new version
3. Switch traffic to new version
4. Keep old version for quick rollback

### Rolling Updates

1. Update containers one by one
2. Health check each updated container
3. Continue if healthy, rollback if not
4. Complete when all containers updated

### Canary Deployment

1. Deploy new version to small subset
2. Monitor metrics and errors
3. Gradually increase traffic
4. Full deployment or rollback based on results

## Troubleshooting

### Common Issues

1. **Container Build Failures**:
   - Check Dockerfile syntax
   - Verify base image availability
   - Check build context size

2. **Deployment Failures**:
   - Verify environment variables
   - Check resource availability
   - Review health check configuration

3. **Scaling Issues**:
   - Monitor auto-scaler logs
   - Check metric collection
   - Verify resource limits

### Debug Commands

```bash
# View service logs
docker-compose -f docker-compose.scale.yml logs -f [service]

# Check service health
curl http://localhost/api/health

# Monitor auto-scaler
curl http://localhost:8080/status

# View container stats
docker stats

# Check scaling metrics
docker-compose -f docker-compose.scale.yml exec prometheus curl localhost:9090/api/v1/query?query=up
```

## Performance Optimization

### Database Optimization

- Connection pooling with pgbouncer
- Query optimization and indexing
- Read replicas for scaling reads
- Automated vacuum and analyze

### Application Optimization

- Redis caching for frequently accessed data
- CDN for static assets
- Gzip compression
- HTTP/2 support

### Container Optimization

- Multi-stage builds for smaller images
- Layer caching optimization
- Resource limits and requests
- Health check optimization

## Backup and Recovery

### Automated Backups

- Database backups before deployments
- User data backups
- Configuration backups
- Container image versioning

### Recovery Procedures

1. **Application Recovery**:
   - Rollback to previous version
   - Restore from backup
   - Health check validation

2. **Data Recovery**:
   - Database point-in-time recovery
   - User data restoration
   - Configuration restoration

## Maintenance

### Regular Tasks

- Update base images
- Security patch application
- Performance monitoring review
- Backup verification
- Log rotation and cleanup

### Scheduled Maintenance

- Database maintenance windows
- Container image updates
- Security updates
- Performance optimization

## Support and Documentation

### Additional Resources

- [Development Setup Guide](DEVELOPMENT_SETUP.md)
- [Container Registry Setup](REGISTRY_SETUP.md)
- [Performance Testing Guide](PERFORMANCE_TESTING.md)
- [Security Best Practices](SECURITY.md)

### Getting Help

1. Check the troubleshooting section
2. Review service logs
3. Check the development dashboard
4. Consult the documentation
5. Contact the development team

---

This infrastructure provides a robust, scalable, and maintainable deployment solution for MindCoach, supporting both development and production environments with automated scaling, monitoring, and deployment capabilities.