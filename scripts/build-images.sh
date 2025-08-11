#!/bin/bash

# Container image build script
# Usage: ./scripts/build-images.sh [tag] [registry]

set -e

TAG=${1:-latest}
REGISTRY=${2:-ghcr.io/mindcoach}
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
GIT_COMMIT=$(git rev-parse --short HEAD)
VERSION=${TAG}

echo "🐳 Building container images..."
echo "Tag: $TAG"
echo "Registry: $REGISTRY"
echo "Build Date: $BUILD_DATE"
echo "Git Commit: $GIT_COMMIT"

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

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check if Docker Buildx is available
if ! docker buildx version &> /dev/null; then
    log_error "Docker Buildx is not available"
    exit 1
fi

# Create buildx builder if it doesn't exist
if ! docker buildx ls | grep -q "mindcoach-builder"; then
    log_info "Creating Docker Buildx builder..."
    docker buildx create --name mindcoach-builder --use
    docker buildx inspect --bootstrap
fi

# Build frontend image
log_info "Building frontend image..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --build-arg BUILD_DATE="$BUILD_DATE" \
    --build-arg GIT_COMMIT="$GIT_COMMIT" \
    --build-arg VERSION="$VERSION" \
    --tag "$REGISTRY/frontend:$TAG" \
    --tag "$REGISTRY/frontend:latest" \
    --file frontend/Dockerfile.prod \
    --push \
    frontend/

if [ $? -eq 0 ]; then
    log_success "Frontend image built successfully"
else
    log_error "Frontend image build failed"
    exit 1
fi

# Build backend image
log_info "Building backend image..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --build-arg BUILD_DATE="$BUILD_DATE" \
    --build-arg GIT_COMMIT="$GIT_COMMIT" \
    --build-arg VERSION="$VERSION" \
    --tag "$REGISTRY/backend:$TAG" \
    --tag "$REGISTRY/backend:latest" \
    --file backend/Dockerfile.prod \
    --push \
    backend/

if [ $? -eq 0 ]; then
    log_success "Backend image built successfully"
else
    log_error "Backend image build failed"
    exit 1
fi

# Build nginx image (if custom configuration exists)
if [ -f "nginx/Dockerfile" ]; then
    log_info "Building nginx image..."
    docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --build-arg BUILD_DATE="$BUILD_DATE" \
        --build-arg GIT_COMMIT="$GIT_COMMIT" \
        --build-arg VERSION="$VERSION" \
        --tag "$REGISTRY/nginx:$TAG" \
        --tag "$REGISTRY/nginx:latest" \
        --file nginx/Dockerfile \
        --push \
        nginx/
    
    if [ $? -eq 0 ]; then
        log_success "Nginx image built successfully"
    else
        log_error "Nginx image build failed"
        exit 1
    fi
fi

# Generate image manifest
log_info "Generating image manifest..."
cat > image-manifest.json << EOF
{
  "build_info": {
    "build_date": "$BUILD_DATE",
    "git_commit": "$GIT_COMMIT",
    "version": "$VERSION",
    "tag": "$TAG"
  },
  "images": {
    "frontend": "$REGISTRY/frontend:$TAG",
    "backend": "$REGISTRY/backend:$TAG"$([ -f "nginx/Dockerfile" ] && echo ",
    \"nginx\": \"$REGISTRY/nginx:$TAG\"")
  },
  "platforms": [
    "linux/amd64",
    "linux/arm64"
  ]
}
EOF

log_success "Image manifest generated: image-manifest.json"

# Security scan (if trivy is available)
if command -v trivy &> /dev/null; then
    log_info "Running security scans..."
    
    trivy image --exit-code 1 --severity HIGH,CRITICAL "$REGISTRY/frontend:$TAG" || log_warning "Frontend image has security vulnerabilities"
    trivy image --exit-code 1 --severity HIGH,CRITICAL "$REGISTRY/backend:$TAG" || log_warning "Backend image has security vulnerabilities"
else
    log_warning "Trivy not found, skipping security scan"
fi

# Test images
log_info "Testing images..."

# Test frontend image
docker run --rm -d --name test-frontend -p 8080:80 "$REGISTRY/frontend:$TAG"
sleep 5
if curl -f http://localhost:8080 > /dev/null 2>&1; then
    log_success "Frontend image test passed"
else
    log_error "Frontend image test failed"
fi
docker stop test-frontend

# Test backend image
docker run --rm -d --name test-backend -p 8081:5000 -e SECRET_KEY=test "$REGISTRY/backend:$TAG"
sleep 10
if curl -f http://localhost:8081/api/health > /dev/null 2>&1; then
    log_success "Backend image test passed"
else
    log_error "Backend image test failed"
fi
docker stop test-backend

log_success "🎉 All images built and tested successfully!"

echo ""
log_info "Image details:"
echo "Frontend: $REGISTRY/frontend:$TAG"
echo "Backend: $REGISTRY/backend:$TAG"
if [ -f "nginx/Dockerfile" ]; then
    echo "Nginx: $REGISTRY/nginx:$TAG"
fi
echo ""
log_info "To deploy these images:"
echo "export FRONTEND_IMAGE=$REGISTRY/frontend:$TAG"
echo "export BACKEND_IMAGE=$REGISTRY/backend:$TAG"
echo "docker-compose -f docker-compose.prod.yml up -d"