#!/bin/bash

# Container registry setup script
# Usage: ./scripts/setup-registry.sh [registry-type]

set -e

REGISTRY_TYPE=${1:-github}

echo "📦 Setting up container registry..."
echo "Registry Type: $REGISTRY_TYPE"

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

# Setup GitHub Container Registry
setup_github_registry() {
    log_info "Setting up GitHub Container Registry..."
    
    # Check if GitHub CLI is installed
    if ! command -v gh &> /dev/null; then
        log_warning "GitHub CLI not found. Please install it for easier setup."
        log_info "Manual setup instructions:"
        echo "1. Go to GitHub Settings > Developer settings > Personal access tokens"
        echo "2. Create a token with 'write:packages' and 'read:packages' permissions"
        echo "3. Login to registry: echo \$GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin"
        return
    fi
    
    # Check if user is logged in to GitHub CLI
    if ! gh auth status &> /dev/null; then
        log_info "Please login to GitHub CLI first:"
        echo "gh auth login"
        return
    fi
    
    # Get GitHub username
    GITHUB_USER=$(gh api user --jq .login)
    
    log_info "GitHub user: $GITHUB_USER"
    
    # Create .env file for registry configuration
    cat > .env.registry << EOF
# GitHub Container Registry Configuration
REGISTRY_URL=ghcr.io
REGISTRY_NAMESPACE=$GITHUB_USER
REGISTRY_USERNAME=$GITHUB_USER

# Image names
FRONTEND_IMAGE=ghcr.io/$GITHUB_USER/mindcoach-frontend
BACKEND_IMAGE=ghcr.io/$GITHUB_USER/mindcoach-backend
NGINX_IMAGE=ghcr.io/$GITHUB_USER/mindcoach-nginx
EOF
    
    log_success "GitHub Container Registry configuration created"
    log_info "Configuration saved to: .env.registry"
    
    # Test registry access
    log_info "Testing registry access..."
    if echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USER" --password-stdin 2>/dev/null; then
        log_success "Registry login successful"
    else
        log_warning "Registry login failed. Please set GITHUB_TOKEN environment variable"
        log_info "Create a token at: https://github.com/settings/tokens"
        log_info "Required permissions: write:packages, read:packages"
    fi
}

# Setup Docker Hub
setup_dockerhub_registry() {
    log_info "Setting up Docker Hub registry..."
    
    read -p "Enter your Docker Hub username: " DOCKERHUB_USER
    read -s -p "Enter your Docker Hub password or access token: " DOCKERHUB_PASSWORD
    echo
    
    # Test login
    if echo "$DOCKERHUB_PASSWORD" | docker login -u "$DOCKERHUB_USER" --password-stdin; then
        log_success "Docker Hub login successful"
    else
        log_error "Docker Hub login failed"
        return 1
    fi
    
    # Create .env file for registry configuration
    cat > .env.registry << EOF
# Docker Hub Registry Configuration
REGISTRY_URL=docker.io
REGISTRY_NAMESPACE=$DOCKERHUB_USER
REGISTRY_USERNAME=$DOCKERHUB_USER

# Image names
FRONTEND_IMAGE=$DOCKERHUB_USER/mindcoach-frontend
BACKEND_IMAGE=$DOCKERHUB_USER/mindcoach-backend
NGINX_IMAGE=$DOCKERHUB_USER/mindcoach-nginx
EOF
    
    log_success "Docker Hub registry configuration created"
}

# Setup AWS ECR
setup_aws_ecr() {
    log_info "Setting up AWS ECR registry..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is required but not installed"
        log_info "Install AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        return 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured"
        log_info "Configure AWS credentials: aws configure"
        return 1
    fi
    
    # Get AWS account ID and region
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    AWS_REGION=${AWS_DEFAULT_REGION:-us-east-1}
    
    log_info "AWS Account ID: $AWS_ACCOUNT_ID"
    log_info "AWS Region: $AWS_REGION"
    
    # Create ECR repositories
    log_info "Creating ECR repositories..."
    
    aws ecr create-repository --repository-name mindcoach-frontend --region "$AWS_REGION" 2>/dev/null || log_info "Frontend repository already exists"
    aws ecr create-repository --repository-name mindcoach-backend --region "$AWS_REGION" 2>/dev/null || log_info "Backend repository already exists"
    aws ecr create-repository --repository-name mindcoach-nginx --region "$AWS_REGION" 2>/dev/null || log_info "Nginx repository already exists"
    
    # Login to ECR
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
    
    # Create .env file for registry configuration
    cat > .env.registry << EOF
# AWS ECR Registry Configuration
REGISTRY_URL=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
REGISTRY_NAMESPACE=
REGISTRY_USERNAME=AWS
AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID
AWS_REGION=$AWS_REGION

# Image names
FRONTEND_IMAGE=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/mindcoach-frontend
BACKEND_IMAGE=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/mindcoach-backend
NGINX_IMAGE=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/mindcoach-nginx
EOF
    
    log_success "AWS ECR registry configuration created"
}

# Setup private registry
setup_private_registry() {
    log_info "Setting up private registry..."
    
    read -p "Enter registry URL (e.g., registry.company.com): " REGISTRY_URL
    read -p "Enter registry username: " REGISTRY_USERNAME
    read -s -p "Enter registry password: " REGISTRY_PASSWORD
    echo
    read -p "Enter namespace/organization (optional): " REGISTRY_NAMESPACE
    
    # Test login
    if echo "$REGISTRY_PASSWORD" | docker login "$REGISTRY_URL" -u "$REGISTRY_USERNAME" --password-stdin; then
        log_success "Private registry login successful"
    else
        log_error "Private registry login failed"
        return 1
    fi
    
    # Create .env file for registry configuration
    cat > .env.registry << EOF
# Private Registry Configuration
REGISTRY_URL=$REGISTRY_URL
REGISTRY_NAMESPACE=$REGISTRY_NAMESPACE
REGISTRY_USERNAME=$REGISTRY_USERNAME

# Image names
FRONTEND_IMAGE=$REGISTRY_URL${REGISTRY_NAMESPACE:+/$REGISTRY_NAMESPACE}/mindcoach-frontend
BACKEND_IMAGE=$REGISTRY_URL${REGISTRY_NAMESPACE:+/$REGISTRY_NAMESPACE}/mindcoach-backend
NGINX_IMAGE=$REGISTRY_URL${REGISTRY_NAMESPACE:+/$REGISTRY_NAMESPACE}/mindcoach-nginx
EOF
    
    log_success "Private registry configuration created"
}

# Create registry helper scripts
create_helper_scripts() {
    log_info "Creating registry helper scripts..."
    
    # Create push script
    cat > scripts/push-images.sh << 'EOF'
#!/bin/bash
# Push images to registry
set -e

source .env.registry 2>/dev/null || { echo "Registry configuration not found"; exit 1; }

TAG=${1:-latest}

echo "Pushing images to registry..."
echo "Frontend: $FRONTEND_IMAGE:$TAG"
echo "Backend: $BACKEND_IMAGE:$TAG"

docker push "$FRONTEND_IMAGE:$TAG"
docker push "$BACKEND_IMAGE:$TAG"

if [ -n "$NGINX_IMAGE" ]; then
    echo "Nginx: $NGINX_IMAGE:$TAG"
    docker push "$NGINX_IMAGE:$TAG"
fi

echo "All images pushed successfully!"
EOF
    
    # Create pull script
    cat > scripts/pull-images.sh << 'EOF'
#!/bin/bash
# Pull images from registry
set -e

source .env.registry 2>/dev/null || { echo "Registry configuration not found"; exit 1; }

TAG=${1:-latest}

echo "Pulling images from registry..."
echo "Frontend: $FRONTEND_IMAGE:$TAG"
echo "Backend: $BACKEND_IMAGE:$TAG"

docker pull "$FRONTEND_IMAGE:$TAG"
docker pull "$BACKEND_IMAGE:$TAG"

if [ -n "$NGINX_IMAGE" ]; then
    echo "Nginx: $NGINX_IMAGE:$TAG"
    docker pull "$NGINX_IMAGE:$TAG"
fi

echo "All images pulled successfully!"
EOF
    
    # Create cleanup script
    cat > scripts/cleanup-registry.sh << 'EOF'
#!/bin/bash
# Cleanup old images from registry
set -e

source .env.registry 2>/dev/null || { echo "Registry configuration not found"; exit 1; }

echo "Cleaning up local Docker images..."

# Remove dangling images
docker image prune -f

# Remove old versions (keep last 5)
docker images --format "table {{.Repository}}:{{.Tag}}" | grep mindcoach | tail -n +6 | while read image; do
    echo "Removing old image: $image"
    docker rmi "$image" 2>/dev/null || true
done

echo "Cleanup completed!"
EOF
    
    # Make scripts executable
    chmod +x scripts/push-images.sh scripts/pull-images.sh scripts/cleanup-registry.sh
    
    log_success "Helper scripts created"
}

# Create registry documentation
create_documentation() {
    log_info "Creating registry documentation..."
    
    cat > docs/REGISTRY_SETUP.md << EOF
# Container Registry Setup

This document describes how to set up and use the container registry for MindCoach.

## Configuration

The registry configuration is stored in \`.env.registry\` file:

\`\`\`bash
source .env.registry
echo "Registry URL: \$REGISTRY_URL"
echo "Frontend Image: \$FRONTEND_IMAGE"
echo "Backend Image: \$BACKEND_IMAGE"
\`\`\`

## Building and Pushing Images

### Build images locally
\`\`\`bash
./scripts/build-images.sh v1.0.0
\`\`\`

### Push to registry
\`\`\`bash
./scripts/push-images.sh v1.0.0
\`\`\`

### Pull from registry
\`\`\`bash
./scripts/pull-images.sh v1.0.0
\`\`\`

## Registry Types

### GitHub Container Registry (ghcr.io)
- Free for public repositories
- Integrated with GitHub Actions
- Requires GitHub personal access token

### Docker Hub
- Free tier available
- Most popular registry
- Easy to use

### AWS ECR
- Integrated with AWS services
- Pay-per-use pricing
- High availability

### Private Registry
- Full control over images
- Custom authentication
- On-premises or cloud-hosted

## CI/CD Integration

The registry is automatically used in GitHub Actions workflows:

\`\`\`yaml
- name: Build and push images
  run: |
    source .env.registry
    docker build -t \$FRONTEND_IMAGE:latest frontend/
    docker push \$FRONTEND_IMAGE:latest
\`\`\`

## Security Best Practices

1. Use specific image tags instead of \`latest\`
2. Scan images for vulnerabilities
3. Use minimal base images
4. Keep registry credentials secure
5. Regularly update base images

## Troubleshooting

### Login Issues
\`\`\`bash
# GitHub Container Registry
echo \$GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Docker Hub
docker login -u USERNAME

# AWS ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
\`\`\`

### Image Not Found
- Check image name and tag
- Verify registry permissions
- Ensure image was pushed successfully

### Push/Pull Failures
- Check network connectivity
- Verify authentication
- Check disk space
EOF
    
    log_success "Registry documentation created: docs/REGISTRY_SETUP.md"
}

# Main setup process
main() {
    case $REGISTRY_TYPE in
        "github"|"ghcr")
            setup_github_registry
            ;;
        "dockerhub"|"docker")
            setup_dockerhub_registry
            ;;
        "aws"|"ecr")
            setup_aws_ecr
            ;;
        "private")
            setup_private_registry
            ;;
        *)
            log_error "Unknown registry type: $REGISTRY_TYPE"
            log_info "Available types: github, dockerhub, aws, private"
            exit 1
            ;;
    esac
    
    create_helper_scripts
    create_documentation
    
    log_success "🎉 Container registry setup completed!"
    log_info "Configuration file: .env.registry"
    log_info "Helper scripts: scripts/push-images.sh, scripts/pull-images.sh"
    log_info "Documentation: docs/REGISTRY_SETUP.md"
}

# Run main function
main "$@"