#!/bin/bash
# =============================================================================
# LET'S ENCRYPT SSL CERTIFICATE SETUP
# Obtain and configure SSL certificate with automatic renewal
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

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check arguments
if [ $# -lt 2 ]; then
    error "Usage: $0 <domain> <email>"
    error "Example: $0 api.example.com admin@example.com"
    exit 1
fi

DOMAIN="$1"
EMAIL="$2"

log "Setting up Let's Encrypt for domain: $DOMAIN"
log "Email: $EMAIL"

# Change to repository root
cd "$(dirname "$0")/../.."

# Check if nginx is running
if ! docker compose ps nginx | grep -q "Up"; then
    error "Nginx container is not running. Start services first with: ./deployment/scripts/deploy.sh"
    exit 1
fi

# =============================================================================
# STEP 1: Obtain Certificate
# =============================================================================

log "Requesting SSL certificate from Let's Encrypt..."

docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d "$DOMAIN"

if [ $? -eq 0 ]; then
    log "✓ Certificate obtained successfully"
else
    error "Failed to obtain certificate"
    exit 1
fi

# =============================================================================
# STEP 2: Update Nginx Configuration
# =============================================================================

log "Updating Nginx configuration to use Let's Encrypt certificate..."

# Backup current config
cp deployment/nginx/conf.d/default.conf deployment/nginx/conf.d/default.conf.backup

# Update certificate paths in nginx config
sed -i "s|ssl_certificate /etc/nginx/ssl/cert.pem;|ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;|" \
    deployment/nginx/conf.d/default.conf

sed -i "s|ssl_certificate_key /etc/nginx/ssl/key.pem;|ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;|" \
    deployment/nginx/conf.d/default.conf

# Update server_name
sed -i "s|server_name _;|server_name $DOMAIN;|" deployment/nginx/conf.d/default.conf

log "✓ Nginx configuration updated"

# =============================================================================
# STEP 3: Reload Nginx
# =============================================================================

log "Reloading Nginx..."

docker compose exec nginx nginx -s reload

if [ $? -eq 0 ]; then
    log "✓ Nginx reloaded successfully"
else
    error "Failed to reload Nginx"
    exit 1
fi

# =============================================================================
# STEP 4: Test Certificate
# =============================================================================

log "Testing SSL certificate..."

sleep 2

if curl -fsS "https://$DOMAIN/health" > /dev/null; then
    log "✓ SSL certificate is working correctly"
else
    warn "SSL test failed - check certificate configuration"
fi

# =============================================================================
# STEP 5: Set Up Auto-Renewal
# =============================================================================

log "Setting up automatic certificate renewal..."

# Create renewal script
cat > deployment/scripts/renew-cert.sh << 'EEOF'
#!/bin/bash
# Auto-renewal script for Let's Encrypt certificates

cd "$(dirname "$0")/../.."

docker compose run --rm certbot renew --quiet

if [ $? -eq 0 ]; then
    docker compose exec nginx nginx -s reload
    echo "[$(date)] Certificate renewed and nginx reloaded" >> logs/cert-renewal.log
fi
EEOF

chmod +x deployment/scripts/renew-cert.sh

# Add to crontab (runs daily at 3 AM, certbot will only renew if needed)
CRON_CMD="0 3 * * * cd $(pwd) && ./deployment/scripts/renew-cert.sh"

# Check if cron job already exists
if ! crontab -l 2>/dev/null | grep -q "renew-cert.sh"; then
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    log "✓ Auto-renewal cron job added"
else
    log "✓ Auto-renewal cron job already exists"
fi

# =============================================================================
# SUMMARY
# =============================================================================

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Let's Encrypt SSL certificate setup completed!"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
log "Domain: $DOMAIN"
log "Certificate: /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
log "Private Key: /etc/letsencrypt/live/$DOMAIN/privkey.pem"
echo ""
log "Auto-renewal: Enabled (daily check at 3 AM)"
log "Certificate expires: 90 days (auto-renews at 30 days)"
echo ""
log "Test your SSL at: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit 0
