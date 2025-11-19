#!/bin/bash
# =============================================================================
# SYSTEM STATUS CHECKER
# Quick health check for all services
# =============================================================================

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
    fi
}

# Change to repository root
cd "$(dirname "$0")/../.."

print_section "🚀 MULTI-AGENT SUPPORT SYSTEM - STATUS CHECK"

# =============================================================================
# SYSTEM INFORMATION
# =============================================================================

print_section "📊 System Information"

echo "Hostname: $(hostname)"
echo "Uptime: $(uptime -p)"
echo "Load Average: $(uptime | awk -F'load average:' '{print $2}')"

PUBLIC_IP=$(curl -s --max-time 5 ifconfig.me)
if [ -n "$PUBLIC_IP" ]; then
    echo "Public IP: $PUBLIC_IP"
fi

# =============================================================================
# DOCKER STATUS
# =============================================================================

print_section "🐳 Docker Status"

if command -v docker &> /dev/null; then
    check_status "Docker installed: $(docker --version | awk '{print $3}')"
    check_status "Docker Compose installed: $(docker compose version --short)"
else
    echo -e "${RED}✗${NC} Docker not installed"
    exit 1
fi

# =============================================================================
# CONTAINER STATUS
# =============================================================================

print_section "📦 Container Status"

echo ""
docker compose ps

echo ""
echo "Container Health:"
for container in fastapi postgres redis qdrant nginx prometheus grafana; do
    if docker compose ps | grep -q "$container.*Up"; then
        if docker compose ps | grep -q "$container.*(healthy)"; then
            echo -e "${GREEN}✓${NC} $container - healthy"
        else
            echo -e "${YELLOW}⚠${NC} $container - running (no health check)"
        fi
    else
        echo -e "${RED}✗${NC} $container - not running"
    fi
done

# =============================================================================
# RESOURCE USAGE
# =============================================================================

print_section "💻 Resource Usage"

echo ""
echo "Memory:"
free -h | awk 'NR==2{printf "  Used: %s / %s (%.1f%%)\n", $3, $2, $3*100/$2}'

echo ""
echo "Disk:"
df -h / | awk 'NR==2{printf "  Used: %s / %s (%.1f%%)\n", $3, $2, $3*100/$2}'

echo ""
echo "CPU Load:"
uptime | awk -F'load average:' '{print "  " $2}'

# =============================================================================
# SERVICE HEALTH CHECKS
# =============================================================================

print_section "🏥 Service Health Checks"

# API Health
echo ""
echo -n "API: "
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Unhealthy${NC}"
fi

# PostgreSQL
echo -n "PostgreSQL: "
if docker compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ready${NC}"
else
    echo -e "${RED}✗ Not Ready${NC}"
fi

# Redis
echo -n "Redis: "
if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Responding${NC}"
else
    echo -e "${RED}✗ Not Responding${NC}"
fi

# Qdrant
echo -n "Qdrant: "
if curl -sf http://localhost:6333/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Unhealthy${NC}"
fi

# Prometheus
echo -n "Prometheus: "
if curl -sf http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Unhealthy${NC}"
fi

# Grafana
echo -n "Grafana: "
if curl -sf http://localhost:3000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Unhealthy${NC}"
fi

# =============================================================================
# DATABASE INFORMATION
# =============================================================================

print_section "🗄️  Database Information"

if docker compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo ""
    echo "Database Size:"
    docker compose exec -T postgres psql -U postgres -d support_agent -c "\l+ support_agent" | grep support_agent | awk '{print "  " $NF}'

    echo ""
    echo "Active Connections:"
    CONNECTIONS=$(docker compose exec -T postgres psql -U postgres -d support_agent -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname='support_agent';" | xargs)
    echo "  $CONNECTIONS connections"

    echo ""
    echo "Recent Tables:"
    docker compose exec -T postgres psql -U postgres -d support_agent -c "\dt" | head -10
fi

# =============================================================================
# MONITORING
# =============================================================================

print_section "📈 Monitoring"

if [ -n "$PUBLIC_IP" ]; then
    echo ""
    echo "Monitoring URLs:"
    echo "  - Prometheus: http://$PUBLIC_IP:9090"
    echo "  - Grafana:    http://$PUBLIC_IP:3000"
    echo "  - API Docs:   https://$PUBLIC_IP/api/docs"
fi

# =============================================================================
# RECENT LOGS (last 10 lines)
# =============================================================================

print_section "📝 Recent Logs (last 10 lines)"

echo ""
echo "FastAPI:"
docker compose logs --tail=10 fastapi 2>/dev/null | sed 's/^/  /'

# =============================================================================
# BACKUPS
# =============================================================================

print_section "💾 Backups"

BACKUP_DIR="./backups"
if [ -d "$BACKUP_DIR" ]; then
    BACKUP_COUNT=$(find "$BACKUP_DIR" -name "postgres_*.sql.gz" 2>/dev/null | wc -l)
    echo ""
    echo "Local Backups: $BACKUP_COUNT"

    if [ $BACKUP_COUNT -gt 0 ]; then
        echo ""
        echo "Latest Backups:"
        ls -lht "$BACKUP_DIR"/postgres_*.sql.gz 2>/dev/null | head -5 | awk '{print "  " $9 " (" $5 ") - " $6 " " $7 " " $8}'
    fi
else
    echo ""
    echo -e "${YELLOW}⚠${NC} Backup directory not found"
fi

# =============================================================================
# SSL CERTIFICATE
# =============================================================================

print_section "🔐 SSL Certificate"

echo ""
if [ -f "deployment/nginx/ssl/cert.pem" ]; then
    echo "Certificate Type: Self-signed"
    EXPIRY=$(openssl x509 -in deployment/nginx/ssl/cert.pem -noout -enddate | cut -d= -f2)
    echo "Expires: $EXPIRY"
elif [ -d "deployment/certbot/conf/live" ]; then
    DOMAIN=$(ls deployment/certbot/conf/live/ 2>/dev/null | head -1)
    if [ -n "$DOMAIN" ]; then
        echo "Certificate Type: Let's Encrypt"
        echo "Domain: $DOMAIN"
        docker compose run --rm certbot certificates 2>/dev/null | grep -A3 "Certificate Name: $DOMAIN" || echo "  Certificate info unavailable"
    fi
else
    echo -e "${YELLOW}⚠${NC} No SSL certificate found"
fi

# =============================================================================
# SUMMARY
# =============================================================================

print_section "✅ Summary"

ALL_HEALTHY=true

# Check critical services
for service in fastapi postgres redis; do
    if ! docker compose ps | grep -q "$service.*Up"; then
        ALL_HEALTHY=false
        break
    fi
done

echo ""
if [ "$ALL_HEALTHY" = true ]; then
    echo -e "${GREEN}✓ All critical services are running${NC}"
else
    echo -e "${RED}✗ Some services are not running${NC}"
    echo ""
    echo "To view logs: docker compose logs -f"
    echo "To restart:   docker compose restart"
fi

echo ""
echo "For detailed logs: docker compose logs -f [service]"
echo "For real-time stats: docker stats"

print_section ""

exit 0
