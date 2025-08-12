# Docker Backup and Recovery Procedures

## Overview

This guide provides comprehensive backup and recovery procedures for the MindCoach containerized application. It covers database backups, volume backups, configuration backups, and disaster recovery procedures.

## Table of Contents

1. [Backup Strategy](#backup-strategy)
2. [Database Backup](#database-backup)
3. [Volume Backup](#volume-backup)
4. [Configuration Backup](#configuration-backup)
5. [Automated Backup Scripts](#automated-backup-scripts)
6. [Recovery Procedures](#recovery-procedures)
7. [Disaster Recovery](#disaster-recovery)
8. [Testing and Validation](#testing-and-validation)
9. [Best Practices](#best-practices)

## Backup Strategy

### Backup Types

1. **Full Backup**: Complete system backup including all data and configurations
2. **Incremental Backup**: Only changes since the last backup
3. **Differential Backup**: Changes since the last full backup
4. **Point-in-Time Backup**: Specific moment in time backup

### Backup Schedule

```bash
# Recommended backup schedule
# Daily: Database backups
# Weekly: Volume backups
# Monthly: Full system backups
# Real-time: Transaction log backups (for critical data)

# Crontab configuration
0 2 * * * /opt/mindcoach/scripts/backup-database.sh daily
0 3 * * 0 /opt/mindcoach/scripts/backup-volumes.sh weekly
0 4 1 * * /opt/mindcoach/scripts/backup-full-system.sh monthly
*/15 * * * * /opt/mindcoach/scripts/backup-transaction-logs.sh
```

### Retention Policy

```bash
# Backup retention policy
DAILY_RETENTION=7      # Keep daily backups for 7 days
WEEKLY_RETENTION=4     # Keep weekly backups for 4 weeks
MONTHLY_RETENTION=12   # Keep monthly backups for 12 months
YEARLY_RETENTION=5     # Keep yearly backups for 5 years
```

## Database Backup

### PostgreSQL Backup Scripts

#### Full Database Backup

```bash
#!/bin/bash
# backup-database.sh

set -e

# Configuration
BACKUP_DIR="/backups/database"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_TYPE=${1:-daily}
RETENTION_DAYS=${2:-7}

# Database connection details
DB_CONTAINER="mindcoach-postgres"
DB_NAME="mindcoach"
DB_USER="postgres"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate backup filename
BACKUP_FILE="mindcoach_${BACKUP_TYPE}_${TIMESTAMP}.sql"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILE"

echo "Starting database backup: $BACKUP_FILE"

# Create database dump
docker exec "$DB_CONTAINER" pg_dump \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --verbose \
    --no-owner \
    --no-privileges \
    --create \
    --clean \
    > "$BACKUP_PATH"

# Verify backup was created
if [ ! -f "$BACKUP_PATH" ]; then
    echo "ERROR: Backup file was not created"
    exit 1
fi

# Get backup size
BACKUP_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
echo "Backup created successfully: $BACKUP_FILE ($BACKUP_SIZE)"

# Compress backup
echo "Compressing backup..."
gzip "$BACKUP_PATH"
COMPRESSED_SIZE=$(du -h "$BACKUP_PATH.gz" | cut -f1)
echo "Backup compressed: $BACKUP_FILE.gz ($COMPRESSED_SIZE)"

# Verify compressed backup
if ! gunzip -t "$BACKUP_PATH.gz"; then
    echo "ERROR: Compressed backup is corrupted"
    exit 1
fi

# Clean up old backups
echo "Cleaning up old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "mindcoach_${BACKUP_TYPE}_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Log backup completion
echo "$(date): Database backup completed - $BACKUP_FILE.gz" >> /var/log/mindcoach-backup.log

# Optional: Upload to cloud storage
if [ "$UPLOAD_TO_CLOUD" = "true" ]; then
    echo "Uploading backup to cloud storage..."
    aws s3 cp "$BACKUP_PATH.gz" "s3://$S3_BUCKET/database/" || echo "Cloud upload failed"
fi

echo "Database backup process completed successfully"
```

#### Incremental Backup with WAL

```bash
#!/bin/bash
# backup-wal.sh

set -e

WAL_BACKUP_DIR="/backups/wal"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create WAL backup directory
mkdir -p "$WAL_BACKUP_DIR"

echo "Starting WAL backup: $TIMESTAMP"

# Archive WAL files
docker exec mindcoach-postgres pg_basebackup \
    -U postgres \
    -D "/tmp/basebackup_$TIMESTAMP" \
    -Ft \
    -z \
    -P \
    -v

# Copy WAL backup from container
docker cp "mindcoach-postgres:/tmp/basebackup_$TIMESTAMP" "$WAL_BACKUP_DIR/"

# Clean up container
docker exec mindcoach-postgres rm -rf "/tmp/basebackup_$TIMESTAMP"

echo "WAL backup completed: $TIMESTAMP"
```

### Database Backup Verification

```bash
#!/bin/bash
# verify-database-backup.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

echo "Verifying database backup: $BACKUP_FILE"

# Test backup file integrity
if ! gunzip -t "$BACKUP_FILE"; then
    echo "ERROR: Backup file is corrupted"
    exit 1
fi

# Create temporary test database
TEST_DB="mindcoach_test_$(date +%s)"
docker exec mindcoach-postgres createdb -U postgres "$TEST_DB"

# Restore backup to test database
gunzip -c "$BACKUP_FILE" | docker exec -i mindcoach-postgres psql -U postgres -d "$TEST_DB"

# Verify restore was successful
TABLE_COUNT=$(docker exec mindcoach-postgres psql -U postgres -d "$TEST_DB" -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")

if [ "$TABLE_COUNT" -gt 0 ]; then
    echo "Backup verification successful: $TABLE_COUNT tables restored"
else
    echo "ERROR: Backup verification failed: No tables found"
    exit 1
fi

# Clean up test database
docker exec mindcoach-postgres dropdb -U postgres "$TEST_DB"

echo "Database backup verification completed successfully"
```

## Volume Backup

### Docker Volume Backup

```bash
#!/bin/bash
# backup-volumes.sh

set -e

BACKUP_DIR="/backups/volumes"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_TYPE=${1:-weekly}

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Starting volume backup: $TIMESTAMP"

# Get list of volumes to backup
VOLUMES=(
    "mindcoach_user-data"
    "mindcoach_app-data"
    "mindcoach_postgres-data"
    "mindcoach_redis-data"
)

for VOLUME in "${VOLUMES[@]}"; do
    echo "Backing up volume: $VOLUME"
    
    BACKUP_FILE="${VOLUME}_${BACKUP_TYPE}_${TIMESTAMP}.tar.gz"
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILE"
    
    # Create volume backup using temporary container
    docker run --rm \
        -v "$VOLUME":/data:ro \
        -v "$BACKUP_DIR":/backup \
        alpine \
        tar czf "/backup/$BACKUP_FILE" -C /data .
    
    # Verify backup was created
    if [ -f "$BACKUP_PATH" ]; then
        BACKUP_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
        echo "Volume backup created: $BACKUP_FILE ($BACKUP_SIZE)"
    else
        echo "ERROR: Volume backup failed for $VOLUME"
        exit 1
    fi
done

# Create backup manifest
MANIFEST_FILE="$BACKUP_DIR/manifest_${TIMESTAMP}.json"
cat > "$MANIFEST_FILE" << EOF
{
    "timestamp": "$TIMESTAMP",
    "backup_type": "$BACKUP_TYPE",
    "volumes": [
$(for VOLUME in "${VOLUMES[@]}"; do
    BACKUP_FILE="${VOLUME}_${BACKUP_TYPE}_${TIMESTAMP}.tar.gz"
    SIZE=$(stat -c%s "$BACKUP_DIR/$BACKUP_FILE" 2>/dev/null || echo "0")
    echo "        {\"volume\": \"$VOLUME\", \"file\": \"$BACKUP_FILE\", \"size\": $SIZE},"
done | sed '$ s/,$//')
    ]
}
EOF

echo "Volume backup completed: $TIMESTAMP"
```

### Application Data Backup

```bash
#!/bin/bash
# backup-app-data.sh

set -e

APP_DATA_DIR="/opt/mindcoach"
BACKUP_DIR="/backups/app-data"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "Starting application data backup: $TIMESTAMP"

# Backup application configuration
tar czf "$BACKUP_DIR/config_$TIMESTAMP.tar.gz" \
    -C "$APP_DATA_DIR" \
    docker-compose*.yml \
    .env* \
    nginx/ \
    scripts/ \
    monitoring/ \
    --exclude='*.log' \
    --exclude='*.tmp'

# Backup user-generated content
if [ -d "$APP_DATA_DIR/users" ]; then
    tar czf "$BACKUP_DIR/users_$TIMESTAMP.tar.gz" \
        -C "$APP_DATA_DIR" \
        users/
fi

# Backup logs (last 7 days)
if [ -d "$APP_DATA_DIR/logs" ]; then
    find "$APP_DATA_DIR/logs" -name "*.log" -mtime -7 | \
    tar czf "$BACKUP_DIR/logs_$TIMESTAMP.tar.gz" -T -
fi

echo "Application data backup completed: $TIMESTAMP"
```

## Configuration Backup

### Docker Compose Configuration Backup

```bash
#!/bin/bash
# backup-configuration.sh

set -e

CONFIG_DIR="/opt/mindcoach"
BACKUP_DIR="/backups/configuration"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "Starting configuration backup: $TIMESTAMP"

# Backup Docker Compose files
tar czf "$BACKUP_DIR/docker-compose_$TIMESTAMP.tar.gz" \
    -C "$CONFIG_DIR" \
    docker-compose*.yml

# Backup environment files (excluding sensitive data)
cp "$CONFIG_DIR/.env.example" "$BACKUP_DIR/env-example_$TIMESTAMP"

# Backup Nginx configuration
if [ -d "$CONFIG_DIR/nginx" ]; then
    tar czf "$BACKUP_DIR/nginx_$TIMESTAMP.tar.gz" \
        -C "$CONFIG_DIR" \
        nginx/
fi

# Backup monitoring configuration
if [ -d "$CONFIG_DIR/monitoring" ]; then
    tar czf "$BACKUP_DIR/monitoring_$TIMESTAMP.tar.gz" \
        -C "$CONFIG_DIR" \
        monitoring/
fi

# Backup scripts
if [ -d "$CONFIG_DIR/scripts" ]; then
    tar czf "$BACKUP_DIR/scripts_$TIMESTAMP.tar.gz" \
        -C "$CONFIG_DIR" \
        scripts/
fi

# Create configuration manifest
cat > "$BACKUP_DIR/config-manifest_$TIMESTAMP.json" << EOF
{
    "timestamp": "$TIMESTAMP",
    "docker_version": "$(docker --version)",
    "compose_version": "$(docker-compose --version)",
    "system_info": {
        "hostname": "$(hostname)",
        "os": "$(uname -a)",
        "disk_usage": "$(df -h /)"
    }
}
EOF

echo "Configuration backup completed: $TIMESTAMP"
```

## Automated Backup Scripts

### Master Backup Script

```bash
#!/bin/bash
# master-backup.sh

set -e

BACKUP_TYPE=${1:-daily}
LOG_FILE="/var/log/mindcoach-backup.log"

echo "$(date): Starting $BACKUP_TYPE backup process" >> "$LOG_FILE"

# Function to log and execute
log_and_execute() {
    local script=$1
    local description=$2
    
    echo "$(date): Starting $description" >> "$LOG_FILE"
    
    if $script; then
        echo "$(date): $description completed successfully" >> "$LOG_FILE"
    else
        echo "$(date): ERROR - $description failed" >> "$LOG_FILE"
        exit 1
    fi
}

# Execute backup scripts based on type
case $BACKUP_TYPE in
    "daily")
        log_and_execute "/opt/mindcoach/scripts/backup-database.sh daily" "Database backup"
        log_and_execute "/opt/mindcoach/scripts/backup-app-data.sh" "Application data backup"
        ;;
    "weekly")
        log_and_execute "/opt/mindcoach/scripts/backup-database.sh weekly" "Database backup"
        log_and_execute "/opt/mindcoach/scripts/backup-volumes.sh weekly" "Volume backup"
        log_and_execute "/opt/mindcoach/scripts/backup-configuration.sh" "Configuration backup"
        ;;
    "monthly")
        log_and_execute "/opt/mindcoach/scripts/backup-database.sh monthly" "Database backup"
        log_and_execute "/opt/mindcoach/scripts/backup-volumes.sh monthly" "Volume backup"
        log_and_execute "/opt/mindcoach/scripts/backup-configuration.sh" "Configuration backup"
        log_and_execute "/opt/mindcoach/scripts/backup-full-system.sh" "Full system backup"
        ;;
    *)
        echo "Usage: $0 {daily|weekly|monthly}"
        exit 1
        ;;
esac

echo "$(date): $BACKUP_TYPE backup process completed successfully" >> "$LOG_FILE"

# Send notification (optional)
if [ "$SEND_NOTIFICATIONS" = "true" ]; then
    echo "$BACKUP_TYPE backup completed successfully" | \
    mail -s "MindCoach Backup Status" "$ADMIN_EMAIL"
fi
```

### Backup Monitoring Script

```bash
#!/bin/bash
# monitor-backups.sh

BACKUP_DIR="/backups"
LOG_FILE="/var/log/mindcoach-backup-monitor.log"
ALERT_EMAIL="admin@mindcoach.com"

echo "$(date): Starting backup monitoring" >> "$LOG_FILE"

# Check if daily backup exists
YESTERDAY=$(date -d "yesterday" +%Y%m%d)
DAILY_BACKUP=$(find "$BACKUP_DIR/database" -name "*daily_${YESTERDAY}*.sql.gz" | head -1)

if [ -z "$DAILY_BACKUP" ]; then
    echo "$(date): ALERT - Daily backup missing for $YESTERDAY" >> "$LOG_FILE"
    echo "Daily backup missing for $YESTERDAY" | \
    mail -s "MindCoach Backup Alert" "$ALERT_EMAIL"
fi

# Check backup sizes
for backup in $(find "$BACKUP_DIR" -name "*.gz" -mtime -1); do
    SIZE=$(stat -c%s "$backup")
    if [ "$SIZE" -lt 1000000 ]; then  # Less than 1MB
        echo "$(date): ALERT - Backup file too small: $backup ($SIZE bytes)" >> "$LOG_FILE"
        echo "Backup file suspiciously small: $backup" | \
        mail -s "MindCoach Backup Alert" "$ALERT_EMAIL"
    fi
done

# Check backup integrity
for backup in $(find "$BACKUP_DIR/database" -name "*.sql.gz" -mtime -1); do
    if ! gunzip -t "$backup"; then
        echo "$(date): ALERT - Corrupted backup: $backup" >> "$LOG_FILE"
        echo "Corrupted backup detected: $backup" | \
        mail -s "MindCoach Backup Alert" "$ALERT_EMAIL"
    fi
done

echo "$(date): Backup monitoring completed" >> "$LOG_FILE"
```## R
ecovery Procedures

### Database Recovery

#### Full Database Restore

```bash
#!/bin/bash
# restore-database.sh

set -e

BACKUP_FILE=$1
RESTORE_TYPE=${2:-full}

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.sql.gz> [full|partial]"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Starting database restore from: $BACKUP_FILE"

# Verify backup integrity
if ! gunzip -t "$BACKUP_FILE"; then
    echo "ERROR: Backup file is corrupted"
    exit 1
fi

# Stop application services
echo "Stopping application services..."
docker-compose -f docker-compose.prod.yml stop backend celery-worker celery-beat

# Create backup of current database
CURRENT_BACKUP="/tmp/pre-restore-backup-$(date +%s).sql"
echo "Creating backup of current database..."
docker exec mindcoach-postgres pg_dump -U postgres mindcoach > "$CURRENT_BACKUP"

if [ "$RESTORE_TYPE" = "full" ]; then
    # Full restore - drop and recreate database
    echo "Performing full database restore..."
    
    # Drop existing database
    docker exec mindcoach-postgres dropdb -U postgres mindcoach || true
    
    # Create new database
    docker exec mindcoach-postgres createdb -U postgres mindcoach
    
    # Restore from backup
    gunzip -c "$BACKUP_FILE" | docker exec -i mindcoach-postgres psql -U postgres -d mindcoach
    
else
    # Partial restore - restore specific tables
    echo "Performing partial database restore..."
    
    # Extract and restore specific tables
    gunzip -c "$BACKUP_FILE" | docker exec -i mindcoach-postgres psql -U postgres -d mindcoach
fi

# Verify restore
echo "Verifying database restore..."
TABLE_COUNT=$(docker exec mindcoach-postgres psql -U postgres -d mindcoach -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")

if [ "$TABLE_COUNT" -gt 0 ]; then
    echo "Database restore successful: $TABLE_COUNT tables restored"
else
    echo "ERROR: Database restore failed"
    
    # Restore from current backup
    echo "Restoring from pre-restore backup..."
    docker exec mindcoach-postgres dropdb -U postgres mindcoach
    docker exec mindcoach-postgres createdb -U postgres mindcoach
    cat "$CURRENT_BACKUP" | docker exec -i mindcoach-postgres psql -U postgres -d mindcoach
    
    exit 1
fi

# Start application services
echo "Starting application services..."
docker-compose -f docker-compose.prod.yml start backend celery-worker celery-beat

# Clean up
rm -f "$CURRENT_BACKUP"

echo "Database restore completed successfully"
```

#### Point-in-Time Recovery

```bash
#!/bin/bash
# point-in-time-recovery.sh

set -e

TARGET_TIME=$1
BASE_BACKUP=$2

if [ -z "$TARGET_TIME" ] || [ -z "$BASE_BACKUP" ]; then
    echo "Usage: $0 <target_time> <base_backup>"
    echo "Example: $0 '2024-01-15 14:30:00' /backups/base_backup.tar.gz"
    exit 1
fi

echo "Starting point-in-time recovery to: $TARGET_TIME"

# Stop PostgreSQL
docker-compose -f docker-compose.prod.yml stop postgres

# Remove current data directory
docker volume rm mindcoach_postgres-data || true

# Create new volume
docker volume create mindcoach_postgres-data

# Restore base backup
echo "Restoring base backup..."
docker run --rm \
    -v mindcoach_postgres-data:/data \
    -v "$(dirname $BASE_BACKUP)":/backup \
    alpine \
    tar xzf "/backup/$(basename $BASE_BACKUP)" -C /data

# Create recovery configuration
RECOVERY_CONF="/tmp/recovery.conf"
cat > "$RECOVERY_CONF" << EOF
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
recovery_target_time = '$TARGET_TIME'
recovery_target_action = 'promote'
EOF

# Copy recovery configuration to data directory
docker run --rm \
    -v mindcoach_postgres-data:/data \
    -v "$RECOVERY_CONF":/recovery.conf \
    alpine \
    cp /recovery.conf /data/

# Start PostgreSQL in recovery mode
docker-compose -f docker-compose.prod.yml start postgres

# Wait for recovery to complete
echo "Waiting for recovery to complete..."
while true; do
    if docker exec mindcoach-postgres pg_isready -U postgres; then
        break
    fi
    sleep 5
done

echo "Point-in-time recovery completed successfully"
```

### Volume Recovery

#### Volume Restore Script

```bash
#!/bin/bash
# restore-volumes.sh

set -e

BACKUP_DIR="/backups/volumes"
RESTORE_DATE=${1:-latest}

if [ "$RESTORE_DATE" = "latest" ]; then
    # Find latest backup
    MANIFEST=$(find "$BACKUP_DIR" -name "manifest_*.json" | sort | tail -1)
    if [ -z "$MANIFEST" ]; then
        echo "ERROR: No backup manifests found"
        exit 1
    fi
    TIMESTAMP=$(basename "$MANIFEST" .json | sed 's/manifest_//')
else
    TIMESTAMP=$RESTORE_DATE
    MANIFEST="$BACKUP_DIR/manifest_$TIMESTAMP.json"
    if [ ! -f "$MANIFEST" ]; then
        echo "ERROR: Backup manifest not found: $MANIFEST"
        exit 1
    fi
fi

echo "Starting volume restore from backup: $TIMESTAMP"

# Stop all services
echo "Stopping all services..."
docker-compose -f docker-compose.prod.yml down

# Parse manifest and restore volumes
VOLUMES=$(jq -r '.volumes[].volume' "$MANIFEST")

for VOLUME in $VOLUMES; do
    BACKUP_FILE=$(jq -r ".volumes[] | select(.volume == \"$VOLUME\") | .file" "$MANIFEST")
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILE"
    
    if [ ! -f "$BACKUP_PATH" ]; then
        echo "ERROR: Backup file not found: $BACKUP_PATH"
        continue
    fi
    
    echo "Restoring volume: $VOLUME from $BACKUP_FILE"
    
    # Remove existing volume
    docker volume rm "$VOLUME" 2>/dev/null || true
    
    # Create new volume
    docker volume create "$VOLUME"
    
    # Restore volume data
    docker run --rm \
        -v "$VOLUME":/data \
        -v "$BACKUP_DIR":/backup \
        alpine \
        tar xzf "/backup/$BACKUP_FILE" -C /data
    
    echo "Volume restored: $VOLUME"
done

# Start services
echo "Starting services..."
docker-compose -f docker-compose.prod.yml up -d

echo "Volume restore completed successfully"
```

### Application Recovery

#### Complete Application Recovery

```bash
#!/bin/bash
# recover-application.sh

set -e

RECOVERY_TYPE=${1:-full}
BACKUP_DATE=${2:-latest}

echo "Starting application recovery: $RECOVERY_TYPE"

case $RECOVERY_TYPE in
    "database-only")
        echo "Recovering database only..."
        if [ "$BACKUP_DATE" = "latest" ]; then
            BACKUP_FILE=$(find /backups/database -name "*.sql.gz" | sort | tail -1)
        else
            BACKUP_FILE=$(find /backups/database -name "*${BACKUP_DATE}*.sql.gz" | head -1)
        fi
        
        if [ -z "$BACKUP_FILE" ]; then
            echo "ERROR: No database backup found"
            exit 1
        fi
        
        ./scripts/restore-database.sh "$BACKUP_FILE"
        ;;
        
    "volumes-only")
        echo "Recovering volumes only..."
        ./scripts/restore-volumes.sh "$BACKUP_DATE"
        ;;
        
    "full")
        echo "Performing full application recovery..."
        
        # Stop all services
        docker-compose -f docker-compose.prod.yml down
        
        # Restore volumes
        ./scripts/restore-volumes.sh "$BACKUP_DATE"
        
        # Restore database
        if [ "$BACKUP_DATE" = "latest" ]; then
            BACKUP_FILE=$(find /backups/database -name "*.sql.gz" | sort | tail -1)
        else
            BACKUP_FILE=$(find /backups/database -name "*${BACKUP_DATE}*.sql.gz" | head -1)
        fi
        
        if [ -n "$BACKUP_FILE" ]; then
            ./scripts/restore-database.sh "$BACKUP_FILE"
        fi
        
        # Restore configuration
        if [ -d "/backups/configuration" ]; then
            CONFIG_BACKUP=$(find /backups/configuration -name "*${BACKUP_DATE}*" | head -1)
            if [ -n "$CONFIG_BACKUP" ]; then
                echo "Restoring configuration..."
                tar xzf "$CONFIG_BACKUP" -C /opt/mindcoach/
            fi
        fi
        
        # Start services
        docker-compose -f docker-compose.prod.yml up -d
        ;;
        
    *)
        echo "Usage: $0 {database-only|volumes-only|full} [backup_date]"
        exit 1
        ;;
esac

# Verify recovery
echo "Verifying application recovery..."
sleep 30

if curl -f http://localhost/api/health; then
    echo "Application recovery successful"
else
    echo "WARNING: Application health check failed"
fi

echo "Recovery process completed"
```

## Disaster Recovery

### Disaster Recovery Plan

```bash
#!/bin/bash
# disaster-recovery.sh

set -e

DR_SITE=${1:-primary}
RECOVERY_LEVEL=${2:-full}

echo "=== DISASTER RECOVERY INITIATED ==="
echo "Site: $DR_SITE"
echo "Recovery Level: $RECOVERY_LEVEL"
echo "Timestamp: $(date)"

# Log disaster recovery initiation
echo "$(date): Disaster recovery initiated - Site: $DR_SITE, Level: $RECOVERY_LEVEL" >> /var/log/disaster-recovery.log

case $DR_SITE in
    "primary")
        echo "Recovering primary site..."
        
        # Check system status
        if docker info > /dev/null 2>&1; then
            echo "Docker daemon is running"
        else
            echo "ERROR: Docker daemon not available"
            exit 1
        fi
        
        # Restore from latest backups
        ./scripts/recover-application.sh full latest
        ;;
        
    "secondary")
        echo "Activating secondary site..."
        
        # Sync latest backups from primary site
        if [ "$SYNC_FROM_PRIMARY" = "true" ]; then
            echo "Syncing backups from primary site..."
            rsync -avz "$PRIMARY_BACKUP_HOST:/backups/" /backups/
        fi
        
        # Deploy application
        docker-compose -f docker-compose.prod.yml up -d
        
        # Update DNS/Load balancer to point to secondary site
        if [ "$UPDATE_DNS" = "true" ]; then
            echo "Updating DNS to point to secondary site..."
            # DNS update logic here
        fi
        ;;
        
    *)
        echo "ERROR: Unknown disaster recovery site: $DR_SITE"
        exit 1
        ;;
esac

# Verify recovery
echo "Verifying disaster recovery..."
sleep 60

HEALTH_CHECK_ATTEMPTS=0
MAX_ATTEMPTS=10

while [ $HEALTH_CHECK_ATTEMPTS -lt $MAX_ATTEMPTS ]; do
    if curl -f http://localhost/api/health; then
        echo "Disaster recovery successful"
        echo "$(date): Disaster recovery completed successfully" >> /var/log/disaster-recovery.log
        
        # Send success notification
        echo "Disaster recovery completed successfully" | \
        mail -s "Disaster Recovery Success" "$ADMIN_EMAIL"
        
        exit 0
    fi
    
    HEALTH_CHECK_ATTEMPTS=$((HEALTH_CHECK_ATTEMPTS + 1))
    echo "Health check attempt $HEALTH_CHECK_ATTEMPTS/$MAX_ATTEMPTS failed, retrying..."
    sleep 30
done

echo "ERROR: Disaster recovery failed - application not responding"
echo "$(date): Disaster recovery failed - application not responding" >> /var/log/disaster-recovery.log

# Send failure notification
echo "Disaster recovery failed - manual intervention required" | \
mail -s "Disaster Recovery Failed" "$ADMIN_EMAIL"

exit 1
```

### Backup Replication

```bash
#!/bin/bash
# replicate-backups.sh

set -e

REMOTE_HOST=${1:-backup-server}
REMOTE_PATH=${2:-/remote/backups}
LOCAL_BACKUP_DIR="/backups"

echo "Starting backup replication to $REMOTE_HOST:$REMOTE_PATH"

# Sync database backups
echo "Syncing database backups..."
rsync -avz --delete \
    "$LOCAL_BACKUP_DIR/database/" \
    "$REMOTE_HOST:$REMOTE_PATH/database/"

# Sync volume backups
echo "Syncing volume backups..."
rsync -avz --delete \
    "$LOCAL_BACKUP_DIR/volumes/" \
    "$REMOTE_HOST:$REMOTE_PATH/volumes/"

# Sync configuration backups
echo "Syncing configuration backups..."
rsync -avz --delete \
    "$LOCAL_BACKUP_DIR/configuration/" \
    "$REMOTE_HOST:$REMOTE_PATH/configuration/"

# Verify replication
echo "Verifying backup replication..."
REMOTE_COUNT=$(ssh "$REMOTE_HOST" "find $REMOTE_PATH -name '*.gz' | wc -l")
LOCAL_COUNT=$(find "$LOCAL_BACKUP_DIR" -name "*.gz" | wc -l)

if [ "$REMOTE_COUNT" -eq "$LOCAL_COUNT" ]; then
    echo "Backup replication successful: $REMOTE_COUNT files replicated"
else
    echo "WARNING: Backup count mismatch - Local: $LOCAL_COUNT, Remote: $REMOTE_COUNT"
fi

echo "Backup replication completed"
```

## Testing and Validation

### Backup Testing Script

```bash
#!/bin/bash
# test-backups.sh

set -e

TEST_ENV="backup-test"
BACKUP_FILE=${1:-latest}

echo "Starting backup testing with: $BACKUP_FILE"

# Create test environment
echo "Creating test environment..."
docker-compose -f docker-compose.test.yml -p "$TEST_ENV" up -d postgres redis

# Wait for services to be ready
sleep 30

# Find backup file if "latest" specified
if [ "$BACKUP_FILE" = "latest" ]; then
    BACKUP_FILE=$(find /backups/database -name "*.sql.gz" | sort | tail -1)
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Test database restore
echo "Testing database restore..."
TEST_DB="mindcoach_test"

# Create test database
docker exec "${TEST_ENV}_postgres_1" createdb -U postgres "$TEST_DB"

# Restore backup
gunzip -c "$BACKUP_FILE" | docker exec -i "${TEST_ENV}_postgres_1" psql -U postgres -d "$TEST_DB"

# Verify restore
TABLE_COUNT=$(docker exec "${TEST_ENV}_postgres_1" psql -U postgres -d "$TEST_DB" -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")

if [ "$TABLE_COUNT" -gt 0 ]; then
    echo "Backup test successful: $TABLE_COUNT tables restored"
    
    # Test data integrity
    USER_COUNT=$(docker exec "${TEST_ENV}_postgres_1" psql -U postgres -d "$TEST_DB" -t -c "SELECT count(*) FROM users;" 2>/dev/null || echo "0")
    echo "User records found: $USER_COUNT"
    
else
    echo "ERROR: Backup test failed: No tables found"
    exit 1
fi

# Clean up test environment
echo "Cleaning up test environment..."
docker-compose -f docker-compose.test.yml -p "$TEST_ENV" down -v

echo "Backup testing completed successfully"
```

### Recovery Testing

```bash
#!/bin/bash
# test-recovery.sh

set -e

echo "Starting recovery testing..."

# Create test data
echo "Creating test data..."
TEST_USER_ID="test-recovery-$(date +%s)"
curl -X POST http://localhost/api/users \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": \"$TEST_USER_ID\", \"email\": \"test@recovery.com\"}"

# Create backup
echo "Creating test backup..."
./scripts/backup-database.sh test

# Simulate data loss
echo "Simulating data loss..."
docker exec mindcoach-postgres psql -U postgres -d mindcoach -c "DELETE FROM users WHERE user_id = '$TEST_USER_ID';"

# Verify data is gone
USER_EXISTS=$(docker exec mindcoach-postgres psql -U postgres -d mindcoach -t -c "SELECT count(*) FROM users WHERE user_id = '$TEST_USER_ID';")
if [ "$USER_EXISTS" -eq 0 ]; then
    echo "Data loss confirmed"
else
    echo "ERROR: Data loss simulation failed"
    exit 1
fi

# Restore from backup
echo "Restoring from backup..."
BACKUP_FILE=$(find /backups/database -name "*test_*.sql.gz" | sort | tail -1)
./scripts/restore-database.sh "$BACKUP_FILE"

# Verify data recovery
USER_EXISTS=$(docker exec mindcoach-postgres psql -U postgres -d mindcoach -t -c "SELECT count(*) FROM users WHERE user_id = '$TEST_USER_ID';")
if [ "$USER_EXISTS" -eq 1 ]; then
    echo "Recovery test successful: Data restored"
else
    echo "ERROR: Recovery test failed: Data not restored"
    exit 1
fi

# Clean up test data
docker exec mindcoach-postgres psql -U postgres -d mindcoach -c "DELETE FROM users WHERE user_id = '$TEST_USER_ID';"

echo "Recovery testing completed successfully"
```

## Best Practices

### Backup Best Practices

1. **3-2-1 Rule**: 3 copies of data, 2 different media types, 1 offsite
2. **Regular Testing**: Test backups regularly to ensure they work
3. **Automation**: Automate backup processes to reduce human error
4. **Monitoring**: Monitor backup processes and alert on failures
5. **Documentation**: Document all backup and recovery procedures

### Security Best Practices

1. **Encryption**: Encrypt backups at rest and in transit
2. **Access Control**: Limit access to backup files and systems
3. **Audit Logging**: Log all backup and recovery operations
4. **Secure Storage**: Store backups in secure, geographically distributed locations
5. **Regular Updates**: Keep backup tools and systems updated

### Performance Best Practices

1. **Incremental Backups**: Use incremental backups to reduce backup time
2. **Compression**: Compress backups to save storage space
3. **Parallel Processing**: Use parallel processing for large backups
4. **Network Optimization**: Optimize network settings for backup transfers
5. **Resource Management**: Schedule backups during low-usage periods

---

This backup and recovery guide provides comprehensive procedures for protecting and recovering the MindCoach application data. Regular review and testing of these procedures ensures data protection and business continuity.