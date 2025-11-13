# Doppler Secrets Management

## Overview

This project uses Doppler as its centralized secrets management solution. Doppler provides secure storage, access control, and synchronization of configuration and secrets across all environments, eliminating the need for local `.env` files and reducing the risk of credential leakage.

## Rationale

Traditional environment file management presents several operational challenges:

- **Security Risk**: Local `.env` files are easily committed to version control
- **Synchronization Issues**: Team members maintain different versions of configuration
- **Audit Trail Gaps**: No visibility into who accessed or modified secrets
- **Rotation Complexity**: Updating credentials requires manual file updates across environments
- **Access Control Limitations**: Binary access (file present or not) with no granular permissions

Doppler addresses these concerns through:

- Centralized secret storage with encryption at rest and in transit
- Automatic synchronization across team members and environments
- Comprehensive audit logging of all secret access and modifications
- Simplified rotation workflows with immediate propagation
- Role-based access control with environment-level permissions

## Architecture

### Environment Structure

The project maintains two primary environments:

- **staging**: Pre-production environment for integration testing and validation
- **production**: Live production environment serving end users

Each environment maintains completely isolated secret stores with independent access controls.

### Secret Injection Workflow

```
Local Development Machine
    ↓
Doppler CLI reads .doppler.yaml
    ↓
Authenticates with Doppler API
    ↓
Fetches secrets from configured environment
    ↓
Injects secrets as environment variables
    ↓
Application process starts with secrets available
```

The application code remains environment-agnostic, reading configuration through standard environment variables via Pydantic Settings.

## Prerequisites

### CLI Installation

**Windows (Scoop)**:
```powershell
scoop bucket add doppler https://github.com/DopplerHQ/scoop-doppler.git
scoop install doppler
```

**macOS (Homebrew)**:
```bash
brew install dopplerhq/cli/doppler
```

**Linux**:
```bash
curl -Ls https://cli.doppler.com/install.sh | sh
```

### Account Setup

1. Register at https://doppler.com
2. Create organization (if not already created)
3. Request access to the `multi-agent-support-system` project from project administrator

## Configuration

### Initial Setup

Authenticate the CLI with your Doppler account:

```bash
doppler login
```

Navigate to the project directory and configure the environment:

```bash
cd /path/to/multi-agent-support-system
doppler setup
```

Select the appropriate project and configuration when prompted. For local development using staging configuration:

- Project: `multi-agent-support-system`
- Config: `stg`

This creates a `.doppler.yaml` file containing the local environment mapping:

```yaml
setup:
  project: multi-agent-support-system
  config: stg
```

**Important**: The `.doppler.yaml` file should never be committed to version control as it contains environment-specific configuration.

### Required Secrets

Each environment must define the following secrets:

#### Application Configuration
- `ENVIRONMENT`: Environment identifier (`staging` or `production`)
- `API_CORS_ORIGINS`: JSON array of allowed CORS origins

#### External Services
- `ANTHROPIC_API_KEY`: Anthropic Claude API key
- `QDRANT_URL`: Qdrant vector database endpoint
- `QDRANT_API_KEY`: Qdrant API authentication token
- `DATABASE_URL`: PostgreSQL connection string (asyncpg format)

#### Observability
- `SENTRY_DSN`: Sentry error tracking DSN
- `SENTRY_ENVIRONMENT`: Sentry environment tag
- `SENTRY_TRACES_SAMPLE_RATE`: Performance monitoring sample rate
- `SENTRY_PROFILES_SAMPLE_RATE`: Profiling sample rate

#### Logging
- `LOG_LEVEL`: Logging verbosity level
- `LOG_FORMAT`: Log output format (`json` or `pretty`)
- `LOG_CORRELATION_ID`: Enable correlation ID tracking
- `LOG_MASK_PII`: Enable PII masking in logs
- `LOG_INCLUDE_TIMESTAMP`: Include timestamps in log output

### Secret Format Requirements

**API_CORS_ORIGINS**: Must be provided as a JSON array with double quotes:
```json
["https://app.example.com","https://api.example.com"]
```

**DATABASE_URL**: Must use asyncpg driver for async PostgreSQL connections:
```
postgresql+asyncpg://username:password@host:port/database
```

## Usage

### Local Development

Execute commands with Doppler secret injection:

```bash
# Run application
doppler run -- python -m uvicorn src.api.main:app --reload

# Run database migrations
doppler run -- alembic upgrade head

# Run tests
doppler run -- pytest

# Install dependencies
doppler run -- pip install -r requirements.txt
```

The `doppler run --` prefix injects secrets as environment variables before executing the command.

### Secret Management

**View all secrets**:
```bash
doppler secrets
```

**View specific secret**:
```bash
doppler secrets get DATABASE_URL
```

**View secrets from different environment**:
```bash
doppler secrets --config=prd
```

**Download secrets for offline use** (emergency fallback only):
```bash
doppler secrets download --format=env-no-quotes > .env.local
```

### Environment Switching

Switch between environments for testing:

```bash
# Switch to production (use with caution)
doppler setup --config=prd

# Verify current configuration
doppler configure get
```

## CI/CD Integration

### Service Token Generation

For automated deployments, generate service tokens with read-only access:

1. Navigate to Doppler dashboard
2. Select project and environment
3. Go to Access → Service Tokens
4. Generate token with appropriate permissions
5. Securely store token in CI/CD platform's secret store

### GitHub Actions Integration

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Doppler CLI
        run: |
          curl -Ls https://cli.doppler.com/install.sh | sh
      
      - name: Deploy Application
        env:
          DOPPLER_TOKEN: ${{ secrets.DOPPLER_TOKEN_STAGING }}
        run: |
          doppler run -- ./deploy.sh
```

Store service tokens as repository secrets:
- `DOPPLER_TOKEN_STAGING`: Service token for staging environment
- `DOPPLER_TOKEN_PRODUCTION`: Service token for production environment

### Server Deployment

Set the service token as an environment variable on the deployment target:

```bash
export DOPPLER_TOKEN=dp.st.your-service-token-here
doppler run -- python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

For systemd services, include the token in the unit file:

```ini
[Service]
Environment="DOPPLER_TOKEN=dp.st.your-service-token"
ExecStart=/usr/bin/doppler run -- python -m uvicorn src.api.main:app
```

## Migration from .env Files

### Coexistence Period

The application supports both Doppler and traditional `.env` files during migration:

**Priority order**:
1. Environment variables (from Doppler or system)
2. `.env` file (if present)
3. Configuration error (if neither available)

This allows gradual team migration while maintaining backward compatibility.

### Complete Migration

Once all team members have configured Doppler:

1. Verify all secrets are present in Doppler dashboard
2. Remove `.env` from project directory
3. Ensure `.env` is listed in `.gitignore`
4. Update deployment scripts to use Doppler exclusively

## Security Best Practices

### Access Control

- Use service tokens for automated systems, not personal tokens
- Implement least-privilege access (read-only for production)
- Rotate service tokens on a regular schedule
- Revoke tokens immediately when team members leave

### Secret Hygiene

- Never log or print secret values
- Avoid storing secrets in application memory longer than necessary
- Use different secrets across staging and production environments
- Rotate credentials regularly, especially after suspected exposure

### Audit and Monitoring

- Review audit logs periodically for anomalous access patterns
- Enable Sentry integration for secret access monitoring
- Set up alerts for production secret modifications
- Document all credential rotation procedures

## Troubleshooting

### Authentication Issues

**Symptom**: `Invalid token` or `Access denied` errors

**Solution**:
```bash
doppler logout
doppler login
```

### Environment Configuration

**Symptom**: `Project not set up` error

**Solution**:
```bash
cd /path/to/project
doppler setup
```

### Missing Secrets

**Symptom**: Application fails with missing environment variable errors

**Verification**:
```bash
# Check current configuration
doppler configure get

# List available secrets
doppler secrets

# Verify specific secret
doppler secrets get SECRET_NAME
```

### CLI Not Found (Windows)

**Symptom**: `doppler: command not found` in VS Code terminal

**Solution**:
1. Close VS Code completely
2. Reopen VS Code
3. Open new terminal
4. Verify PATH includes Doppler installation directory

### CORS Format Error

**Symptom**: `JSONDecodeError` when parsing `API_CORS_ORIGINS`

**Cause**: CORS origins provided as comma-separated string instead of JSON array

**Solution**: Update secret in Doppler dashboard to use JSON array format:
```json
["https://origin1.com","https://origin2.com"]
```

## Additional Resources

- Doppler Documentation: https://docs.doppler.com
- Doppler CLI Reference: https://docs.doppler.com/docs/cli
- API Documentation: https://docs.doppler.com/reference
- Community Support: https://community.doppler.com

## Support

For Doppler-related issues:
1. Consult this documentation
2. Check Doppler status page: https://status.doppler.com
3. Contact project administrator for access issues
4. Submit support ticket at https://doppler.com/support for platform issues