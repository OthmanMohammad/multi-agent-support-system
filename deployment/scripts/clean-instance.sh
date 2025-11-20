#!/bin/bash
# =============================================================================
# CLEAN INSTANCE SCRIPT
# Safely removes all Docker containers, volumes, and project files
# WITHOUT deleting the Oracle Cloud instance itself
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Confirmation prompt
section "⚠️  INSTANCE CLEANUP WARNING"
echo ""
warn "This script will remove:"
echo "  - All Docker containers (running and stopped)"
echo "  - All Docker volumes (database data, logs, etc.)"
echo "  - All Docker networks"
echo "  - Project directory: ~/multi-agent-support-system"
echo "  - Doppler configuration: ~/.doppler"
echo ""
info "This will NOT remove:"
echo "  - The Oracle Cloud instance itself"
echo "  - Docker installation"
echo "  - System packages"
echo "  - SSH keys"
echo "  - Firewall configuration"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to proceed): " -r
echo
if [[ ! $REPLY =~ ^yes$ ]]; then
    error "Cleanup cancelled"
    exit 1
fi

section "1. STOPPING ALL DOCKER CONTAINERS"

log "Navigating to project directory..."
cd ~/multi-agent-support-system 2>/dev/null || log "Project directory not found, continuing..."

log "Stopping Docker Compose stack..."
docker compose down -v 2>/dev/null || log "No compose stack found"

log "Stopping all running containers..."
if [ "$(docker ps -q)" ]; then
    docker stop $(docker ps -q) 2>/dev/null || log "No containers to stop"
else
    log "No running containers found"
fi

log "✓ All containers stopped"

section "2. REMOVING DOCKER CONTAINERS"

log "Removing all containers..."
if [ "$(docker ps -aq)" ]; then
    docker rm $(docker ps -aq) 2>/dev/null || log "No containers to remove"
else
    log "No containers to remove"
fi

log "✓ All containers removed"

section "3. REMOVING DOCKER VOLUMES"

log "Removing all Docker volumes..."
if [ "$(docker volume ls -q)" ]; then
    docker volume rm $(docker volume ls -q) 2>/dev/null || log "Some volumes in use, forcing removal..."
    docker volume prune -f 2>/dev/null || log "Volume cleanup complete"
else
    log "No volumes to remove"
fi

log "✓ All volumes removed"

section "4. REMOVING DOCKER NETWORKS"

log "Removing custom networks..."
docker network prune -f 2>/dev/null || log "Network cleanup complete"

log "✓ Networks cleaned"

section "5. DOCKER SYSTEM CLEANUP"

log "Running full system cleanup..."
docker system prune -af --volumes 2>/dev/null || log "System cleanup complete"

log "✓ Docker system cleaned"

section "6. REMOVING PROJECT DIRECTORY"

cd ~
log "Removing project directory..."
rm -rf ~/multi-agent-support-system 2>/dev/null || log "Project directory already removed"
rm -rf ~/multi-agent-system 2>/dev/null || log "Old project directory removed"

log "✓ Project directory removed"

section "7. REMOVING DOPPLER CONFIGURATION"

log "Removing Doppler configuration..."
rm -rf ~/.doppler 2>/dev/null || log "Doppler config already removed"

log "✓ Doppler configuration removed"

section "8. VERIFICATION"

log "Verifying cleanup..."
echo ""

info "Docker Containers:"
docker ps -a
echo ""

info "Docker Volumes:"
docker volume ls
echo ""

info "Docker Networks:"
docker network ls
echo ""

info "Project Directory:"
ls -la ~ | grep multi || echo "  (none found - clean!)"
echo ""

info "Disk Space:"
df -h /
echo ""

section "✅ CLEANUP COMPLETE"

echo ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Instance cleaned successfully!"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
info "Your Oracle Cloud instance is still running ✅"
info "Docker is still installed ✅"
info "You can now deploy fresh from scratch ✅"
echo ""
info "NEXT STEPS:"
echo ""
echo "1. Clone repository:"
echo "   cd ~"
echo "   git clone https://github.com/OthmanMohammad/multi-agent-support-system.git"
echo "   cd multi-agent-support-system"
echo ""
echo "2. Follow deployment guide:"
echo "   cat deployment/scripts/CLEAN_DEPLOY_ORACLE.md"
echo ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit 0
