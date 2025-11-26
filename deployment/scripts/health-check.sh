#!/bin/bash
# =============================================================================
# Health Check Script
# Multi-Agent Support System
# Comprehensive system health verification
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================
DEPLOY_PATH="${DEPLOY_PATH:-/opt/multi-agent-support}"
DOMAIN="${DOMAIN:-thatagentsproject.com}"
API_DOMAIN="${API_DOMAIN:-api.thatagentsproject.com}"

# Timeouts
HTTP_TIMEOUT=10
MAX_RETRIES=3

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# =============================================================================
# Parse Arguments
# =============================================================================
VERBOSE=false
JSON_OUTPUT=false
CHECK_EXTERNAL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --external)
            CHECK_EXTERNAL=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose    Show detailed output"
            echo "  --json           Output results as JSON"
            echo "  --external       Check external services (Qdrant, etc.)"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

# =============================================================================
# Output Functions
# =============================================================================
declare -A RESULTS

print_status() {
    local name=$1
    local status=$2
    local details=${3:-""}

    RESULTS[$name]=$status

    if [[ "$JSON_OUTPUT" == "true" ]]; then
        return
    fi

    case $status in
        "healthy")
            echo -e "  ${GREEN}✓${NC} $name ${GREEN}[HEALTHY]${NC} $details"
            ;;
        "degraded")
            echo -e "  ${YELLOW}⚠${NC} $name ${YELLOW}[DEGRADED]${NC} $details"
            ;;
        "unhealthy")
            echo -e "  ${RED}✗${NC} $name ${RED}[UNHEALTHY]${NC} $details"
            ;;
        *)
            echo -e "  ${BLUE}?${NC} $name [UNKNOWN] $details"
            ;;
    esac
}

# =============================================================================
# HTTP Check Function
# =============================================================================
check_http() {
    local url=$1
    local expected_code=${2:-200}
    local attempt=1

    while [[ $attempt -le $MAX_RETRIES ]]; do
        local response=$(curl -s -o /dev/null -w "%{http_code}" \
            --connect-timeout $HTTP_TIMEOUT \
            --max-time $HTTP_TIMEOUT \
            "$url" 2>/dev/null || echo "000")

        if [[ "$response" == "$expected_code" ]]; then
            return 0
        fi

        ((attempt++))
        sleep 1
    done

    return 1
}

# =============================================================================
# Container Health Checks
# =============================================================================
check_containers() {
    echo ""
    echo -e "${BLUE}Container Health:${NC}"

    cd "$DEPLOY_PATH" 2>/dev/null || cd "$(dirname "$0")/../.."

    local services=("fastapi" "frontend" "postgres" "redis" "nginx" "prometheus" "grafana")

    for service in "${services[@]}"; do
        local status=$(docker compose -f docker-compose.production.yml ps --format json "$service" 2>/dev/null | \
            grep -o '"Health":"[^"]*"' | cut -d'"' -f4 || echo "unknown")

        local state=$(docker compose -f docker-compose.production.yml ps --format json "$service" 2>/dev/null | \
            grep -o '"State":"[^"]*"' | cut -d'"' -f4 || echo "unknown")

        if [[ "$state" == "running" ]]; then
            if [[ "$status" == "healthy" ]] || [[ "$status" == "" ]]; then
                print_status "$service" "healthy" "($state)"
            else
                print_status "$service" "degraded" "($status)"
            fi
        else
            print_status "$service" "unhealthy" "($state)"
        fi
    done
}

# =============================================================================
# Backend API Health Checks
# =============================================================================
check_backend_api() {
    echo ""
    echo -e "${BLUE}Backend API Health:${NC}"

    # Health endpoint
    if check_http "http://localhost:8000/health"; then
        print_status "health-endpoint" "healthy"
    else
        print_status "health-endpoint" "unhealthy"
    fi

    # Ready endpoint
    if check_http "http://localhost:8000/health/ready"; then
        print_status "ready-endpoint" "healthy"
    else
        print_status "ready-endpoint" "unhealthy"
    fi

    # API docs
    if check_http "http://localhost:8000/docs"; then
        print_status "api-docs" "healthy"
    else
        print_status "api-docs" "degraded"
    fi

    # Metrics endpoint
    if check_http "http://localhost:8000/metrics"; then
        print_status "metrics" "healthy"
    else
        print_status "metrics" "degraded"
    fi
}

# =============================================================================
# Frontend Health Checks
# =============================================================================
check_frontend() {
    echo ""
    echo -e "${BLUE}Frontend Health:${NC}"

    # Frontend health
    if check_http "http://localhost:3000"; then
        print_status "frontend-server" "healthy"
    else
        print_status "frontend-server" "unhealthy"
    fi

    # NextAuth API
    if check_http "http://localhost:3000/api/auth/providers"; then
        print_status "nextauth" "healthy"
    else
        print_status "nextauth" "degraded"
    fi
}

# =============================================================================
# Database Health Checks
# =============================================================================
check_database() {
    echo ""
    echo -e "${BLUE}Database Health:${NC}"

    cd "$DEPLOY_PATH" 2>/dev/null || cd "$(dirname "$0")/../.."

    # PostgreSQL connection
    if docker compose -f docker-compose.production.yml exec -T postgres \
        pg_isready -U postgres -d support_agent > /dev/null 2>&1; then
        print_status "postgres-connection" "healthy"
    else
        print_status "postgres-connection" "unhealthy"
    fi

    # Check active connections
    local connections=$(docker compose -f docker-compose.production.yml exec -T postgres \
        psql -U postgres -d support_agent -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | tr -d ' ' || echo "0")

    if [[ "$connections" -lt 180 ]]; then
        print_status "postgres-connections" "healthy" "($connections active)"
    else
        print_status "postgres-connections" "degraded" "($connections active - nearing limit)"
    fi

    # Redis connection
    if docker compose -f docker-compose.production.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_status "redis-connection" "healthy"
    else
        print_status "redis-connection" "unhealthy"
    fi

    # Redis memory
    local redis_memory=$(docker compose -f docker-compose.production.yml exec -T redis \
        redis-cli INFO memory 2>/dev/null | grep "used_memory_human" | cut -d: -f2 | tr -d '\r' || echo "unknown")
    print_status "redis-memory" "healthy" "($redis_memory)"
}

# =============================================================================
# External Endpoint Checks
# =============================================================================
check_external_endpoints() {
    if [[ "$CHECK_EXTERNAL" != "true" ]]; then
        return 0
    fi

    echo ""
    echo -e "${BLUE}External Endpoints:${NC}"

    # Public API
    if check_http "https://$API_DOMAIN/health"; then
        print_status "public-api" "healthy"
    else
        print_status "public-api" "unhealthy"
    fi

    # Public frontend
    if check_http "https://$DOMAIN"; then
        print_status "public-frontend" "healthy"
    else
        print_status "public-frontend" "unhealthy"
    fi

    # SSL certificate expiry
    local ssl_expiry=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | \
        openssl x509 -noout -dates 2>/dev/null | grep notAfter | cut -d= -f2 || echo "unknown")

    if [[ "$ssl_expiry" != "unknown" ]]; then
        local expiry_epoch=$(date -d "$ssl_expiry" +%s 2>/dev/null || echo "0")
        local now_epoch=$(date +%s)
        local days_left=$(( (expiry_epoch - now_epoch) / 86400 ))

        if [[ $days_left -gt 30 ]]; then
            print_status "ssl-certificate" "healthy" "($days_left days until expiry)"
        elif [[ $days_left -gt 7 ]]; then
            print_status "ssl-certificate" "degraded" "($days_left days until expiry)"
        else
            print_status "ssl-certificate" "unhealthy" "($days_left days until expiry - RENEW NOW)"
        fi
    fi
}

# =============================================================================
# Resource Checks
# =============================================================================
check_resources() {
    echo ""
    echo -e "${BLUE}System Resources:${NC}"

    # Disk space
    local disk_usage=$(df -h "$DEPLOY_PATH" 2>/dev/null | awk 'NR==2 {print $5}' | tr -d '%' || echo "0")
    if [[ "$disk_usage" -lt 80 ]]; then
        print_status "disk-space" "healthy" "(${disk_usage}% used)"
    elif [[ "$disk_usage" -lt 90 ]]; then
        print_status "disk-space" "degraded" "(${disk_usage}% used)"
    else
        print_status "disk-space" "unhealthy" "(${disk_usage}% used - LOW SPACE)"
    fi

    # Memory
    local mem_available=$(free -m | awk 'NR==2 {print $7}' || echo "0")
    if [[ "$mem_available" -gt 2000 ]]; then
        print_status "memory" "healthy" "(${mem_available}MB available)"
    elif [[ "$mem_available" -gt 1000 ]]; then
        print_status "memory" "degraded" "(${mem_available}MB available)"
    else
        print_status "memory" "unhealthy" "(${mem_available}MB available - LOW MEMORY)"
    fi

    # CPU load
    local load_avg=$(cat /proc/loadavg 2>/dev/null | awk '{print $1}' || echo "0")
    local cpu_cores=$(nproc 2>/dev/null || echo "4")
    local load_per_core=$(echo "$load_avg $cpu_cores" | awk '{printf "%.2f", $1/$2}')

    if (( $(echo "$load_per_core < 0.7" | bc -l) )); then
        print_status "cpu-load" "healthy" "(load: $load_avg)"
    elif (( $(echo "$load_per_core < 0.9" | bc -l) )); then
        print_status "cpu-load" "degraded" "(load: $load_avg)"
    else
        print_status "cpu-load" "unhealthy" "(load: $load_avg - HIGH CPU)"
    fi
}

# =============================================================================
# Generate JSON Output
# =============================================================================
generate_json() {
    echo "{"
    echo '  "timestamp": "'$(date -Iseconds)'",'
    echo '  "checks": {'

    local first=true
    for key in "${!RESULTS[@]}"; do
        if [[ "$first" != "true" ]]; then
            echo ","
        fi
        echo -n "    \"$key\": \"${RESULTS[$key]}\""
        first=false
    done

    echo ""
    echo "  },"

    # Calculate overall status
    local overall="healthy"
    for status in "${RESULTS[@]}"; do
        if [[ "$status" == "unhealthy" ]]; then
            overall="unhealthy"
            break
        elif [[ "$status" == "degraded" ]]; then
            overall="degraded"
        fi
    done

    echo "  \"overall\": \"$overall\""
    echo "}"
}

# =============================================================================
# Main
# =============================================================================
main() {
    if [[ "$JSON_OUTPUT" != "true" ]]; then
        echo ""
        echo -e "${BLUE}========================================${NC}"
        echo -e "${BLUE}   Multi-Agent Support System${NC}"
        echo -e "${BLUE}   Health Check Report${NC}"
        echo -e "${BLUE}   $(date)${NC}"
        echo -e "${BLUE}========================================${NC}"
    fi

    check_containers
    check_backend_api
    check_frontend
    check_database
    check_external_endpoints
    check_resources

    if [[ "$JSON_OUTPUT" == "true" ]]; then
        generate_json
    else
        echo ""
        echo -e "${BLUE}========================================${NC}"

        # Calculate overall status
        local overall="healthy"
        local unhealthy_count=0
        local degraded_count=0

        for status in "${RESULTS[@]}"; do
            if [[ "$status" == "unhealthy" ]]; then
                ((unhealthy_count++))
                overall="unhealthy"
            elif [[ "$status" == "degraded" ]]; then
                ((degraded_count++))
                if [[ "$overall" != "unhealthy" ]]; then
                    overall="degraded"
                fi
            fi
        done

        case $overall in
            "healthy")
                echo -e "${GREEN}Overall Status: HEALTHY${NC}"
                ;;
            "degraded")
                echo -e "${YELLOW}Overall Status: DEGRADED ($degraded_count warnings)${NC}"
                ;;
            "unhealthy")
                echo -e "${RED}Overall Status: UNHEALTHY ($unhealthy_count critical)${NC}"
                exit 1
                ;;
        esac

        echo -e "${BLUE}========================================${NC}"
        echo ""
    fi
}

main
