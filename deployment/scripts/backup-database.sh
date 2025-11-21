#!/bin/bash
# =============================================================================
# DATABASE BACKUP SCRIPT
# Backs up PostgreSQL database and uploads to Oracle Object Storage
# =============================================================================

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Configuration
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=${RETENTION_DAYS:-7}
DB_NAME="${POSTGRES_DB:-support_agent}"
DB_USER="${POSTGRES_USER:-postgres}"

# Oracle Object Storage configuration (set via environment or Doppler)
OCI_BUCKET_NAME="${OCI_BUCKET_NAME:-multi-agent-backups}"
OCI_NAMESPACE="${OCI_NAMESPACE:-}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check if running in Docker context
if [ -f /.dockerenv ]; then
    # Running inside container
    DOCKER_CMD=""
else
    # Running on host
    DOCKER_CMD="docker compose exec -T postgres"
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# =============================================================================
# STEP 1: Backup PostgreSQL Database
# =============================================================================

log "Starting PostgreSQL backup..."
BACKUP_FILE="${BACKUP_DIR}/postgres_${TIMESTAMP}.sql"

if [ -z "$DOCKER_CMD" ]; then
    # Inside container
    pg_dump -U "$DB_USER" -d "$DB_NAME" --clean --if-exists > "$BACKUP_FILE"
else
    # On host
    $DOCKER_CMD pg_dump -U "$DB_USER" -d "$DB_NAME" --clean --if-exists > "$BACKUP_FILE"
fi

if [ $? -eq 0 ]; then
    log "✓ Database dumped to: $BACKUP_FILE"
else
    error "Failed to dump database"
    exit 1
fi

# =============================================================================
# STEP 2: Compress Backup
# =============================================================================

log "Compressing backup..."
gzip -9 "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "✓ Backup compressed: $BACKUP_FILE ($BACKUP_SIZE)"
else
    error "Failed to compress backup"
    exit 1
fi

# =============================================================================
# STEP 3: Upload to Oracle Object Storage (if configured)
# =============================================================================

if command -v oci &> /dev/null && [ -n "$OCI_NAMESPACE" ]; then
    log "Uploading to Oracle Object Storage..."

    oci os object put \
        --bucket-name "$OCI_BUCKET_NAME" \
        --namespace "$OCI_NAMESPACE" \
        --file "$BACKUP_FILE" \
        --name "$(basename $BACKUP_FILE)" \
        --force

    if [ $? -eq 0 ]; then
        log "✓ Backup uploaded to Object Storage: $OCI_BUCKET_NAME/$(basename $BACKUP_FILE)"
    else
        warn "Failed to upload to Object Storage (backup saved locally)"
    fi
else
    warn "OCI CLI not configured - backup saved locally only"
    if [ -z "$OCI_NAMESPACE" ]; then
        warn "Set OCI_NAMESPACE environment variable to enable Object Storage uploads"
    fi
fi

# =============================================================================
# STEP 4: Clean Old Backups (Local)
# =============================================================================

log "Cleaning up old local backups (retention: ${RETENTION_DAYS} days)..."
find "$BACKUP_DIR" -name "postgres_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
REMAINING=$(find "$BACKUP_DIR" -name "postgres_*.sql.gz" | wc -l)
log "✓ Local backups remaining: $REMAINING"

# =============================================================================
# STEP 5: Clean Old Backups (Object Storage)
# =============================================================================

if command -v oci &> /dev/null && [ -n "$OCI_NAMESPACE" ]; then
    log "Cleaning up old Object Storage backups..."

    # List objects and delete old ones (this is a simplified version)
    # In production, you might want to use lifecycle policies instead
    CUTOFF_DATE=$(date -d "${RETENTION_DAYS} days ago" +%Y-%m-%d)

    # Note: OCI CLI lifecycle policy is better for this
    warn "Consider configuring lifecycle policies in OCI for automatic deletion"
fi

# =============================================================================
# SUMMARY
# =============================================================================

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Backup completed successfully!"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Backup file: $BACKUP_FILE"
log "Size: $BACKUP_SIZE"
log "Timestamp: $TIMESTAMP"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit 0
