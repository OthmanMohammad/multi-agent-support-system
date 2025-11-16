"""Add authentication system (User and API Key models)

Revision ID: 20251116120000
Revises: 20251117000000
Create Date: 2025-11-16 12:00:00

This migration adds the authentication and authorization infrastructure:
- User model for authentication (password + OAuth)
- APIKey model for programmatic access
- RBAC (Role-Based Access Control)
- Email verification
- Password reset
- Usage tracking
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '20251116120000'
down_revision = '20251117000000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create users and api_keys tables"""

    # Create users table
    op.create_table(
        'users',
        # Primary key (from BaseModel)
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Authentication
        sa.Column('email', sa.String(length=255), nullable=False, comment='User email (used for login)'),
        sa.Column('password_hash', sa.String(length=255), nullable=True, comment='Bcrypt password hash'),

        # Profile
        sa.Column('full_name', sa.String(length=255), nullable=False, comment='User full name'),
        sa.Column('organization', sa.String(length=255), nullable=True, comment='Organization name'),

        # Role and permissions
        sa.Column('role', sa.String(length=50), nullable=False, server_default='user', comment='User role for RBAC'),
        sa.Column('scopes', sa.String(length=1000), nullable=True, comment='Comma-separated permission scopes'),

        # Account status
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending_verification', comment='Account status'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Whether user can log in'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false', comment='Whether email is verified'),

        # OAuth
        sa.Column('oauth_provider', sa.String(length=50), nullable=True, comment='OAuth provider (if OAuth user)'),
        sa.Column('oauth_id', sa.String(length=255), nullable=True, comment='OAuth provider user ID'),

        # Email verification
        sa.Column('email_verification_token', sa.String(length=255), nullable=True, comment='Email verification token'),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when email was verified'),

        # Password reset
        sa.Column('password_reset_token', sa.String(length=255), nullable=True, comment='Password reset token'),
        sa.Column('password_reset_expires_at', sa.DateTime(timezone=True), nullable=True, comment='Password reset token expiration'),

        # Session tracking
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True, comment='Last successful login timestamp'),
        sa.Column('last_login_ip', sa.String(length=50), nullable=True, comment='Last login IP address'),

        # Timestamps (from BaseModel)
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        # Audit (from BaseModel)
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Soft delete (from BaseModel)
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Indexes
        sa.Index('ix_users_email', 'email', unique=True),
        sa.Index('ix_users_role', 'role'),
        sa.Index('ix_users_status', 'status'),
        sa.Index('ix_users_is_active', 'is_active'),
        sa.Index('ix_users_oauth_id', 'oauth_id'),
        sa.Index('ix_users_deleted_at', 'deleted_at'),
    )

    # Create api_keys table
    op.create_table(
        'api_keys',
        # Primary key (from BaseModel)
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Foreign key to user
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='User who owns this API key'),

        # Key information
        sa.Column('name', sa.String(length=100), nullable=False, comment='Human-readable key name'),
        sa.Column('key_prefix', sa.String(length=20), nullable=False, comment='Key prefix for quick lookup'),
        sa.Column('key_hash', sa.String(length=255), nullable=False, comment='Bcrypt hash of the API key'),

        # Permissions
        sa.Column('scopes', sa.String(length=1000), nullable=True, comment='Comma-separated permission scopes'),

        # Expiration
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, comment='Expiration timestamp'),

        # Usage tracking
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True, comment='Last time key was used'),
        sa.Column('last_used_ip', sa.String(length=50), nullable=True, comment='IP address of last use'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0', comment='Number of times key has been used'),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Whether key is active'),

        # Metadata
        sa.Column('description', sa.Text(), nullable=True, comment='Optional description of key purpose'),

        # Timestamps (from BaseModel)
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        # Audit (from BaseModel)
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Soft delete (from BaseModel)
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Foreign key constraint
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),

        # Indexes
        sa.Index('ix_api_keys_user_id', 'user_id'),
        sa.Index('ix_api_keys_key_prefix', 'key_prefix', unique=True),
        sa.Index('ix_api_keys_expires_at', 'expires_at'),
        sa.Index('ix_api_keys_is_active', 'is_active'),
        sa.Index('ix_api_keys_deleted_at', 'deleted_at'),
    )

    # Create trigger for updated_at on users
    op.execute("""
        CREATE OR REPLACE FUNCTION update_users_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER users_updated_at_trigger
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION update_users_updated_at();
    """)

    # Create trigger for updated_at on api_keys
    op.execute("""
        CREATE OR REPLACE FUNCTION update_api_keys_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER api_keys_updated_at_trigger
        BEFORE UPDATE ON api_keys
        FOR EACH ROW
        EXECUTE FUNCTION update_api_keys_updated_at();
    """)


def downgrade() -> None:
    """Drop users and api_keys tables"""

    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS users_updated_at_trigger ON users")
    op.execute("DROP FUNCTION IF EXISTS update_users_updated_at()")
    op.execute("DROP TRIGGER IF EXISTS api_keys_updated_at_trigger ON api_keys")
    op.execute("DROP FUNCTION IF EXISTS update_api_keys_updated_at()")

    # Drop tables (api_keys first due to foreign key)
    op.drop_table('api_keys')
    op.drop_table('users')
