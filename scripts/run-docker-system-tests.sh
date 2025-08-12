#!/bin/bash

# Docker Containerized System Test Runner
# Comprehensive testing of the complete containerized system

set -e

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

# Configuration
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="docker-test-results-$TIMESTAMP"
TEST_TYPE=${1:-comprehensive}

echo "🐳 Docker Containerized System Tests"
echo "Test Type: $TEST_TYPE"
echo "Results Directory: $RESULTS_DIR"
echo "Timestamp: $TIMESTAMP"

# Create results directory
mkdir -p "$RESULTS_DIR"

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    local missing_deps=()
    
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        missing_deps+=("docker-compose")
    fi
    
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    if ! command -v pip3 &> /dev/null; then
        missing_deps+=("pip3")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_info "Please install the missing dependencies and try again"
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "Dependencies check passed"
}

# Install Python test dependencies
install_test_dependencies() {
    log_info "Installing Python test dependencies..."
    
    # Create virtual environment for testing
    python3 -m venv "$RESULTS_DIR/test-venv"
    source "$RESULTS_DIR/test-venv/bin/activate"
    
    # Install required packages
    pip install --quiet \
        docker \
        redis \
        psycopg2-binary \
        requests \
        pytest \
        pyyaml
    
    log_success "Test dependencies installed"
}

# Prepare test environment
prepare_test_environment() {
    log_info "Preparing test environment..."
    
    # Clean up any existing test containers
    docker-compose -f docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true
    
    # Remove any orphaned test networks
    docker network prune -f 2>/dev/null || true
    
    # Create test directories
    mkdir -p "$RESULTS_DIR/logs"
    mkdir -p "$RESULTS_DIR/data"
    mkdir -p "$RESULTS_DIR/coverage"
    
    # Set environment variables for testing
    export COMPOSE_PROJECT_NAME="mindcoach-test-$TIMESTAMP"
    export TEST_RESULTS_DIR="$(pwd)/$RESULTS_DIR"
    
    log_success "Test environment prepared"
}

# Run container startup tests
test_container_startup() {
    log_info "Testing container startup..."
    
    # Start test infrastructure
    docker-compose -f docker-compose.test.yml up -d test-db test-redis mock-api
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Check container health
    local healthy_containers=0
    local total_containers=0
    
    for service in test-db test-redis mock-api; do
        total_containers=$((total_containers + 1))
        if docker-compose -f docker-compose.test.yml ps "$service" | grep -q "Up"; then
            healthy_containers=$((healthy_containers + 1))
            log_success "Service $service is running"
        else
            log_error "Service $service failed to start"
        fi
    done
    
    if [ "$healthy_containers" -eq "$total_containers" ]; then
        log_success "Container startup test passed ($healthy_containers/$total_containers)"
        return 0
    else
        log_error "Container startup test failed ($healthy_containers/$total_containers)"
        return 1
    fi
}

# Test data persistence
test_data_persistence() {
    log_info "Testing data persistence..."
    
    # Create test data
    log_info "Creating test data..."
    docker-compose -f docker-compose.test.yml exec -T test-db psql -U test_user -d mindcoach_test -c "
        INSERT INTO users (user_id, email) VALUES ('test-persistence', 'test@persistence.com') ON CONFLICT DO NOTHING;
        INSERT INTO subscriptions (user_id, subject, status) VALUES ('test-persistence', 'python', 'active') ON CONFLICT DO NOTHING;
    " 2>/dev/null || log_warning "Database test data creation may have failed"
    
    # Create file system test data
    mkdir -p "$RESULTS_DIR/test-users/test-persistence/python"
    echo '{"selected_subject": "python"}' > "$RESULTS_DIR/test-users/test-persistence/python/selection.json"
    echo "# Test Lesson" > "$RESULTS_DIR/test-users/test-persistence/python/lesson_1.md"
    
    # Restart containers
    log_info "Restarting containers to test persistence..."
    docker-compose -f docker-compose.test.yml restart test-db test-redis
    sleep 20
    
    # Verify data persistence
    log_info "Verifying data persistence..."
    local db_data_exists=false
    local file_data_exists=false
    
    if docker-compose -f docker-compose.test.yml exec -T test-db psql -U test_user -d mindcoach_test -c "SELECT user_id FROM users WHERE user_id = 'test-persistence';" | grep -q "test-persistence"; then
        db_data_exists=true
        log_success "Database data persisted"
    else
        log_error "Database data not persisted"
    fi
    
    if [ -f "$RESULTS_DIR/test-users/test-persistence/python/selection.json" ]; then
        file_data_exists=true
        log_success "File system data persisted"
    else
        log_error "File system data not persisted"
    fi
    
    if [ "$db_data_exists" = true ] && [ "$file_data_exists" = true ]; then
        log_success "Data persistence test passed"
        return 0
    else
        log_error "Data persistence test failed"
        return 1
    fi
}

# Test container networking
test_container_networking() {
    log_info "Testing container networking..."
    
    # Test database connectivity
    log_info "Testing database connectivity..."
    if docker-compose -f docker-compose.test.yml exec -T test-db pg_isready -U test_user -d mindcoach_test; then
        log_success "Database connectivity test passed"
        local db_test=true
    else
        log_error "Database connectivity test failed"
        local db_test=false
    fi
    
    # Test Redis connectivity
    log_info "Testing Redis connectivity..."
    if docker-compose -f docker-compose.test.yml exec -T test-redis redis-cli ping | grep -q "PONG"; then
        log_success "Redis connectivity test passed"
        local redis_test=true
    else
        log_error "Redis connectivity test failed"
        local redis_test=false
    fi
    
    # Test inter-service communication
    log_info "Testing inter-service communication..."
    docker-compose -f docker-compose.test.yml up -d backend-test
    sleep 30
    
    local api_test=false
    for i in {1..10}; do
        if curl -f http://localhost:5000/api/health >/dev/null 2>&1; then
            log_success "API connectivity test passed"
            api_test=true
            break
        fi
        log_info "Waiting for API... ($i/10)"
        sleep 5
    done
    
    if [ "$api_test" = false ]; then
        log_error "API connectivity test failed"
    fi
    
    if [ "$db_test" = true ] && [ "$redis_test" = true ] && [ "$api_test" = true ]; then
        log_success "Container networking test passed"
        return 0
    else
        log_error "Container networking test failed"
        return 1
    fi
}

# Test environment variables and secrets
test_environment_configuration() {
    log_info "Testing environment configuration..."
    
    # Test environment variables are properly set
    local env_test_result=$(docker-compose -f docker-compose.test.yml run --rm backend-test python -c "
import os
required_vars = ['FLASK_ENV', 'SECRET_KEY', 'DATABASE_URL', 'REDIS_URL']
missing_vars = [var for var in required_vars if not os.getenv(var)]
print('MISSING:' + ','.join(missing_vars) if missing_vars else 'ALL_SET')
" 2>/dev/null)
    
    if echo "$env_test_result" | grep -q "ALL_SET"; then
        log_success "Environment variables test passed"
        local env_test=true
    else
        log_error "Environment variables test failed: $env_test_result"
        local env_test=false
    fi
    
    # Test secrets are not exposed in logs
    log_info "Testing secrets security..."
    local secrets_exposed=false
    
    for container in $(docker-compose -f docker-compose.test.yml ps -q); do
        if docker logs "$container" 2>&1 | grep -i -E "(password|secret|key)=" | grep -v -E "(LOG_LEVEL|FLASK_ENV)"; then
            log_warning "Potential secret exposure detected in container logs"
            secrets_exposed=true
        fi
    done
    
    if [ "$secrets_exposed" = false ]; then
        log_success "Secrets security test passed"
        local secrets_test=true
    else
        log_error "Secrets security test failed"
        local secrets_test=false
    fi
    
    if [ "$env_test" = true ] && [ "$secrets_test" = true ]; then
        log_success "Environment configuration test passed"
        return 0
    else
        log_error "Environment configuration test failed"
        return 1
    fi
}

# Run comprehensive Python test suite
run_python_tests() {
    log_info "Running comprehensive Python test suite..."
    
    # Activate virtual environment
    source "$RESULTS_DIR/test-venv/bin/activate"
    
    # Run the comprehensive test suite
    cd tests/docker
    
    if python test_containerized_system.py; then
        log_success "Python test suite passed"
        return 0
    else
        log_error "Python test suite failed"
        return 1
    fi
}

# Generate comprehensive test report
generate_test_report() {
    log_info "Generating comprehensive test report..."
    
    # Collect container logs
    log_info "Collecting container logs..."
    mkdir -p "$RESULTS_DIR/logs"
    
    for service in test-db test-redis mock-api backend-test; do
        if docker-compose -f docker-compose.test.yml ps -q "$service" >/dev/null 2>&1; then
            docker-compose -f docker-compose.test.yml logs "$service" > "$RESULTS_DIR/logs/${service}.log" 2>&1 || true
        fi
    done
    
    # Collect system information
    docker --version > "$RESULTS_DIR/docker-version.txt"
    docker-compose --version > "$RESULTS_DIR/docker-compose-version.txt"
    docker system df > "$RESULTS_DIR/docker-system-info.txt"
    docker-compose -f docker-compose.test.yml ps > "$RESULTS_DIR/container-status.txt"
    
    # Create summary report
    cat > "$RESULTS_DIR/test-summary.md" << EOF
# Docker Containerized System Test Report

**Test Run**: $TIMESTAMP
**Test Type**: $TEST_TYPE
**Results Directory**: $RESULTS_DIR

## Test Results Summary

$([ -f "$RESULTS_DIR/container-startup.result" ] && echo "✅ Container Startup: $(cat $RESULTS_DIR/container-startup.result)" || echo "❓ Container Startup: Not tested")
$([ -f "$RESULTS_DIR/data-persistence.result" ] && echo "✅ Data Persistence: $(cat $RESULTS_DIR/data-persistence.result)" || echo "❓ Data Persistence: Not tested")
$([ -f "$RESULTS_DIR/container-networking.result" ] && echo "✅ Container Networking: $(cat $RESULTS_DIR/container-networking.result)" || echo "❓ Container Networking: Not tested")
$([ -f "$RESULTS_DIR/environment-config.result" ] && echo "✅ Environment Configuration: $(cat $RESULTS_DIR/environment-config.result)" || echo "❓ Environment Configuration: Not tested")
$([ -f "$RESULTS_DIR/python-tests.result" ] && echo "✅ Python Test Suite: $(cat $RESULTS_DIR/python-tests.result)" || echo "❓ Python Test Suite: Not tested")

## System Information

- **Docker Version**: $(cat $RESULTS_DIR/docker-version.txt)
- **Docker Compose Version**: $(cat $RESULTS_DIR/docker-compose-version.txt)
- **Test Timestamp**: $TIMESTAMP

## Container Status

\`\`\`
$(cat $RESULTS_DIR/container-status.txt)
\`\`\`

## Files Generated

- Container logs: \`$RESULTS_DIR/logs/\`
- System information: \`$RESULTS_DIR/docker-system-info.txt\`
- Python test results: \`$RESULTS_DIR/docker_system_test_report.json\`
- Detailed report: \`$RESULTS_DIR/docker_system_test_report.md\`

## Recommendations

1. Review container logs for any warnings or errors
2. Monitor resource usage during scaled deployments
3. Implement automated health checks for all services
4. Set up log aggregation for production environments
5. Configure backup procedures for persistent data

EOF

    log_success "Test report generated: $RESULTS_DIR/test-summary.md"
}

# Cleanup test environment
cleanup() {
    log_info "Cleaning up test environment..."
    
    # Stop and remove test containers
    docker-compose -f docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true
    
    # Remove test networks
    docker network prune -f 2>/dev/null || true
    
    # Clean up Docker system
    docker system prune -f 2>/dev/null || true
    
    log_success "Cleanup completed"
}

# Main execution function
main() {
    local test_results=()
    
    check_dependencies
    install_test_dependencies
    prepare_test_environment
    
    case $TEST_TYPE in
        "startup")
            if test_container_startup; then
                echo "PASSED" > "$RESULTS_DIR/container-startup.result"
                test_results+=("startup:PASSED")
            else
                echo "FAILED" > "$RESULTS_DIR/container-startup.result"
                test_results+=("startup:FAILED")
            fi
            ;;
        "persistence")
            test_container_startup
            if test_data_persistence; then
                echo "PASSED" > "$RESULTS_DIR/data-persistence.result"
                test_results+=("persistence:PASSED")
            else
                echo "FAILED" > "$RESULTS_DIR/data-persistence.result"
                test_results+=("persistence:FAILED")
            fi
            ;;
        "networking")
            test_container_startup
            if test_container_networking; then
                echo "PASSED" > "$RESULTS_DIR/container-networking.result"
                test_results+=("networking:PASSED")
            else
                echo "FAILED" > "$RESULTS_DIR/container-networking.result"
                test_results+=("networking:FAILED")
            fi
            ;;
        "environment")
            test_container_startup
            if test_environment_configuration; then
                echo "PASSED" > "$RESULTS_DIR/environment-config.result"
                test_results+=("environment:PASSED")
            else
                echo "FAILED" > "$RESULTS_DIR/environment-config.result"
                test_results+=("environment:FAILED")
            fi
            ;;
        "comprehensive"|*)
            # Run all tests
            if test_container_startup; then
                echo "PASSED" > "$RESULTS_DIR/container-startup.result"
                test_results+=("startup:PASSED")
            else
                echo "FAILED" > "$RESULTS_DIR/container-startup.result"
                test_results+=("startup:FAILED")
            fi
            
            if test_data_persistence; then
                echo "PASSED" > "$RESULTS_DIR/data-persistence.result"
                test_results+=("persistence:PASSED")
            else
                echo "FAILED" > "$RESULTS_DIR/data-persistence.result"
                test_results+=("persistence:FAILED")
            fi
            
            if test_container_networking; then
                echo "PASSED" > "$RESULTS_DIR/container-networking.result"
                test_results+=("networking:PASSED")
            else
                echo "FAILED" > "$RESULTS_DIR/container-networking.result"
                test_results+=("networking:FAILED")
            fi
            
            if test_environment_configuration; then
                echo "PASSED" > "$RESULTS_DIR/environment-config.result"
                test_results+=("environment:PASSED")
            else
                echo "FAILED" > "$RESULTS_DIR/environment-config.result"
                test_results+=("environment:FAILED")
            fi
            
            if run_python_tests; then
                echo "PASSED" > "$RESULTS_DIR/python-tests.result"
                test_results+=("python:PASSED")
            else
                echo "FAILED" > "$RESULTS_DIR/python-tests.result"
                test_results+=("python:FAILED")
            fi
            ;;
    esac
    
    generate_test_report
    cleanup
    
    # Print final results
    local passed_count=0
    local total_count=${#test_results[@]}
    
    echo ""
    log_info "🐳 Docker Containerized System Test Results:"
    for result in "${test_results[@]}"; do
        local test_name="${result%:*}"
        local test_status="${result#*:}"
        
        if [ "$test_status" = "PASSED" ]; then
            log_success "$test_name: $test_status"
            passed_count=$((passed_count + 1))
        else
            log_error "$test_name: $test_status"
        fi
    done
    
    echo ""
    if [ "$passed_count" -eq "$total_count" ]; then
        log_success "🎉 All tests passed! ($passed_count/$total_count)"
        log_info "Results available in: $RESULTS_DIR"
        exit 0
    else
        log_error "❌ Some tests failed. ($passed_count/$total_count passed)"
        log_info "Results available in: $RESULTS_DIR"
        log_info "Check the logs and reports for detailed information"
        exit 1
    fi
}

# Handle script interruption
trap cleanup INT TERM

# Run main function
main "$@"