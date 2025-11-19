#!/bin/bash
# =============================================================================
# ORACLE CLOUD SERVER SETUP SCRIPT
# Automated setup for Ubuntu 22.04 ARM64 on Oracle Cloud
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
    error "Do not run this script as root. Run as ubuntu user with sudo access."
    exit 1
fi

section "1. SYSTEM UPDATE"

log "Updating system packages..."
sudo apt update && sudo apt upgrade -y

log "Installing essential tools..."
sudo apt install -y \
    git \
    curl \
    wget \
    vim \
    htop \
    net-tools \
    ufw \
    fail2ban \
    unattended-upgrades \
    ca-certificates \
    gnupg \
    lsb-release \
    software-properties-common

section "2. FIREWALL CONFIGURATION (UFW)"

log "Configuring UFW firewall..."

# Reset UFW to default state
sudo ufw --force reset

# Set default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Get current IP for SSH restriction (optional)
MY_IP=$(curl -s ifconfig.me)
if [ -n "$MY_IP" ]; then
    info "Your current IP: $MY_IP"
    read -p "Restrict SSH to your IP only? (recommended) [y/N]: " RESTRICT_SSH
    if [[ "$RESTRICT_SSH" =~ ^[Yy]$ ]]; then
        sudo ufw allow from "$MY_IP" to any port 22 proto tcp
        log "SSH restricted to $MY_IP"
    else
        sudo ufw allow 22/tcp
        warn "SSH open to all IPs (not recommended for production)"
    fi
else
    warn "Could not detect your IP. Allowing SSH from all IPs."
    sudo ufw allow 22/tcp
fi

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow monitoring ports (restrict these after initial setup)
info "Opening monitoring ports (9090, 3000) - restrict these after setup!"
sudo ufw allow 9090/tcp comment "Prometheus"
sudo ufw allow 3000/tcp comment "Grafana"

# Enable firewall
sudo ufw --force enable

log "✓ Firewall configured and enabled"
sudo ufw status verbose

section "3. FAIL2BAN SETUP (SSH Protection)"

log "Configuring Fail2ban..."

sudo tee /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
destemail = root@localhost
sendername = Fail2Ban
action = %(action_)s

[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
EOF

sudo systemctl enable fail2ban
sudo systemctl restart fail2ban

log "✓ Fail2ban configured and running"

section "4. SSH HARDENING"

log "Hardening SSH configuration..."

# Backup original sshd_config
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Disable password authentication
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

section "5. AUTOMATIC SECURITY UPDATES"

log "Configuring automatic security updates..."

sudo dpkg-reconfigure -plow unattended-upgrades

# Verify configuration
if grep -q "APT::Periodic::Unattended-Upgrade \"1\"" /etc/apt/apt.conf.d/20auto-upgrades; then
    log "✓ Automatic security updates enabled"
else
    warn "Automatic updates may not be fully configured"
fi

section "6. DOCKER INSTALLATION"

log "Installing Docker..."

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER

log "✓ Docker installed: $(docker --version)"
log "✓ Docker Compose installed: $(docker compose version)"

section "7. DOCKER PRODUCTION CONFIGURATION"

log "Configuring Docker for production..."

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
sudo systemctl enable docker

log "✓ Docker configured for production"

section "8. CREATE APPLICATION DIRECTORY"

log "Creating application directory structure..."

APP_DIR="$HOME/multi-agent-system"
mkdir -p "$APP_DIR"/{logs,backups}

log "✓ Directory created: $APP_DIR"

section "9. ORACLE CLI INSTALLATION (Optional)"

read -p "Install Oracle Cloud CLI for backup to Object Storage? [y/N]: " INSTALL_OCI

if [[ "$INSTALL_OCI" =~ ^[Yy]$ ]]; then
    log "Installing Oracle Cloud CLI..."
    bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)" -- --accept-all-defaults
    log "✓ OCI CLI installed"
    info "Configure OCI CLI with: oci setup config"
else
    info "Skipping OCI CLI installation"
fi

section "✅ SERVER SETUP COMPLETE"

echo ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Server setup completed successfully!"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
info "NEXT STEPS:"
echo ""
echo "1. Log out and log back in for Docker group to take effect:"
echo "   exit"
echo "   ssh ubuntu@your-server-ip"
echo ""
echo "2. Clone the repository:"
echo "   cd $APP_DIR"
echo "   git clone https://github.com/YOUR_USERNAME/multi-agent-support-system.git ."
echo ""
echo "3. Set up environment variables (use Doppler or create .env file)"
echo ""
echo "4. Generate SSL certificate:"
echo "   ./deployment/nginx/generate-self-signed-cert.sh"
echo "   # Or for Let's Encrypt with domain:"
echo "   # ./deployment/scripts/setup-letsencrypt.sh your-domain.com your@email.com"
echo ""
echo "5. Deploy the stack:"
echo "   ./deployment/scripts/deploy.sh"
echo ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit 0
