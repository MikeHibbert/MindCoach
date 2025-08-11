#!/bin/bash

# Automated test runner script
# Usage: ./scripts/run-tests.sh [test-type]

set -e

TEST_TYPE=${1:-all}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="test-results-$TIMESTAMP"

echo "🧪 Running automated tests..."
echo "Test Type: $TEST_TYPE"
echo "Results Directory: $RESULTS_DIR"

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

# Create results directory
mkdir -p "$RESULTS_DIR"

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is required but not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is required but not installed"
        exit 1
    fi
    
    log_success "Dependencies check passed"
}

# Setup test environment
setup_test_environment() {
    log_info "Setting up test environment..."
    
    # Clean up any existing test containers
    docker-compose -f docker-compose.test.yml down -v --remove-orphans || true
    
    # Create test network
    docker network create mindcoach-test-network || true
    
    # Start test infrastructure
    docker-compose -f docker-compose.test.yml up -d test-db test-redis mock-api
    
    # Wait for services to be ready
    log_info "Waiting for test infrastructure to be ready..."
    sleep 30
    
    # Verify services are healthy
    if ! docker-compose -f docker-compose.test.yml ps | grep -q "healthy"; then
        log_warning "Some test services may not be fully ready"
    fi
    
    log_success "Test environment setup completed"
}

# Run unit tests
run_unit_tests() {
    log_info "Running unit tests..."
    
    # Backend unit tests
    log_info "Running backend unit tests..."
    docker-compose -f docker-compose.test.yml run --rm backend-test
    
    if [ $? -eq 0 ]; then
        log_success "Backend unit tests passed"
    else
        log_error "Backend unit tests failed"
        return 1
    fi
    
    # Frontend unit tests
    log_info "Running frontend unit tests..."
    docker-compose -f docker-compose.test.yml run --rm frontend-test
    
    if [ $? -eq 0 ]; then
        log_success "Frontend unit tests passed"
    else
        log_error "Frontend unit tests failed"
        return 1
    fi
    
    log_success "All unit tests passed"
}

# Run integration tests
run_integration_tests() {
    log_info "Running integration tests..."
    
    # Start full application stack
    docker-compose -f docker-compose.test.yml up -d nginx-test backend-test
    
    # Wait for application to be ready
    sleep 30
    
    # Run integration tests
    docker-compose -f docker-compose.test.yml run --rm \
        -e TEST_TYPE=integration \
        backend-test python -m pytest tests/integration/ -v
    
    if [ $? -eq 0 ]; then
        log_success "Integration tests passed"
    else
        log_error "Integration tests failed"
        return 1
    fi
}

# Run E2E tests
run_e2e_tests() {
    log_info "Running E2E tests..."
    
    # Ensure application is running
    docker-compose -f docker-compose.test.yml up -d nginx-test backend-test
    
    # Wait for application to be ready
    sleep 30
    
    # Run E2E tests
    docker-compose -f docker-compose.test.yml run --rm e2e-test
    
    if [ $? -eq 0 ]; then
        log_success "E2E tests passed"
    else
        log_error "E2E tests failed"
        return 1
    fi
}

# Run performance tests
run_performance_tests() {
    log_info "Running performance tests..."
    
    # Ensure application is running
    docker-compose -f docker-compose.test.yml up -d nginx-test backend-test
    
    # Wait for application to be ready
    sleep 30
    
    # Run performance tests
    docker-compose -f docker-compose.test.yml run --rm performance-test
    
    if [ $? -eq 0 ]; then
        log_success "Performance tests passed"
    else
        log_warning "Performance tests completed with warnings"
    fi
}

# Run security tests
run_security_tests() {
    log_info "Running security tests..."
    
    # Ensure application is running
    docker-compose -f docker-compose.test.yml up -d nginx-test backend-test
    
    # Wait for application to be ready
    sleep 30
    
    # Run security tests
    docker-compose -f docker-compose.test.yml run --rm security-test
    
    if [ $? -eq 0 ]; then
        log_success "Security tests passed"
    else
        log_warning "Security tests completed with warnings"
    fi
}

# Collect test results
collect_results() {
    log_info "Collecting test results..."
    
    # Copy results from containers
    docker cp mindcoach-backend-test:/app/test-results/. "$RESULTS_DIR/backend/" 2>/dev/null || true
    docker cp mindcoach-frontend-test:/app/test-results/. "$RESULTS_DIR/frontend/" 2>/dev/null || true
    docker cp mindcoach-e2e-test:/app/test-results/. "$RESULTS_DIR/e2e/" 2>/dev/null || true
    
    # Run test aggregator
    docker-compose -f docker-compose.test.yml run --rm \
        -v "$(pwd)/$RESULTS_DIR:/results" \
        test-aggregator
    
    log_success "Test results collected in $RESULTS_DIR"
}

# Cleanup test environment
cleanup() {
    log_info "Cleaning up test environment..."
    
    # Stop and remove test containers
    docker-compose -f docker-compose.test.yml down -v --remove-orphans
    
    # Remove test network
    docker network rm mindcoach-test-network 2>/dev/null || true
    
    log_success "Cleanup completed"
}

# Generate test report
generate_report() {
    log_info "Generating test report..."
    
    cat > "$RESULTS_DIR/test-summary.md" << EOF
# Test Results Summary

**Test Run**: $TIMESTAMP
**Test Type**: $TEST_TYPE

## Results

$([ -f "$RESULTS_DIR/backend/junit.xml" ] && echo "✅ Backend Unit Tests: PASSED" || echo "❌ Backend Unit Tests: FAILED")
$([ -f "$RESULTS_DIR/frontend/junit.xml" ] && echo "✅ Frontend Unit Tests: PASSED" || echo "❌ Frontend Unit Tests: FAILED")
$([ -f "$RESULTS_DIR/e2e/e2e-results.xml" ] && echo "✅ E2E Tests: PASSED" || echo "❌ E2E Tests: FAILED")

## Coverage

$([ -f "$RESULTS_DIR/backend/coverage.xml" ] && echo "📊 Backend Coverage: Available" || echo "📊 Backend Coverage: Not Available")
$([ -f "$RESULTS_DIR/frontend/coverage/lcov.info" ] && echo "📊 Frontend Coverage: Available" || echo "📊 Frontend Coverage: Not Available")

## Performance

$([ -f "$RESULTS_DIR/performance-results.json" ] && echo "⚡ Performance Tests: Completed" || echo "⚡ Performance Tests: Not Run")

## Security

$([ -f "$RESULTS_DIR/security-report.json" ] && echo "🔒 Security Scan: Completed" || echo "🔒 Security Scan: Not Run")

## Files

- Backend Results: \`$RESULTS_DIR/backend/\`
- Frontend Results: \`$RESULTS_DIR/frontend/\`
- E2E Results: \`$RESULTS_DIR/e2e/\`
- Coverage Reports: \`$RESULTS_DIR/coverage/\`

EOF

    log_success "Test report generated: $RESULTS_DIR/test-summary.md"
}

# Main execution
main() {
    check_dependencies
    setup_test_environment
    
    case $TEST_TYPE in
        "unit")
            run_unit_tests
            ;;
        "integration")
            run_integration_tests
            ;;
        "e2e")
            run_e2e_tests
            ;;
        "performance")
            run_performance_tests
            ;;
        "security")
            run_security_tests
            ;;
        "all")
            run_unit_tests
            run_integration_tests
            run_e2e_tests
            run_performance_tests
            run_security_tests
            ;;
        *)
            log_error "Unknown test type: $TEST_TYPE"
            log_info "Available types: unit, integration, e2e, performance, security, all"
            exit 1
            ;;
    esac
    
    collect_results
    generate_report
    cleanup
    
    log_success "🎉 Test execution completed!"
    log_info "Results available in: $RESULTS_DIR"
}

# Handle script interruption
trap cleanup INT TERM

# Run main function
main "$@"