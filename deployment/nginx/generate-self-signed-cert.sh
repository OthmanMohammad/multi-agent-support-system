#!/bin/bash
# =============================================================================
# Generate Self-Signed SSL Certificate
# For testing without a domain name
# =============================================================================

set -e

CERT_DIR="./deployment/nginx/ssl"
DAYS=365

# Create directory if it doesn't exist
mkdir -p "$CERT_DIR"

echo "Generating self-signed SSL certificate..."

# Generate private key and certificate
openssl req -x509 -nodes -days $DAYS -newkey rsa:2048 \
    -keyout "$CERT_DIR/key.pem" \
    -out "$CERT_DIR/cert.pem" \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Set permissions
chmod 600 "$CERT_DIR/key.pem"
chmod 644 "$CERT_DIR/cert.pem"

echo "✓ Self-signed certificate generated at $CERT_DIR"
echo "  Certificate: $CERT_DIR/cert.pem"
echo "  Private Key: $CERT_DIR/key.pem"
echo ""
echo "⚠️  This is a self-signed certificate for testing only."
echo "    Browsers will show a security warning."
echo ""
echo "For production with a domain, use Let's Encrypt:"
echo "  ./deployment/scripts/setup-letsencrypt.sh your-domain.com your@email.com"
