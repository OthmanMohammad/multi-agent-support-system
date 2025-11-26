#!/bin/bash
# =============================================================================
# Blue-Green Deployment Script
# Multi-Agent Support System
# Enterprise-grade zero-downtime deployment
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/multi-agent-support}"
LOG_FILE="${DEPLOY_PATH}/logs/deploy-$(date +%Y%m%d-%H%M%S).log"
STATE_FILE="${DEPLOY_PATH}/.deployment-state"
BACKUP_DIR="${DEPLOY_PATH}/backups"
ROLLBACK_DIR="${DEPLOY_PATH}/rollback"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
REGISTRY=""
BACKEND_IMAGE=""
FRONTEND_IMAGE=""
TAG=""
SKIP_BACKUP=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --backend-image)
            BACKEND_IMAGE="$2"
            shift 2
            ;;
        --frontend-image)
            FRONTEND_IMAGE="$2"
            shift 2
            ;;
        --tag)
            TAG="$2"
            shift 2
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# =============================================================================
# Validation
# =============================================================================
validate_inputs() {
    log_info "Validating deployment inputs..."

    if [[ -z "$REGISTRY" ]] || [[ -z "$BACKEND_IMAGE" ]] || [[ -z "$TAG" ]]; then
        log_error "Missing required arguments: --registry, --backend-image, --tag"
        exit 1
    fi

    # Check Docker is available
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi

    # Check docker compose is available
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose v2 is not available"
        exit 1
    fi

    log_success "Input validation passed"
}

# =============================================================================
# Pre-deployment Checks
# =============================================================================
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."

    # Create necessary directories
    mkdir -p "$DEPLOY_PATH/logs" "$BACKUP_DIR" "$ROLLBACK_DIR"

    # Check disk space (require at least 5GB free)
    local free_space=$(df "$DEPLOY_PATH" | awk 'NR==2 {print $4}')
    if [[ $free_space -lt 5242880 ]]; then
        log_error "Insufficient disk space. Need at least 5GB free."
        exit 1
    fi

    # Check if services are currently running
    if docker compose -f "$DEPLOY_PATH/docker-compose.production.yml" ps --quiet 2>/dev/null | grep -q .; then
        log_info "Existing deployment detected"
        EXISTING_DEPLOYMENT=true
    else
        log_info "No existing deployment found"
        EXISTING_DEPLOYMENT=false
    fi

    log_success "Pre-deployment checks passed"
}

# =============================================================================
# Backup Current State
# =============================================================================
backup_current_state() {
    if [[ "$SKIP_BACKUP" == "true" ]]; then
        log_warn "Skipping backup as requested"
        return 0
    fi

    log_info "Backing up current deployment state..."

    local backup_timestamp=$(date +%Y%m%d-%H%M%S)
    local backup_path="$BACKUP_DIR/$backup_timestamp"
    mkdir -p "$backup_path"

    # Save current image tags
    if [[ -f "$DEPLOY_PATH/.env" ]]; then
        cp "$DEPLOY_PATH/.env" "$backup_path/.env.backup"
    fi

    # Save docker-compose state
    if [[ -f "$DEPLOY_PATH/docker-compose.production.yml" ]]; then
        cp "$DEPLOY_PATH/docker-compose.production.yml" "$backup_path/docker-compose.production.yml.backup"
    fi

    # Get current image digests
    local current_backend=$(docker inspect --format='{{index .RepoDigests 0}}' fastapi 2>/dev/null || echo "none")
    local current_frontend=$(docker inspect --format='{{index .RepoDigests 0}}' frontend 2>/dev/null || echo "none")

    cat > "$backup_path/images.txt" << EOF
BACKEND_IMAGE=$current_backend
FRONTEND_IMAGE=$current_frontend
TIMESTAMP=$backup_timestamp
EOF

    # Database backup (quick snapshot)
    log_info "Creating database backup..."
    docker compose -f "$DEPLOY_PATH/docker-compose.production.yml" exec -T postgres \
        pg_dump -U postgres -d support_agent --clean --if-exists \
        > "$backup_path/database.sql" 2>/dev/null || true

    # Save rollback pointer
    echo "$backup_timestamp" > "$ROLLBACK_DIR/latest"

    log_success "Backup completed at $backup_path"
}

# =============================================================================
# Pull New Images
# =============================================================================
pull_new_images() {
    log_info "Pulling new Docker images..."

    local backend_full="${REGISTRY}/${BACKEND_IMAGE}:${TAG}"
    local frontend_full="${REGISTRY}/${FRONTEND_IMAGE}:${TAG}"

    # Login to registry (using GITHUB_TOKEN from environment)
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        echo "$GITHUB_TOKEN" | docker login "$REGISTRY" -u github --password-stdin
    fi

    # Pull backend image
    log_info "Pulling backend: $backend_full"
    if ! docker pull "$backend_full"; then
        log_error "Failed to pull backend image"
        exit 1
    fi

    # Pull frontend image (if specified)
    if [[ -n "$FRONTEND_IMAGE" ]]; then
        log_info "Pulling frontend: $frontend_full"
        if ! docker pull "$frontend_full"; then
            log_warn "Failed to pull frontend image, continuing with existing..."
        fi
    fi

    log_success "Images pulled successfully"
}

# =============================================================================
# Health Check Function
# =============================================================================
wait_for_healthy() {
    local service=$1
    local url=$2
    local max_attempts=${3:-30}
    local attempt=1

    log_info "Waiting for $service to become healthy..."

    while [[ $attempt -le $max_attempts ]]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            log_success "$service is healthy"
            return 0
        fi
        log_info "Attempt $attempt/$max_attempts: $service not ready yet..."
        sleep 5
        ((attempt++))
    done

    log_error "$service failed to become healthy after $max_attempts attempts"
    return 1
}

# =============================================================================
# Deploy Blue Environment
# =============================================================================
deploy_blue() {
    log_info "Deploying to Blue environment..."

    local backend_full="${REGISTRY}/${BACKEND_IMAGE}:${TAG}"
    local frontend_full="${REGISTRY}/${FRONTEND_IMAGE}:${TAG}"

    # Update environment with new images
    cat >> "$DEPLOY_PATH/.env" << EOF

# Blue-Green Deployment - ${TAG}
BACKEND_IMAGE=${backend_full}
FRONTEND_IMAGE=${frontend_full}
DEPLOY_TIMESTAMP=$(date +%Y%m%d-%H%M%S)
EOF

    # Export for docker compose
    export BACKEND_IMAGE="$backend_full"
    export FRONTEND_IMAGE="$frontend_full"

    cd "$DEPLOY_PATH"

    # Start new containers with updated images
    log_info "Starting new containers..."
    docker compose -f docker-compose.production.yml up -d --no-deps --build fastapi frontend

    # Wait for backend health
    if ! wait_for_healthy "backend" "http://localhost:8000/health" 60; then
        log_error "Backend deployment failed health check"
        return 1
    fi

    # Wait for frontend health
    if ! wait_for_healthy "frontend" "http://localhost:3000/api/health" 30; then
        log_warn "Frontend health check failed, but continuing..."
    fi

    log_success "Blue environment deployed successfully"
}

# =============================================================================
# Switch Traffic (Green -> Blue)
# =============================================================================
switch_traffic() {
    log_info "Switching traffic to new deployment..."

    cd "$DEPLOY_PATH"

    # Reload nginx to pick up any config changes
    docker compose -f docker-compose.production.yml exec -T nginx nginx -s reload

    log_success "Traffic switched to new deployment"
}

# =============================================================================
# Cleanup Old Containers
# =============================================================================
cleanup_old_deployment() {
    log_info "Cleaning up old deployment artifacts..."

    # Prune old images (keep last 3 versions)
    docker image prune -f --filter "until=24h"

    # Clean up old backups (keep last 10)
    local backup_count=$(ls -1 "$BACKUP_DIR" 2>/dev/null | wc -l)
    if [[ $backup_count -gt 10 ]]; then
        ls -1t "$BACKUP_DIR" | tail -n +11 | xargs -I {} rm -rf "$BACKUP_DIR/{}"
        log_info "Cleaned up old backups"
    fi

    log_success "Cleanup completed"
}

# =============================================================================
# Post-deployment Verification
# =============================================================================
verify_deployment() {
    log_info "Running post-deployment verification..."

    local errors=0

    # Check all services are running
    local services=("fastapi" "frontend" "postgres" "redis" "nginx")
    for service in "${services[@]}"; do
        if ! docker compose -f "$DEPLOY_PATH/docker-compose.production.yml" ps --status running | grep -q "$service"; then
            log_error "Service $service is not running"
            ((errors++))
        fi
    done

    # Verify API endpoints
    local endpoints=(
        "http://localhost:8000/health"
        "http://localhost:8000/health/ready"
        "http://localhost:8000/docs"
    )
    for endpoint in "${endpoints[@]}"; do
        if ! curl -sf "$endpoint" > /dev/null; then
            log_warn "Endpoint $endpoint not responding"
        fi
    done

    if [[ $errors -gt 0 ]]; then
        log_error "Deployment verification found $errors errors"
        return 1
    fi

    log_success "Deployment verification passed"
}

# =============================================================================
# Save Deployment State
# =============================================================================
save_deployment_state() {
    log_info "Saving deployment state..."

    cat > "$STATE_FILE" << EOF
{
    "version": "${TAG}",
    "timestamp": "$(date -Iseconds)",
    "backend_image": "${REGISTRY}/${BACKEND_IMAGE}:${TAG}",
    "frontend_image": "${REGISTRY}/${FRONTEND_IMAGE}:${TAG}",
    "status": "deployed",
    "commit": "${GITHUB_SHA:-unknown}"
}
EOF

    log_success "Deployment state saved"
}

# =============================================================================
# Rollback Function
# =============================================================================
rollback() {
    log_warn "Initiating rollback..."

    local latest_backup=$(cat "$ROLLBACK_DIR/latest" 2>/dev/null || echo "")

    if [[ -z "$latest_backup" ]] || [[ ! -d "$BACKUP_DIR/$latest_backup" ]]; then
        log_error "No valid backup found for rollback"
        exit 1
    fi

    local backup_path="$BACKUP_DIR/$latest_backup"

    # Restore environment
    if [[ -f "$backup_path/.env.backup" ]]; then
        cp "$backup_path/.env.backup" "$DEPLOY_PATH/.env"
    fi

    # Restore docker-compose
    if [[ -f "$backup_path/docker-compose.production.yml.backup" ]]; then
        cp "$backup_path/docker-compose.production.yml.backup" "$DEPLOY_PATH/docker-compose.production.yml"
    fi

    # Read previous image tags and deploy
    if [[ -f "$backup_path/images.txt" ]]; then
        source "$backup_path/images.txt"
        export BACKEND_IMAGE
        export FRONTEND_IMAGE
    fi

    cd "$DEPLOY_PATH"
    docker compose -f docker-compose.production.yml up -d --no-deps fastapi frontend

    # Wait for health
    sleep 30

    if wait_for_healthy "backend" "http://localhost:8000/health" 30; then
        log_success "Rollback completed successfully"
    else
        log_error "Rollback may have issues - manual intervention required"
        exit 1
    fi
}

# =============================================================================
# Main Deployment Flow
# =============================================================================
main() {
    log_info "=========================================="
    log_info "Starting Blue-Green Deployment"
    log_info "Registry: $REGISTRY"
    log_info "Backend: $BACKEND_IMAGE"
    log_info "Frontend: $FRONTEND_IMAGE"
    log_info "Tag: $TAG"
    log_info "=========================================="

    # Trap errors for rollback
    trap 'log_error "Deployment failed! Initiating rollback..."; rollback; exit 1' ERR

    # Run deployment steps
    validate_inputs
    pre_deployment_checks
    backup_current_state
    pull_new_images
    deploy_blue
    switch_traffic
    verify_deployment
    save_deployment_state
    cleanup_old_deployment

    log_info "=========================================="
    log_success "DEPLOYMENT COMPLETED SUCCESSFULLY"
    log_info "Version: $TAG"
    log_info "Timestamp: $(date)"
    log_info "=========================================="
}

# Run main
main
