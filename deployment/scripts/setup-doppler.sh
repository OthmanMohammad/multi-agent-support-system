#!/bin/bash
# =============================================================================
# Doppler Secrets Management Setup
# Multi-Agent Support System
# Enterprise-grade secrets management integration
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================
DOPPLER_PROJECT="${DOPPLER_PROJECT:-multi-agent-support}"
DOPPLER_CONFIG="${DOPPLER_CONFIG:-production}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/multi-agent-support}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# =============================================================================
# Logging
# =============================================================================
log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# =============================================================================
# Install Doppler CLI
# =============================================================================
install_doppler() {
    log_info "Installing Doppler CLI..."

    if command -v doppler &> /dev/null; then
        log_info "Doppler CLI already installed"
        doppler --version
        return 0
    fi

    # Install Doppler CLI
    curl -Ls https://cli.doppler.com/install.sh | sh

    log_success "Doppler CLI installed"
    doppler --version
}

# =============================================================================
# Configure Doppler
# =============================================================================
configure_doppler() {
    log_info "Configuring Doppler..."

    if [[ -z "${DOPPLER_TOKEN:-}" ]]; then
        log_error "DOPPLER_TOKEN environment variable is not set"
        log_info "Please set DOPPLER_TOKEN with your service token"
        log_info "Generate one at: https://dashboard.doppler.com/workplace/projects/$DOPPLER_PROJECT/configs/$DOPPLER_CONFIG/access"
        exit 1
    fi

    # Configure Doppler with service token
    doppler configure set token "$DOPPLER_TOKEN" --scope "$DEPLOY_PATH"

    log_success "Doppler configured for project: $DOPPLER_PROJECT, config: $DOPPLER_CONFIG"
}

# =============================================================================
# Sync Secrets
# =============================================================================
sync_secrets() {
    log_info "Syncing secrets from Doppler..."

    # Fetch secrets and write to .env file
    doppler secrets download \
        --project "$DOPPLER_PROJECT" \
        --config "$DOPPLER_CONFIG" \
        --format env \
        --no-file \
        > "$DEPLOY_PATH/.env.doppler"

    # Verify secrets were retrieved
    local secret_count=$(wc -l < "$DEPLOY_PATH/.env.doppler")

    if [[ $secret_count -lt 5 ]]; then
        log_error "Failed to retrieve secrets or too few secrets found"
        exit 1
    fi

    log_success "Retrieved $secret_count secrets from Doppler"

    # Merge with existing .env if needed
    if [[ -f "$DEPLOY_PATH/.env" ]]; then
        log_info "Merging with existing .env file..."
        # Keep Doppler secrets as primary, append any local-only vars
        cp "$DEPLOY_PATH/.env.doppler" "$DEPLOY_PATH/.env.new"
        grep -v "^#" "$DEPLOY_PATH/.env" | while read -r line; do
            key=$(echo "$line" | cut -d= -f1)
            if [[ -n "$key" ]] && ! grep -q "^$key=" "$DEPLOY_PATH/.env.new"; then
                echo "$line" >> "$DEPLOY_PATH/.env.new"
            fi
        done
        mv "$DEPLOY_PATH/.env.new" "$DEPLOY_PATH/.env"
        rm -f "$DEPLOY_PATH/.env.doppler"
    else
        mv "$DEPLOY_PATH/.env.doppler" "$DEPLOY_PATH/.env"
    fi

    # Set secure permissions
    chmod 600 "$DEPLOY_PATH/.env"

    log_success "Secrets synced to $DEPLOY_PATH/.env"
}

# =============================================================================
# Verify Required Secrets
# =============================================================================
verify_secrets() {
    log_info "Verifying required secrets..."

    local required_secrets=(
        "DATABASE_URL"
        "ANTHROPIC_API_KEY"
        "JWT_SECRET_KEY"
        "QDRANT_URL"
        "POSTGRES_PASSWORD"
    )

    local missing=()

    for secret in "${required_secrets[@]}"; do
        if ! grep -q "^$secret=" "$DEPLOY_PATH/.env"; then
            missing+=("$secret")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required secrets:"
        for secret in "${missing[@]}"; do
            echo "  - $secret"
        done
        exit 1
    fi

    log_success "All required secrets present"
}

# =============================================================================
# Setup Doppler Run (for runtime secret injection)
# =============================================================================
setup_doppler_run() {
    log_info "Setting up Doppler Run wrapper..."

    cat > "$DEPLOY_PATH/doppler-run.sh" << 'EOF'
#!/bin/bash
# Wrapper script to run commands with Doppler secrets injected
exec doppler run --project multi-agent-support --config production -- "$@"
EOF

    chmod +x "$DEPLOY_PATH/doppler-run.sh"

    log_success "Doppler Run wrapper created at $DEPLOY_PATH/doppler-run.sh"
    log_info "Usage: ./doppler-run.sh <command>"
}

# =============================================================================
# Create Systemd Service for Auto-sync
# =============================================================================
setup_auto_sync() {
    log_info "Setting up automatic secret sync..."

    # Create sync script
    cat > "/usr/local/bin/doppler-sync.sh" << EOF
#!/bin/bash
cd $DEPLOY_PATH
doppler secrets download \\
    --project $DOPPLER_PROJECT \\
    --config $DOPPLER_CONFIG \\
    --format env \\
    --no-file \\
    > .env.new && mv .env.new .env
chmod 600 .env
EOF
    chmod +x /usr/local/bin/doppler-sync.sh

    # Create systemd timer
    cat > "/etc/systemd/system/doppler-sync.service" << EOF
[Unit]
Description=Sync Doppler secrets
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/doppler-sync.sh
Environment=DOPPLER_TOKEN=$DOPPLER_TOKEN
User=root
EOF

    cat > "/etc/systemd/system/doppler-sync.timer" << EOF
[Unit]
Description=Sync Doppler secrets every hour

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # Enable timer
    systemctl daemon-reload
    systemctl enable doppler-sync.timer
    systemctl start doppler-sync.timer

    log_success "Automatic secret sync configured (hourly)"
}

# =============================================================================
# Show Current Configuration
# =============================================================================
show_config() {
    log_info "Current Doppler Configuration:"
    echo ""
    echo "  Project: $DOPPLER_PROJECT"
    echo "  Config:  $DOPPLER_CONFIG"
    echo "  Path:    $DEPLOY_PATH"
    echo ""

    if [[ -f "$DEPLOY_PATH/.env" ]]; then
        local count=$(grep -c "=" "$DEPLOY_PATH/.env" || echo "0")
        echo "  Secrets in .env: $count"
    fi

    echo ""
    log_info "To view secrets in Doppler dashboard:"
    echo "  https://dashboard.doppler.com/workplace/projects/$DOPPLER_PROJECT/configs/$DOPPLER_CONFIG"
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}   Doppler Secrets Management Setup${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    case "${1:-setup}" in
        install)
            install_doppler
            ;;
        configure)
            configure_doppler
            ;;
        sync)
            sync_secrets
            verify_secrets
            ;;
        verify)
            verify_secrets
            ;;
        auto-sync)
            setup_auto_sync
            ;;
        status)
            show_config
            ;;
        setup|*)
            install_doppler
            configure_doppler
            sync_secrets
            verify_secrets
            setup_doppler_run
            show_config
            ;;
    esac

    echo ""
    log_success "Doppler setup complete"
}

main "$@"
