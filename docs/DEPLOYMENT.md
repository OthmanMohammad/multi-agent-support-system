# 🚀 Production Deployment Guide - Oracle Cloud

Complete step-by-step guide for deploying the Multi-Agent Support System on Oracle Cloud Always Free Tier.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Phase 1: Oracle Cloud Setup](#phase-1-oracle-cloud-setup)
- [Phase 2: Server Configuration](#phase-2-server-configuration)
- [Phase 3: Application Deployment](#phase-3-application-deployment)
- [Phase 4: SSL Configuration](#phase-4-ssl-configuration)
- [Phase 5: Monitoring & Backups](#phase-5-monitoring--backups)
- [Verification & Testing](#verification--testing)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts

1. **Oracle Cloud Account** (Always Free Tier)
   - Sign up: https://www.oracle.com/cloud/free/
   - Credit card required (not charged for free tier)

2. **Anthropic API Key**
   - Get from: https://console.anthropic.com/
   - Required for LLM functionality

3. **Sentry Account** (Optional but recommended)
   - Sign up: https://sentry.io/
   - Free tier available for error tracking

### Local Requirements

- SSH client (ssh command)
- Git
- Text editor

---

## Phase 1: Oracle Cloud Setup

### Step 1.1: Create Oracle Cloud Account

1. Visit https://www.oracle.com/cloud/free/
2. Click "Start for free"
3. Fill in account details and verify email
4. Complete identity verification (credit card required)
5. Access Oracle Cloud Console

### Step 1.2: Provision Ampere A1 Compute Instance

1. In Oracle Cloud Console, navigate to: **Compute → Instances**

2. Click **Create Instance**

3. Configure instance:
   ```
   Name: multi-agent-production
   Compartment: (root) or create new

   Image and Shape:
   - Image: Canonical Ubuntu 22.04 LTS (ARM64)
   - Shape: VM.Standard.A1.Flex
     - OCPUs: 4
     - Memory: 24 GB

   Boot Volume:
   - Size: 200 GB
   - Performance: Balanced
   ```

4. **Networking Configuration:**
   - Create new VCN: `multi-agent-vcn`
   - Subnet: Public subnet
   - Assign public IPv4 address: Yes
   - Click "Create VCN"

5. **Add SSH Key:**

   Generate SSH key pair (if you don't have one):
   ```bash
   ssh-keygen -t ed25519 -C "oracle-cloud-deploy" -f ~/.ssh/oracle_deploy_key
   ```

   - Choose: "Paste public keys"
   - Paste contents of `~/.ssh/oracle_deploy_key.pub`

6. Click **Create**

7. **Save your information:**
   ```
   Instance OCID: ocid1.instance.oc1...
   Public IP Address: XXX.XXX.XXX.XXX
   Private IP Address: 10.0.0.X
   ```

### Step 1.3: Configure Security Lists (Firewall Rules)

1. Navigate to: **Networking → Virtual Cloud Networks**
2. Click on `multi-agent-vcn`
3. Click **Security Lists** → **Default Security List**
4. Click **Add Ingress Rules**

Add these ingress rules:

| Type | Source CIDR | Protocol | Port Range | Description |
|------|-------------|----------|------------|-------------|
| Ingress | YOUR_IP/32 | TCP | 22 | SSH (your IP only) |
| Ingress | 0.0.0.0/0 | TCP | 80 | HTTP |
| Ingress | 0.0.0.0/0 | TCP | 443 | HTTPS |
| Ingress | YOUR_IP/32 | TCP | 9090 | Prometheus (restricted) |
| Ingress | YOUR_IP/32 | TCP | 3000 | Grafana (restricted) |

**Important:** Replace `YOUR_IP` with your actual IP address (find it at: https://ifconfig.me/)

5. Verify Egress Rules (allow all outbound):
   - Destination: 0.0.0.0/0
   - Protocol: All

### Step 1.4: Connect to Instance

Test SSH connection:

```bash
# Replace with your public IP
ssh -i ~/.ssh/oracle_deploy_key ubuntu@XXX.XXX.XXX.XXX
```

If successful, you should see Ubuntu welcome message.

---

## Phase 2: Server Configuration

### Step 2.1: Run Automated Setup Script

1. **Clone repository:**

   ```bash
   cd ~
   git clone https://github.com/OthmanMohammad/multi-agent-support-system.git
   cd multi-agent-support-system
   ```

2. **Run server setup script:**

   ```bash
   chmod +x deployment/scripts/setup-server.sh
   ./deployment/scripts/setup-server.sh
   ```

   This script will:
   - ✅ Update system packages
   - ✅ Configure UFW firewall
   - ✅ Set up Fail2ban (SSH protection)
   - ✅ Harden SSH (disable password auth)
   - ✅ Enable automatic security updates
   - ✅ Install Docker & Docker Compose
   - ✅ Configure Docker for production
   - ✅ Create application directories

3. **Log out and back in** (required for Docker group):

   ```bash
   exit
   ssh -i ~/.ssh/oracle_deploy_key ubuntu@XXX.XXX.XXX.XXX
   ```

4. **Verify Docker:**

   ```bash
   docker --version
   docker compose version
   docker ps  # Should work without sudo
   ```

### Step 2.2: Configure Environment Variables

**Option A: Using Doppler (Recommended)**

```bash
# Install Doppler CLI
curl -sLf https://cli.doppler.com/install.sh | sh

# Login
doppler login

# Setup project
doppler setup
# Select: multi-agent-support-system
# Config: production

# Add secrets
doppler secrets set POSTGRES_PASSWORD="$(openssl rand -base64 32)"
doppler secrets set JWT_SECRET_KEY="$(openssl rand -hex 32)"
doppler secrets set GRAFANA_ADMIN_PASSWORD="$(openssl rand -base64 32)"
doppler secrets set ANTHROPIC_API_KEY="sk-ant-your-key-here"
doppler secrets set SENTRY_DSN="https://..."
```

**Option B: Manual .env file**

```bash
cd ~/multi-agent-support-system

# Copy template
cp .env.production.example .env

# Generate secure passwords
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)"
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)"
echo "GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 32)"

# Edit .env file
nano .env
```

Required values:
- `POSTGRES_PASSWORD` - Strong database password
- `JWT_SECRET_KEY` - Random 64-character hex key
- `GRAFANA_ADMIN_PASSWORD` - Strong password for Grafana
- `ANTHROPIC_API_KEY` - Your Anthropic API key
- `SENTRY_DSN` - Sentry error tracking DSN
- `API_CORS_ORIGINS` - Your frontend domain(s) in JSON array format

---

## Phase 3: Application Deployment

### Step 3.1: Generate SSL Certificate

**Without Domain (Testing):**

```bash
cd ~/multi-agent-support-system
./deployment/nginx/generate-self-signed-cert.sh
```

**With Domain (Production):**

First, configure DNS:
1. Add A record pointing to your Oracle Cloud public IP
2. Wait for DNS propagation (check with: `dig yourdomain.com`)

Then generate Let's Encrypt certificate:

```bash
./deployment/scripts/setup-letsencrypt.sh yourdomain.com your@email.com
```

### Step 3.2: Deploy Application

Run the deployment script:

```bash
cd ~/multi-agent-support-system
./deployment/scripts/deploy.sh
```

This will:
1. ✅ Build Docker images
2. ✅ Start PostgreSQL, Redis, Qdrant
3. ✅ Run database migrations
4. ✅ Initialize knowledge base
5. ✅ Start all services (FastAPI, Nginx, monitoring)
6. ✅ Run health checks

Expected output:
```
✓ Database is ready
✓ Migrations completed
✓ Knowledge base initialized
✓ API is healthy
```

### Step 3.3: Verify Deployment

Check container status:

```bash
docker compose ps
```

All containers should show "Up" and "healthy":
```
NAME                        STATUS
multi-agent-fastapi         Up (healthy)
multi-agent-postgres        Up (healthy)
multi-agent-redis           Up (healthy)
multi-agent-qdrant          Up
multi-agent-nginx           Up (healthy)
multi-agent-prometheus      Up (healthy)
multi-agent-grafana         Up (healthy)
```

View logs:

```bash
# All logs
docker compose logs -f

# Specific service
docker compose logs -f fastapi
```

---

## Phase 4: SSL Configuration

### Without Domain (Self-Signed Certificate)

Already configured if you ran `generate-self-signed-cert.sh`.

Access points (with browser warning):
```
https://YOUR_IP/health
https://YOUR_IP/api/docs
```

### With Domain (Let's Encrypt)

Already configured if you ran `setup-letsencrypt.sh`.

Access points:
```
https://yourdomain.com/health
https://yourdomain.com/api/docs
```

**Auto-renewal** is automatically configured (daily check at 3 AM).

---

## Phase 5: Monitoring & Backups

### Step 5.1: Access Monitoring Tools

**Prometheus:**
```
http://YOUR_IP:9090
```

**Grafana:**
```
http://YOUR_IP:3000
```

Login:
- Username: `admin`
- Password: (from `GRAFANA_ADMIN_PASSWORD` in .env or Doppler)

### Step 5.2: Configure Automated Backups

**Setup daily backups:**

```bash
# Test backup manually
./deployment/scripts/backup-database.sh

# Add to crontab for daily backups at 3 AM
crontab -e

# Add this line:
0 3 * * * cd /home/ubuntu/multi-agent-support-system && ./deployment/scripts/backup-database.sh >> logs/backup.log 2>&1
```

**Backups are saved to:**
- Local: `~/multi-agent-support-system/backups/`
- Oracle Object Storage: (if configured)

### Step 5.3: Configure Oracle Object Storage (Optional)

For cloud backups:

1. **Create Object Storage Bucket:**
   - Navigate to: Storage → Buckets
   - Click: Create Bucket
   - Name: `multi-agent-backups`
   - Storage Tier: Standard
   - Click: Create

2. **Install OCI CLI:**

   ```bash
   bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
   ```

3. **Configure OCI CLI:**

   ```bash
   oci setup config
   ```

   You'll need:
   - User OCID (Profile → User Settings)
   - Tenancy OCID (Profile → Tenancy)
   - Region (e.g., us-ashburn-1)
   - Generate API key pair

4. **Update environment:**

   ```bash
   # If using Doppler
   doppler secrets set OCI_NAMESPACE="your-tenancy-namespace"
   doppler secrets set OCI_BUCKET_NAME="multi-agent-backups"

   # If using .env
   echo 'OCI_NAMESPACE=your-tenancy-namespace' >> .env
   echo 'OCI_BUCKET_NAME=multi-agent-backups' >> .env
   ```

5. **Test backup:**

   ```bash
   ./deployment/scripts/backup-database.sh
   ```

---

## Verification & Testing

### Health Check Tests

```bash
# Get your public IP
PUBLIC_IP=$(curl -s ifconfig.me)

# Test API health
curl https://$PUBLIC_IP/health

# Expected response:
# {
#   "status": "healthy",
#   "database": "connected",
#   "redis": "connected",
#   "version": "1.3.0"
# }
```

### API Tests

```bash
# Get API info
curl https://$PUBLIC_IP/api

# Test authentication
curl -X POST https://$PUBLIC_IP/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# View API documentation
# Open in browser: https://$PUBLIC_IP/api/docs
```

### Monitoring Tests

```bash
# Prometheus metrics
curl http://$PUBLIC_IP:9090/api/v1/targets

# Grafana health
curl http://$PUBLIC_IP:3000/api/health
```

### Load Test (Optional)

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Run load test (1000 requests, 10 concurrent)
ab -n 1000 -c 10 https://$PUBLIC_IP/health
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs fastapi

# Check container status
docker compose ps

# Restart specific service
docker compose restart fastapi

# Full restart
docker compose down
docker compose up -d
```

### Database Connection Errors

```bash
# Check PostgreSQL
docker compose exec postgres pg_isready -U postgres

# View database logs
docker compose logs postgres

# Check database size
docker compose exec postgres psql -U postgres -c "\l+"

# Test connection
docker compose exec fastapi python -c "from src.database.connection import test_connection; test_connection()"
```

### SSL Certificate Issues

```bash
# Check certificate
openssl s_client -connect $PUBLIC_IP:443 -servername $PUBLIC_IP

# Regenerate self-signed cert
./deployment/nginx/generate-self-signed-cert.sh

# Check Let's Encrypt cert
docker compose run --rm certbot certificates

# Renew Let's Encrypt manually
docker compose run --rm certbot renew

# Reload Nginx
docker compose exec nginx nginx -s reload
```

### High Memory Usage

```bash
# Check container stats
docker stats

# Check system resources
htop

# Reduce workers in Dockerfile if needed
# Edit: CMD workers from 4 to 2
```

### Firewall Issues

```bash
# Check UFW status
sudo ufw status verbose

# Check iptables
sudo iptables -L -n

# Temporarily disable firewall (testing only)
sudo ufw disable

# Re-enable
sudo ufw enable
```

### Application Logs

```bash
# Real-time logs
docker compose logs -f fastapi

# Last 100 lines
docker compose logs --tail=100 fastapi

# Logs from specific time
docker compose logs --since 1h fastapi

# Search logs
docker compose logs fastapi | grep ERROR
```

### Performance Issues

```bash
# Check Prometheus metrics
curl http://localhost:9090/api/v1/query?query=up

# Database performance
docker compose exec postgres psql -U postgres -d support_agent -c "
  SELECT * FROM pg_stat_statements
  ORDER BY total_exec_time DESC
  LIMIT 10;
"

# Redis info
docker compose exec redis redis-cli INFO

# API performance test
time curl https://$PUBLIC_IP/health
```

---

## Useful Commands

### Docker Management

```bash
# View all containers
docker compose ps

# View logs
docker compose logs -f [service]

# Restart service
docker compose restart [service]

# Stop all
docker compose down

# Start all
docker compose up -d

# Rebuild and restart
docker compose up -d --build

# Remove all volumes (WARNING: deletes data)
docker compose down -v
```

### Database Management

```bash
# Access PostgreSQL
docker compose exec postgres psql -U postgres -d support_agent

# Backup database
./deployment/scripts/backup-database.sh

# Restore database
./deployment/scripts/restore-database.sh postgres_20250118_120000.sql.gz

# Run migrations
docker compose exec fastapi alembic upgrade head

# Rollback migration
docker compose exec fastapi alembic downgrade -1
```

### Monitoring

```bash
# System resources
htop
df -h
free -h

# Docker stats
docker stats

# Network connections
sudo netstat -tulpn

# Check open ports
sudo ss -tulpn
```

---

## Security Best Practices

1. **Restrict Monitoring Ports:**
   ```bash
   # After setup, restrict Prometheus and Grafana to your IP only
   sudo ufw delete allow 9090/tcp
   sudo ufw delete allow 3000/tcp
   sudo ufw allow from YOUR_IP to any port 9090 proto tcp
   sudo ufw allow from YOUR_IP to any port 3000 proto tcp
   ```

2. **Regular Updates:**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Update Docker images
   docker compose pull
   docker compose up -d
   ```

3. **Monitor Logs:**
   ```bash
   # Check for suspicious activity
   sudo tail -f /var/log/auth.log
   sudo fail2ban-client status sshd
   ```

4. **Backup Regularly:**
   ```bash
   # Test restore procedure quarterly
   ./deployment/scripts/restore-database.sh [backup-file]
   ```

5. **Rotate Secrets:**
   ```bash
   # Rotate JWT secret annually
   # Update in Doppler or .env, then:
   docker compose restart fastapi
   ```

---

## Next Steps

1. **Configure Domain (if not done):**
   - Point domain to your Oracle Cloud IP
   - Run Let's Encrypt setup
   - Update CORS origins

2. **Set Up CI/CD:**
   - Configure GitHub Actions for automated deployments
   - See `.github/workflows/` for examples

3. **Scale Resources:**
   - Monitor usage in Grafana
   - Adjust Docker resource limits if needed
   - Consider adding more OCPUs if necessary

4. **Add Monitoring Alerts:**
   - Configure Prometheus Alertmanager
   - Set up Slack/Email notifications
   - Review alert rules in `deployment/prometheus/rules/`

5. **Optimize Performance:**
   - Review slow query logs
   - Adjust PostgreSQL configuration
   - Configure Redis eviction policies
   - Enable API response caching

---

## Support

For issues and questions:

- GitHub Issues: https://github.com/OthmanMohammad/multi-agent-support-system/issues
- Documentation: https://github.com/OthmanMohammad/multi-agent-support-system/docs
- Oracle Cloud Docs: https://docs.oracle.com/en-us/iaas/Content/home.htm

---

**Deployment completed! 🎉**

Your Multi-Agent Support System is now running on Oracle Cloud with:
- ✅ Production-grade infrastructure
- ✅ SSL/TLS encryption
- ✅ Automated backups
- ✅ Comprehensive monitoring
- ✅ Security hardening
