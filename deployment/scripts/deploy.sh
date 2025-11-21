#!/bin/bash
# =============================================================================
# DEPLOYMENT SCRIPT
# Deploy Multi-Agent Support System on Oracle Cloud
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

# Change to repository root
cd "$(dirname "$0")/../.."

section "1. PRE-FLIGHT CHECKS"

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    error "Docker is not installed. Run setup-server.sh first."
    exit 1
fi

# Check if docker compose is available
if ! docker compose version &> /dev/null; then
    error "Docker Compose is not available."
    exit 1
fi

log "✓ Docker: $(docker --version)"
log "✓ Docker Compose: $(docker compose version)"

# Check if .env file exists or Doppler is configured
if [ ! -f .env ] && ! command -v doppler &> /dev/null; then
    error "No .env file found and Doppler is not installed."
    error "Either create .env file or install Doppler: curl -sLf https://cli.doppler.com/install.sh | sh"
    exit 1
fi

if [ -f .env ]; then
    log "✓ Environment file found: .env"
    ENV_CMD=""
else
    log "✓ Doppler CLI detected"
    doppler setup --no-interactive || warn "Doppler not configured - using existing setup"
    ENV_CMD="doppler run --"
fi

# Check if SSL certificate exists
if [ ! -f deployment/nginx/ssl/cert.pem ] || [ ! -f deployment/nginx/ssl/key.pem ]; then
    warn "SSL certificate not found!"
    warn "Generating self-signed certificate..."
    ./deployment/nginx/generate-self-signed-cert.sh
fi

section "2. BUILD DOCKER IMAGES"

log "Building Docker images..."
$ENV_CMD docker compose build --pull

log "✓ Images built successfully"

section "3. CREATE REQUIRED DIRECTORIES"

log "Creating required directories..."
mkdir -p logs backups deployment/certbot/{www,conf}

log "✓ Directories created"

section "4. PULL EXTERNAL IMAGES"

log "Pulling external images..."
$ENV_CMD docker compose pull

log "✓ Images pulled"

section "5. START SERVICES"

log "Starting services..."

# Start database and cache first
log "Starting PostgreSQL and Redis..."
$ENV_CMD docker compose up -d postgres redis qdrant

# Wait for database to be ready
log "Waiting for database to be ready..."
sleep 10

until docker compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
    log "Waiting for PostgreSQL..."
    sleep 2
done

log "✓ PostgreSQL health check passed"
log "Waiting additional 10 seconds for PostgreSQL to fully initialize..."
sleep 10

log "✓ Database is ready"

# Run migrations
section "6. DATABASE MIGRATIONS"

log "Running database migrations..."
$ENV_CMD docker compose run --rm fastapi alembic upgrade head

log "✓ Migrations completed"

# Initialize knowledge base
section "7. INITIALIZE KNOWLEDGE BASE"

log "Initializing knowledge base..."
if $ENV_CMD docker compose run --rm fastapi python scripts/init_knowledge_base.py; then
    log "✓ Knowledge base initialized"
else
    warn "Knowledge base initialization failed or already initialized"
fi

# Start remaining services
section "8. START ALL SERVICES"

log "Starting all services..."
$ENV_CMD docker compose up -d

log "Waiting for services to be healthy..."
sleep 15

section "9. HEALTH CHECKS"

# Check container status
log "Checking container status..."
docker compose ps

echo ""

# Check API health
log "Checking API health..."
sleep 5

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    log "✓ API is healthy"
else
    warn "API health check failed - check logs with: docker compose logs fastapi"
fi

section "10. DEPLOYMENT SUMMARY"

echo ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Deployment completed successfully!"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me)
if [ -n "$PUBLIC_IP" ]; then
    info "Public IP: $PUBLIC_IP"
    echo ""
    info "Access points:"
    echo "  - API:        https://$PUBLIC_IP/api"
    echo "  - API Docs:   https://$PUBLIC_IP/api/docs"
    echo "  - Health:     https://$PUBLIC_IP/health"
    echo "  - Prometheus: http://$PUBLIC_IP:9090"
    echo "  - Grafana:    http://$PUBLIC_IP:3000"
    echo ""
    warn "⚠️  Using self-signed certificate - browsers will show security warning"
    echo ""
fi

info "Useful commands:"
echo "  - View logs:           docker compose logs -f"
echo "  - View specific logs:  docker compose logs -f fastapi"
echo "  - Restart service:     docker compose restart fastapi"
echo "  - Stop all:            docker compose down"
echo "  - Backup database:     ./deployment/scripts/backup-database.sh"
echo ""

info "Default Grafana credentials:"
echo "  - Username: admin"
echo "  - Password: (check GRAFANA_ADMIN_PASSWORD in .env or Doppler)"
echo ""

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit 0
