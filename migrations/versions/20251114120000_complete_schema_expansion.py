"""complete schema expansion - 30+ tables

Revision ID: 20251114120000
Revises: efaa6e584823
Create Date: 2025-11-14 12:00:00.000000

This migration adds comprehensive schema support for 243-agent system:
- Expands existing tables (customers, conversations, messages)
- Adds 26+ new tables for subscriptions, sales, analytics, workflows, security
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251114120000'
down_revision = 'efaa6e584823'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply schema expansions and create new tables"""

    # ===================================================================
    # PART 1: EXPAND EXISTING TABLES
    # ===================================================================

    # Expand customers table
    op.add_column('customers', sa.Column('company_name', sa.String(length=255), nullable=True))
    op.add_column('customers', sa.Column('company_size', sa.Integer(), nullable=True))
    op.add_column('customers', sa.Column('industry', sa.String(length=100), nullable=True))
    op.add_column('customers', sa.Column('mrr', sa.DECIMAL(precision=10, scale=2), server_default='0', nullable=False))
    op.add_column('customers', sa.Column('ltv', sa.DECIMAL(precision=10, scale=2), server_default='0', nullable=False))
    op.add_column('customers', sa.Column('health_score', sa.Integer(), server_default='50', nullable=False))
    op.add_column('customers', sa.Column('churn_risk', sa.DECIMAL(precision=3, scale=2), server_default='0', nullable=False))
    op.add_column('customers', sa.Column('nps_score', sa.Integer(), nullable=True))
    op.add_column('customers', sa.Column('lead_source', sa.String(length=50), nullable=True))
    op.add_column('customers', sa.Column('country', sa.String(length=2), nullable=True))
    op.add_column('customers', sa.Column('timezone', sa.String(length=50), server_default='UTC', nullable=False))
    op.add_column('customers', sa.Column('language', sa.String(length=10), server_default='en', nullable=False))

    # Add indexes on new customer columns
    op.create_index('idx_customers_health_score', 'customers', ['health_score'], unique=False)
    op.create_index('idx_customers_churn_risk', 'customers', ['churn_risk'], unique=False)
    op.create_index('idx_customers_mrr', 'customers', ['mrr'], unique=False)
    op.create_index('idx_customers_industry', 'customers', ['industry'], unique=False)

    # Add check constraints on customers
    op.create_check_constraint(
        'check_customer_health_score',
        'customers',
        'health_score BETWEEN 0 AND 100'
    )
    op.create_check_constraint(
        'check_customer_churn_risk',
        'customers',
        'churn_risk BETWEEN 0 AND 1'
    )

    # Expand conversations table
    op.add_column('conversations', sa.Column('channel', sa.String(length=50), server_default='web_chat', nullable=False))
    op.add_column('conversations', sa.Column('intent_confidence', sa.DECIMAL(precision=3, scale=2), nullable=True))
    op.add_column('conversations', sa.Column('emotion', sa.String(length=50), nullable=True))
    op.add_column('conversations', sa.Column('resolved_by_agent', sa.String(length=50), nullable=True))
    op.add_column('conversations', sa.Column('first_response_time_seconds', sa.Integer(), nullable=True))
    op.add_column('conversations', sa.Column('csat_score', sa.Integer(), nullable=True))
    op.add_column('conversations', sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True))

    # Add indexes on conversation columns
    op.create_index('idx_conversations_channel', 'conversations', ['channel'], unique=False)
    op.create_index('idx_conversations_emotion', 'conversations', ['emotion'], unique=False)
    op.create_index('idx_conversations_last_activity', 'conversations', ['last_activity_at'], unique=False)

    # Add check constraints on conversations
    op.create_check_constraint(
        'check_conversation_channel',
        'conversations',
        "channel IN ('web_chat', 'email', 'phone', 'slack', 'api', 'widget')"
    )
    op.create_check_constraint(
        'check_conversation_csat',
        'conversations',
        'csat_score BETWEEN 1 AND 5'
    )

    # Expand messages table (FIXED: removed duplicate tokens_used)
    op.add_column('messages', sa.Column('agent_confidence', sa.DECIMAL(precision=3, scale=2), nullable=True))
    op.add_column('messages', sa.Column('urgency', sa.String(length=20), nullable=True))
    op.add_column('messages', sa.Column('model_used', sa.String(length=100), nullable=True))
    # NOTE: tokens_used already exists in messages table, so we don't add it again

    # Add check constraint on messages
    op.create_check_constraint(
        'check_message_urgency',
        'messages',
        "urgency IN ('low', 'medium', 'high', 'critical')"
    )

    # ===================================================================
    # PART 2: CREATE NEW TABLES
    # ===================================================================

    # ===================================================================
    # CUSTOMER DOMAIN (5 new tables)
    # ===================================================================

    # customer_health_events table
    op.create_table(
        'customer_health_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('old_value', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('new_value', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('detected_by', sa.String(length=50), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "event_type IN ('health_score_change', 'churn_risk_change', 'engagement_drop', 'usage_spike')",
            name='check_health_event_type'
        ),
        sa.CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name='check_health_event_severity'
        )
    )
    op.create_index('idx_customer_health_customer_date', 'customer_health_events', ['customer_id', 'created_at'], unique=False)
    op.create_index('idx_customer_health_severity', 'customer_health_events', ['severity', 'created_at'], unique=False)
    op.create_index('idx_customer_health_soft_delete', 'customer_health_events', ['deleted_at'], unique=False)

    # customer_segments table
    op.create_table(
        'customer_segments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('segment_name', sa.String(length=100), nullable=False),
        sa.Column('segment_type', sa.String(length=50), nullable=False),
        sa.Column('confidence_score', sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('assigned_by', sa.String(length=50), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "segment_type IN ('industry', 'lifecycle', 'value', 'behavior', 'risk')",
            name='check_segment_type'
        )
    )
    op.create_index('idx_customer_segments_customer', 'customer_segments', ['customer_id'], unique=False)
    op.create_index('idx_customer_segments_name', 'customer_segments', ['segment_name'], unique=False)
    op.create_index('idx_customer_segments_soft_delete', 'customer_segments', ['deleted_at'], unique=False)

    # customer_notes table
    op.create_table(
        'customer_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('note_type', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_internal', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('visibility', sa.String(length=20), nullable=False, server_default='team'),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "note_type IN ('general', 'support', 'sales', 'success', 'technical')",
            name='check_note_type'
        ),
        sa.CheckConstraint(
            "visibility IN ('private', 'team', 'company')",
            name='check_note_visibility'
        )
    )
    op.create_index('idx_customer_notes_customer', 'customer_notes', ['customer_id', 'created_at'], unique=False)
    op.create_index('idx_customer_notes_soft_delete', 'customer_notes', ['deleted_at'], unique=False)

    # customer_contacts table
    op.create_table(
        'customer_contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "role IN ('admin', 'billing', 'technical', 'business', 'user')",
            name='check_contact_role'
        )
    )
    op.create_index('idx_customer_contacts_customer', 'customer_contacts', ['customer_id'], unique=False)
    op.create_index('idx_customer_contacts_email', 'customer_contacts', ['email'], unique=False)
    op.create_index('idx_customer_contacts_soft_delete', 'customer_contacts', ['deleted_at'], unique=False)

    # customer_integrations table
    op.create_table(
        'customer_integrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('integration_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_sync_status', sa.String(length=20), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "status IN ('active', 'paused', 'error', 'disconnected')",
            name='check_integration_status'
        )
    )
    op.create_index('idx_customer_integrations_customer', 'customer_integrations', ['customer_id'], unique=False)
    op.create_index('idx_customer_integrations_type', 'customer_integrations', ['integration_type'], unique=False)
    op.create_index('idx_customer_integrations_soft_delete', 'customer_integrations', ['deleted_at'], unique=False)

    # ===================================================================
    # CONVERSATION DOMAIN (3 new tables)
    # ===================================================================

    # agent_handoffs table
    op.create_table(
        'agent_handoffs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_agent', sa.String(length=50), nullable=False),
        sa.Column('to_agent', sa.String(length=50), nullable=False),
        sa.Column('handoff_reason', sa.Text(), nullable=False),
        sa.Column('state_transferred', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence_before', sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.CheckConstraint('from_agent != to_agent', name='check_handoff_different_agents')
    )
    op.create_index('idx_handoffs_conversation', 'agent_handoffs', ['conversation_id', 'timestamp'], unique=False)
    op.create_index('idx_handoffs_agents', 'agent_handoffs', ['from_agent', 'to_agent'], unique=False)
    op.create_index('idx_handoffs_soft_delete', 'agent_handoffs', ['deleted_at'], unique=False)

    # agent_collaborations table
    op.create_table(
        'agent_collaborations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('collaboration_type', sa.String(length=50), nullable=False),
        sa.Column('agents_involved', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('coordinator_agent', sa.String(length=50), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('outcome', sa.Text(), nullable=True),
        sa.Column('consensus_reached', sa.Boolean(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "collaboration_type IN ('sequential', 'parallel', 'debate', 'verification', 'expert_panel')",
            name='check_collaboration_type'
        )
    )
    op.create_index('idx_collaborations_conversation', 'agent_collaborations', ['conversation_id'], unique=False)
    op.create_index('idx_collaborations_type', 'agent_collaborations', ['collaboration_type'], unique=False)
    op.create_index('idx_collaborations_soft_delete', 'agent_collaborations', ['deleted_at'], unique=False)

    # conversation_tags table
    op.create_table(
        'conversation_tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tag', sa.String(length=50), nullable=False),
        sa.Column('tag_category', sa.String(length=50), nullable=True),
        sa.Column('confidence', sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column('tagged_by', sa.String(length=50), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE')
    )
    op.create_index('idx_conversation_tags_conversation', 'conversation_tags', ['conversation_id'], unique=False)
    op.create_index('idx_conversation_tags_tag', 'conversation_tags', ['tag'], unique=False)
    op.create_index('idx_conversation_tags_soft_delete', 'conversation_tags', ['deleted_at'], unique=False)

    # ===================================================================
    # SUBSCRIPTION & BILLING DOMAIN (5 new tables)
    # ===================================================================

    # subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan', sa.String(length=50), nullable=False),
        sa.Column('billing_cycle', sa.String(length=20), nullable=False),
        sa.Column('mrr', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('arr', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('seats_total', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('seats_used', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('canceled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "plan IN ('free', 'basic', 'premium', 'enterprise')",
            name='check_subscription_plan'
        ),
        sa.CheckConstraint(
            "billing_cycle IN ('monthly', 'annual')",
            name='check_billing_cycle'
        ),
        sa.CheckConstraint(
            "status IN ('active', 'past_due', 'canceled', 'unpaid', 'trialing')",
            name='check_subscription_status'
        ),
        sa.CheckConstraint('seats_used <= seats_total', name='check_seats_capacity')
    )
    op.create_index('idx_subscriptions_customer', 'subscriptions', ['customer_id'], unique=False)
    op.create_index('idx_subscriptions_status', 'subscriptions', ['status'], unique=False)
    op.create_index('idx_subscriptions_soft_delete', 'subscriptions', ['deleted_at'], unique=False)

    # invoices table
    op.create_table(
        'invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('invoice_number', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='SET NULL'),
        sa.CheckConstraint(
            "status IN ('draft', 'open', 'paid', 'void', 'uncollectible')",
            name='check_invoice_status'
        )
    )
    op.create_index('idx_invoices_customer', 'invoices', ['customer_id'], unique=False)
    op.create_index('idx_invoices_number', 'invoices', ['invoice_number'], unique=True)
    op.create_index('idx_invoices_status', 'invoices', ['status'], unique=False)
    op.create_index('idx_invoices_soft_delete', 'invoices', ['deleted_at'], unique=False)

    # payments table
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('amount', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('transaction_id', sa.String(length=255), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_reason', sa.Text(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='SET NULL'),
        sa.CheckConstraint(
            "status IN ('pending', 'succeeded', 'failed', 'canceled', 'refunded')",
            name='check_payment_status'
        )
    )
    op.create_index('idx_payments_customer', 'payments', ['customer_id'], unique=False)
    op.create_index('idx_payments_invoice', 'payments', ['invoice_id'], unique=False)
    op.create_index('idx_payments_status', 'payments', ['status'], unique=False)
    op.create_index('idx_payments_soft_delete', 'payments', ['deleted_at'], unique=False)

    # usage_events table
    op.create_table(
        'usage_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE')
    )
    op.create_index('idx_usage_events_customer', 'usage_events', ['customer_id', 'timestamp'], unique=False)
    op.create_index('idx_usage_events_type', 'usage_events', ['event_type'], unique=False)
    op.create_index('idx_usage_events_soft_delete', 'usage_events', ['deleted_at'], unique=False)

    # credits table
    op.create_table(
        'credits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('credit_type', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('used_amount', sa.DECIMAL(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "credit_type IN ('promotional', 'refund', 'goodwill', 'migration')",
            name='check_credit_type'
        ),
        sa.CheckConstraint(
            "status IN ('active', 'used', 'expired', 'canceled')",
            name='check_credit_status'
        ),
        sa.CheckConstraint('used_amount <= amount', name='check_credit_usage')
    )
    op.create_index('idx_credits_customer', 'credits', ['customer_id'], unique=False)
    op.create_index('idx_credits_status', 'credits', ['status'], unique=False)
    op.create_index('idx_credits_soft_delete', 'credits', ['deleted_at'], unique=False)

    # ===================================================================
    # SALES & LEADS DOMAIN (5 new tables)
    # ===================================================================

    # employees table (needed for leads.assigned_to FK)
    op.create_table(
        'employees',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('department', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_index('idx_employees_email', 'employees', ['email'], unique=True)
    op.create_index('idx_employees_role', 'employees', ['role'], unique=False)
    op.create_index('idx_employees_soft_delete', 'employees', ['deleted_at'], unique=False)

    # leads table
    op.create_table(
        'leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('company', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('budget', sa.String(length=50), nullable=True),
        sa.Column('authority', sa.String(length=50), nullable=True),
        sa.Column('need_score', sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column('timeline', sa.String(length=50), nullable=True),
        sa.Column('lead_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('qualification_status', sa.String(length=50), nullable=False, server_default='new'),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('converted_to_customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('converted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to'], ['employees.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['converted_to_customer_id'], ['customers.id'], ondelete='SET NULL'),
        sa.CheckConstraint(
            "qualification_status IN ('new', 'mql', 'sql', 'qualified', 'disqualified', 'converted')",
            name='check_lead_qualification_status'
        ),
        sa.CheckConstraint('lead_score BETWEEN 0 AND 100', name='check_lead_score_range'),
        sa.CheckConstraint('need_score IS NULL OR (need_score BETWEEN 0 AND 1)', name='check_need_score_range')
    )
    op.create_index('idx_leads_email', 'leads', ['email'], unique=False)
    op.create_index('idx_leads_qualification', 'leads', ['qualification_status'], unique=False)
    op.create_index('idx_leads_score', 'leads', ['lead_score'], unique=False)
    op.create_index('idx_leads_assigned', 'leads', ['assigned_to'], unique=False)
    op.create_index('idx_leads_soft_delete', 'leads', ['deleted_at'], unique=False)

    # deals table
    op.create_table(
        'deals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('value', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('stage', sa.String(length=50), nullable=False, server_default='prospecting'),
        sa.Column('probability', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expected_close_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('lost_reason', sa.Text(), nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_to'], ['employees.id'], ondelete='SET NULL'),
        sa.CheckConstraint(
            "stage IN ('prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost')",
            name='check_deal_stage'
        ),
        sa.CheckConstraint('probability BETWEEN 0 AND 100', name='check_deal_probability')
    )
    op.create_index('idx_deals_lead', 'deals', ['lead_id'], unique=False)
    op.create_index('idx_deals_customer', 'deals', ['customer_id'], unique=False)
    op.create_index('idx_deals_stage', 'deals', ['stage'], unique=False)
    op.create_index('idx_deals_assigned', 'deals', ['assigned_to'], unique=False)
    op.create_index('idx_deals_soft_delete', 'deals', ['deleted_at'], unique=False)

    # sales_activities table
    op.create_table(
        'sales_activities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('deal_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('activity_type', sa.String(length=50), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('outcome', sa.String(length=50), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('performed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['performed_by'], ['employees.id'], ondelete='SET NULL'),
        sa.CheckConstraint(
            "activity_type IN ('call', 'email', 'meeting', 'demo', 'proposal', 'follow_up')",
            name='check_activity_type'
        )
    )
    op.create_index('idx_sales_activities_deal', 'sales_activities', ['deal_id'], unique=False)
    op.create_index('idx_sales_activities_lead', 'sales_activities', ['lead_id'], unique=False)
    op.create_index('idx_sales_activities_type', 'sales_activities', ['activity_type'], unique=False)
    op.create_index('idx_sales_activities_soft_delete', 'sales_activities', ['deleted_at'], unique=False)

    # quotes table
    op.create_table(
        'quotes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('deal_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('quote_number', sa.String(length=50), nullable=False),
        sa.Column('total_amount', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('line_items', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='SET NULL'),
        sa.CheckConstraint(
            "status IN ('draft', 'sent', 'accepted', 'declined', 'expired')",
            name='check_quote_status'
        )
    )
    op.create_index('idx_quotes_deal', 'quotes', ['deal_id'], unique=False)
    op.create_index('idx_quotes_customer', 'quotes', ['customer_id'], unique=False)
    op.create_index('idx_quotes_number', 'quotes', ['quote_number'], unique=True)
    op.create_index('idx_quotes_soft_delete', 'quotes', ['deleted_at'], unique=False)

    # ===================================================================
    # ANALYTICS & METRICS DOMAIN (3 new tables)
    # ===================================================================

    # conversation_analytics table
    op.create_table(
        'conversation_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=True),
        sa.Column('total_conversations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('resolved_conversations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('escalated_conversations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_resolution_time_seconds', sa.Integer(), nullable=True),
        sa.Column('avg_sentiment', sa.Float(), nullable=True),
        sa.Column('avg_csat', sa.Float(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_index('idx_conversation_analytics_date', 'conversation_analytics', ['date'], unique=False)
    op.create_index('idx_conversation_analytics_channel', 'conversation_analytics', ['channel', 'date'], unique=False)
    op.create_index('idx_conversation_analytics_soft_delete', 'conversation_analytics', ['deleted_at'], unique=False)

    # feature_usage table
    op.create_table(
        'feature_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feature_name', sa.String(length=100), nullable=False),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE')
    )
    op.create_index('idx_feature_usage_customer', 'feature_usage', ['customer_id', 'date'], unique=False)
    op.create_index('idx_feature_usage_feature', 'feature_usage', ['feature_name'], unique=False)
    op.create_index('idx_feature_usage_unique', 'feature_usage', ['customer_id', 'feature_name', 'date'], unique=True)
    op.create_index('idx_feature_usage_soft_delete', 'feature_usage', ['deleted_at'], unique=False)

    # ab_tests table
    op.create_table(
        'ab_tests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('test_name', sa.String(length=100), nullable=False),
        sa.Column('variant', sa.String(length=50), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('outcome', sa.String(length=50), nullable=True),
        sa.Column('metric_value', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE')
    )
    op.create_index('idx_ab_tests_name', 'ab_tests', ['test_name'], unique=False)
    op.create_index('idx_ab_tests_variant', 'ab_tests', ['variant'], unique=False)
    op.create_index('idx_ab_tests_soft_delete', 'ab_tests', ['deleted_at'], unique=False)

    # ===================================================================
    # AUTOMATION & WORKFLOW DOMAIN (3 new tables)
    # ===================================================================

    # workflows table
    op.create_table(
        'workflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('trigger_type', sa.String(length=50), nullable=False),
        sa.Column('trigger_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('actions', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint(
            "trigger_type IN ('time_based', 'event_based', 'condition_based', 'manual')",
            name='check_workflow_trigger_type'
        )
    )
    op.create_index('idx_workflows_name', 'workflows', ['name'], unique=False)
    op.create_index('idx_workflows_active', 'workflows', ['is_active'], unique=False)
    op.create_index('idx_workflows_soft_delete', 'workflows', ['deleted_at'], unique=False)

    # workflow_executions table
    op.create_table(
        'workflow_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='running'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_log', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "status IN ('running', 'completed', 'failed', 'canceled')",
            name='check_workflow_execution_status'
        )
    )
    op.create_index('idx_workflow_executions_workflow', 'workflow_executions', ['workflow_id'], unique=False)
    op.create_index('idx_workflow_executions_status', 'workflow_executions', ['status'], unique=False)
    op.create_index('idx_workflow_executions_soft_delete', 'workflow_executions', ['deleted_at'], unique=False)

    # scheduled_tasks table
    op.create_table(
        'scheduled_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('task_name', sa.String(length=100), nullable=False),
        sa.Column('task_type', sa.String(length=50), nullable=False),
        sa.Column('schedule', sa.String(length=100), nullable=False),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_index('idx_scheduled_tasks_name', 'scheduled_tasks', ['task_name'], unique=False)
    op.create_index('idx_scheduled_tasks_active', 'scheduled_tasks', ['is_active'], unique=False)
    op.create_index('idx_scheduled_tasks_next_run', 'scheduled_tasks', ['next_run_at'], unique=False)
    op.create_index('idx_scheduled_tasks_soft_delete', 'scheduled_tasks', ['deleted_at'], unique=False)

    # ===================================================================
    # SECURITY & COMPLIANCE DOMAIN (1 new table)
    # ===================================================================

    # audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('actor_type', sa.String(length=50), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('changes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.CheckConstraint(
            "action IN ('create', 'read', 'update', 'delete', 'login', 'logout', 'export')",
            name='check_audit_action'
        ),
        sa.CheckConstraint(
            "actor_type IN ('user', 'agent', 'system', 'api')",
            name='check_audit_actor_type'
        )
    )
    op.create_index('idx_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'], unique=False)
    op.create_index('idx_audit_logs_actor', 'audit_logs', ['actor_type', 'actor_id'], unique=False)
    op.create_index('idx_audit_logs_timestamp', 'audit_logs', ['timestamp'], unique=False)
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'], unique=False)


def downgrade() -> None:
    """Rollback schema expansions"""

    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_table('audit_logs')
    op.drop_table('scheduled_tasks')
    op.drop_table('workflow_executions')
    op.drop_table('workflows')
    op.drop_table('ab_tests')
    op.drop_table('feature_usage')
    op.drop_table('conversation_analytics')
    op.drop_table('quotes')
    op.drop_table('sales_activities')
    op.drop_table('deals')
    op.drop_table('leads')
    op.drop_table('employees')
    op.drop_table('credits')
    op.drop_table('usage_events')
    op.drop_table('payments')
    op.drop_table('invoices')
    op.drop_table('subscriptions')
    op.drop_table('conversation_tags')
    op.drop_table('agent_collaborations')
    op.drop_table('agent_handoffs')
    op.drop_table('customer_integrations')
    op.drop_table('customer_contacts')
    op.drop_table('customer_notes')
    op.drop_table('customer_segments')
    op.drop_table('customer_health_events')

    # Remove columns from existing tables (customers)
    op.drop_index('idx_customers_industry', 'customers')
    op.drop_index('idx_customers_mrr', 'customers')
    op.drop_index('idx_customers_churn_risk', 'customers')
    op.drop_index('idx_customers_health_score', 'customers')
    op.drop_constraint('check_customer_churn_risk', 'customers')
    op.drop_constraint('check_customer_health_score', 'customers')
    op.drop_column('customers', 'language')
    op.drop_column('customers', 'timezone')
    op.drop_column('customers', 'country')
    op.drop_column('customers', 'lead_source')
    op.drop_column('customers', 'nps_score')
    op.drop_column('customers', 'churn_risk')
    op.drop_column('customers', 'health_score')
    op.drop_column('customers', 'ltv')
    op.drop_column('customers', 'mrr')
    op.drop_column('customers', 'industry')
    op.drop_column('customers', 'company_size')
    op.drop_column('customers', 'company_name')

    # Remove columns from conversations
    op.drop_index('idx_conversations_last_activity', 'conversations')
    op.drop_index('idx_conversations_emotion', 'conversations')
    op.drop_index('idx_conversations_channel', 'conversations')
    op.drop_constraint('check_conversation_csat', 'conversations')
    op.drop_constraint('check_conversation_channel', 'conversations')
    op.drop_column('conversations', 'last_activity_at')
    op.drop_column('conversations', 'csat_score')
    op.drop_column('conversations', 'first_response_time_seconds')
    op.drop_column('conversations', 'resolved_by_agent')
    op.drop_column('conversations', 'emotion')
    op.drop_column('conversations', 'intent_confidence')
    op.drop_column('conversations', 'channel')

    # Remove columns from messages (FIXED: no longer trying to drop tokens_used)
    op.drop_constraint('check_message_urgency', 'messages')
    op.drop_column('messages', 'model_used')
    op.drop_column('messages', 'urgency')
    op.drop_column('messages', 'agent_confidence')
