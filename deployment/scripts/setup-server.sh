#!/bin/bash
# =============================================================================
# ORACLE LINUX SERVER SETUP SCRIPT
# Automated setup for Oracle Linux 8 ARM64 on Oracle Cloud
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

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    error "Do not run this script as root. Run as opc user with sudo access."
    exit 1
fi

section "1. SYSTEM UPDATE"

log "Updating system packages..."
sudo dnf update -y

log "Installing essential tools..."
sudo dnf install -y \
    git \
    curl \
    wget \
    vim \
    htop \
    net-tools \
    ca-certificates \
    openssl

section "2. FIREWALL CONFIGURATION (firewalld)"

log "Configuring firewalld..."

# Start and enable firewalld
sudo systemctl start firewalld
sudo systemctl enable firewalld

# Allow SSH (already open but make sure)
sudo firewall-cmd --permanent --add-service=ssh

# Allow HTTP/HTTPS
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https

# Allow monitoring ports
info "Opening monitoring ports (9090, 3000) - restrict these after setup!"
sudo firewall-cmd --permanent --add-port=9090/tcp  # Prometheus
sudo firewall-cmd --permanent --add-port=3000/tcp  # Grafana

# Reload firewall
sudo firewall-cmd --reload

log "✓ Firewall configured and enabled"
sudo firewall-cmd --list-all

section "3. SSH HARDENING"

log "Hardening SSH configuration..."

# Backup original sshd_config
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Disable password authentication (keys only)
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Enable public key authentication
sudo sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# Disable root login
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# Restart SSH
sudo systemctl restart sshd

log "✓ SSH hardened (password auth disabled, keys only)"

section "4. DOCKER INSTALLATION"

log "Installing Docker..."

# Remove old versions if any
sudo dnf remove -y docker docker-client docker-client-latest docker-common \
    docker-latest docker-latest-logrotate docker-logrotate docker-engine \
    podman runc 2>/dev/null || true

# Install required packages
sudo dnf install -y dnf-plugins-core

# Add Docker repository
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Install Docker
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER

log "✓ Docker installed: $(docker --version)"
log "✓ Docker Compose installed: $(docker compose version)"

section "5. DOCKER PRODUCTION CONFIGURATION"

log "Configuring Docker for production..."

sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
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
  }
}
EOF

sudo systemctl restart docker

log "✓ Docker configured for production"

section "6. CREATE APPLICATION DIRECTORY"

log "Creating application directory structure..."

APP_DIR="$HOME/multi-agent-system"
mkdir -p "$APP_DIR"/{logs,backups}

log "✓ Directory created: $APP_DIR"

section "7. SELINUX CONFIGURATION"

log "Configuring SELinux for Docker..."

# Set SELinux to permissive for Docker (required for Oracle Linux)
sudo setenforce 0
sudo sed -i 's/^SELINUX=enforcing/SELINUX=permissive/' /etc/selinux/config

warn "SELinux set to permissive mode for Docker compatibility"

section "✅ SERVER SETUP COMPLETE"

echo ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Server setup completed successfully!"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
info "IMPORTANT: Log out and log back in for Docker group to take effect"
echo ""
info "NEXT STEPS:"
echo ""
echo "1. Log out and log back in:"
echo "   exit"
echo "   ssh opc@your-server-ip"
echo ""
echo "2. Navigate to repository:"
echo "   cd ~/multi-agent-support-system"
echo ""
echo "3. Set up environment variables:"
echo "   cp .env.production.example .env"
echo "   nano .env"
echo ""
echo "4. Generate SSL certificate:"
echo "   ./deployment/nginx/generate-self-signed-cert.sh"
echo ""
echo "5. Deploy the stack:"
echo "   ./deployment/scripts/deploy.sh"
echo ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit 0
