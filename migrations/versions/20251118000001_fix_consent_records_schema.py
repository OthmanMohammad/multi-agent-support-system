"""Fix consent_records schema mismatch

Revision ID: 20251118000001
Revises: 20251118000000
Create Date: 2025-11-18 00:00:01.000000

Fix schema mismatch in consent_records table.
The model expects different columns than what was created.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251118000001'
down_revision = '20251118000000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Fix consent_records table schema to match model"""

    # Drop and recreate consent_records with correct schema
    op.drop_table('consent_records')

    op.create_table(
        'consent_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False, index=True),
        # Consent details
        sa.Column('consent_type', sa.String(100), nullable=False, index=True),
        sa.Column('consent_granted', sa.Boolean(), nullable=False),  # ← Fixed: was 'consented'
        sa.Column('consent_purpose', sa.String(255), nullable=True),
        sa.Column('consent_text', sa.Text(), nullable=True),
        # Tracking
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('withdrawn_at', sa.DateTime(timezone=True), nullable=True),  # ← Fixed: was 'revoked_at'
        sa.Column('consent_method', sa.String(100), nullable=True),
        # Data subject rights
        sa.Column('data_access_requested', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('data_deletion_requested', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('data_portability_requested', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('request_fulfilled_at', sa.DateTime(timezone=True), nullable=True),
        # Compliance
        sa.Column('regulation', sa.String(50), nullable=True),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    print("✓ Fixed consent_records schema to match ConsentRecord model")


def downgrade() -> None:
    """Revert to old (incorrect) schema"""

    op.drop_table('consent_records')

    # Recreate with old (incorrect) schema
    op.create_table(
        'consent_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('consent_type', sa.String(100), nullable=False),
        sa.Column('consented', sa.Boolean(), nullable=False),
        sa.Column('consent_text', sa.Text(), nullable=True),
        sa.Column('consent_version', sa.String(50), nullable=True),
        sa.Column('consent_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )