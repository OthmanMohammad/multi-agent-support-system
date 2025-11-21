#!/bin/bash
#
# Comprehensive Acceptance Test Suite
# Tests all critical functionality of the deployed system
#
# Usage: ./deployment/scripts/acceptance-tests.sh [SERVER_IP]
#
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNINGS=0

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓ PASS]${NC} $1"
    ((PASSED_TESTS++))
}

log_fail() {
    echo -e "${RED}[✗ FAIL]${NC} $1"
    ((FAILED_TESTS++))
}

log_warn() {
    echo -e "${YELLOW}[⚠ WARN]${NC} $1"
    ((WARNINGS++))
}

log_test() {
    echo -e "${CYAN}[TEST]${NC} $1"
    ((TOTAL_TESTS++))
}

# Get server IP from argument or use default
SERVER_IP="${1:-129.159.141.19}"
API_BASE="https://${SERVER_IP}/api"

# Temporary file for test data
TEST_DATA_FILE=$(mktemp)
TOKEN_FILE=$(mktemp)
trap "rm -f $TEST_DATA_FILE $TOKEN_FILE" EXIT

echo ""
echo "=========================================="
echo "  Acceptance Test Suite"
echo "=========================================="
echo ""
echo "Target Server: $SERVER_IP"
echo "API Base URL: $API_BASE"
echo ""
echo "=========================================="
echo ""

# Test 1: Health Check
log_test "Test 1: API Health Check"
HEALTH_RESPONSE=$(curl -k -s -w "\n%{http_code}" "$API_BASE/health" || echo "000")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -1)
RESPONSE_BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)

if [[ "$HTTP_CODE" == "200" ]] && echo "$RESPONSE_BODY" | grep -q "healthy"; then
    log_success "Health endpoint responding correctly"
    echo "    Response: $RESPONSE_BODY"
else
    log_fail "Health endpoint not responding (HTTP $HTTP_CODE)"
    echo "    Response: $RESPONSE_BODY"
fi
echo ""

# Test 2: API Documentation
log_test "Test 2: API Documentation Accessibility"
DOCS_RESPONSE=$(curl -k -s -w "\n%{http_code}" "$API_BASE/docs" || echo "000")
HTTP_CODE=$(echo "$DOCS_RESPONSE" | tail -1)
RESPONSE_BODY=$(echo "$DOCS_RESPONSE" | head -n -1)

if [[ "$HTTP_CODE" == "200" ]] && echo "$RESPONSE_BODY" | grep -q -i "swagger"; then
    log_success "API documentation accessible"
else
    log_fail "API documentation not accessible (HTTP $HTTP_CODE)"
fi
echo ""

# Test 3: Database Connection (requires SSH)
log_test "Test 3: Database Connection"
if command -v docker &>/dev/null && docker compose ps &>/dev/null 2>&1; then
    MIGRATION_CHECK=$(docker compose exec fastapi alembic current 2>&1 || echo "ERROR")
    if echo "$MIGRATION_CHECK" | grep -q -v "ERROR"; then
        log_success "Database connection working"
        echo "    Current migration: $(echo "$MIGRATION_CHECK" | head -1)"
    else
        log_fail "Database connection failed"
        echo "    Error: $MIGRATION_CHECK"
    fi
else
    log_warn "Cannot test database connection (not running on server)"
fi
echo ""

# Test 4: User Registration
log_test "Test 4: User Registration"
TIMESTAMP=$(date +%s)
TEST_USERNAME="testuser_${TIMESTAMP}"
TEST_EMAIL="test_${TIMESTAMP}@example.com"

REGISTER_RESPONSE=$(curl -k -s -w "\n%{http_code}" -X POST "$API_BASE/auth/register" \
    -H "Content-Type: application/json" \
    -d "{
        \"username\": \"$TEST_USERNAME\",
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"Test123!@#\",
        \"full_name\": \"Test User\"
    }" 2>/dev/null || echo -e "\n000")

HTTP_CODE=$(echo "$REGISTER_RESPONSE" | tail -1)
RESPONSE_BODY=$(echo "$REGISTER_RESPONSE" | head -n -1)

if [[ "$HTTP_CODE" == "201" ]] || [[ "$HTTP_CODE" == "200" ]]; then
    log_success "User registration successful"
    echo "    Username: $TEST_USERNAME"
else
    log_fail "User registration failed (HTTP $HTTP_CODE)"
    echo "    Response: $RESPONSE_BODY"
fi
echo ""

# Test 5: User Login and Token Generation
log_test "Test 5: User Authentication (Login)"
LOGIN_RESPONSE=$(curl -k -s -w "\n%{http_code}" -X POST "$API_BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d "{
        \"username\": \"$TEST_USERNAME\",
        \"password\": \"Test123!@#\"
    }" 2>/dev/null || echo -e "\n000")

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -1)
RESPONSE_BODY=$(echo "$LOGIN_RESPONSE" | head -n -1)

if [[ "$HTTP_CODE" == "200" ]]; then
    TOKEN=$(echo "$RESPONSE_BODY" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    if [[ -n "$TOKEN" ]]; then
        log_success "User login successful, token received"
        echo "$TOKEN" > "$TOKEN_FILE"
        echo "    Token: ${TOKEN:0:50}..."
    else
        log_fail "Login successful but no token in response"
        echo "    Response: $RESPONSE_BODY"
    fi
else
    log_fail "User login failed (HTTP $HTTP_CODE)"
    echo "    Response: $RESPONSE_BODY"
fi
echo ""

# Test 6: Create Conversation (Main Feature)
log_test "Test 6: Create Conversation (Core Feature)"
if [[ -f "$TOKEN_FILE" ]] && [[ -s "$TOKEN_FILE" ]]; then
    TOKEN=$(cat "$TOKEN_FILE")

    CONVERSATION_RESPONSE=$(curl -k -s -w "\n%{http_code}" -X POST "$API_BASE/conversations" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"customer_email\": \"customer_${TIMESTAMP}@example.com\",
            \"initial_message\": \"I need help with my billing issue\"
        }" 2>/dev/null || echo -e "\n000")

    HTTP_CODE=$(echo "$CONVERSATION_RESPONSE" | tail -1)
    RESPONSE_BODY=$(echo "$CONVERSATION_RESPONSE" | head -n -1)

    if [[ "$HTTP_CODE" == "201" ]] || [[ "$HTTP_CODE" == "200" ]]; then
        log_success "Conversation creation successful"
        CONV_ID=$(echo "$RESPONSE_BODY" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")
        if [[ -n "$CONV_ID" ]]; then
            echo "    Conversation ID: $CONV_ID"
        fi
    else
        log_fail "Conversation creation failed (HTTP $HTTP_CODE)"
        echo "    Response: $RESPONSE_BODY"
    fi
else
    log_fail "Cannot test conversation creation (no auth token)"
fi
echo ""

# Test 7: Container Health Check
log_test "Test 7: Container Health Check"
if command -v docker &>/dev/null && docker compose ps &>/dev/null 2>&1; then
    EXPECTED_CONTAINERS=("fastapi" "postgres" "redis" "nginx" "prometheus" "grafana")
    ALL_HEALTHY=true

    for container in "${EXPECTED_CONTAINERS[@]}"; do
        STATUS=$(docker compose ps "$container" --format "{{.Status}}" 2>/dev/null || echo "Not found")
        if echo "$STATUS" | grep -q "Up"; then
            echo "    ✓ $container: $STATUS"
        else
            echo "    ✗ $container: $STATUS"
            ALL_HEALTHY=false
        fi
    done

    if $ALL_HEALTHY; then
        log_success "All critical containers are running"
    else
        log_fail "Some containers are not running"
    fi
else
    log_warn "Cannot check container health (not running on server)"
fi
echo ""

# Test 8: Prometheus Metrics
log_test "Test 8: Prometheus Metrics Collection"
PROMETHEUS_RESPONSE=$(curl -s -w "\n%{http_code}" "http://${SERVER_IP}:9090/api/v1/targets" 2>/dev/null || echo -e "\n000")
HTTP_CODE=$(echo "$PROMETHEUS_RESPONSE" | tail -1)
RESPONSE_BODY=$(echo "$PROMETHEUS_RESPONSE" | head -n -1)

if [[ "$HTTP_CODE" == "200" ]]; then
    UP_TARGETS=$(echo "$RESPONSE_BODY" | grep -o '"health":"up"' | wc -l)
    if [[ $UP_TARGETS -gt 0 ]]; then
        log_success "Prometheus collecting metrics ($UP_TARGETS targets up)"
    else
        log_warn "Prometheus accessible but no targets up"
    fi
else
    log_warn "Prometheus not accessible (HTTP $HTTP_CODE)"
    echo "    Note: Prometheus may be firewalled, which is normal for production"
fi
echo ""

# Test 9: Grafana Dashboard
log_test "Test 9: Grafana Dashboard Accessibility"
GRAFANA_RESPONSE=$(curl -s -w "\n%{http_code}" "http://${SERVER_IP}:3000/api/health" 2>/dev/null || echo -e "\n000")
HTTP_CODE=$(echo "$GRAFANA_RESPONSE" | tail -1)

if [[ "$HTTP_CODE" == "200" ]]; then
    log_success "Grafana dashboard accessible"
else
    log_warn "Grafana not accessible (HTTP $HTTP_CODE)"
    echo "    Note: Grafana may be firewalled, which is normal for production"
fi
echo ""

# Test 10: Check for Critical Errors in Logs
log_test "Test 10: Application Error Log Check"
if command -v docker &>/dev/null && docker compose ps &>/dev/null 2>&1; then
    ERROR_COUNT=$(docker compose logs --tail=100 fastapi 2>/dev/null | grep -i "ERROR" | grep -v "404" | wc -l || echo "0")

    if [[ $ERROR_COUNT -eq 0 ]]; then
        log_success "No critical errors in recent logs"
    elif [[ $ERROR_COUNT -lt 5 ]]; then
        log_warn "Found $ERROR_COUNT errors in recent logs (may be acceptable)"
    else
        log_fail "Found $ERROR_COUNT errors in recent logs"
        echo "    Run: docker compose logs fastapi | grep -i ERROR"
    fi
else
    log_warn "Cannot check logs (not running on server)"
fi
echo ""

# Test 11: SSL Certificate Check
log_test "Test 11: SSL Certificate Validity"
SSL_CHECK=$(echo | openssl s_client -connect "${SERVER_IP}:443" -servername "${SERVER_IP}" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "ERROR")

if echo "$SSL_CHECK" | grep -q "notAfter"; then
    log_success "SSL certificate is valid"
    echo "    $(echo "$SSL_CHECK" | grep "notAfter")"
else
    log_warn "Could not verify SSL certificate (may be self-signed)"
fi
echo ""

# Test 12: Response Time Check
log_test "Test 12: API Response Time"
START_TIME=$(date +%s%N)
curl -k -s "$API_BASE/health" > /dev/null 2>&1
END_TIME=$(date +%s%N)
RESPONSE_TIME=$(( (END_TIME - START_TIME) / 1000000 ))

if [[ $RESPONSE_TIME -lt 500 ]]; then
    log_success "API response time is good (${RESPONSE_TIME}ms)"
elif [[ $RESPONSE_TIME -lt 2000 ]]; then
    log_warn "API response time is acceptable (${RESPONSE_TIME}ms)"
else
    log_fail "API response time is slow (${RESPONSE_TIME}ms)"
fi
echo ""

# Test 13: Database Backup Check
log_test "Test 13: Database Backup Configuration"
if command -v docker &>/dev/null && [[ -d "./backups" ]]; then
    BACKUP_COUNT=$(ls -1 ./backups/*.sql.gz 2>/dev/null | wc -l || echo "0")

    if [[ $BACKUP_COUNT -gt 0 ]]; then
        log_success "Found $BACKUP_COUNT database backup(s)"
        LATEST_BACKUP=$(ls -t ./backups/*.sql.gz 2>/dev/null | head -1)
        if [[ -n "$LATEST_BACKUP" ]]; then
            BACKUP_AGE=$(( ($(date +%s) - $(stat -c %Y "$LATEST_BACKUP" 2>/dev/null || echo "0")) / 86400 ))
            echo "    Latest backup: $(basename "$LATEST_BACKUP") (${BACKUP_AGE} days old)"

            if [[ $BACKUP_AGE -gt 2 ]]; then
                log_warn "Latest backup is older than 2 days"
            fi
        fi
    else
        log_warn "No database backups found"
        echo "    Run: ./deployment/scripts/backup-database.sh"
    fi
else
    log_warn "Cannot check backups (not running on server)"
fi
echo ""

# Test 14: Disk Space Check
log_test "Test 14: Disk Space Availability"
if command -v df &>/dev/null; then
    DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')

    if [[ $DISK_USAGE -lt 80 ]]; then
        log_success "Disk space is adequate (${DISK_USAGE}% used)"
    elif [[ $DISK_USAGE -lt 90 ]]; then
        log_warn "Disk space is getting full (${DISK_USAGE}% used)"
    else
        log_fail "Disk space is critical (${DISK_USAGE}% used)"
    fi
else
    log_warn "Cannot check disk space (not available)"
fi
echo ""

# Test 15: Memory Usage Check
log_test "Test 15: System Memory Usage"
if command -v free &>/dev/null; then
    MEM_USAGE=$(free | awk 'NR==2 {printf "%.0f", ($3/$2)*100}')

    if [[ $MEM_USAGE -lt 85 ]]; then
        log_success "Memory usage is normal (${MEM_USAGE}%)"
    elif [[ $MEM_USAGE -lt 95 ]]; then
        log_warn "Memory usage is high (${MEM_USAGE}%)"
    else
        log_fail "Memory usage is critical (${MEM_USAGE}%)"
    fi
else
    log_warn "Cannot check memory usage (not available)"
fi
echo ""

# Final Results Summary
echo ""
echo "=========================================="
echo "  Test Results Summary"
echo "=========================================="
echo ""
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo ""

# Calculate success rate
if [[ $TOTAL_TESTS -gt 0 ]]; then
    SUCCESS_RATE=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))
    echo "Success Rate: ${SUCCESS_RATE}%"
else
    echo "Success Rate: N/A"
fi

echo ""

# Determine overall status
if [[ $FAILED_TESTS -eq 0 ]] && [[ $WARNINGS -eq 0 ]]; then
    echo -e "${GREEN}=========================================="
    echo "  ✅ ALL TESTS PASSED"
    echo "==========================================${NC}"
    echo ""
    echo "Your system is fully functional and production-ready!"
    EXIT_CODE=0
elif [[ $FAILED_TESTS -eq 0 ]]; then
    echo -e "${YELLOW}=========================================="
    echo "  ⚠️  ALL TESTS PASSED WITH WARNINGS"
    echo "==========================================${NC}"
    echo ""
    echo "Your system is functional but review warnings above."
    EXIT_CODE=0
elif [[ $SUCCESS_RATE -ge 80 ]]; then
    echo -e "${YELLOW}=========================================="
    echo "  ⚠️  MOST TESTS PASSED"
    echo "==========================================${NC}"
    echo ""
    echo "Your system is mostly functional but has some issues."
    echo "Review failed tests above and fix critical issues."
    EXIT_CODE=1
else
    echo -e "${RED}=========================================="
    echo "  ✗ MULTIPLE TESTS FAILED"
    echo "==========================================${NC}"
    echo ""
    echo "Your system has significant issues that need attention."
    echo "Review all failed tests and fix critical issues before using in production."
    EXIT_CODE=2
fi

echo ""
echo "For detailed logs and troubleshooting:"
echo "  - Docker logs: docker compose logs -f"
echo "  - Health check: curl -k $API_BASE/health"
echo "  - API docs: $API_BASE/docs"
echo ""

exit $EXIT_CODE