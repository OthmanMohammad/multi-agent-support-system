"""add_performance_indexes_and_constraints

Revision ID: f85f82502d01
Revises: 552eac7fda0c
Create Date: 2025-11-04 22:09:57.329693

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '[GENERATED_ID]'  # Keep the generated ID
down_revision: Union[str, Sequence[str], None] = '552eac7fda0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes and optimize queries"""
    
    # ===== CONVERSATION INDEXES =====
    
    # Composite index for intent + status queries
    op.create_index(
        'idx_conversations_intent_status',
        'conversations',
        ['primary_intent', 'status'],
        unique=False
    )
    
    # Partial index for finding old unresolved conversations
    op.create_index(
        'idx_conversations_active_unresolved',
        'conversations',
        ['status', 'started_at'],
        unique=False,
        postgresql_where=sa.text("status = 'active'")
    )
    
    # Index for customer + status queries
    op.create_index(
        'idx_conversations_customer_status',
        'conversations',
        ['customer_id', 'status'],
        unique=False
    )
    
    # ===== MESSAGE INDEXES =====
    
    # Composite index for conversation + created_at (chronological message retrieval)
    op.create_index(
        'idx_messages_conversation_created',
        'messages',
        ['conversation_id', 'created_at'],
        unique=False
    )
    
    # Composite index for agent + created_at (agent performance queries)
    op.create_index(
        'idx_messages_agent_created',
        'messages',
        ['agent_name', 'created_at'],
        unique=False
    )
    
    # Index for role filtering
    op.create_index(
        'idx_messages_role',
        'messages',
        ['role'],
        unique=False
    )
    
    # ===== CUSTOMER INDEXES =====
    
    # Index for plan-based queries (already exists in original schema)
    # Keeping this comment for documentation
    
    # ===== AGENT PERFORMANCE INDEXES =====
    
    # Composite index for date range queries
    op.create_index(
        'idx_agent_performance_date_range',
        'agent_performance',
        ['agent_name', 'date'],
        unique=False
    )
    
    print("✓ Performance indexes created successfully")


def downgrade() -> None:
    """Remove performance indexes"""
    
    # Drop in reverse order
    op.drop_index('idx_agent_performance_date_range', table_name='agent_performance')
    op.drop_index('idx_messages_role', table_name='messages')
    op.drop_index('idx_messages_agent_created', table_name='messages')
    op.drop_index('idx_messages_conversation_created', table_name='messages')
    op.drop_index('idx_conversations_customer_status', table_name='conversations')
    op.drop_index('idx_conversations_active_unresolved', table_name='conversations')
    op.drop_index('idx_conversations_intent_status', table_name='conversations')
    
    print("✓ Performance indexes dropped successfully")