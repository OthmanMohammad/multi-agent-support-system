#!/bin/bash
# =============================================================================
# Smoke Test Script
# Multi-Agent Support System
# Post-deployment verification tests
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================
DOMAIN="${DOMAIN:-thatagentsproject.com}"
API_DOMAIN="${API_DOMAIN:-api.thatagentsproject.com}"
USE_HTTPS="${USE_HTTPS:-true}"

if [[ "$USE_HTTPS" == "true" ]]; then
    FRONTEND_URL="https://$DOMAIN"
    API_URL="https://$API_DOMAIN"
else
    FRONTEND_URL="http://localhost:3000"
    API_URL="http://localhost:8000"
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# =============================================================================
# Test Functions
# =============================================================================
run_test() {
    local name=$1
    local command=$2

    echo -n "  Testing: $name ... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}PASSED${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

skip_test() {
    local name=$1
    local reason=$2

    echo -e "  Testing: $name ... ${YELLOW}SKIPPED${NC} ($reason)"
    ((TESTS_SKIPPED++))
}

# =============================================================================
# API Smoke Tests
# =============================================================================
test_api() {
    echo ""
    echo -e "${BLUE}API Smoke Tests:${NC}"

    # Health endpoints
    run_test "API Health" "curl -sf '$API_URL/health'"
    run_test "API Ready" "curl -sf '$API_URL/health/ready'"

    # Documentation
    run_test "OpenAPI Docs" "curl -sf '$API_URL/docs'"
    run_test "ReDoc" "curl -sf '$API_URL/redoc'"
    run_test "OpenAPI Schema" "curl -sf '$API_URL/openapi.json'"

    # Auth endpoints (should return 405 for GET or redirect)
    run_test "Auth Endpoint Exists" "curl -sf -o /dev/null -w '%{http_code}' '$API_URL/auth/login' | grep -E '(200|405|422)'"

    # Agents endpoint
    run_test "Agents List" "curl -sf '$API_URL/agents' | grep -q 'agents\|error'"

    # OAuth providers
    run_test "OAuth Providers" "curl -sf '$API_URL/oauth/providers'"
}

# =============================================================================
# Frontend Smoke Tests
# =============================================================================
test_frontend() {
    echo ""
    echo -e "${BLUE}Frontend Smoke Tests:${NC}"

    # Main page
    run_test "Homepage" "curl -sf '$FRONTEND_URL' | grep -qi 'html'"

    # Static assets
    run_test "Static Assets" "curl -sf -o /dev/null '$FRONTEND_URL/_next/static/'"

    # NextAuth endpoints
    run_test "NextAuth Providers" "curl -sf '$FRONTEND_URL/api/auth/providers'"
    run_test "NextAuth CSRF" "curl -sf '$FRONTEND_URL/api/auth/csrf'"
}

# =============================================================================
# Database Smoke Tests
# =============================================================================
test_database() {
    echo ""
    echo -e "${BLUE}Database Smoke Tests:${NC}"

    local deploy_path="${DEPLOY_PATH:-/opt/multi-agent-support}"

    if [[ -f "$deploy_path/docker-compose.production.yml" ]]; then
        cd "$deploy_path"

        # PostgreSQL
        run_test "PostgreSQL Connection" \
            "docker compose -f docker-compose.production.yml exec -T postgres pg_isready -U postgres"

        run_test "PostgreSQL Query" \
            "docker compose -f docker-compose.production.yml exec -T postgres psql -U postgres -d support_agent -c 'SELECT 1'"

        # Check tables exist
        run_test "Database Tables" \
            "docker compose -f docker-compose.production.yml exec -T postgres psql -U postgres -d support_agent -c '\dt' | grep -q 'users\|conversations'"

        # Redis
        run_test "Redis Connection" \
            "docker compose -f docker-compose.production.yml exec -T redis redis-cli ping"

        run_test "Redis Set/Get" \
            "docker compose -f docker-compose.production.yml exec -T redis redis-cli SET smoke_test 'ok' && docker compose -f docker-compose.production.yml exec -T redis redis-cli GET smoke_test"
    else
        skip_test "Database Tests" "docker-compose.production.yml not found"
    fi
}

# =============================================================================
# SSL/TLS Tests
# =============================================================================
test_ssl() {
    if [[ "$USE_HTTPS" != "true" ]]; then
        skip_test "SSL Tests" "HTTPS not enabled"
        return
    fi

    echo ""
    echo -e "${BLUE}SSL/TLS Smoke Tests:${NC}"

    # Certificate validity
    run_test "SSL Certificate Valid" \
        "echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -checkend 0"

    # HTTPS redirect
    run_test "HTTP->HTTPS Redirect" \
        "curl -sf -o /dev/null -w '%{http_code}' 'http://$DOMAIN' | grep -E '(301|302)'"

    # HSTS header
    run_test "HSTS Header" \
        "curl -sI 'https://$DOMAIN' | grep -qi 'strict-transport-security'"

    # Certificate chain
    run_test "Certificate Chain" \
        "curl -sf --cert-status 'https://$DOMAIN' 2>/dev/null || curl -sf 'https://$DOMAIN'"
}

# =============================================================================
# Performance Smoke Tests
# =============================================================================
test_performance() {
    echo ""
    echo -e "${BLUE}Performance Smoke Tests:${NC}"

    # Response time tests
    local api_time=$(curl -sf -o /dev/null -w '%{time_total}' "$API_URL/health" || echo "999")
    if (( $(echo "$api_time < 1.0" | bc -l) )); then
        run_test "API Response Time (<1s)" "true"
    else
        run_test "API Response Time (<1s)" "false"
    fi

    local frontend_time=$(curl -sf -o /dev/null -w '%{time_total}' "$FRONTEND_URL" || echo "999")
    if (( $(echo "$frontend_time < 3.0" | bc -l) )); then
        run_test "Frontend Response Time (<3s)" "true"
    else
        run_test "Frontend Response Time (<3s)" "false"
    fi

    # Concurrent requests test
    run_test "Concurrent Requests" \
        "for i in {1..10}; do curl -sf '$API_URL/health' & done; wait"
}

# =============================================================================
# Security Headers Test
# =============================================================================
test_security_headers() {
    echo ""
    echo -e "${BLUE}Security Headers Tests:${NC}"

    local headers=$(curl -sI "$FRONTEND_URL" 2>/dev/null)

    run_test "X-Frame-Options" "echo '$headers' | grep -qi 'x-frame-options'"
    run_test "X-Content-Type-Options" "echo '$headers' | grep -qi 'x-content-type-options'"
    run_test "X-XSS-Protection" "echo '$headers' | grep -qi 'x-xss-protection'"

    local api_headers=$(curl -sI "$API_URL/health" 2>/dev/null)
    run_test "API CORS Headers" "echo '$api_headers' | grep -qi 'access-control'"
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}   Multi-Agent Support System${NC}"
    echo -e "${BLUE}   Smoke Test Suite${NC}"
    echo -e "${BLUE}   $(date)${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "Frontend: $FRONTEND_URL"
    echo -e "API: $API_URL"

    test_api
    test_frontend
    test_database
    test_ssl
    test_performance
    test_security_headers

    # Summary
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}   Test Summary${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "  ${GREEN}Passed:${NC}  $TESTS_PASSED"
    echo -e "  ${RED}Failed:${NC}  $TESTS_FAILED"
    echo -e "  ${YELLOW}Skipped:${NC} $TESTS_SKIPPED"
    echo ""

    local total=$((TESTS_PASSED + TESTS_FAILED))
    if [[ $total -gt 0 ]]; then
        local success_rate=$((TESTS_PASSED * 100 / total))
        echo -e "  Success Rate: $success_rate%"
    fi

    echo ""
    echo -e "${BLUE}========================================${NC}"

    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo -e "${RED}SMOKE TESTS FAILED${NC}"
        exit 1
    else
        echo -e "${GREEN}ALL SMOKE TESTS PASSED${NC}"
        exit 0
    fi
}

main "$@"
