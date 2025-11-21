#!/bin/bash
#
# Automated Backup Cron Job Setup Script
# Sets up daily database backups at 3:00 AM
#
# Usage: ./deployment/scripts/setup-backup-cron.sh
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo ""
echo "=========================================="
echo "  Automated Backup Setup"
echo "=========================================="
echo ""

# Get current directory (project root)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKUP_SCRIPT="$PROJECT_DIR/deployment/scripts/backup-database.sh"
LOG_DIR="$PROJECT_DIR/logs"

log_info "Project directory: $PROJECT_DIR"

# Step 1: Verify backup script exists
if [[ ! -f "$BACKUP_SCRIPT" ]]; then
    log_error "Backup script not found at: $BACKUP_SCRIPT"
    exit 1
fi
log_success "Backup script found"

# Step 2: Ensure backup script is executable
if [[ ! -x "$BACKUP_SCRIPT" ]]; then
    log_info "Making backup script executable..."
    chmod +x "$BACKUP_SCRIPT"
fi
log_success "Backup script is executable"

# Step 3: Create logs directory if it doesn't exist
if [[ ! -d "$LOG_DIR" ]]; then
    log_info "Creating logs directory..."
    mkdir -p "$LOG_DIR"
fi
log_success "Logs directory ready: $LOG_DIR"

# Step 4: Test backup script manually
log_info "Testing backup script (this may take a few moments)..."
if "$BACKUP_SCRIPT"; then
    log_success "Backup script executed successfully"
else
    log_error "Backup script test failed"
    log_error "Please check the script and try again"
    exit 1
fi

# Step 5: Check if DOPPLER_TOKEN is set
if [[ -z "${DOPPLER_TOKEN:-}" ]]; then
    log_warn "DOPPLER_TOKEN environment variable is not set"
    log_warn "The cron job will need access to this token"
    echo ""
    echo "Please add the following to your ~/.bashrc:"
    echo "  export DOPPLER_TOKEN=\"your_token_here\""
    echo ""
    echo "Then run: source ~/.bashrc"
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Setup cancelled"
        exit 0
    fi
fi

# Step 6: Check if cron job already exists
log_info "Checking for existing cron jobs..."
EXISTING_CRON=$(crontab -l 2>/dev/null | grep -F "$BACKUP_SCRIPT" || true)

if [[ -n "$EXISTING_CRON" ]]; then
    log_warn "A cron job for this backup script already exists:"
    echo "  $EXISTING_CRON"
    echo ""
    read -p "Do you want to replace it? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Keeping existing cron job"
        exit 0
    fi

    # Remove existing cron job
    log_info "Removing existing cron job..."
    (crontab -l 2>/dev/null | grep -vF "$BACKUP_SCRIPT") | crontab -
    log_success "Existing cron job removed"
fi

# Step 7: Create new cron job
log_info "Setting up daily backup at 3:00 AM..."

# Build cron command
CRON_COMMAND="0 3 * * * cd $PROJECT_DIR && $BACKUP_SCRIPT >> $LOG_DIR/backup.log 2>&1"

# Add to crontab
(crontab -l 2>/dev/null || echo "") | {
    cat
    echo "# Automated database backup for multi-agent support system"
    echo "$CRON_COMMAND"
} | crontab -

log_success "Cron job added successfully"

echo ""
echo "=========================================="
echo "  ✅ Backup Setup Complete"
echo "=========================================="
echo ""

# Display current crontab
log_info "Current crontab:"
echo ""
crontab -l | tail -5
echo ""

# Show backup information
log_info "Backup Configuration:"
echo "  - Schedule: Daily at 3:00 AM"
echo "  - Backup Script: $BACKUP_SCRIPT"
echo "  - Log File: $LOG_DIR/backup.log"
echo "  - Backup Location: $PROJECT_DIR/backups/"
echo ""

# Show how to verify backups
log_info "How to verify backups:"
echo ""
echo "  1. Check backup files:"
echo "     ls -lh $PROJECT_DIR/backups/"
echo ""
echo "  2. View backup log:"
echo "     tail -f $LOG_DIR/backup.log"
echo ""
echo "  3. Test manual backup:"
echo "     $BACKUP_SCRIPT"
echo ""
echo "  4. List cron jobs:"
echo "     crontab -l"
echo ""

# Important notes
log_warn "Important Notes:"
echo "  1. Backups will be stored locally in the backups/ directory"
echo "  2. Only the last 7 days of backups are kept (older ones are auto-deleted)"
echo "  3. For offsite backups, configure Oracle Object Storage separately"
echo "  4. Test the backup manually before relying on the cron job"
echo "  5. Monitor the backup.log file regularly for any errors"
echo ""

log_success "Automated backups are now configured and will run daily at 3:00 AM"
echo ""