# 📦 Deployment Configuration

This directory contains all production deployment configurations for Oracle Cloud.

## 🗂️ Directory Structure

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
├── scripts/                        # Deployment scripts
│   ├── setup-server.sh             # Initial server setup
│   ├── deploy.sh                   # Application deployment
│   ├── setup-letsencrypt.sh        # SSL certificate setup
│   ├── backup-database.sh          # Database backup
│   └── restore-database.sh         # Database restore
│
└── backups/                        # Local backups directory
```

## 🚀 Quick Start

### 1. Initial Server Setup

```bash
./deployment/scripts/setup-server.sh
```

This configures:
- System updates
- Firewall (UFW)
- Fail2ban
- SSH hardening
- Docker installation

### 2. Deploy Application

```bash
./deployment/scripts/deploy.sh
```

This deploys:
- PostgreSQL database
- Redis cache
- Qdrant vector store
- FastAPI application
- Nginx reverse proxy
- Prometheus monitoring
- Grafana dashboards

### 3. Configure SSL

**Without domain (self-signed):**
```bash
./deployment/nginx/generate-self-signed-cert.sh
```

**With domain (Let's Encrypt):**
```bash
./deployment/scripts/setup-letsencrypt.sh yourdomain.com your@email.com
```

## 📝 Configuration Files

### Nginx

- **nginx.conf**: Main configuration with performance tuning
- **default.conf**: Virtual host with:
  - HTTP to HTTPS redirect
  - Rate limiting
  - Security headers
  - Upstream configuration

### PostgreSQL

- **postgresql.conf**: Production-tuned for 6GB RAM allocation
  - Memory: 1.5GB shared_buffers, 4.6GB effective_cache_size
  - Connection pooling: 200 max connections
  - SSD optimized
  - Query logging for slow queries (>1s)

### Redis

- **redis.conf**: Production-tuned for 2GB RAM
  - Max memory: 2GB with LRU eviction
  - RDB persistence (15min/5min/1min snapshots)
  - Connection tuning
  - Dangerous commands disabled

### Prometheus

- **prometheus.yml**: Scrape configurations for:
  - FastAPI application
  - PostgreSQL (via postgres_exporter)
  - Redis (via redis_exporter)
  - System metrics (via node_exporter)
  - Qdrant vector store

- **alerts.yml**: Alert rules for:
  - Application (API down, high error rate, latency)
  - Database (connections, slow queries, deadlocks)
  - Redis (memory, evictions, connections)
  - System (CPU, memory, disk)
  - Business logic (LLM errors, agent failures)

### Grafana

- **datasources/prometheus.yml**: Auto-provisions Prometheus datasource
- **dashboards/default.yml**: Auto-loads dashboards from `/grafana/dashboards`

## 🔧 Management Scripts

### Backup & Restore

```bash
# Backup database
./deployment/scripts/backup-database.sh

# Restore database
./deployment/scripts/restore-database.sh postgres_20250118_120000.sql.gz

# List backups
ls -lh deployment/backups/
```

### SSL Management

```bash
# Generate self-signed certificate
./deployment/nginx/generate-self-signed-cert.sh

# Set up Let's Encrypt
./deployment/scripts/setup-letsencrypt.sh yourdomain.com your@email.com

# Renew certificate (auto-runs daily)
docker compose run --rm certbot renew
docker compose exec nginx nginx -s reload
```

## 🔐 Security Configuration

### Firewall Rules (UFW)

```bash
# SSH (restricted)
sudo ufw allow from YOUR_IP to any port 22 proto tcp

# HTTP/HTTPS (public)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Monitoring (restricted)
sudo ufw allow from YOUR_IP to any port 9090 proto tcp  # Prometheus
sudo ufw allow from YOUR_IP to any port 3000 proto tcp  # Grafana
```

### Oracle Cloud Security Lists

Required ingress rules:
- Port 22: SSH (restricted to your IP)
- Port 80: HTTP
- Port 443: HTTPS
- Port 9090: Prometheus (restricted to your IP)
- Port 3000: Grafana (restricted to your IP)

### Fail2ban

Configuration: `/etc/fail2ban/jail.local`
- Ban time: 1 hour
- Max retries: 3
- Find time: 10 minutes

Check status:
```bash
sudo fail2ban-client status sshd
```

## 📊 Resource Allocation

Total available: 4 vCPUs, 24GB RAM, 200GB storage

| Service | CPU Limit | Memory Limit | Purpose |
|---------|-----------|--------------|---------|
| FastAPI | 2 cores | 2GB | Application server |
| PostgreSQL | 2 cores | 6GB | Database |
| Redis | 1 core | 2GB | Cache & rate limiting |
| Qdrant | 2 cores | 4GB | Vector store |
| Nginx | 1 core | 512MB | Reverse proxy |
| Prometheus | 1 core | 2GB | Metrics collection |
| Grafana | 1 core | 1GB | Monitoring dashboard |
| Exporters | 0.25 each | 128MB each | Metrics exporters |

## 🔍 Monitoring

### Access Points

- **Prometheus**: http://YOUR_IP:9090
- **Grafana**: http://YOUR_IP:3000 (admin / GRAFANA_ADMIN_PASSWORD)
- **API Metrics**: http://localhost:8000/metrics

### Key Metrics

**Application:**
- HTTP request rate
- Error rate (5xx responses)
- Request latency (p50, p95, p99)
- Active connections

**Database:**
- Connection pool usage
- Query performance
- Cache hit ratio
- Transaction rate

**System:**
- CPU usage
- Memory usage
- Disk I/O
- Network throughput

## 🚨 Alerts

Configured alerts (in prometheus/rules/alerts.yml):

**Critical:**
- API down (>2min)
- PostgreSQL down (>1min)
- Redis down (>1min)
- High error rate (>5%)
- Disk space critical (<5%)

**Warning:**
- High CPU usage (>80%)
- High memory usage (>85%)
- High request latency (p95 >2s)
- Slow queries
- Disk space low (<15%)

## 🔄 Updates

### Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### Update Application

```bash
cd ~/multi-agent-support-system
git pull
docker compose build
docker compose up -d
```

### Update Docker Images

```bash
docker compose pull
docker compose up -d
```

## 🐛 Troubleshooting

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f fastapi

# Last 100 lines
docker compose logs --tail=100 fastapi
```

### Container Status

```bash
docker compose ps
docker stats
```

### Service Health

```bash
# API
curl http://localhost:8000/health

# PostgreSQL
docker compose exec postgres pg_isready

# Redis
docker compose exec redis redis-cli ping
```

### Restart Services

```bash
# Single service
docker compose restart fastapi

# All services
docker compose restart

# Full restart (recreate containers)
docker compose down
docker compose up -d
```

## 📚 Documentation

- **Full Deployment Guide**: `/docs/DEPLOYMENT.md`
- **Main README**: `/README.md`
- **API Documentation**: https://YOUR_IP/api/docs

## 🆘 Support

Issues: https://github.com/OthmanMohammad/multi-agent-support-system/issues

---

**Note**: Replace `YOUR_IP` with your actual Oracle Cloud public IP address.
