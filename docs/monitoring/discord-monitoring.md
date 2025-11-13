# Sentry Discord Integration

## Overview

This document describes the Sentry Discord integration for real-time error and performance monitoring notifications. The integration provides immediate visibility into production issues, enabling faster incident response and resolution.

### Purpose

The Discord integration serves three primary objectives:

1. **Immediate Notification**: Alert engineering teams of critical errors within minutes of occurrence
2. **Prioritized Response**: Route alerts to appropriate channels based on severity
3. **Context Enrichment**: Provide sufficient information to begin investigation without requiring immediate Sentry dashboard access

### Architecture

```
Application Error/Performance Issue
         ↓
Sentry SDK (Capture & Enrich)
         ↓
Sentry Backend (Process & Analyze)
         ↓
Alert Rules Engine (Evaluate Conditions)
         ↓
Discord Webhook (Deliver Notification)
         ↓
Team Response
```

## Prerequisites

### Required Access

- Sentry account with project admin permissions
- Discord server with administrative privileges
- SENTRY_DSN configured in application environment

### Required Sentry Plan

Discord integration requires Sentry Team plan or higher. The integration is not available on the free tier for automated alerts, though manual "Send Test Notification" functionality remains available.

### Application Requirements

- Sentry SDK initialized in application (see `src/utils/monitoring/sentry_config.py`)
- Performance monitoring enabled (`SENTRY_TRACES_SAMPLE_RATE > 0`)
- Proper error handling and exception capture

## Discord Channel Configuration

### Recommended Channel Structure

Create a dedicated monitoring category in Discord with the following channels:

```
Discord Server
└── Monitoring (Category)
    ├── sentry-critical     (High-priority errors requiring immediate attention)
    ├── sentry-errors       (Standard errors and warnings)
    └── sentry-performance  (Performance degradation alerts)
```

### Channel Permissions

Configure channel permissions to ensure appropriate visibility:

**sentry-critical:**
- Visible to: All engineering team members, on-call engineers, engineering managers
- Notification settings: @mentions enabled, high priority

**sentry-errors:**
- Visible to: Engineering team members
- Notification settings: Standard priority

**sentry-performance:**
- Visible to: Engineering team members, platform team
- Notification settings: Low priority, review during business hours

### Webhook Creation

For each channel:

1. Navigate to Channel Settings → Integrations → Webhooks
2. Create new webhook with descriptive name (e.g., "Sentry Critical Alerts")
3. Copy webhook URL for Sentry configuration
4. Document webhook URL in team password manager or secrets management system

**Security Note**: Treat webhook URLs as sensitive credentials. They provide write access to Discord channels without authentication.

## Sentry Configuration

### Integration Setup

1. Navigate to Sentry Dashboard → Settings → Integrations
2. Search for "Discord" in available integrations
3. Click "Add Integration" or "Install"
4. Authorize Sentry to access Discord server
5. Complete OAuth flow

### Alert Rule Configuration

#### Rule 1: Critical Error Alerts

**Purpose**: Immediate notification of fatal errors and high-priority issues

**Configuration:**
```
Name: Critical Errors to Discord
Environment: Production (or All Environments for testing)

Conditions:
  When: An issue is first seen
  If: (Optional filters)
      - Level equals error OR fatal
      - Priority equals high (if using priority tagging)

Actions:
  Send notification to: Discord
  Channel: #sentry-critical
  Tags: environment, level, transaction, correlation_id
  
Action Interval: 1 hour
```

**Rationale**: One-hour interval prevents alert fatigue while ensuring persistent issues receive follow-up notifications.

#### Rule 2: Standard Error Alerts

**Purpose**: Notification of all errors and warnings for tracking and analysis

**Configuration:**
```
Name: All Errors to Discord
Environment: Production (or All Environments)

Conditions:
  When: An issue is first seen
  If: (Optional filters)
      - Level equals error OR warning

Actions:
  Send notification to: Discord
  Channel: #sentry-errors
  Tags: environment, level, transaction
  
Action Interval: 24 hours
```

**Rationale**: 24-hour interval is appropriate for standard errors as they typically require investigation rather than immediate response.

#### Rule 3: Performance Degradation Alerts

**Purpose**: Notification of sustained performance issues

**Configuration:**
```
Name: Performance Degradation
Environment: Production

Conditions:
  Metric: p95(transaction.duration)
  Threshold: Above 5000ms (5 seconds)
  Duration: 5 minutes (sustained)

Actions:
  Send notification to: Discord
  Channel: #sentry-performance
  Tags: environment, transaction, url
  
Action Interval: 24 hours
```

**Rationale**: Performance alerts require sustained degradation to avoid false positives from transient issues. 24-hour interval is appropriate as performance issues typically require analysis rather than immediate action.

### Tag Configuration

Tags provide context in Discord notifications. Configure the following tags for optimal information density:

**Essential Tags (All Alerts):**
- `environment`: Distinguishes production from staging/development
- `level`: Error severity (fatal, error, warning)
- `transaction`: Identifies affected endpoint or operation

**Optional Tags (Based on Application Context):**
- `correlation_id`: Links to application logs for deeper investigation
- `agent_name`: Identifies which agent failed (multi-agent architectures)
- `customer_id`: Business impact assessment
- `url`: Direct identification of affected endpoint

**Tag Implementation**: Tags must be set in application code via Sentry SDK. See `src/utils/monitoring/sentry_config.py` for implementation details.

## Testing Procedures

### Integration Test

Verify Discord integration configuration:

```bash
# Set environment variables
export SENTRY_DSN="your-sentry-dsn"

# Run integration test suite
python -m pytest tests/integration/test_sentry_discord.py -v

# Expected output:
# - Test errors sent to Sentry
# - Discord notifications received in appropriate channels
# - Tags present in notifications
```

### Manual Verification

1. **Sentry Dashboard Test**:
   - Navigate to Alerts → Alert Rule → Send Test Notification
   - Verify notification arrives in Discord within 60 seconds
   - Confirm channel routing is correct

2. **Application Test**:
   ```bash
   # Start application
   uvicorn src.api.main:app --reload
   
   # Trigger test error
   curl http://localhost:8000/test-error-endpoint
   
   # Verify in Discord (1-2 minute delay expected)
   ```

3. **Performance Test**:
   ```bash
   # Generate slow requests
   python scripts/generate_sentry_performance_load.py
   
   # Wait 5-10 minutes
   # Verify performance alert in Discord
   ```

### Validation Checklist

After initial setup, verify:

- [ ] Critical errors appear in #sentry-critical
- [ ] Standard errors appear in #sentry-errors
- [ ] Performance alerts appear in #sentry-performance
- [ ] Tags are present and accurate
- [ ] Correlation IDs match application logs
- [ ] PII is properly masked (emails, tokens, passwords)
- [ ] Alert intervals function as configured

## Maintenance

### Regular Review

**Weekly:**
- Review alert volume and noise levels
- Identify recurring issues for permanent fixes
- Verify alert routing is appropriate

**Monthly:**
- Review alert rule thresholds for relevance
- Analyze alert response times
- Update documentation if processes change

### Alert Tuning

If experiencing alert fatigue:

1. **Increase Action Intervals**: Change from 1 hour to 4 hours for less critical alerts
2. **Add Filters**: Narrow conditions to reduce false positives
3. **Adjust Thresholds**: For performance alerts, increase duration or threshold values
4. **Consolidate**: Consider combining related alerts

If missing important alerts:

1. **Decrease Action Intervals**: More frequent notifications
2. **Broaden Conditions**: Remove overly restrictive filters
3. **Lower Thresholds**: Earlier detection of performance issues
4. **Add Alert Rules**: Create specific rules for critical paths

### Channel Hygiene

Periodically clean Discord channels:

1. Archive or delete test notifications
2. Mark resolved issues with reactions or threads
3. Use pinned messages for recurring issues requiring permanent fixes
4. Document post-mortems in dedicated threads

## Troubleshooting

### No Notifications Received

**Symptom**: Errors visible in Sentry dashboard, but no Discord notifications

**Diagnosis:**

1. **Verify Alert Rules Are Enabled**:
   - Sentry → Alerts → Check toggle status
   - Rules must show green "Enabled" status

2. **Check Alert History**:
   - Sentry → Alerts → Alert Name → History tab
   - Verify if alerts were triggered but failed delivery

3. **Verify Discord Integration**:
   - Sentry → Settings → Integrations → Discord
   - Confirm "Installed" status
   - Re-authorize if necessary

4. **Test Webhook Directly**:
   ```bash
   curl -X POST "DISCORD_WEBHOOK_URL" \
     -H "Content-Type: application/json" \
     -d '{"content": "Test message"}'
   ```

**Resolution**: Based on diagnosis, either re-enable rules, fix webhook URLs, or re-authorize Discord integration.

### Notifications in Wrong Channel

**Symptom**: Alerts arriving in incorrect Discord channel

**Diagnosis**: Verify channel IDs in alert rule configuration

**Resolution**:
1. Get correct channel ID from Discord (Right-click channel → Copy Channel ID)
2. Update alert rule in Sentry
3. Send test notification to verify

### Missing Context in Notifications

**Symptom**: Tags like correlation_id or agent_name not appearing in Discord

**Diagnosis**: Tags not being set as Sentry tags in application code

**Resolution**: Update `before_send` hook in `src/utils/monitoring/sentry_config.py` to set context as tags:

```python
event.setdefault("tags", {})["correlation_id"] = correlation_id
event.setdefault("tags", {})["agent_name"] = agent_name
```

### Excessive Alert Volume

**Symptom**: Too many notifications, alert fatigue

**Resolution Options**:

1. **Increase action intervals**:
   - Change critical alerts from 1 hour to 4 hours
   - Change standard alerts from 24 hours to 48 hours

2. **Add error count thresholds**:
   - Trigger only when error occurs >10 times in 5 minutes
   - Filters transient issues

3. **Implement error sampling**:
   - Adjust `sample_rate` in Sentry configuration
   - Reduces volume while maintaining visibility

4. **Use issue states**:
   - Alert only on "first seen" events
   - Prevents repeated notifications for known issues

## Security Considerations

### Webhook Protection

Discord webhooks provide unauthenticated write access to channels. Protect them by:

1. **Secure Storage**: Store webhook URLs in password manager or secrets management system
2. **Access Control**: Limit access to webhook URLs to authorized personnel only
3. **Rotation**: Regenerate webhooks if exposed or when team members leave
4. **Monitoring**: Review webhook usage in Discord audit logs

### PII Masking

Sentry automatically masks PII via `before_send` hook in `src/utils/monitoring/sentry_config.py`:

- Email addresses: `user@example.com` → `us***@example.com`
- Passwords, tokens, API keys: Completely masked as `***MASKED***`
- Credit card numbers: Last 4 digits shown only
- Custom sensitive fields: Add to `SENSITIVE_KEYS` set

**Verification**: Review notifications in Discord to ensure no PII exposure.

### Access Control

Implement appropriate access controls:

1. **Channel Visibility**: Limit error channels to engineering team only
2. **Webhook Permissions**: Restrict webhook creation to administrators
3. **Sentry Access**: Use role-based access control for alert configuration
4. **Audit Logging**: Enable Discord audit logs for webhook activity tracking

## Best Practices

### Alert Design

1. **Actionable Alerts**: Every alert should have a clear action or investigation path
2. **Appropriate Severity**: Reserve critical channel for truly urgent issues
3. **Context Sufficiency**: Include enough information to begin investigation
4. **Consistent Formatting**: Use standardized tag sets across alerts

### Response Process

1. **Acknowledge**: React to message to indicate investigation started
2. **Thread Discussion**: Use threads for investigation notes
3. **Resolution Documentation**: Note resolution in thread for future reference
4. **Follow-up**: Close thread when issue resolved

### Integration with Incident Management

For production incidents:

1. Discord alert triggers initial investigation
2. Escalate to formal incident management system (PagerDuty, Opsgenie)
3. Link Discord thread in incident documentation
4. Use correlation ID to trace across systems

### Documentation Requirements

Maintain documentation for:

1. **Alert Routing**: Which alerts go to which channels and why
2. **Response Procedures**: How to respond to different alert types
3. **Escalation Paths**: When and how to escalate issues
4. **On-Call Schedules**: Who responds to critical alerts

## Performance Monitoring Specifics

### Transaction Sampling

Performance monitoring uses transaction sampling to manage volume:

- Default: 10% of requests (`SENTRY_TRACES_SAMPLE_RATE=0.1`)
- Recommendation: 10-20% for production systems
- Higher sampling increases costs but improves accuracy

### Alert Thresholds

Performance thresholds should reflect user experience requirements:

**API Services:**
- Critical: p95 > 5000ms (5 seconds)
- Warning: p95 > 3000ms (3 seconds)

**Background Jobs:**
- Critical: p95 > 30000ms (30 seconds)
- Warning: p95 > 15000ms (15 seconds)

**Adjust based on application SLAs and user experience targets.**

### Sustained Degradation Requirement

Performance alerts require sustained issues to trigger:

- Minimum duration: 5 minutes
- Rationale: Avoids false positives from transient spikes
- Trade-off: Slower detection but higher signal-to-noise ratio

## Rollback Procedures

If Discord integration requires emergency disabling:

1. **Immediate Disablement**:
   - Sentry → Alerts → Toggle alert rules OFF
   - Takes effect immediately, no deployment required

2. **Temporary Suspension**:
   - Discord → Channel Settings → Delete webhook
   - Breaks connection without affecting Sentry configuration

3. **Complete Removal**:
   - Sentry → Settings → Integrations → Discord → Uninstall
   - Removes integration entirely

**Recovery**: Re-authorize integration and re-enable alert rules to restore functionality.

## Appendix

### Related Documentation

- Sentry Configuration: `src/utils/monitoring/sentry_config.py`
- Integration Tests: `tests/integration/test_sentry_discord.py`
- Performance Testing: `docs/monitoring/performance-testing.md`
- Sentry Official Docs: https://docs.sentry.io/product/integrations/notification-incidents/discord/

### Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-12 | 1.0.0 | Initial documentation for Phase 2.1 Discord integration | System |

### Contact

For questions or issues with Discord monitoring:

talk to Mohammad Othman

---
