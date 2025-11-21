# Deployment Configuration

This directory contains all production deployment configurations and automation scripts for Oracle Cloud Always Free Tier deployment.

---

## Directory Structure

```
deployment/
├── nginx/                          # Nginx reverse proxy configuration
│   ├── nginx.conf                  # Main Nginx config
│   ├── conf.d/
│   │   └── default.conf            # Virtual host configuration
│   ├── ssl/                        # SSL certificates
│   └── generate-self-signed-cert.sh
│
├── postgres/                       # PostgreSQL configuration
│   └── postgresql.conf             # Production-tuned PostgreSQL config
│
├── redis/                          # Redis configuration
│   └── redis.conf                  # Production-tuned Redis config
│
├── prometheus/                     # Monitoring configuration
│   ├── prometheus.yml              # Prometheus scrape configs
│   └── rules/
│       └── alerts.yml              # Alert rules
│
├── grafana/                        # Grafana configuration
│   └── provisioning/
│       ├── datasources/            # Auto-provision datasources
│       └── dashboards/             # Auto-provision dashboards
│
├── certbot/                        # Let's Encrypt certificates
│   ├── www/                        # ACME challenge directory
│   └── conf/                       # Certificate storage
│
├── scripts/                        # Deployment and management scripts
│   ├── deploy.sh                   # Master deployment script
│   ├── backup-database.sh          # Database backup
│   ├── restore-database.sh         # Database restore
│   ├── setup-letsencrypt.sh        # SSL certificate setup
│   ├── setup-backup-cron.sh        # Automated backup configuration
│   ├── verify-knowledge-base.sh    # Knowledge base verification
│   ├── acceptance-tests.sh         # Comprehensive system tests
│   └── README.md                   # Detailed script documentation
│
└── backups/                        # Local backups directory
```

---

## Deployment Scripts

All deployment and management scripts are located in `deployment/scripts/`. Each script serves a specific purpose in the deployment lifecycle.

### deploy.sh - Master Deployment Script

**Purpose**: Complete automated deployment from scratch on a fresh server.

**Usage**:
```bash
./deployment/scripts/deploy.sh
```

**When to Run**:
- First-time deployment on a new server
- After complete system rebuild (rm -rf and git clone)
- ONE TIME ONLY per server

**What It Does** (11 automated steps):
1. Cleans existing deployment state
2. Configures system settings (sysctl, ulimits, swap)
3. Installs and configures Docker
4. Verifies Doppler secrets management setup
5. Configures Oracle Object Storage (if available)
6. Deploys all application containers
7. Applies database migrations
8. Initializes knowledge base with vector embeddings
9. Sets up automated daily backups
10. Configures monitoring and alerting
11. Runs comprehensive health checks

**Dependencies**: Doppler CLI, Docker, Docker Compose

**Execution Time**: 10-15 minutes

**Important**: This script should only be run once. For daily operations, use `doppler run -- docker compose` commands directly.

---

### backup-database.sh - Database Backup

**Purpose**: Create compressed PostgreSQL database backup with optional cloud upload.

**Usage**:
```bash
# Automatic (via cron)
# Runs daily at 3:00 AM automatically

# Manual execution
./deployment/scripts/backup-database.sh
```

**When to Run**:
- Automatically runs daily at 3:00 AM via cron job
- Manually before major changes or updates
- Before running database migrations
- Before system maintenance

**What It Does**:
1. Dumps PostgreSQL database to SQL file
2. Compresses backup with gzip
3. Names with timestamp: `postgres_YYYYMMDD_HHMMSS.sql.gz`
4. Saves to `backups/` directory
5. Uploads to Oracle Object Storage (if configured)
6. Deletes local backups older than 7 days
7. Logs all operations

**Backup Location**: `PROJECT_ROOT/backups/`

**Retention Policy**: 7 days local, configurable for cloud storage

**Execution Time**: 1-3 minutes

**Environment Variables**:
- `BACKUP_DIR`: Override default backup directory
- `RETENTION_DAYS`: Override 7-day retention (default: 7)
- `OCI_BUCKET_NAME`: Oracle Object Storage bucket name
- `OCI_NAMESPACE`: Oracle Object Storage namespace

---

### restore-database.sh - Database Restore

**Purpose**: Restore PostgreSQL database from a backup file.

**Usage**:
```bash
./deployment/scripts/restore-database.sh <backup-file>

# Example
./deployment/scripts/restore-database.sh postgres_20251121_180505.sql.gz

# List available backups
ls -lh backups/
```

**When to Run**:
- After data loss or corruption
- When reverting to a previous system state
- During disaster recovery
- When migrating data between servers

**What It Does**:
1. Prompts for confirmation (destructive operation)
2. Stops FastAPI application container
3. Drops existing database
4. Creates new empty database
5. Restores data from backup file
6. Restarts FastAPI application
7. Waits for health check confirmation

**Execution Time**: 3-5 minutes

**Warning**: This operation is destructive. All current database data will be replaced with backup data. Ensure you have a recent backup before proceeding.

---

### setup-backup-cron.sh - Automated Backup Configuration

**Purpose**: Configure automated daily database backups via cron job.

**Usage**:
```bash
./deployment/scripts/setup-backup-cron.sh
```

**When to Run**:
- After initial deployment (optional, deploy.sh already configures this)
- To verify cron job configuration
- To update backup schedule
- After manually removing cron jobs

**What It Does**:
1. Verifies backup script exists and is executable
2. Creates logs directory if missing
3. Tests backup script with manual execution
4. Checks for and removes existing backup cron jobs
5. Adds new cron job for daily 3:00 AM backups
6. Configures logging to `logs/backup.log`
7. Displays current crontab for verification

**Execution Time**: 2-3 minutes

**Cron Schedule**: Daily at 3:00 AM UTC

**Log Location**: `PROJECT_ROOT/logs/backup.log`

**Verification**:
```bash
# View configured cron jobs
crontab -l

# Check backup log
tail -f logs/backup.log

# List recent backups
ls -lh backups/
```

---

### verify-knowledge-base.sh - Knowledge Base Verification

**Purpose**: Comprehensive verification of knowledge base and vector search functionality.

**Usage**:
```bash
./deployment/scripts/verify-knowledge-base.sh
```

**When to Run**:
- After initial deployment
- After knowledge base updates or changes
- When troubleshooting vector search issues
- After adding new articles or documents
- During system health checks

**What It Does**:
1. Verifies FastAPI container is running
2. Initializes knowledge base (idempotent operation)
3. Tests Qdrant Cloud connection
4. Lists all collections and vector counts
5. Tests vector search functionality
6. Validates embedding model (all-MiniLM-L6-v2)
7. Provides detailed status report

**Execution Time**: 2-5 minutes

**Expected Output**:
- Connection status to Qdrant Cloud
- Number of collections
- Vector counts per collection
- Embedding model validation
- Search functionality confirmation

**Note**: This script can be safely run multiple times. It performs idempotent operations that will not duplicate data.

---

### acceptance-tests.sh - Comprehensive System Tests

**Purpose**: Run comprehensive test suite covering all critical system functionality.

**Usage**:
```bash
# From server
./deployment/scripts/acceptance-tests.sh

# From remote with custom IP
./deployment/scripts/acceptance-tests.sh 192.168.1.100
```

**When to Run**:
- After initial deployment
- Before production release
- After major system updates
- As part of CI/CD pipeline
- During regular health checks
- Before and after maintenance windows

**Test Suite** (15 comprehensive tests):
1. API Health Check - Verifies API is responding
2. API Documentation - Confirms Swagger UI accessibility
3. Database Connection - Tests database connectivity
4. User Registration - Validates user creation
5. User Authentication - Tests JWT token generation
6. Conversation Creation - Verifies core feature functionality
7. Container Health - Checks all container status
8. Prometheus Metrics - Validates metrics collection
9. Grafana Dashboard - Tests monitoring dashboard
10. Application Logs - Scans for critical errors
11. SSL Certificate - Validates SSL configuration
12. API Response Time - Tests performance
13. Database Backups - Verifies backup configuration
14. Disk Space - Checks available storage
15. Memory Usage - Monitors system resources

**Execution Time**: 5-10 minutes

**Output Format**:
- Color-coded pass/fail/warning indicators
- Detailed test results
- Success rate percentage
- Final summary report

**Exit Codes**:
- 0: All tests passed
- 1: Tests passed with warnings
- 2: One or more tests failed

---

### setup-letsencrypt.sh - SSL Certificate Configuration

**Purpose**: Configure Let's Encrypt SSL certificate for production domains.

**Usage**:
```bash
./deployment/scripts/setup-letsencrypt.sh <domain> <email>

# Example
./deployment/scripts/setup-letsencrypt.sh example.com admin@example.com
```

**When to Run**:
- When you have a registered domain name
- After DNS configuration is complete
- To replace self-signed certificates

**Prerequisites**:
- Domain name registered and active
- DNS A record pointing to server IP
- DNS propagation complete (verify with `dig` or `nslookup`)
- Email address for certificate notifications

**What It Does**:
1. Validates domain and email parameters
2. Obtains Let's Encrypt SSL certificate
3. Configures Nginx for HTTPS
4. Sets up automatic certificate renewal
5. Reloads Nginx configuration
6. Verifies certificate installation

**Execution Time**: 5-10 minutes

**Certificate Renewal**: Automatic via certbot container

**Note**: Only use this if you have a domain name. For IP-based deployments, the self-signed certificate is adequate.

---

## Configuration Files

### Nginx Configuration

**nginx.conf**: Main configuration with performance tuning
- Worker processes: auto
- Events: 1024 connections per worker
- Gzip compression enabled
- Client body size: 20MB
- Timeouts optimized for production

**default.conf**: Virtual host configuration
- HTTP to HTTPS redirect
- Rate limiting (10 requests/second)
- Security headers (HSTS, X-Frame-Options, CSP)
- Upstream configuration for FastAPI
- SSL/TLS configuration
- Static file serving

### PostgreSQL Configuration

**postgresql.conf**: Production-tuned for 6GB RAM allocation
- Shared buffers: 1.5GB
- Effective cache size: 4.6GB
- Work memory: 8MB
- Maintenance work memory: 384MB
- Max connections: 200
- Checkpoint completion target: 0.9
- Random page cost: 1.1 (SSD optimized)
- Effective I/O concurrency: 200
- Query logging: Slow queries over 1 second
- Connection logging enabled

### Redis Configuration

**redis.conf**: Production-tuned for 2GB RAM
- Max memory: 2GB
- Eviction policy: LRU (Least Recently Used)
- RDB persistence: 15min/5min/1min snapshots
- AOF disabled (using RDB only)
- TCP backlog: 511
- Timeout: 300 seconds
- Max clients: 10000
- Dangerous commands disabled (FLUSHDB, FLUSHALL, KEYS)

### Prometheus Configuration

**prometheus.yml**: Scrape configurations
- Scrape interval: 15 seconds
- Evaluation interval: 15 seconds
- Targets:
  - FastAPI application metrics
  - PostgreSQL via postgres_exporter
  - Redis via redis_exporter
  - System metrics via node_exporter
  - Qdrant Cloud (if accessible)

**alerts.yml**: Alert rule definitions
- Critical alerts: API down, database down, disk full
- Warning alerts: High CPU, high memory, slow queries
- Business logic alerts: LLM failures, agent errors
- Threshold-based alerts with configurable durations

### Grafana Configuration

**datasources/prometheus.yml**: Auto-provisions Prometheus datasource
- Access: Proxy mode
- URL: http://prometheus:9090
- Default datasource enabled

**dashboards/default.yml**: Auto-loads dashboards
- Dashboard location: /grafana/dashboards
- System overview dashboard included
- Custom dashboards can be added to this directory

---

## Resource Allocation

Target system: Oracle Cloud Always Free Tier (4 vCPUs, 24GB RAM, 200GB storage)

| Service | CPU Limit | Memory Limit | Memory Reserve | Purpose |
|---------|-----------|--------------|----------------|---------|
| FastAPI | 2 cores | 2GB | 1GB | Application server |
| PostgreSQL | 2 cores | 6GB | 4GB | Primary database |
| Redis | 1 core | 2GB | 1GB | Cache and rate limiting |
| Nginx | 1 core | 512MB | 256MB | Reverse proxy and SSL |
| Prometheus | 1 core | 2GB | 1GB | Metrics collection |
| Grafana | 1 core | 1GB | 512MB | Monitoring dashboards |
| Node Exporter | 0.25 cores | 128MB | 64MB | System metrics |
| Postgres Exporter | 0.25 cores | 128MB | 64MB | Database metrics |
| Redis Exporter | 0.25 cores | 128MB | 64MB | Cache metrics |
| Certbot | 0.25 cores | 128MB | 64MB | SSL certificate renewal |

**Total Allocated**: ~3.5 cores, ~14GB RAM (leaves headroom for system operations)

**Note**: Qdrant runs as external cloud service and does not consume local resources.

---

## Security Configuration

### Oracle Cloud Security Lists

Required ingress rules in Oracle Cloud Console:

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 22 | TCP | Restricted IP | SSH access |
| 80 | TCP | 0.0.0.0/0 | HTTP (redirects to HTTPS) |
| 443 | TCP | 0.0.0.0/0 | HTTPS (API and web access) |
| 3000 | TCP | Restricted IP | Grafana dashboard (optional) |
| 9090 | TCP | Restricted IP | Prometheus UI (optional) |

### Container Security

- All containers run as non-root users
- Read-only root filesystems where possible
- Resource limits enforced via Docker Compose
- Security scanning enabled in CI/CD
- Regular image updates from official sources
- Secrets managed via Doppler (not in containers)

### Network Security

- All services communicate via internal Docker network
- Only Nginx exposed to public internet
- Database and Redis not directly accessible
- Monitoring tools accessible only from restricted IPs
- Rate limiting on API endpoints
- CORS configuration restricts origins

---

## Monitoring

### Access Points

- **Prometheus**: http://SERVER_IP:9090
- **Grafana**: http://SERVER_IP:3000
  - Default credentials: admin / GRAFANA_ADMIN_PASSWORD (from Doppler)
- **API Metrics**: http://localhost:8000/metrics
- **FastAPI Health**: https://SERVER_IP/api/health

### Key Metrics

**Application Metrics**:
- HTTP request rate and duration
- Error rate by status code
- Active connections and request queue
- Response time percentiles (p50, p95, p99)
- Endpoint-specific performance

**Database Metrics**:
- Connection pool usage
- Query execution time
- Cache hit ratio
- Transaction rate and rollbacks
- Table and index sizes
- Slow query count

**System Metrics**:
- CPU usage per core
- Memory usage and swap
- Disk I/O operations
- Network throughput
- File system usage

**Business Metrics**:
- Conversations created per hour
- Message processing time
- Agent response time
- Knowledge base queries
- LLM API latency

### Alert Configuration

Alerts are configured in `prometheus/rules/alerts.yml`:

**Critical Alerts** (immediate action required):
- API endpoint down for more than 2 minutes
- PostgreSQL down for more than 1 minute
- Redis down for more than 1 minute
- Error rate exceeds 5% for 5 minutes
- Disk space below 5%

**Warning Alerts** (investigation required):
- CPU usage above 80% for 10 minutes
- Memory usage above 85% for 5 minutes
- Request latency p95 above 2 seconds
- Slow query count increasing
- Disk space below 15%

---

## Backup Strategy

### Automated Backups

- **Schedule**: Daily at 3:00 AM UTC via cron job
- **Location**: `PROJECT_ROOT/backups/`
- **Format**: Compressed SQL dump (gzip)
- **Naming**: `postgres_YYYYMMDD_HHMMSS.sql.gz`
- **Retention**: 7 days locally
- **Cloud Upload**: Optional (Oracle Object Storage)

### Manual Backup

```bash
# Create backup
./deployment/scripts/backup-database.sh

# List backups
ls -lh backups/

# View backup log
tail -f logs/backup.log
```

### Restore Procedure

```bash
# Stop application
doppler run -- docker compose stop fastapi

# Restore from backup
./deployment/scripts/restore-database.sh postgres_20251121_180505.sql.gz

# Application automatically restarts after restore
```

### Offsite Backup Configuration

To enable Oracle Object Storage backups:

1. Install OCI CLI on server
2. Configure OCI authentication
3. Set environment variables:
   - `OCI_BUCKET_NAME`: Bucket name
   - `OCI_NAMESPACE`: Object Storage namespace
4. Run backup script - will automatically upload

---

## Daily Operations

### Starting Services

```bash
# All services
doppler run -- docker compose up -d

# Specific service
doppler run -- docker compose up -d fastapi
```

### Stopping Services

```bash
# All services
doppler run -- docker compose down

# Specific service
doppler run -- docker compose stop fastapi
```

### Updating Application

```bash
# Pull latest code
git pull

# Rebuild and restart
doppler run -- docker compose build
doppler run -- docker compose up -d

# Verify deployment
docker compose ps
curl -k https://SERVER_IP/api/health
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f fastapi

# Last 100 lines
docker compose logs --tail=100 fastapi

# With timestamps
docker compose logs -f --timestamps fastapi
```

### Checking Status

```bash
# Container status
docker compose ps

# Resource usage
docker stats

# Health checks
curl -k https://SERVER_IP/api/health
docker compose exec postgres pg_isready
docker compose exec redis redis-cli ping
```

---

## Troubleshooting

### Common Issues

**Issue: Variable warnings when running docker compose commands**
- **Cause**: Running docker compose without Doppler prefix
- **Solution**: Use `doppler run -- docker compose` commands
- **Note**: These warnings are cosmetic. Containers already have secrets from initial startup.

**Issue: Container shows as unhealthy**
- **Check logs**: `docker compose logs <service>`
- **Restart service**: `doppler run -- docker compose restart <service>`
- **Check health**: `docker compose exec <service> <health-command>`

**Issue: Database connection failures**
- **Verify database**: `docker compose exec postgres pg_isready`
- **Check connections**: `docker compose logs postgres`
- **Restart database**: `doppler run -- docker compose restart postgres`

**Issue: High memory usage**
- **Check stats**: `docker stats`
- **Review logs**: Look for memory leaks
- **Restart service**: `doppler run -- docker compose restart <service>`

**Issue: Backup failures**
- **Check log**: `cat logs/backup.log`
- **Verify permissions**: `ls -la deployment/scripts/backup-database.sh`
- **Test manually**: `./deployment/scripts/backup-database.sh`

### Service Health Commands

```bash
# FastAPI
curl -k https://localhost/api/health

# PostgreSQL
docker compose exec postgres pg_isready
docker compose exec postgres psql -U postgres -c "SELECT 1;"

# Redis
docker compose exec redis redis-cli ping

# Nginx
docker compose exec nginx nginx -t

# Prometheus
curl http://localhost:9090/-/healthy

# Grafana
curl http://localhost:3000/api/health
```

### Container Management

```bash
# Restart specific container
doppler run -- docker compose restart fastapi

# Rebuild container
doppler run -- docker compose build fastapi
doppler run -- docker compose up -d fastapi

# View container details
docker inspect multi-agent-fastapi

# Execute commands in container
docker compose exec fastapi bash
```

---

## Performance Optimization

### Database Optimization

```bash
# Analyze database
docker compose exec postgres psql -U postgres -d support_agent -c "ANALYZE;"

# Vacuum database
docker compose exec postgres psql -U postgres -d support_agent -c "VACUUM;"

# Check slow queries
docker compose logs postgres | grep "duration:"
```

### Cache Management

```bash
# Check Redis info
docker compose exec redis redis-cli info

# Monitor Redis commands
docker compose exec redis redis-cli monitor

# Check cache hit rate
docker compose exec redis redis-cli info stats | grep hits
```

### Resource Monitoring

```bash
# Real-time container stats
docker stats

# System resource usage
free -h
df -h
top

# Network connections
ss -tuln
```

---

## Documentation

- **Main README**: `/README.md` - Project overview
- **Deployment Guide**: `/docs/DEPLOYMENT.md` - Detailed deployment instructions
- **How It Works**: `/HOW_IT_WORKS.md` - Deployment workflow explanation
- **Deployed Config**: `/DEPLOYED_CONFIG.md` - Current deployment configuration
- **Scripts Documentation**: `/deployment/scripts/README.md` - Detailed script reference
- **API Documentation**: `https://SERVER_IP/api/docs` - Interactive API documentation

---

## Support

For issues, questions, or contributions:

- **GitHub Issues**: https://github.com/OthmanMohammad/multi-agent-support-system/issues
- **API Documentation**: https://SERVER_IP/api/docs
- **Monitoring Dashboard**: http://SERVER_IP:3000

---

**Important Notes**:

1. Replace `SERVER_IP` with your actual Oracle Cloud public IP address throughout this documentation.
2. All sensitive credentials are managed via Doppler and should never be committed to version control.
3. The deploy.sh script should only be run once per server for initial setup.
4. For daily operations, use `doppler run -- docker compose` commands directly.
5. Regular backups are automated and run daily at 3:00 AM UTC.
6. Monitor the system regularly using Grafana dashboards and Prometheus alerts.

---

**Last Updated**: 2025-11-21
**Deployment Status**: Production Ready
**Oracle Cloud Configuration**: (4 vCPUs, 24GB RAM)