# Docker Security Guidelines for Production Deployment

## Overview

This guide provides comprehensive security guidelines for deploying the MindCoach application in production using Docker containers. It covers container security, network security, secrets management, and compliance requirements.

## Table of Contents

1. [Container Security](#container-security)
2. [Image Security](#image-security)
3. [Network Security](#network-security)
4. [Secrets Management](#secrets-management)
5. [Access Control](#access-control)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Compliance and Auditing](#compliance-and-auditing)
8. [Security Automation](#security-automation)
9. [Incident Response](#incident-response)
10. [Best Practices](#best-practices)

## Container Security

### Non-Root User Configuration

```dockerfile
# Dockerfile.secure
FROM python:3.11-slim

# Create non-root user and group
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Install dependencies as root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and set ownership
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser

# Expose port (non-privileged)
EXPOSE 8000

CMD ["python", "run.py"]
```

### Container Runtime Security

```yaml
# docker-compose.secure.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.secure
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Only if needed for port binding
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
      - /var/run:noexec,nosuid,size=50m
    ulimits:
      nproc: 65535
      nofile:
        soft: 65535
        hard: 65535
    sysctls:
      - net.core.somaxconn=1024
    user: "1001:1001"
    environment:
      - PYTHONDONTWRITEBYTECODE=1
      - PYTHONUNBUFFERED=1
    volumes:
      - ./data:/app/data:rw,noexec,nosuid
      - ./logs:/app/logs:rw,noexec,nosuid
```

### Resource Limits and Constraints

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
          pids: 100
        reservations:
          cpus: '1.0'
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Container Isolation

```bash
#!/bin/bash
# setup-container-isolation.sh

# Enable user namespaces
echo 'kernel.unprivileged_userns_clone=1' >> /etc/sysctl.conf
sysctl -p

# Configure Docker daemon for user namespaces
cat > /etc/docker/daemon.json << EOF
{
  "userns-remap": "default",
  "live-restore": true,
  "userland-proxy": false,
  "no-new-privileges": true,
  "seccomp-profile": "/etc/docker/seccomp-profile.json"
}
EOF

# Restart Docker daemon
systemctl restart docker
```

## Image Security

### Secure Base Images

```dockerfile
# Use minimal, security-focused base images
FROM python:3.11-slim-bullseye

# Update package lists and install security updates
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Verify package signatures
RUN apt-get update && \
    apt-get install -y --no-install-recommends gnupg && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys <KEY_ID>
```

### Image Scanning and Vulnerability Management

```bash
#!/bin/bash
# scan-images.sh

set -e

IMAGES=(
    "mindcoach/backend:latest"
    "mindcoach/frontend:latest"
    "postgres:15-alpine"
    "redis:7-alpine"
    "nginx:alpine"
)

echo "Starting security scan of Docker images..."

for IMAGE in "${IMAGES[@]}"; do
    echo "Scanning image: $IMAGE"
    
    # Trivy scan
    trivy image --severity HIGH,CRITICAL --exit-code 1 "$IMAGE"
    
    # Docker Scout scan (if available)
    docker scout cves "$IMAGE" || echo "Docker Scout not available"
    
    # Snyk scan (if available)
    snyk container test "$IMAGE" || echo "Snyk not available"
    
    echo "Scan completed for: $IMAGE"
done

echo "All image scans completed"
```

### Image Signing and Verification

```bash
#!/bin/bash
# sign-images.sh

set -e

# Enable Docker Content Trust
export DOCKER_CONTENT_TRUST=1
export DOCKER_CONTENT_TRUST_SERVER=https://notary.docker.io

# Generate signing keys
docker trust key generate mindcoach-signer

# Sign and push images
docker trust sign mindcoach/backend:latest
docker trust sign mindcoach/frontend:latest

# Verify signatures
docker trust inspect --pretty mindcoach/backend:latest
docker trust inspect --pretty mindcoach/frontend:latest

echo "Image signing completed"
```

### Dockerfile Security Best Practices

```dockerfile
# Secure Dockerfile template
FROM python:3.11-slim-bullseye as builder

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim-bullseye

# Create non-root user
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

# Install runtime dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/* \
        && rm -rf /tmp/* \
        && rm -rf /var/tmp/*

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appgroup . .

# Remove sensitive files
RUN find . -name "*.pyc" -delete && \
    find . -name "__pycache__" -type d -exec rm -rf {} + && \
    rm -rf .git .gitignore .env* *.md

# Switch to non-root user
USER appuser

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "run.py"]
```

## Network Security

### Network Segmentation

```yaml
# docker-compose.network-security.yml
version: '3.8'

networks:
  frontend-network:
    driver: bridge
    internal: false
    ipam:
      config:
        - subnet: 172.20.0.0/24
  backend-network:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.21.0.0/24
  database-network:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.22.0.0/24

services:
  nginx:
    image: nginx:alpine
    networks:
      - frontend-network
    ports:
      - "80:80"
      - "443:443"
    
  backend:
    build: ./backend
    networks:
      - frontend-network
      - backend-network
    expose:
      - "8000"
    
  postgres:
    image: postgres:15-alpine
    networks:
      - database-network
    expose:
      - "5432"
    
  redis:
    image: redis:7-alpine
    networks:
      - backend-network
    expose:
      - "6379"
```

### SSL/TLS Configuration

```nginx
# nginx/ssl.conf
server {
    listen 443 ssl http2;
    server_name mindcoach.com;
    
    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_dhparam /etc/nginx/ssl/dhparam.pem;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Security Headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';" always;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/nginx/ssl/chain.pem;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    
    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Security headers for proxied requests
        proxy_hide_header X-Powered-By;
        proxy_hide_header Server;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name mindcoach.com;
    return 301 https://$server_name$request_uri;
}
```

### Firewall Configuration

```bash
#!/bin/bash
# setup-firewall.sh

set -e

echo "Configuring firewall for Docker containers..."

# Enable UFW
ufw --force enable

# Default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (adjust port as needed)
ufw allow 22/tcp

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow Docker daemon (if remote access needed)
# ufw allow 2376/tcp

# Docker-specific rules
# Allow Docker containers to communicate
ufw allow in on docker0
ufw allow out on docker0

# Allow container-to-container communication
ufw allow in on br-+
ufw allow out on br-+

# Block direct access to container ports
ufw deny 5432/tcp  # PostgreSQL
ufw deny 6379/tcp  # Redis
ufw deny 8000/tcp  # Backend (should go through nginx)

# Log dropped packets
ufw logging on

echo "Firewall configuration completed"
```

## Secrets Management### Doc
ker Secrets

```yaml
# docker-compose.secrets.yml
version: '3.8'

secrets:
  db_password:
    external: true
  api_key:
    external: true
  ssl_cert:
    external: true
  ssl_key:
    external: true

services:
  backend:
    image: mindcoach/backend:latest
    secrets:
      - db_password
      - api_key
    environment:
      - DATABASE_PASSWORD_FILE=/run/secrets/db_password
      - API_KEY_FILE=/run/secrets/api_key
    
  postgres:
    image: postgres:15-alpine
    secrets:
      - db_password
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
    
  nginx:
    image: nginx:alpine
    secrets:
      - ssl_cert
      - ssl_key
    volumes:
      - type: bind
        source: /run/secrets/ssl_cert
        target: /etc/nginx/ssl/cert.pem
        read_only: true
      - type: bind
        source: /run/secrets/ssl_key
        target: /etc/nginx/ssl/key.pem
        read_only: true
```

```bash
#!/bin/bash
# manage-secrets.sh

set -e

ACTION=${1:-create}
SECRET_NAME=$2
SECRET_VALUE=$3

case $ACTION in
    "create")
        if [ -z "$SECRET_NAME" ] || [ -z "$SECRET_VALUE" ]; then
            echo "Usage: $0 create <secret_name> <secret_value>"
            exit 1
        fi
        
        echo "$SECRET_VALUE" | docker secret create "$SECRET_NAME" -
        echo "Secret created: $SECRET_NAME"
        ;;
        
    "update")
        if [ -z "$SECRET_NAME" ] || [ -z "$SECRET_VALUE" ]; then
            echo "Usage: $0 update <secret_name> <secret_value>"
            exit 1
        fi
        
        # Remove old secret
        docker secret rm "$SECRET_NAME" || true
        
        # Create new secret
        echo "$SECRET_VALUE" | docker secret create "$SECRET_NAME" -
        echo "Secret updated: $SECRET_NAME"
        ;;
        
    "list")
        docker secret ls
        ;;
        
    "remove")
        if [ -z "$SECRET_NAME" ]; then
            echo "Usage: $0 remove <secret_name>"
            exit 1
        fi
        
        docker secret rm "$SECRET_NAME"
        echo "Secret removed: $SECRET_NAME"
        ;;
        
    *)
        echo "Usage: $0 {create|update|list|remove} [secret_name] [secret_value]"
        exit 1
        ;;
esac
```

### External Secret Management

```python
# secrets_manager.py
import os
import boto3
import hvac
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

class SecretsManager:
    def __init__(self, provider='aws'):
        self.provider = provider
        self._init_client()
    
    def _init_client(self):
        if self.provider == 'aws':
            self.client = boto3.client('secretsmanager')
        elif self.provider == 'vault':
            self.client = hvac.Client(url=os.getenv('VAULT_URL'))
            self.client.token = os.getenv('VAULT_TOKEN')
        elif self.provider == 'azure':
            credential = DefaultAzureCredential()
            vault_url = os.getenv('AZURE_VAULT_URL')
            self.client = SecretClient(vault_url=vault_url, credential=credential)
    
    def get_secret(self, secret_name):
        try:
            if self.provider == 'aws':
                response = self.client.get_secret_value(SecretId=secret_name)
                return response['SecretString']
            elif self.provider == 'vault':
                response = self.client.secrets.kv.v2.read_secret_version(path=secret_name)
                return response['data']['data']
            elif self.provider == 'azure':
                secret = self.client.get_secret(secret_name)
                return secret.value
        except Exception as e:
            raise Exception(f"Failed to retrieve secret {secret_name}: {e}")
    
    def set_secret(self, secret_name, secret_value):
        try:
            if self.provider == 'aws':
                self.client.create_secret(Name=secret_name, SecretString=secret_value)
            elif self.provider == 'vault':
                self.client.secrets.kv.v2.create_or_update_secret(
                    path=secret_name, 
                    secret={'value': secret_value}
                )
            elif self.provider == 'azure':
                self.client.set_secret(secret_name, secret_value)
        except Exception as e:
            raise Exception(f"Failed to set secret {secret_name}: {e}")

# Usage in application
def load_secrets():
    secrets_manager = SecretsManager(provider=os.getenv('SECRETS_PROVIDER', 'aws'))
    
    return {
        'database_password': secrets_manager.get_secret('mindcoach/db/password'),
        'api_key': secrets_manager.get_secret('mindcoach/api/key'),
        'jwt_secret': secrets_manager.get_secret('mindcoach/jwt/secret')
    }
```

### Environment Variable Security

```bash
#!/bin/bash
# secure-env-setup.sh

set -e

ENV_FILE=".env.secure"
TEMPLATE_FILE=".env.template"

echo "Setting up secure environment variables..."

# Create template if it doesn't exist
if [ ! -f "$TEMPLATE_FILE" ]; then
    cat > "$TEMPLATE_FILE" << EOF
# Database Configuration
DATABASE_URL=postgresql://user:PASSWORD_PLACEHOLDER@postgres:5432/mindcoach
POSTGRES_PASSWORD=PASSWORD_PLACEHOLDER

# API Keys
XAI_API_KEY=API_KEY_PLACEHOLDER
JWT_SECRET_KEY=JWT_SECRET_PLACEHOLDER

# Security
SECRET_KEY=SECRET_KEY_PLACEHOLDER
ENCRYPTION_KEY=ENCRYPTION_KEY_PLACEHOLDER

# External Services
REDIS_URL=redis://redis:6379/0
CORS_ORIGINS=https://mindcoach.com
EOF
fi

# Generate secure environment file
cp "$TEMPLATE_FILE" "$ENV_FILE"

# Generate secure passwords and keys
DB_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 64)
SECRET_KEY=$(openssl rand -base64 32)
ENCRYPTION_KEY=$(openssl rand -base64 32)

# Replace placeholders
sed -i "s/PASSWORD_PLACEHOLDER/$DB_PASSWORD/g" "$ENV_FILE"
sed -i "s/JWT_SECRET_PLACEHOLDER/$JWT_SECRET/g" "$ENV_FILE"
sed -i "s/SECRET_KEY_PLACEHOLDER/$SECRET_KEY/g" "$ENV_FILE"
sed -i "s/ENCRYPTION_KEY_PLACEHOLDER/$ENCRYPTION_KEY/g" "$ENV_FILE"

# Set secure permissions
chmod 600 "$ENV_FILE"

echo "Secure environment file created: $ENV_FILE"
echo "Please update API_KEY_PLACEHOLDER with your actual API key"
```

## Access Control

### Role-Based Access Control (RBAC)

```python
# rbac.py
from functools import wraps
from flask import request, jsonify, g
import jwt

class Role:
    ADMIN = 'admin'
    USER = 'user'
    READONLY = 'readonly'

class Permission:
    READ = 'read'
    WRITE = 'write'
    DELETE = 'delete'
    ADMIN = 'admin'

ROLE_PERMISSIONS = {
    Role.ADMIN: [Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN],
    Role.USER: [Permission.READ, Permission.WRITE],
    Role.READONLY: [Permission.READ]
}

def require_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user from JWT token
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            
            try:
                payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
                user_role = payload.get('role', Role.READONLY)
                
                # Check if user has required permission
                if permission not in ROLE_PERMISSIONS.get(user_role, []):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                g.current_user = payload
                return f(*args, **kwargs)
                
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid token'}), 401
                
        return decorated_function
    return decorator

# Usage
@app.route('/api/admin/users')
@require_permission(Permission.ADMIN)
def admin_users():
    return jsonify({'users': get_all_users()})

@app.route('/api/users/<user_id>')
@require_permission(Permission.READ)
def get_user(user_id):
    return jsonify({'user': get_user_by_id(user_id)})
```

### Container Access Control

```yaml
# docker-compose.access-control.yml
version: '3.8'

services:
  backend:
    image: mindcoach/backend:latest
    user: "1001:1001"
    security_opt:
      - no-new-privileges:true
      - seccomp:unconfined  # Only if needed, prefer default seccomp profile
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Only if binding to privileged ports
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
    volumes:
      - ./data:/app/data:rw,noexec,nosuid
      - ./logs:/app/logs:rw,noexec,nosuid
    environment:
      - DOCKER_USER=appuser
      - DOCKER_GROUP=appgroup
```

### API Authentication and Authorization

```python
# auth.py
import jwt
import bcrypt
from datetime import datetime, timedelta
from flask import request, jsonify, current_app

class AuthManager:
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        app.config.setdefault('JWT_SECRET_KEY', 'your-secret-key')
        app.config.setdefault('JWT_EXPIRATION_DELTA', timedelta(hours=24))
        app.config.setdefault('JWT_ALGORITHM', 'HS256')
    
    def hash_password(self, password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    def verify_password(self, password, hashed):
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    
    def generate_token(self, user_id, role='user'):
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.utcnow() + current_app.config['JWT_EXPIRATION_DELTA'],
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config['JWT_ALGORITHM']
        )
    
    def verify_token(self, token):
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=[current_app.config['JWT_ALGORITHM']]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception('Token has expired')
        except jwt.InvalidTokenError:
            raise Exception('Invalid token')

# Middleware for token validation
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401
        
        try:
            token = auth_header.split(' ')[1]  # Bearer <token>
            auth_manager = AuthManager()
            payload = auth_manager.verify_token(token)
            g.current_user = payload
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': str(e)}), 401
    
    return decorated_function
```

## Monitoring and Logging

### Security Event Logging

```python
# security_logger.py
import logging
import json
from datetime import datetime
from flask import request, g

class SecurityLogger:
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        # Configure security logger
        security_logger = logging.getLogger('security')
        security_logger.setLevel(logging.INFO)
        
        # File handler for security events
        handler = logging.FileHandler('/var/log/mindcoach/security.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        security_logger.addHandler(handler)
        
        self.logger = security_logger
    
    def log_auth_attempt(self, user_id, success, ip_address, user_agent):
        event = {
            'event_type': 'authentication',
            'user_id': user_id,
            'success': success,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, json.dumps(event))
    
    def log_access_attempt(self, user_id, resource, action, success):
        event = {
            'event_type': 'access_control',
            'user_id': user_id,
            'resource': resource,
            'action': action,
            'success': success,
            'ip_address': request.remote_addr,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, json.dumps(event))
    
    def log_security_event(self, event_type, details):
        event = {
            'event_type': event_type,
            'details': details,
            'ip_address': request.remote_addr,
            'user_id': getattr(g, 'current_user', {}).get('user_id'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.logger.warning(json.dumps(event))

# Usage
security_logger = SecurityLogger()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user_id = data.get('user_id')
    password = data.get('password')
    
    # Authenticate user
    user = authenticate_user(user_id, password)
    
    # Log authentication attempt
    security_logger.log_auth_attempt(
        user_id=user_id,
        success=user is not None,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    
    if user:
        token = generate_token(user_id)
        return jsonify({'token': token})
    else:
        return jsonify({'error': 'Invalid credentials'}), 401
```

### Container Security Monitoring

```bash
#!/bin/bash
# security-monitor.sh

set -e

LOG_FILE="/var/log/mindcoach/security-monitor.log"
ALERT_EMAIL="security@mindcoach.com"

echo "$(date): Starting security monitoring" >> "$LOG_FILE"

# Monitor for privilege escalation attempts
check_privilege_escalation() {
    # Check for containers running as root
    ROOT_CONTAINERS=$(docker ps --format "table {{.Names}}\t{{.Image}}" --filter "label=com.docker.compose.project=mindcoach" | \
        while read name image; do
            if [ "$name" != "NAMES" ]; then
                user=$(docker inspect --format='{{.Config.User}}' "$name" 2>/dev/null || echo "root")
                if [ "$user" = "root" ] || [ -z "$user" ]; then
                    echo "$name"
                fi
            fi
        done)
    
    if [ -n "$ROOT_CONTAINERS" ]; then
        echo "$(date): SECURITY ALERT - Containers running as root: $ROOT_CONTAINERS" >> "$LOG_FILE"
        echo "Containers running as root detected: $ROOT_CONTAINERS" | \
        mail -s "Security Alert: Root Containers" "$ALERT_EMAIL"
    fi
}

# Monitor for suspicious network activity
check_network_activity() {
    # Check for unexpected port bindings
    EXPOSED_PORTS=$(docker ps --format "table {{.Names}}\t{{.Ports}}" --filter "label=com.docker.compose.project=mindcoach" | \
        grep -E "0\.0\.0\.0:[0-9]+" | grep -v ":80\|:443\|:22" || true)
    
    if [ -n "$EXPOSED_PORTS" ]; then
        echo "$(date): SECURITY ALERT - Unexpected exposed ports: $EXPOSED_PORTS" >> "$LOG_FILE"
        echo "Unexpected exposed ports detected: $EXPOSED_PORTS" | \
        mail -s "Security Alert: Exposed Ports" "$ALERT_EMAIL"
    fi
}

# Monitor for container escapes
check_container_escapes() {
    # Check for containers with privileged mode
    PRIVILEGED_CONTAINERS=$(docker ps --format "table {{.Names}}" --filter "label=com.docker.compose.project=mindcoach" | \
        while read name; do
            if [ "$name" != "NAMES" ]; then
                privileged=$(docker inspect --format='{{.HostConfig.Privileged}}' "$name" 2>/dev/null || echo "false")
                if [ "$privileged" = "true" ]; then
                    echo "$name"
                fi
            fi
        done)
    
    if [ -n "$PRIVILEGED_CONTAINERS" ]; then
        echo "$(date): SECURITY ALERT - Privileged containers detected: $PRIVILEGED_CONTAINERS" >> "$LOG_FILE"
        echo "Privileged containers detected: $PRIVILEGED_CONTAINERS" | \
        mail -s "Security Alert: Privileged Containers" "$ALERT_EMAIL"
    fi
}

# Monitor for resource abuse
check_resource_abuse() {
    # Check for containers using excessive resources
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemPerc}}" | \
    while read container cpu mem; do
        if [ "$container" != "CONTAINER" ]; then
            cpu_num=$(echo "$cpu" | sed 's/%//')
            mem_num=$(echo "$mem" | sed 's/%//')
            
            if (( $(echo "$cpu_num > 90" | bc -l) )) || (( $(echo "$mem_num > 90" | bc -l) )); then
                echo "$(date): SECURITY ALERT - High resource usage: $container (CPU: $cpu, Memory: $mem)" >> "$LOG_FILE"
            fi
        fi
    done
}

# Run security checks
check_privilege_escalation
check_network_activity
check_container_escapes
check_resource_abuse

echo "$(date): Security monitoring completed" >> "$LOG_FILE"
```

### Log Analysis and SIEM Integration

```python
# siem_integration.py
import json
import requests
from datetime import datetime

class SIEMIntegration:
    def __init__(self, siem_endpoint, api_key):
        self.siem_endpoint = siem_endpoint
        self.api_key = api_key
    
    def send_security_event(self, event_type, severity, details):
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'mindcoach-docker',
            'event_type': event_type,
            'severity': severity,
            'details': details,
            'host': os.uname().nodename
        }
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                self.siem_endpoint,
                json=event,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"Failed to send event to SIEM: {e}")
    
    def send_authentication_event(self, user_id, success, ip_address):
        self.send_security_event(
            event_type='authentication',
            severity='medium' if not success else 'low',
            details={
                'user_id': user_id,
                'success': success,
                'ip_address': ip_address
            }
        )
    
    def send_access_violation(self, user_id, resource, action):
        self.send_security_event(
            event_type='access_violation',
            severity='high',
            details={
                'user_id': user_id,
                'resource': resource,
                'action': action
            }
        )

# Usage
siem = SIEMIntegration(
    siem_endpoint=os.getenv('SIEM_ENDPOINT'),
    api_key=os.getenv('SIEM_API_KEY')
)

# Send events to SIEM
siem.send_authentication_event('user123', False, '192.168.1.100')
siem.send_access_violation('user456', '/admin/users', 'DELETE')
```

## Best Practices

### Security Checklist

```bash
#!/bin/bash
# security-checklist.sh

echo "=== Docker Security Checklist ==="

# Container Security
echo "1. Container Security:"
echo "   - Non-root user: $(docker inspect mindcoach_backend_1 --format='{{.Config.User}}' 2>/dev/null || echo 'NOT SET')"
echo "   - Read-only filesystem: $(docker inspect mindcoach_backend_1 --format='{{.HostConfig.ReadonlyRootfs}}' 2>/dev/null || echo 'NOT SET')"
echo "   - No new privileges: $(docker inspect mindcoach_backend_1 --format='{{.HostConfig.SecurityOpt}}' 2>/dev/null | grep -o 'no-new-privileges' || echo 'NOT SET')"

# Image Security
echo "2. Image Security:"
echo "   - Base image updates: $(docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}' | grep -E 'python|postgres|redis|nginx')"

# Network Security
echo "3. Network Security:"
echo "   - Internal networks: $(docker network ls --filter driver=bridge --format '{{.Name}}' | grep -v bridge)"
echo "   - Exposed ports: $(docker ps --format 'table {{.Names}}\t{{.Ports}}' | grep '0.0.0.0')"

# Secrets Management
echo "4. Secrets Management:"
echo "   - Docker secrets: $(docker secret ls --format '{{.Name}}' 2>/dev/null || echo 'NOT CONFIGURED')"
echo "   - Environment files: $(ls -la .env* 2>/dev/null | awk '{print $1, $9}' || echo 'NOT FOUND')"

# Access Control
echo "5. Access Control:"
echo "   - Container capabilities: $(docker inspect mindcoach_backend_1 --format='{{.HostConfig.CapDrop}}' 2>/dev/null || echo 'NOT SET')"

echo "=== Security Checklist Complete ==="
```

### Automated Security Testing

```bash
#!/bin/bash
# security-tests.sh

set -e

echo "Starting automated security tests..."

# Test 1: Container privilege escalation
test_privilege_escalation() {
    echo "Testing privilege escalation protection..."
    
    # Try to escalate privileges in container
    if docker exec mindcoach_backend_1 sudo whoami 2>/dev/null; then
        echo "FAIL: Privilege escalation possible"
        return 1
    else
        echo "PASS: Privilege escalation blocked"
        return 0
    fi
}

# Test 2: File system write protection
test_filesystem_protection() {
    echo "Testing filesystem write protection..."
    
    # Try to write to read-only filesystem
    if docker exec mindcoach_backend_1 touch /test_file 2>/dev/null; then
        echo "FAIL: Filesystem is writable"
        return 1
    else
        echo "PASS: Filesystem is read-only"
        return 0
    fi
}

# Test 3: Network isolation
test_network_isolation() {
    echo "Testing network isolation..."
    
    # Try to access external network from internal container
    if docker exec mindcoach_postgres_1 curl -m 5 google.com 2>/dev/null; then
        echo "FAIL: External network access from internal container"
        return 1
    else
        echo "PASS: Network isolation working"
        return 0
    fi
}

# Test 4: Secret exposure
test_secret_exposure() {
    echo "Testing secret exposure..."
    
    # Check if secrets are exposed in environment
    if docker exec mindcoach_backend_1 env | grep -i "password\|secret\|key" | grep -v "_FILE"; then
        echo "FAIL: Secrets exposed in environment"
        return 1
    else
        echo "PASS: Secrets not exposed"
        return 0
    fi
}

# Run all tests
TESTS=(
    "test_privilege_escalation"
    "test_filesystem_protection"
    "test_network_isolation"
    "test_secret_exposure"
)

PASSED=0
TOTAL=${#TESTS[@]}

for test in "${TESTS[@]}"; do
    if $test; then
        PASSED=$((PASSED + 1))
    fi
done

echo "Security tests completed: $PASSED/$TOTAL passed"

if [ $PASSED -eq $TOTAL ]; then
    echo "All security tests passed!"
    exit 0
else
    echo "Some security tests failed!"
    exit 1
fi
```

---

This security guide provides comprehensive guidelines for securing the MindCoach Docker deployment. Regular review and updates of security practices ensure protection against evolving threats.