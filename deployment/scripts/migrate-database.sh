#!/bin/bash
# =============================================================================
# Database Migration Script
# Multi-Agent Support System
# Safe Alembic migrations with backup and rollback capability
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/multi-agent-support}"
BACKUP_DIR="${DEPLOY_PATH}/backups/migrations"
LOG_FILE="${DEPLOY_PATH}/logs/migration-$(date +%Y%m%d-%H%M%S).log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# =============================================================================
# Logging
# =============================================================================
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "${BLUE}$*${NC}"; }
log_success() { log "SUCCESS" "${GREEN}$*${NC}"; }
log_warn() { log "WARN" "${YELLOW}$*${NC}"; }
log_error() { log "ERROR" "${RED}$*${NC}"; }

# =============================================================================
# Parse Arguments
# =============================================================================
ACTION="upgrade"
REVISION="head"
DRY_RUN=false
SKIP_BACKUP=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        upgrade)
            ACTION="upgrade"
            REVISION="${2:-head}"
            shift
            ;;
        downgrade)
            ACTION="downgrade"
            REVISION="${2:--1}"
            shift
            ;;
        current)
            ACTION="current"
            shift
            ;;
        history)
            ACTION="history"
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [ACTION] [REVISION] [OPTIONS]"
            echo ""
            echo "Actions:"
            echo "  upgrade [REV]    Upgrade to revision (default: head)"
            echo "  downgrade [REV]  Downgrade by revision (default: -1)"
            echo "  current          Show current revision"
            echo "  history          Show migration history"
            echo ""
            echo "Options:"
            echo "  --dry-run        Show what would be done without executing"
            echo "  --skip-backup    Skip database backup before migration"
            echo "  --force          Skip confirmation prompts"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

# =============================================================================
# Create Backup
# =============================================================================
create_backup() {
    if [[ "$SKIP_BACKUP" == "true" ]]; then
        log_warn "Skipping backup as requested"
        return 0
    fi

    log_info "Creating database backup before migration..."

    mkdir -p "$BACKUP_DIR"
    local backup_file="$BACKUP_DIR/pre-migration-$(date +%Y%m%d-%H%M%S).sql"

    cd "$DEPLOY_PATH"

    # Get current revision for backup naming
    local current_rev=$(docker compose -f docker-compose.production.yml exec -T fastapi \
        alembic current 2>/dev/null | grep -oP '[a-f0-9]+(?= \(head\))' || echo "unknown")

    backup_file="$BACKUP_DIR/pre-migration-${current_rev}-$(date +%Y%m%d-%H%M%S).sql"

    if docker compose -f docker-compose.production.yml exec -T postgres \
        pg_dump -U postgres -d support_agent --clean --if-exists > "$backup_file"; then

        # Compress the backup
        gzip "$backup_file"
        log_success "Backup created: ${backup_file}.gz"

        # Save backup reference
        echo "${backup_file}.gz" > "$BACKUP_DIR/latest-migration-backup"
    else
        log_error "Failed to create backup"
        exit 1
    fi
}

# =============================================================================
# Show Current Revision
# =============================================================================
show_current() {
    log_info "Current database revision:"
    cd "$DEPLOY_PATH"
    docker compose -f docker-compose.production.yml exec -T fastapi alembic current
}

# =============================================================================
# Show History
# =============================================================================
show_history() {
    log_info "Migration history:"
    cd "$DEPLOY_PATH"
    docker compose -f docker-compose.production.yml exec -T fastapi alembic history --verbose
}

# =============================================================================
# Run Migration
# =============================================================================
run_migration() {
    cd "$DEPLOY_PATH"

    log_info "=========================================="
    log_info "Database Migration"
    log_info "Action: $ACTION"
    log_info "Revision: $REVISION"
    log_info "=========================================="

    # Show current state
    log_info "Current revision:"
    docker compose -f docker-compose.production.yml exec -T fastapi alembic current || true

    # Show what will happen
    if [[ "$ACTION" == "upgrade" ]]; then
        log_info "Pending migrations:"
        docker compose -f docker-compose.production.yml exec -T fastapi \
            alembic history --indicate-current 2>/dev/null || true
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN - No changes will be made"
        log_info "Would run: alembic $ACTION $REVISION"
        return 0
    fi

    # Confirmation
    if [[ "$FORCE" != "true" ]]; then
        read -p "Proceed with migration? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Migration cancelled"
            exit 0
        fi
    fi

    # Create backup
    create_backup

    # Run migration
    log_info "Running migration..."
    if docker compose -f docker-compose.production.yml exec -T fastapi \
        alembic "$ACTION" "$REVISION"; then
        log_success "Migration completed successfully"

        # Show new state
        log_info "New revision:"
        docker compose -f docker-compose.production.yml exec -T fastapi alembic current
    else
        log_error "Migration failed!"
        log_warn "To rollback, run: $0 downgrade -1"
        log_warn "To restore from backup: $0 restore"
        exit 1
    fi
}

# =============================================================================
# Restore from Backup
# =============================================================================
restore_from_backup() {
    log_info "Restoring database from latest migration backup..."

    local latest_backup=$(cat "$BACKUP_DIR/latest-migration-backup" 2>/dev/null || echo "")

    if [[ -z "$latest_backup" ]] || [[ ! -f "$latest_backup" ]]; then
        log_error "No backup file found"
        exit 1
    fi

    log_warn "This will REPLACE the current database with the backup!"
    log_info "Backup file: $latest_backup"

    if [[ "$FORCE" != "true" ]]; then
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Restore cancelled"
            exit 0
        fi
    fi

    cd "$DEPLOY_PATH"

    # Decompress if needed
    local sql_file="$latest_backup"
    if [[ "$latest_backup" == *.gz ]]; then
        sql_file="${latest_backup%.gz}"
        gunzip -k "$latest_backup" 2>/dev/null || true
    fi

    # Restore
    if docker compose -f docker-compose.production.yml exec -T postgres \
        psql -U postgres -d support_agent < "$sql_file"; then
        log_success "Database restored from backup"
        rm -f "$sql_file"  # Remove uncompressed file
    else
        log_error "Failed to restore database"
        exit 1
    fi
}

# =============================================================================
# Main
# =============================================================================
mkdir -p "$(dirname "$LOG_FILE")"

case "$ACTION" in
    current)
        show_current
        ;;
    history)
        show_history
        ;;
    upgrade|downgrade)
        run_migration
        ;;
    restore)
        restore_from_backup
        ;;
    *)
        log_error "Unknown action: $ACTION"
        exit 1
        ;;
esac
