#!/bin/bash
# =============================================================================
# Rollback Script
# Multi-Agent Support System
# Restore previous deployment version
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/multi-agent-support}"
BACKUP_DIR="${DEPLOY_PATH}/backups"
ROLLBACK_DIR="${DEPLOY_PATH}/rollback"
LOG_FILE="${DEPLOY_PATH}/logs/rollback-$(date +%Y%m%d-%H%M%S).log"

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
AUTO_ROLLBACK=false
SPECIFIC_VERSION=""
LIST_BACKUPS=false
RESTORE_DB=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --auto)
            AUTO_ROLLBACK=true
            shift
            ;;
        --version)
            SPECIFIC_VERSION="$2"
            shift 2
            ;;
        --list)
            LIST_BACKUPS=true
            shift
            ;;
        --restore-db)
            RESTORE_DB=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --auto          Automatic rollback (used by CI/CD)"
            echo "  --version VER   Rollback to specific version"
            echo "  --list          List available backups"
            echo "  --restore-db    Also restore database from backup"
            echo "  -h, --help      Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# =============================================================================
# List Available Backups
# =============================================================================
list_backups() {
    log_info "Available backups:"
    echo ""
    echo "VERSION              | BACKEND IMAGE                           | TIMESTAMP"
    echo "-------------------- | --------------------------------------- | ---------"

    for backup in $(ls -1t "$BACKUP_DIR" 2>/dev/null); do
        if [[ -f "$BACKUP_DIR/$backup/images.txt" ]]; then
            source "$BACKUP_DIR/$backup/images.txt"
            printf "%-20s | %-39s | %s\n" "$backup" "${BACKEND_IMAGE:0:39}" "$TIMESTAMP"
        fi
    done

    echo ""
    local latest=$(cat "$ROLLBACK_DIR/latest" 2>/dev/null || echo "none")
    log_info "Latest backup pointer: $latest"
}

if [[ "$LIST_BACKUPS" == "true" ]]; then
    list_backups
    exit 0
fi

# =============================================================================
# Get Backup Version
# =============================================================================
get_backup_version() {
    if [[ -n "$SPECIFIC_VERSION" ]]; then
        if [[ -d "$BACKUP_DIR/$SPECIFIC_VERSION" ]]; then
            echo "$SPECIFIC_VERSION"
        else
            log_error "Backup version '$SPECIFIC_VERSION' not found"
            exit 1
        fi
    else
        local latest=$(cat "$ROLLBACK_DIR/latest" 2>/dev/null || echo "")
        if [[ -z "$latest" ]] || [[ ! -d "$BACKUP_DIR/$latest" ]]; then
            log_error "No valid backup found"
            exit 1
        fi
        echo "$latest"
    fi
}

# =============================================================================
# Health Check
# =============================================================================
wait_for_healthy() {
    local service=$1
    local url=$2
    local max_attempts=${3:-30}
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            return 0
        fi
        sleep 5
        ((attempt++))
    done
    return 1
}

# =============================================================================
# Perform Rollback
# =============================================================================
perform_rollback() {
    local backup_version=$(get_backup_version)
    local backup_path="$BACKUP_DIR/$backup_version"

    log_info "=========================================="
    log_info "Starting Rollback"
    log_info "Restoring to: $backup_version"
    log_info "=========================================="

    # Confirmation (skip if auto)
    if [[ "$AUTO_ROLLBACK" != "true" ]]; then
        read -p "Are you sure you want to rollback to $backup_version? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Rollback cancelled"
            exit 0
        fi
    fi

    cd "$DEPLOY_PATH"

    # Load backup images
    if [[ -f "$backup_path/images.txt" ]]; then
        source "$backup_path/images.txt"
        log_info "Backend image: $BACKEND_IMAGE"
        log_info "Frontend image: $FRONTEND_IMAGE"
    else
        log_error "Backup images.txt not found"
        exit 1
    fi

    # Export for docker compose
    export BACKEND_IMAGE
    export FRONTEND_IMAGE

    # Restore .env if exists
    if [[ -f "$backup_path/.env.backup" ]]; then
        log_info "Restoring environment configuration..."
        cp "$backup_path/.env.backup" "$DEPLOY_PATH/.env"
    fi

    # Pull the backup images (they might have been pruned)
    log_info "Ensuring backup images are available..."
    docker pull "$BACKEND_IMAGE" 2>/dev/null || true
    docker pull "$FRONTEND_IMAGE" 2>/dev/null || true

    # Stop current containers
    log_info "Stopping current containers..."
    docker compose -f docker-compose.production.yml stop fastapi frontend || true

    # Start with backup images
    log_info "Starting containers with backup images..."
    docker compose -f docker-compose.production.yml up -d --no-deps fastapi frontend

    # Restore database if requested
    if [[ "$RESTORE_DB" == "true" ]] && [[ -f "$backup_path/database.sql" ]]; then
        log_info "Restoring database from backup..."
        log_warn "This will REPLACE current database data!"

        if [[ "$AUTO_ROLLBACK" != "true" ]]; then
            read -p "Continue with database restore? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "Skipping database restore"
            else
                docker compose -f docker-compose.production.yml exec -T postgres \
                    psql -U postgres -d support_agent < "$backup_path/database.sql"
                log_success "Database restored"
            fi
        fi
    fi

    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 10

    if wait_for_healthy "backend" "http://localhost:8000/health" 30; then
        log_success "Backend is healthy"
    else
        log_error "Backend health check failed after rollback"
        exit 1
    fi

    if wait_for_healthy "frontend" "http://localhost:3000/api/health" 20; then
        log_success "Frontend is healthy"
    else
        log_warn "Frontend health check failed, but continuing..."
    fi

    # Reload nginx
    docker compose -f docker-compose.production.yml exec -T nginx nginx -s reload || true

    # Update deployment state
    cat > "${DEPLOY_PATH}/.deployment-state" << EOF
{
    "version": "${backup_version}",
    "timestamp": "$(date -Iseconds)",
    "backend_image": "${BACKEND_IMAGE}",
    "frontend_image": "${FRONTEND_IMAGE}",
    "status": "rolled_back",
    "rollback_from": "current"
}
EOF

    log_info "=========================================="
    log_success "ROLLBACK COMPLETED SUCCESSFULLY"
    log_info "Restored to: $backup_version"
    log_info "Timestamp: $(date)"
    log_info "=========================================="
}

# =============================================================================
# Main
# =============================================================================
mkdir -p "$(dirname "$LOG_FILE")"
perform_rollback
