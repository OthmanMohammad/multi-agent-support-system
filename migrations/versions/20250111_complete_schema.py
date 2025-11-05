"""complete_schema_with_audit_trail

Revision ID: 20250111_complete_schema
Revises: 
Create Date: 2025-01-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250111_complete_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create complete schema with audit trail"""
    
    # ===== CUSTOMERS TABLE =====
    op.create_table('customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('plan', sa.String(length=50), nullable=False),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint("plan IN ('free', 'basic', 'premium', 'enterprise')", name='check_customer_plan_values'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_customers_email', 'customers', ['email'], unique=True)
    op.create_index('ix_customers_plan', 'customers', ['plan'], unique=False)
    op.create_index('idx_customers_not_deleted', 'customers', ['deleted_at'], 
                    unique=False, postgresql_where=sa.text('deleted_at IS NULL'))
    
    # ===== CONVERSATIONS TABLE =====
    op.create_table('conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('primary_intent', sa.String(length=100), nullable=True),
        sa.Column('agents_involved', sa.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('sentiment_avg', sa.Float(), nullable=True),
        sa.Column('kb_articles_used', sa.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_time_seconds', sa.Integer(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint("status IN ('active', 'resolved', 'escalated')", name='check_conversation_status_values'),
        sa.CheckConstraint('sentiment_avg IS NULL OR (sentiment_avg >= -1 AND sentiment_avg <= 1)', 
                          name='check_conversation_sentiment_range'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_conversations_customer_id', 'conversations', ['customer_id'], unique=False)
    op.create_index('ix_conversations_primary_intent', 'conversations', ['primary_intent'], unique=False)
    op.create_index('ix_conversations_started_at', 'conversations', ['started_at'], unique=False)
    op.create_index('ix_conversations_status', 'conversations', ['status'], unique=False)
    op.create_index('idx_conversations_not_deleted', 'conversations', ['deleted_at'], 
                    unique=False, postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_conversations_intent_status', 'conversations', ['primary_intent', 'status'], unique=False)
    op.create_index('idx_conversations_customer_status', 'conversations', ['customer_id', 'status'], unique=False)
    
    # ===== MESSAGES TABLE =====
    op.create_table('messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('agent_name', sa.String(length=50), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(length=100), nullable=True),
        sa.Column('sentiment', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint("role IN ('user', 'assistant', 'system')", name='check_message_role_values'),
        sa.CheckConstraint('confidence IS NULL OR (confidence >= 0 AND confidence <= 1)', 
                          name='check_message_confidence_range'),
        sa.CheckConstraint('sentiment IS NULL OR (sentiment >= -1 AND sentiment <= 1)', 
                          name='check_message_sentiment_range'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_messages_agent_name', 'messages', ['agent_name'], unique=False)
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'], unique=False)
    op.create_index('ix_messages_created_at', 'messages', ['created_at'], unique=False)
    op.create_index('idx_messages_not_deleted', 'messages', ['deleted_at'], 
                    unique=False, postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_messages_conversation_created', 'messages', ['conversation_id', 'created_at'], unique=False)
    op.create_index('idx_messages_agent_created', 'messages', ['agent_name', 'created_at'], unique=False)
    
    # ===== AGENT_PERFORMANCE TABLE =====
    op.create_table('agent_performance',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_name', sa.String(length=50), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_interactions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_resolutions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('escalations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_confidence', sa.Float(), nullable=True),
        sa.Column('avg_sentiment', sa.Float(), nullable=True),
        sa.Column('avg_response_time_ms', sa.Integer(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_performance_agent_name', 'agent_performance', ['agent_name'], unique=False)
    op.create_index('ix_agent_performance_date', 'agent_performance', ['date'], unique=False)
    op.create_index('idx_agent_performance_unique', 'agent_performance', ['agent_name', 'date'], unique=True)
    op.create_index('idx_agent_performance_not_deleted', 'agent_performance', ['deleted_at'], 
                    unique=False, postgresql_where=sa.text('deleted_at IS NULL'))
    
    print("✓ Complete schema created with audit trail and indexes")


def downgrade() -> None:
    """Drop all tables"""
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('customers')
    op.drop_table('agent_performance')
    print("✓ All tables dropped")