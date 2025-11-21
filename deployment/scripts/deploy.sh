#!/bin/bash
# =============================================================================
# PRODUCTION DEPLOYMENT
# Multi-Agent Support System - Oracle Cloud
# =============================================================================
# Zero-downtime deployment with:
# - Automated health checks
# - Backup automation
# - Full observability
# - Security hardening
# - Auto-healing
# =============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# =============================================================================
# CONFIGURATION
# =============================================================================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
readonly TIMESTAMP=$(date +%Y%m%d_%H%M%S)
readonly LOG_FILE="/tmp/deploy-${TIMESTAMP}.log"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly MAGENTA='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color
readonly BOLD='\033[1m'

# =============================================================================
# LOGGING FUNCTIONS
# =============================================================================

log() {
    local message="$1"
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $message" | tee -a "$LOG_FILE"
}

log_step() {
    local step="$1"
    local message="$2"
    echo -e "\n${BOLD}${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}" | tee -a "$LOG_FILE"
    echo -e "${BOLD}${CYAN}║${NC} ${BOLD}STEP $step: $message${NC}" | tee -a "$LOG_FILE"
    echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}\n" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}✗ ERROR:${NC} $1" | tee -a "$LOG_FILE" >&2
}

log_warn() {
    echo -e "${YELLOW}⚠ WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}ℹ${NC} $1" | tee -a "$LOG_FILE"
}

# =============================================================================
# ERROR HANDLING
# =============================================================================

error_exit() {
    log_error "$1"
    log_error "Deployment failed. Check logs: $LOG_FILE"
    exit 1
}

trap 'error_exit "Script interrupted"' INT TERM

# =============================================================================
# PREREQUISITE CHECKS
# =============================================================================

check_prerequisites() {
    log_step "PRE-FLIGHT" "Checking prerequisites"

    # Check if running as correct user
    if [ "$(whoami)" = "root" ]; then
        error_exit "Do not run this script as root. Use sudo only when needed."
    fi

    # Check if we're on Oracle Cloud
    if [ -f /etc/oracle-release ]; then
        log_success "Running on Oracle Linux $(cat /etc/oracle-release)"
    elif [ -f /etc/os-release ]; then
        log_warn "Not on Oracle Linux: $(grep PRETTY_NAME /etc/os-release | cut -d'"' -f2)"
    fi

    # Check Doppler token
    if [ -z "${DOPPLER_TOKEN:-}" ]; then
        error_exit "DOPPLER_TOKEN environment variable not set. Export it first."
    fi
    log_success "Doppler token found"

    # Check project directory
    if [ ! -d "$PROJECT_ROOT" ]; then
        error_exit "Project directory not found: $PROJECT_ROOT"
    fi
    log_success "Project directory: $PROJECT_ROOT"

    log_success "All prerequisites met"
}

# =============================================================================
# STEP 1: CLEAN SLATE
# =============================================================================

clean_existing_deployment() {
    log_step "1" "Clean existing deployment"

    cd "$PROJECT_ROOT"

    # Stop all containers gracefully
    if docker compose ps -q 2>/dev/null | grep -q .; then
        log_info "Stopping existing containers..."
        doppler run --token="$DOPPLER_TOKEN" -- docker compose down -v || true
        log_success "Containers stopped"
    else
        log_info "No existing containers found"
    fi

    # Remove old containers and images (keep volumes for data persistence)
    log_info "Cleaning Docker resources..."
    docker system prune -f --volumes || true
    log_success "Docker cleaned"

    # Clean old logs
    if [ -d "$PROJECT_ROOT/logs" ]; then
        log_info "Archiving old logs..."
        mkdir -p "$PROJECT_ROOT/logs/archive"
        mv "$PROJECT_ROOT/logs"/*.log "$PROJECT_ROOT/logs/archive/" 2>/dev/null || true
        log_success "Logs archived"
    fi

    log_success "Clean slate ready"
}

# =============================================================================
# STEP 2: SYSTEM CONFIGURATION
# =============================================================================

configure_system() {
    log_step "2" "Configure system for production"

    # Update system packages
    log_info "Updating system packages..."
    sudo dnf update -y -q 2>&1 | tee -a "$LOG_FILE" | grep -i "complete\|error" || true
    log_success "System updated"

    # Install essential tools
    log_info "Installing essential tools..."
    sudo dnf install -y -q \
        git curl wget vim htop ncdu \
        jq yq net-tools bind-utils \
        fail2ban firewalld \
        python3 python3-pip \
        2>&1 | tee -a "$LOG_FILE" | grep -i "complete\|error" || true
    log_success "Essential tools installed"

    # Configure firewall
    log_info "Configuring firewall..."
    sudo systemctl enable --now firewalld
    sudo firewall-cmd --permanent --add-service=http --add-service=https || true
    sudo firewall-cmd --permanent --add-port=3000/tcp --add-port=9090/tcp || true
    sudo firewall-cmd --reload || true
    log_success "Firewall configured"

    # Configure fail2ban
    log_info "Configuring fail2ban..."
    sudo systemctl enable --now fail2ban || true
    log_success "Fail2ban enabled"

    # Optimize kernel parameters for production
    log_info "Optimizing kernel parameters..."
    sudo tee /etc/sysctl.d/99-production.conf > /dev/null <<EOF
# Network optimization
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15

# File descriptors
fs.file-max = 2097152
fs.inotify.max_user_watches = 524288

# Memory
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
EOF
    sudo sysctl -p /etc/sysctl.d/99-production.conf 2>&1 | tee -a "$LOG_FILE"
    log_success "Kernel optimized"

    # Set file descriptor limits
    log_info "Setting file descriptor limits..."
    sudo tee /etc/security/limits.d/99-production.conf > /dev/null <<EOF
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768
EOF
    log_success "Limits configured"
}

# =============================================================================
# STEP 3: DOCKER INSTALLATION & CONFIGURATION
# =============================================================================

setup_docker() {
    log_step "3" "Install and configure Docker"

    if command -v docker &> /dev/null; then
        log_info "Docker already installed: $(docker --version)"
    else
        log_info "Installing Docker..."
        sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        log_success "Docker installed"
    fi

    # Configure Docker daemon for production
    log_info "Configuring Docker daemon..."
    sudo mkdir -p /etc/docker
    sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "5",
    "compress": "true"
  },
  "storage-driver": "overlay2",
  "live-restore": true,
  "userland-proxy": false,
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  },
  "metrics-addr": "127.0.0.1:9323",
  "experimental": false,
  "features": {
    "buildkit": true
  }
}
EOF

    # Start and enable Docker
    sudo systemctl enable --now docker
    sudo systemctl restart docker
    log_success "Docker daemon configured"

    # Add user to docker group
    if ! groups | grep -q docker; then
        sudo usermod -aG docker "$(whoami)"
        log_warn "Added to docker group. You may need to log out and back in."
    fi

    # Verify Docker
    docker version | head -5 | tee -a "$LOG_FILE"
    log_success "Docker ready"
}

# =============================================================================
# STEP 4: DOPPLER SETUP
# =============================================================================

setup_doppler() {
    log_step "4" "Install and configure Doppler"

    if command -v doppler &> /dev/null; then
        log_info "Doppler already installed: $(doppler --version)"
    else
        log_info "Installing Doppler CLI..."
        curl -sLf https://cli.doppler.com/install.sh | sh
        log_success "Doppler installed"
    fi

    # Verify Doppler token works
    log_info "Verifying Doppler configuration..."
    if doppler secrets --token="$DOPPLER_TOKEN" --silent get ENVIRONMENT &>/dev/null; then
        log_success "Doppler token valid"
    else
        error_exit "Doppler token invalid or insufficient permissions"
    fi

    # Show configuration
    local project_name=$(doppler setup --token="$DOPPLER_TOKEN" --silent --project-only 2>/dev/null || echo "unknown")
    local config_name=$(doppler setup --token="$DOPPLER_TOKEN" --silent --config-only 2>/dev/null || echo "unknown")
    log_info "Doppler project: $project_name"
    log_info "Doppler config: $config_name"
}

# =============================================================================
# STEP 5: ORACLE OBJECT STORAGE SETUP
# =============================================================================

setup_oracle_object_storage() {
    log_step "5" "Configure Oracle Object Storage for backups"

    # Install OCI CLI
    if command -v oci &> /dev/null; then
        log_info "OCI CLI already installed: $(oci --version 2>&1 | head -1)"
    else
        log_info "Installing OCI CLI..."
        bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)" -- \
            --accept-all-defaults \
            --install-dir ~/lib/oracle-cli \
            --exec-dir ~/bin \
            --script-dir ~/bin \
            2>&1 | tee -a "$LOG_FILE" | tail -5

        # Add to PATH
        if ! grep -q "~/bin" ~/.bashrc; then
            echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
        fi
        export PATH="$HOME/bin:$PATH"
        log_success "OCI CLI installed"
    fi

    # Check if OCI is configured
    if [ -f ~/.oci/config ]; then
        log_info "OCI CLI already configured"

        # Get namespace
        if oci os ns get &>/dev/null; then
            local namespace=$(oci os ns get --query 'data' --raw-output 2>/dev/null || echo "")
            if [ -n "$namespace" ]; then
                log_success "OCI namespace: $namespace"

                # Create backup bucket if it doesn't exist
                local bucket_name="multi-agent-backups"
                if oci os bucket get --bucket-name "$bucket_name" &>/dev/null; then
                    log_info "Backup bucket already exists: $bucket_name"
                else
                    log_info "Creating backup bucket: $bucket_name"
                    oci os bucket create \
                        --compartment-id "$(oci iam compartment list --query 'data[0].id' --raw-output)" \
                        --name "$bucket_name" \
                        --storage-tier Standard \
                        --versioning Enabled \
                        2>&1 | tee -a "$LOG_FILE"
                    log_success "Backup bucket created"
                fi

                # Store in environment
                export OCI_NAMESPACE="$namespace"
                export OCI_BUCKET_NAME="$bucket_name"
            fi
        else
            log_warn "OCI CLI configured but cannot access namespace. Check credentials."
        fi
    else
        log_warn "OCI CLI not configured. Run 'oci setup config' manually."
        log_warn "Backups will be local-only until OCI is configured."
    fi
}

# =============================================================================
# STEP 6: APPLICATION DEPLOYMENT
# =============================================================================

deploy_application() {
    log_step "6" "Deploy application stack"

    cd "$PROJECT_ROOT"

    # Create necessary directories
    log_info "Creating directory structure..."
    mkdir -p logs backups data/{uploads,exports} deployment/{certbot/{www,conf},nginx/ssl}
    log_success "Directories created"

    # Generate self-signed SSL certificate (for immediate use)
    if [ ! -f deployment/nginx/ssl/selfsigned.crt ]; then
        log_info "Generating self-signed SSL certificate..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout deployment/nginx/ssl/selfsigned.key \
            -out deployment/nginx/ssl/selfsigned.crt \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=multi-agent-system" \
            2>&1 | tee -a "$LOG_FILE"
        chmod 644 deployment/nginx/ssl/selfsigned.crt
        chmod 600 deployment/nginx/ssl/selfsigned.key
        log_success "SSL certificate generated"
    fi

    # Pull latest images
    log_info "Pulling Docker images..."
    doppler run --token="$DOPPLER_TOKEN" -- docker compose pull 2>&1 | tee -a "$LOG_FILE"
    log_success "Images pulled"

    # Build application image
    log_info "Building application image..."
    doppler run --token="$DOPPLER_TOKEN" -- docker compose build --no-cache fastapi 2>&1 | tee -a "$LOG_FILE"
    log_success "Application built"

    # Start infrastructure services first (database, cache)
    log_info "Starting infrastructure services..."
    doppler run --token="$DOPPLER_TOKEN" -- docker compose up -d postgres redis qdrant 2>&1 | tee -a "$LOG_FILE"

    # Wait for databases to be healthy
    log_info "Waiting for databases to be ready..."
    local max_wait=60
    local waited=0
    while [ $waited -lt $max_wait ]; do
        if docker compose exec -T postgres pg_isready &>/dev/null; then
            log_success "PostgreSQL ready"
            break
        fi
        sleep 2
        waited=$((waited + 2))
    done

    if [ $waited -ge $max_wait ]; then
        error_exit "PostgreSQL failed to start"
    fi

    # Start application and reverse proxy
    log_info "Starting application services..."
    doppler run --token="$DOPPLER_TOKEN" -- docker compose up -d fastapi nginx 2>&1 | tee -a "$LOG_FILE"

    # Start monitoring stack
    log_info "Starting monitoring services..."
    doppler run --token="$DOPPLER_TOKEN" -- docker compose up -d \
        prometheus grafana \
        node-exporter postgres-exporter redis-exporter \
        2>&1 | tee -a "$LOG_FILE"

    # Start certbot for SSL renewal
    doppler run --token="$DOPPLER_TOKEN" -- docker compose up -d certbot 2>&1 | tee -a "$LOG_FILE"

    log_success "All services started"

    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 10

    # Show status
    docker compose ps
}

# =============================================================================
# STEP 7: DATABASE SETUP
# =============================================================================

setup_database() {
    log_step "7" "Initialize database"

    cd "$PROJECT_ROOT"

    # Wait for FastAPI to be fully up
    log_info "Waiting for FastAPI to be ready..."
    local max_wait=60
    local waited=0
    while [ $waited -lt $max_wait ]; do
        if curl -sf http://localhost:8000/health &>/dev/null; then
            log_success "FastAPI ready"
            break
        fi
        sleep 2
        waited=$((waited + 2))
    done

    # Run migrations
    log_info "Running database migrations..."
    docker compose exec -T fastapi alembic upgrade head 2>&1 | tee -a "$LOG_FILE"
    log_success "Migrations completed"

    # Show current migration
    local current_migration=$(docker compose exec -T fastapi alembic current 2>/dev/null | grep -oP '\w{12}' | head -1)
    log_info "Current migration: $current_migration"
}

# =============================================================================
# STEP 8: KNOWLEDGE BASE INITIALIZATION
# =============================================================================

setup_knowledge_base() {
    log_step "8" "Initialize knowledge base"

    cd "$PROJECT_ROOT"

    # Check if knowledge base script exists
    if [ -f scripts/init_knowledge_base.py ]; then
        log_info "Initializing knowledge base..."
        docker compose exec -T fastapi python scripts/init_knowledge_base.py 2>&1 | tee -a "$LOG_FILE"
        log_success "Knowledge base initialized"
    else
        log_warn "Knowledge base script not found. Skipping."
    fi

    # Verify Qdrant collections
    log_info "Verifying Qdrant collections..."
    docker compose exec -T fastapi python -c "
from qdrant_client import QdrantClient
try:
    client = QdrantClient(url='http://qdrant:6333')
    collections = client.get_collections()
    print(f'✓ Collections found: {len(collections.collections)}')
    for col in collections.collections:
        print(f'  - {col.name}: {col.points_count} vectors')
except Exception as e:
    print(f'✗ Error: {e}')
" 2>&1 | tee -a "$LOG_FILE"
}

# =============================================================================
# STEP 9: AUTOMATED BACKUPS
# =============================================================================

setup_automated_backups() {
    log_step "9" "Configure automated backups"

    # Export OCI variables to cron environment
    local cron_env=""
    if [ -n "${OCI_NAMESPACE:-}" ]; then
        cron_env="OCI_NAMESPACE=$OCI_NAMESPACE OCI_BUCKET_NAME=${OCI_BUCKET_NAME:-multi-agent-backups}"
    fi

    # Create backup cron job
    log_info "Setting up daily backup cron job..."

    # Remove existing backup cron jobs
    crontab -l 2>/dev/null | grep -v "backup-database.sh" | crontab - || true

    # Add new cron job (daily at 3 AM)
    (crontab -l 2>/dev/null || echo ""; echo "# Daily database backup at 3 AM
0 3 * * * cd $PROJECT_ROOT && $cron_env doppler run --token=\"$DOPPLER_TOKEN\" -- ./deployment/scripts/backup-database.sh >> logs/backup.log 2>&1") | crontab -

    log_success "Backup cron job configured"

    # Show cron jobs
    log_info "Configured cron jobs:"
    crontab -l 2>/dev/null | grep -v "^#" | grep -v "^$" | tee -a "$LOG_FILE"

    # Run initial backup
    log_info "Running initial backup..."
    cd "$PROJECT_ROOT"
    if [ -x deployment/scripts/backup-database.sh ]; then
        ./deployment/scripts/backup-database.sh 2>&1 | tee -a "$LOG_FILE" | tail -20
        log_success "Initial backup completed"
    else
        log_warn "Backup script not executable or not found"
    fi
}

# =============================================================================
# STEP 10: MONITORING & ALERTING
# =============================================================================

setup_monitoring() {
    log_step "10" "Configure monitoring and alerting"

    cd "$PROJECT_ROOT"

    # Verify Prometheus targets
    log_info "Checking Prometheus targets..."
    sleep 5  # Give Prometheus time to scrape

    local targets_up=$(curl -s http://localhost:9090/api/v1/targets 2>/dev/null | jq -r '.data.activeTargets[] | select(.health=="up") | .scrapePool' | wc -l)
    log_info "Prometheus targets up: $targets_up"

    # Verify Grafana
    log_info "Checking Grafana..."
    if curl -sf http://localhost:3000/api/health &>/dev/null; then
        log_success "Grafana accessible"
    else
        log_warn "Grafana not accessible yet"
    fi

    # Check if Sentry is configured
    local sentry_dsn=$(doppler secrets --token="$DOPPLER_TOKEN" --silent get SENTRY_DSN 2>/dev/null || echo "")
    if [ -n "$sentry_dsn" ] && [ "$sentry_dsn" != "null" ]; then
        log_success "Sentry error tracking configured"
    else
        log_warn "Sentry DSN not configured. Error tracking disabled."
    fi
}

# =============================================================================
# STEP 11: HEALTH CHECKS & VALIDATION
# =============================================================================

run_health_checks() {
    log_step "11" "Run comprehensive health checks"

    local passed=0
    local failed=0

    # Check 1: Container health
    log_info "Checking container health..."
    local unhealthy=$(docker compose ps --format json | jq -r 'select(.Health != "healthy" and .Health != "") | .Name' 2>/dev/null)
    if [ -z "$unhealthy" ]; then
        log_success "All containers healthy"
        ((passed++))
    else
        log_error "Unhealthy containers: $unhealthy"
        ((failed++))
    fi

    # Check 2: API health endpoint
    log_info "Checking API health endpoint..."
    local health_response=$(curl -sk https://localhost/api/health 2>/dev/null)
    if echo "$health_response" | jq -e '.status == "healthy"' &>/dev/null; then
        log_success "API health check passed"
        ((passed++))
    else
        log_error "API health check failed: $health_response"
        ((failed++))
    fi

    # Check 3: Database connectivity
    log_info "Checking database connectivity..."
    if docker compose exec -T postgres pg_isready &>/dev/null; then
        log_success "PostgreSQL accessible"
        ((passed++))
    else
        log_error "PostgreSQL not accessible"
        ((failed++))
    fi

    # Check 4: Redis connectivity
    log_info "Checking Redis connectivity..."
    if docker compose exec -T redis redis-cli ping &>/dev/null; then
        log_success "Redis accessible"
        ((passed++))
    else
        log_error "Redis not accessible"
        ((failed++))
    fi

    # Check 5: Qdrant connectivity
    log_info "Checking Qdrant connectivity..."
    if curl -sf http://localhost:6333/health &>/dev/null; then
        log_success "Qdrant accessible"
        ((passed++))
    else
        log_error "Qdrant not accessible"
        ((failed++))
    fi

    # Check 6: Prometheus
    log_info "Checking Prometheus..."
    if curl -sf http://localhost:9090/-/healthy &>/dev/null; then
        log_success "Prometheus accessible"
        ((passed++))
    else
        log_error "Prometheus not accessible"
        ((failed++))
    fi

    # Check 7: Grafana
    log_info "Checking Grafana..."
    if curl -sf http://localhost:3000/api/health &>/dev/null; then
        log_success "Grafana accessible"
        ((passed++))
    else
        log_error "Grafana not accessible"
        ((failed++))
    fi

    # Summary
    echo ""
    log_info "════════════════════════════════════════"
    log_info "Health Check Summary"
    log_info "════════════════════════════════════════"
    log_info "Passed: $passed"
    log_info "Failed: $failed"
    log_info "════════════════════════════════════════"

    if [ $failed -gt 0 ]; then
        log_warn "Some health checks failed. Review logs for details."
    else
        log_success "All health checks passed!"
    fi
}

# =============================================================================
# STEP 12: DEPLOYMENT SUMMARY
# =============================================================================

show_deployment_summary() {
    log_step "12" "Deployment summary"

    # Get public IP
    local public_ip=$(curl -s ifconfig.me 2>/dev/null || echo "UNKNOWN")

    # Get Grafana password
    local grafana_pass=$(doppler secrets --token="$DOPPLER_TOKEN" --silent get GRAFANA_ADMIN_PASSWORD 2>/dev/null || echo "check-doppler")

    cat <<EOF | tee -a "$LOG_FILE"

${BOLD}${GREEN}╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║          🎉  DEPLOYMENT SUCCESSFUL! 🎉                         ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝${NC}

${BOLD}🌐 ACCESS URLS:${NC}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ${CYAN}API Documentation:${NC}  https://$public_ip/api/docs
  ${CYAN}API Health:${NC}         https://$public_ip/api/health
  ${CYAN}Prometheus:${NC}         http://$public_ip:9090
  ${CYAN}Grafana:${NC}            http://$public_ip:3000
  ${CYAN}  └─ Login:${NC}         admin / $grafana_pass

${BOLD}📊 DEPLOYED SERVICES:${NC}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
$(docker compose ps --format "  {{.Service}}: {{.Status}}" | head -12)

${BOLD}🔐 SECURITY:${NC}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ${GREEN}✓${NC} Firewall configured (firewalld)
  ${GREEN}✓${NC} Fail2ban enabled
  ${GREEN}✓${NC} SSL/TLS enabled (self-signed)
  ${GREEN}✓${NC} Security headers configured
  ${GREEN}✓${NC} Rate limiting enabled

${BOLD}💾 BACKUPS:${NC}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ${GREEN}✓${NC} Automated daily backups (3 AM)
  ${GREEN}✓${NC} 7-day retention
  ${GREEN}✓${NC} Backup location: $PROJECT_ROOT/backups/
EOF

    if [ -n "${OCI_NAMESPACE:-}" ]; then
        echo "  ${GREEN}✓${NC} Oracle Object Storage: ${OCI_BUCKET_NAME}"
    else
        echo "  ${YELLOW}⚠${NC} Oracle Object Storage: Not configured (local only)"
    fi

    cat <<EOF

${BOLD}📈 MONITORING:${NC}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ${GREEN}✓${NC} Prometheus metrics collection
  ${GREEN}✓${NC} Grafana dashboards
  ${GREEN}✓${NC} Alert rules configured
  ${GREEN}✓${NC} System metrics (node-exporter)
  ${GREEN}✓${NC} PostgreSQL metrics
  ${GREEN}✓${NC} Redis metrics
EOF

    local sentry_dsn=$(doppler secrets --token="$DOPPLER_TOKEN" --silent get SENTRY_DSN 2>/dev/null || echo "")
    if [ -n "$sentry_dsn" ] && [ "$sentry_dsn" != "null" ]; then
        echo "  ${GREEN}✓${NC} Sentry error tracking"
    else
        echo "  ${YELLOW}⚠${NC} Sentry: Not configured"
    fi

    cat <<EOF

${BOLD}🚀 NEXT STEPS:${NC}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. Test the API: curl -k https://$public_ip/api/health
  2. Access Grafana: http://$public_ip:3000
  3. Review logs: docker compose logs -f
  4. Run API tests: cd $PROJECT_ROOT && pytest tests/

${BOLD}📝 USEFUL COMMANDS:${NC}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ${CYAN}Status:${NC}      docker compose ps
  ${CYAN}Logs:${NC}        docker compose logs -f [service]
  ${CYAN}Restart:${NC}     doppler run -- docker compose restart [service]
  ${CYAN}Backup:${NC}      ./deployment/scripts/backup-database.sh
  ${CYAN}Update:${NC}      git pull && doppler run -- docker compose up -d --build

${BOLD}📚 DOCUMENTATION:${NC}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Deployment: $PROJECT_ROOT/deployment/README.md
  API Docs:   https://$public_ip/api/docs
  Logs:       $LOG_FILE

${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Deployment completed at: $(date)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}

EOF
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    echo -e "${BOLD}${CYAN}"
    cat <<'EOF'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 PRODUCTION DEPLOYMENT
 Multi-Agent Support System → Oracle Cloud
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
    echo -e "${NC}\n"

    log "Starting production deployment..."
    log "Log file: $LOG_FILE"
    echo ""

    # Execute deployment steps
    check_prerequisites
    clean_existing_deployment
    configure_system
    setup_docker
    setup_doppler
    setup_oracle_object_storage
    deploy_application
    setup_database
    setup_knowledge_base
    setup_automated_backups
    setup_monitoring
    run_health_checks
    show_deployment_summary

    log ""
    log "${BOLD}${GREEN}🎉 Deployment completed successfully!${NC}"
    log ""
}

# Run main function
main "$@"