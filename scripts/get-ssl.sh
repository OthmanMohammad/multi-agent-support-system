#!/bin/bash
# Quick SSL setup for thatagentsproject.com
# Just run this script - it handles everything

set -e

DOMAIN="thatagentsproject.com"
EMAIL="Mo@MohammadOthman.com"

echo "🔐 Getting SSL certificates for $DOMAIN..."
echo ""

# Stop nginx
echo "Stopping nginx..."
docker compose stop nginx

# Get certificates (override the broken entrypoint)
echo "Requesting certificates from Let's Encrypt..."
docker compose run --rm \
  --entrypoint certbot \
  -p 80:80 \
  certbot certonly \
  --standalone \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  --non-interactive \
  -d "$DOMAIN" \
  -d "www.$DOMAIN" \
  -d "api.$DOMAIN"

if [ $? -ne 0 ]; then
    echo "❌ Failed to get certificates"
    docker compose start nginx
    exit 1
fi

echo "✅ Certificates obtained!"
echo ""

# Update nginx config to use Let's Encrypt certs
echo "Updating nginx configuration..."

NGINX_CONF="deployment/nginx/conf.d/${DOMAIN}.conf"

# Backup
cp "$NGINX_CONF" "${NGINX_CONF}.backup"

# Update all 3 server blocks
sed -i 's|ssl_certificate /etc/nginx/ssl/cert.pem;|# ssl_certificate /etc/nginx/ssl/cert.pem;|g' "$NGINX_CONF"
sed -i 's|ssl_certificate_key /etc/nginx/ssl/key.pem;|# ssl_certificate_key /etc/nginx/ssl/key.pem;|g' "$NGINX_CONF"
sed -i 's|# ssl_certificate /etc/letsencrypt/live/thatagentsproject.com/fullchain.pem;|ssl_certificate /etc/letsencrypt/live/thatagentsproject.com/fullchain.pem;|g' "$NGINX_CONF"
sed -i 's|# ssl_certificate_key /etc/letsencrypt/live/thatagentsproject.com/privkey.pem;|ssl_certificate_key /etc/letsencrypt/live/thatagentsproject.com/privkey.pem;|g' "$NGINX_CONF"
sed -i 's|# ssl_stapling on;|ssl_stapling on;|g' "$NGINX_CONF"
sed -i 's|# ssl_stapling_verify on;|ssl_stapling_verify on;|g' "$NGINX_CONF"
sed -i 's|# ssl_trusted_certificate /etc/letsencrypt/live/thatagentsproject.com/chain.pem;|ssl_trusted_certificate /etc/letsencrypt/live/thatagentsproject.com/chain.pem;|g' "$NGINX_CONF"

echo "✅ Nginx config updated!"
echo ""

# Start nginx
echo "Starting nginx..."
docker compose start nginx

# Wait for nginx to start
sleep 3

# Test
echo "Testing SSL..."
if curl -fsSL https://$DOMAIN/health > /dev/null 2>&1; then
    echo "✅ SSL is working!"
else
    echo "⚠️  SSL test failed - but certificates are installed"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DONE! Your site now has Let's Encrypt SSL!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Test it:"
echo "  curl https://$DOMAIN/health"
echo "  curl https://api.$DOMAIN/health"
echo ""
echo "Open in browser:"
echo "  https://$DOMAIN/api/docs"
echo ""
