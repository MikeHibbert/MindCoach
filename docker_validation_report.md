# Docker Containerized System Validation Report

## Validation Summary

- **Start Time**: 2025-08-12T07:12:46.083868
- **Duration**: 80.50 seconds
- **Total Validations**: 6
- **Passed**: 5
- **Failed**: 1

## Validation Results

### [FAIL] Container Startup

**Status**: FAILED

- **Running Containers**: 2
- **Container Details**: mindcoach-test-db	Up 45 seconds (healthy)
mindcoach-test-redis	Up 45 seconds (healthy)


### [PASS] Database Connectivity

**Status**: PASSED

- **Connection Test**: True
- **Basic Operations**: True

### [PASS] Redis Connectivity

**Status**: PASSED

- **Connection Test**: True
- **Basic Operations**: True

### [PASS] Data Persistence

**Status**: PASSED

- **Database Persistence**: True
- **Redis Persistence**: True

### [PASS] Container Networking

**Status**: PASSED

- **Database Network**: True
- **Redis Network**: True
- **Api Network**: True

### [PASS] Environment Configuration

**Status**: PASSED

- **Database Env Vars**: True
- **Redis Env Check**: True
- **Secrets Secure**: True

## Environment Information

- **Docker Version**: Docker version 28.3.2, build 578ccf6
- **Docker Compose Version**: Docker Compose version v2.38.2-desktop.1
- **Python Version**: 3.10.8 (tags/v3.10.8:aaaf517, Oct 11 2022, 16:50:30) [MSC v.1933 64 bit (AMD64)]
- **Test Data Directory**: C:\Users\Mike\AppData\Local\Temp\docker_validation_c3tai_9b

## Recommendations

1. Check Docker daemon status and container resource limits

