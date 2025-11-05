"""add_audit_fields

Revision ID: 20250511_add_audit_fields
Revises: f85f82502d01
Create Date: 2025-05-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250111_add_audit_fields'
down_revision: Union[str, Sequence[str], None] = 'f85f82502d01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add audit trail fields to all tables"""
    
    # ===== CUSTOMERS TABLE =====
    print("Adding audit fields to customers...")
    op.add_column('customers', 
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('customers', 
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('customers', 
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('customers', 
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Index for soft delete queries
    op.create_index(
        'idx_customers_not_deleted',
        'customers',
        ['deleted_at'],
        unique=False,
        postgresql_where=sa.text('deleted_at IS NULL')
    )
    
    # ===== CONVERSATIONS TABLE =====
    print("Adding audit fields to conversations...")
    op.add_column('conversations', 
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('conversations', 
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('conversations', 
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('conversations', 
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True))
    
    op.create_index(
        'idx_conversations_not_deleted',
        'conversations',
        ['deleted_at'],
        unique=False,
        postgresql_where=sa.text('deleted_at IS NULL')
    )
    
    # ===== MESSAGES TABLE =====
    print("Adding audit fields to messages...")
    op.add_column('messages', 
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('messages', 
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('messages', 
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('messages', 
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True))
    
    op.create_index(
        'idx_messages_not_deleted',
        'messages',
        ['deleted_at'],
        unique=False,
        postgresql_where=sa.text('deleted_at IS NULL')
    )
    
    # ===== AGENT_PERFORMANCE TABLE =====
    print("Adding audit fields to agent_performance...")
    op.add_column('agent_performance', 
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('agent_performance', 
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('agent_performance', 
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True))
    # Note: agent_performance already has created_at but not created_by
    op.add_column('agent_performance', 
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True))
    
    op.create_index(
        'idx_agent_performance_not_deleted',
        'agent_performance',
        ['deleted_at'],
        unique=False,
        postgresql_where=sa.text('deleted_at IS NULL')
    )
    
    print("✓ Audit fields added successfully")


def downgrade() -> None:
    """Remove audit trail fields"""
    
    # Drop indexes first
    op.drop_index('idx_agent_performance_not_deleted', table_name='agent_performance')
    op.drop_index('idx_messages_not_deleted', table_name='messages')
    op.drop_index('idx_conversations_not_deleted', table_name='conversations')
    op.drop_index('idx_customers_not_deleted', table_name='customers')
    
    # Drop columns
    # Agent Performance
    op.drop_column('agent_performance', 'deleted_by')
    op.drop_column('agent_performance', 'deleted_at')
    op.drop_column('agent_performance', 'updated_by')
    op.drop_column('agent_performance', 'created_by')
    
    # Messages
    op.drop_column('messages', 'deleted_by')
    op.drop_column('messages', 'deleted_at')
    op.drop_column('messages', 'updated_by')
    op.drop_column('messages', 'created_by')
    
    # Conversations
    op.drop_column('conversations', 'deleted_by')
    op.drop_column('conversations', 'deleted_at')
    op.drop_column('conversations', 'updated_by')
    op.drop_column('conversations', 'created_by')
    
    # Customers
    op.drop_column('customers', 'deleted_by')
    op.drop_column('customers', 'deleted_at')
    op.drop_column('customers', 'updated_by')
    op.drop_column('customers', 'created_by')
    
    print("✓ Audit fields removed successfully")