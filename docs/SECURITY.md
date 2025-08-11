# Security Best Practices

This document outlines security best practices, implementation guidelines, and compliance requirements for MindCoach.

## Security Overview

MindCoach implements a comprehensive security strategy covering:

- **Application Security**: Secure coding practices and vulnerability prevention
- **Infrastructure Security**: Container and deployment security
- **Data Protection**: User data privacy and encryption
- **Access Control**: Authentication and authorization
- **Monitoring**: Security monitoring and incident response

## Security Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │  Load Balancer  │    │    Backend      │
│   (React)       │    │   (HAProxy)     │    │   (Flask)       │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • HTTPS Only    │    │ • SSL/TLS       │    │ • Input Valid.  │
│ • CSP Headers   │    │ • Rate Limiting │    │ • SQL Injection │
│ • XSS Protection│    │ • DDoS Protect. │    │ • CSRF Tokens   │
│ • Secure Cookies│    │ • Security Hdrs │    │ • Auth/Authz    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Database      │
                    │ (PostgreSQL)    │
                    ├─────────────────┤
                    │ • Encryption    │
                    │ • Access Control│
                    │ • Audit Logging │
                    │ • Backup Encrypt│
                    └─────────────────┘
```

## Application Security

### Input Validation

**Backend Validation** (Flask/Marshmallow):
```python
from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    user_id = fields.Str(
        required=True,
        validate=validate.Regexp(r'^[a-zA-Z0-9_-]+$'),
        error_messages={'invalid': 'Invalid user ID format'}
    )
    email = fields.Email(required=True)
    subject = fields.Str(
        required=True,
        validate=validate.OneOf(['python', 'javascript', 'react', 'nodejs'])
    )
```

**Frontend Validation** (React):
```javascript
const validateInput = (input) => {
  // Sanitize HTML
  const sanitized = DOMPurify.sanitize(input);
  
  // Validate format
  const isValid = /^[a-zA-Z0-9\s\-_]+$/.test(sanitized);
  
  return { sanitized, isValid };
};
```

### SQL Injection Prevention

**Parameterized Queries**:
```python
# SQLAlchemy ORM (Safe)
user = User.query.filter_by(user_id=user_id).first()

# Raw SQL with parameters (Safe)
result = db.session.execute(
    text("SELECT * FROM users WHERE user_id = :user_id"),
    {"user_id": user_id}
)

# NEVER do this (Vulnerable)
# query = f"SELECT * FROM users WHERE user_id = '{user_id}'"
```

### Cross-Site Scripting (XSS) Prevention

**Content Security Policy**:
```javascript
// CSP Header
app.use((req, res, next) => {
  res.setHeader(
    'Content-Security-Policy',
    "default-src 'self'; " +
    "script-src 'self' 'unsafe-inline'; " +
    "style-src 'self' 'unsafe-inline'; " +
    "img-src 'self' data: https:; " +
    "connect-src 'self' https://api.x.ai;"
  );
  next();
});
```

**Output Encoding**:
```javascript
// React automatically escapes content
const UserContent = ({ content }) => (
  <div>{content}</div> // Automatically escaped
);

// For HTML content, use DOMPurify
import DOMPurify from 'dompurify';

const SafeHTML = ({ html }) => (
  <div dangerouslySetInnerHTML={{
    __html: DOMPurify.sanitize(html)
  }} />
);
```

### Cross-Site Request Forgery (CSRF) Prevention

**CSRF Tokens**:
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

@app.route('/api/users', methods=['POST'])
@csrf.exempt  # For API endpoints, use other protection
def create_user():
    # Verify origin header
    origin = request.headers.get('Origin')
    if origin not in app.config['ALLOWED_ORIGINS']:
        abort(403)
    
    # Process request
    pass
```

**SameSite Cookies**:
```python
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)
```

## Authentication and Authorization

### Session Management

**Secure Session Configuration**:
```python
import secrets

app.config.update(
    SECRET_KEY=secrets.token_urlsafe(32),
    SESSION_COOKIE_SECURE=True,      # HTTPS only
    SESSION_COOKIE_HTTPONLY=True,    # No JavaScript access
    SESSION_COOKIE_SAMESITE='Lax',   # CSRF protection
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24)
)
```

**Redis Session Store**:
```python
from backend.app.services.session_service import SessionService

session_service = SessionService()

# Create secure session
session_id = session_service.create_session(
    user_id=user_id,
    data={'role': 'user', 'permissions': ['read', 'write']}
)

# Validate session
session_data = session_service.get_session(session_id)
if not session_data:
    abort(401, 'Invalid session')
```

### API Authentication

**API Key Management**:
```python
import hashlib
import hmac

def verify_api_key(api_key, signature, payload):
    """Verify API key signature"""
    expected_signature = hmac.new(
        api_key.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)
```

**Rate Limiting**:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/users', methods=['POST'])
@limiter.limit("5 per minute")
def create_user():
    pass
```

## Data Protection

### Encryption at Rest

**Database Encryption**:
```sql
-- PostgreSQL encryption
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    email_encrypted BYTEA,  -- Encrypted email
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Application-level encryption
INSERT INTO users (user_id, email_encrypted) 
VALUES ($1, pgp_sym_encrypt($2, $3));
```

**File System Encryption**:
```python
from cryptography.fernet import Fernet

class FileEncryption:
    def __init__(self, key):
        self.cipher = Fernet(key)
    
    def encrypt_file(self, file_path, data):
        encrypted_data = self.cipher.encrypt(data.encode())
        with open(file_path, 'wb') as f:
            f.write(encrypted_data)
    
    def decrypt_file(self, file_path):
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()
        return self.cipher.decrypt(encrypted_data).decode()
```

### Encryption in Transit

**HTTPS Configuration** (HAProxy):
```
frontend https_frontend
    bind *:443 ssl crt /etc/ssl/certs/mindcoach.pem
    
    # Security headers
    http-response set-header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    http-response set-header X-Frame-Options "DENY"
    http-response set-header X-Content-Type-Options "nosniff"
    http-response set-header X-XSS-Protection "1; mode=block"
    http-response set-header Referrer-Policy "strict-origin-when-cross-origin"
    
    # Redirect HTTP to HTTPS
    redirect scheme https code 301 if !{ ssl_fc }
```

**API Communication**:
```python
import requests

# Always use HTTPS for external APIs
response = requests.post(
    'https://api.x.ai/v1/chat/completions',
    headers={
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    },
    json=payload,
    verify=True  # Verify SSL certificates
)
```

## Container Security

### Dockerfile Security

**Backend Dockerfile**:
```dockerfile
# Use specific version, not latest
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install security updates
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run application
CMD ["python", "run.py"]
```

### Container Runtime Security

**Docker Compose Security**:
```yaml
services:
  backend:
    build: ./backend
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    user: "1000:1000"
    networks:
      - backend-network
```

### Image Scanning

**Trivy Security Scanning**:
```bash
# Scan container images
trivy image --exit-code 1 --severity HIGH,CRITICAL mindcoach/backend:latest
trivy image --exit-code 1 --severity HIGH,CRITICAL mindcoach/frontend:latest

# Scan filesystem
trivy fs --exit-code 1 --severity HIGH,CRITICAL .
```

**GitHub Actions Integration**:
```yaml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'mindcoach/backend:latest'
    format: 'sarif'
    output: 'trivy-results.sarif'

- name: Upload Trivy scan results
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: 'trivy-results.sarif'
```

## Infrastructure Security

### Network Security

**Network Segmentation**:
```yaml
# Docker Compose networks
networks:
  frontend-network:
    driver: bridge
    internal: false
  backend-network:
    driver: bridge
    internal: true
  database-network:
    driver: bridge
    internal: true
```

**Firewall Rules**:
```bash
# UFW firewall configuration
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

### Access Control

**SSH Hardening**:
```bash
# /etc/ssh/sshd_config
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
Protocol 2
ClientAliveInterval 300
ClientAliveCountMax 2
MaxAuthTries 3
```

**Docker Socket Security**:
```bash
# Restrict Docker socket access
sudo groupadd docker
sudo usermod -aG docker $USER
sudo chmod 660 /var/run/docker.sock
```

## Security Monitoring

### Logging and Auditing

**Security Event Logging**:
```python
import logging
from datetime import datetime

security_logger = logging.getLogger('security')

def log_security_event(event_type, user_id, details):
    security_logger.warning({
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'user_id': user_id,
        'details': details,
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent')
    })

# Usage
@app.route('/api/login', methods=['POST'])
def login():
    if not authenticate_user(credentials):
        log_security_event('failed_login', user_id, 'Invalid credentials')
        abort(401)
```

**Audit Trail**:
```python
class AuditLog:
    @staticmethod
    def log_data_access(user_id, resource, action):
        audit_entry = {
            'timestamp': datetime.utcnow(),
            'user_id': user_id,
            'resource': resource,
            'action': action,
            'ip_address': request.remote_addr
        }
        # Store in secure audit log
        db.session.add(AuditEntry(**audit_entry))
        db.session.commit()
```

### Intrusion Detection

**Fail2Ban Configuration**:
```ini
# /etc/fail2ban/jail.local
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10
```

**Application-Level Detection**:
```python
from collections import defaultdict
from datetime import datetime, timedelta

class IntrusionDetection:
    def __init__(self):
        self.failed_attempts = defaultdict(list)
    
    def record_failed_attempt(self, ip_address):
        now = datetime.utcnow()
        self.failed_attempts[ip_address].append(now)
        
        # Clean old attempts
        cutoff = now - timedelta(minutes=15)
        self.failed_attempts[ip_address] = [
            attempt for attempt in self.failed_attempts[ip_address]
            if attempt > cutoff
        ]
        
        # Check for suspicious activity
        if len(self.failed_attempts[ip_address]) > 10:
            self.block_ip(ip_address)
    
    def block_ip(self, ip_address):
        # Add to blocklist
        blocked_ips.add(ip_address)
        log_security_event('ip_blocked', None, f'IP {ip_address} blocked')
```

## Vulnerability Management

### Dependency Scanning

**Python Dependencies**:
```bash
# Safety check for Python packages
pip install safety
safety check

# Bandit for security issues in code
pip install bandit
bandit -r backend/app/
```

**Node.js Dependencies**:
```bash
# npm audit for vulnerabilities
npm audit

# Fix vulnerabilities
npm audit fix

# Snyk for comprehensive scanning
npm install -g snyk
snyk test
snyk monitor
```

### Automated Security Testing

**OWASP ZAP Integration**:
```yaml
# GitHub Actions security testing
- name: OWASP ZAP Baseline Scan
  uses: zaproxy/action-baseline@v0.7.0
  with:
    target: 'http://localhost:3000'
    rules_file_name: '.zap/rules.tsv'
    cmd_options: '-a'
```

**Security Headers Testing**:
```python
def test_security_headers():
    response = client.get('/')
    
    assert 'X-Frame-Options' in response.headers
    assert response.headers['X-Frame-Options'] == 'DENY'
    
    assert 'X-Content-Type-Options' in response.headers
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    
    assert 'Strict-Transport-Security' in response.headers
```

## Incident Response

### Security Incident Handling

**Incident Response Plan**:
1. **Detection**: Automated monitoring and alerting
2. **Assessment**: Determine severity and impact
3. **Containment**: Isolate affected systems
4. **Eradication**: Remove threat and vulnerabilities
5. **Recovery**: Restore normal operations
6. **Lessons Learned**: Post-incident analysis

**Emergency Procedures**:
```bash
# Emergency shutdown
./scripts/emergency-shutdown.sh

# Isolate compromised container
docker stop <container_id>
docker network disconnect <network> <container>

# Enable maintenance mode
echo "maintenance" > /var/www/html/maintenance.flag
```

### Backup and Recovery

**Secure Backups**:
```bash
#!/bin/bash
# Encrypted backup script

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backup_${BACKUP_DATE}.tar.gz.enc"

# Create encrypted backup
tar -czf - /app/data /app/users | \
gpg --cipher-algo AES256 --compress-algo 1 --symmetric \
    --output "/backups/${BACKUP_FILE}"

# Verify backup integrity
gpg --decrypt "/backups/${BACKUP_FILE}" | tar -tzf - > /dev/null
```

**Recovery Testing**:
```bash
# Regular recovery testing
./scripts/test-backup-recovery.sh

# Disaster recovery simulation
./scripts/disaster-recovery-test.sh
```

## Compliance and Standards

### GDPR Compliance

**Data Protection**:
```python
class GDPRCompliance:
    @staticmethod
    def anonymize_user_data(user_id):
        """Anonymize user data for GDPR compliance"""
        user = User.query.filter_by(user_id=user_id).first()
        if user:
            user.email = f"anonymized_{uuid.uuid4()}"
            user.personal_data = None
            db.session.commit()
    
    @staticmethod
    def export_user_data(user_id):
        """Export user data for GDPR data portability"""
        user_data = {
            'user_info': User.query.filter_by(user_id=user_id).first(),
            'subscriptions': Subscription.query.filter_by(user_id=user_id).all(),
            'survey_results': SurveyResult.query.filter_by(user_id=user_id).all()
        }
        return user_data
```

### Security Standards

**OWASP Top 10 Compliance**:
- ✅ A01: Broken Access Control
- ✅ A02: Cryptographic Failures
- ✅ A03: Injection
- ✅ A04: Insecure Design
- ✅ A05: Security Misconfiguration
- ✅ A06: Vulnerable Components
- ✅ A07: Authentication Failures
- ✅ A08: Software Integrity Failures
- ✅ A09: Security Logging Failures
- ✅ A10: Server-Side Request Forgery

## Security Checklist

### Development Security Checklist

- [ ] Input validation on all user inputs
- [ ] Parameterized queries for database access
- [ ] Output encoding for XSS prevention
- [ ] CSRF protection for state-changing operations
- [ ] Secure session management
- [ ] Proper error handling (no information disclosure)
- [ ] Security headers implementation
- [ ] Dependency vulnerability scanning
- [ ] Code security analysis (SAST)

### Deployment Security Checklist

- [ ] HTTPS/TLS configuration
- [ ] Container security hardening
- [ ] Network segmentation
- [ ] Access control implementation
- [ ] Security monitoring setup
- [ ] Backup encryption
- [ ] Incident response procedures
- [ ] Security testing automation
- [ ] Vulnerability management process

### Operational Security Checklist

- [ ] Regular security updates
- [ ] Log monitoring and analysis
- [ ] Access review and cleanup
- [ ] Security training for team
- [ ] Penetration testing
- [ ] Backup testing and recovery
- [ ] Security metrics tracking
- [ ] Compliance auditing

---

This security guide provides comprehensive coverage of security best practices for MindCoach. Regular security reviews and updates ensure the platform maintains strong security posture against evolving threats.