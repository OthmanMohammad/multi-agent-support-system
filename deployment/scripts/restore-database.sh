#!/bin/bash
# =============================================================================
# DATABASE RESTORE SCRIPT
# Restores PostgreSQL database from backup
# =============================================================================

set -e

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

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/home/ubuntu/multi-agent-system/backups}"
DB_NAME="${POSTGRES_DB:-support_agent}"
DB_USER="${POSTGRES_USER:-postgres}"

# Check arguments
if [ -z "$1" ]; then
    error "Usage: $0 <backup-file>"
    error "Example: $0 postgres_20250118_120000.sql.gz"
    echo ""
    echo "Available backups:"
    ls -lh "$BACKUP_DIR"/postgres_*.sql.gz 2>/dev/null || echo "No backups found in $BACKUP_DIR"
    exit 1
fi

BACKUP_FILE="$1"

# If relative path, prepend backup directory
if [[ "$BACKUP_FILE" != /* ]]; then
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILE}"
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# =============================================================================
# CONFIRMATION
# =============================================================================

warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
warn "WARNING: This will REPLACE the current database!"
warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
warn "Database: $DB_NAME"
warn "Backup file: $BACKUP_FILE"
warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    log "Restore cancelled"
    exit 0
fi

# =============================================================================
# STEP 1: Stop Application
# =============================================================================

log "Stopping FastAPI application..."
docker compose stop fastapi || warn "Could not stop fastapi container"

# =============================================================================
# STEP 2: Decompress Backup (if needed)
# =============================================================================

if [[ "$BACKUP_FILE" == *.gz ]]; then
    log "Decompressing backup..."
    TEMP_FILE="${BACKUP_FILE%.gz}"
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
    RESTORE_FILE="$TEMP_FILE"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

# =============================================================================
# STEP 3: Restore Database
# =============================================================================

log "Restoring database from backup..."

docker compose exec -T postgres psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
docker compose exec -T postgres psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;"
docker compose exec -T postgres psql -U "$DB_USER" -d "$DB_NAME" < "$RESTORE_FILE"

if [ $? -eq 0 ]; then
    log "✓ Database restored successfully"
else
    error "Failed to restore database"

    # Clean up temp file
    if [ -n "$TEMP_FILE" ] && [ -f "$TEMP_FILE" ]; then
        rm -f "$TEMP_FILE"
    fi

    exit 1
fi

# =============================================================================
# STEP 4: Clean Up
# =============================================================================

if [ -n "$TEMP_FILE" ] && [ -f "$TEMP_FILE" ]; then
    log "Cleaning up temporary files..."
    rm -f "$TEMP_FILE"
fi

# =============================================================================
# STEP 5: Restart Application
# =============================================================================

log "Starting FastAPI application..."
docker compose start fastapi

# Wait for health check
log "Waiting for application to become healthy..."
sleep 10

if docker compose ps fastapi | grep -q "Up"; then
    log "✓ Application restarted successfully"
else
    warn "Application may not be healthy - check logs with: docker compose logs fastapi"
fi

# =============================================================================
# SUMMARY
# =============================================================================

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Database restore completed successfully!"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Database: $DB_NAME"
log "Restored from: $(basename $BACKUP_FILE)"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit 0
