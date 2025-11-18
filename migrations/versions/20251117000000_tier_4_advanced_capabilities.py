"""Tier 4: Advanced Capabilities - 49 agents schema

Revision ID: 20251117000000
Revises: 20251116000000
Create Date: 2025-11-17 00:00:00.000000

This migration adds comprehensive schema support for Tier 4 Advanced Capabilities:
- Predictive Intelligence Swarm (10 agents): 5 tables
- Personalization Swarm (9 agents): 3 tables
- Competitive Intelligence Swarm (10 agents): 4 tables
- Content Generation Swarm (10 agents): 2 tables
- Learning & Improvement Swarm (10 agents): 3 tables

Total: 17 new tables for advanced capabilities
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '20251117000000'
down_revision = '20251116120000'  # Fixed: Should point to authentication migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Tier 4 advanced capabilities tables"""

    # ===================================================================
    # PREDICTIVE INTELLIGENCE SWARM TABLES (5 tables)
    # ===================================================================

    # ML Predictions Table (TASK-4011 to TASK-4020)
    op.create_table(
        'ml_predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('prediction_type', sa.String(50), nullable=False, index=True),  # churn, upsell, renewal, etc.
        sa.Column('prediction_value', sa.Float(), nullable=False),  # Probability or numeric prediction
        sa.Column('prediction_label', sa.String(50), nullable=True),  # high/medium/low or categorical
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),  # Full prediction details
        sa.Column('actual_outcome', sa.Boolean(), nullable=True),  # Fill in later for accuracy tracking
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('valid_until', sa.TIMESTAMP(), nullable=True),
        sa.Index('idx_customer_predictions', 'customer_id', 'prediction_type'),
        sa.Index('idx_prediction_date', 'created_at'),
        sa.Index('idx_prediction_type_date', 'prediction_type', 'created_at')
    )

    # ML Model Performance Table
    op.create_table(
        'ml_model_performance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('model_name', sa.String(100), nullable=False, index=True),
        sa.Column('version', sa.String(50), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('precision', sa.Float(), nullable=True),
        sa.Column('recall', sa.Float(), nullable=True),
        sa.Column('f1_score', sa.Float(), nullable=True),
        sa.Column('auc', sa.Float(), nullable=True),
        sa.Column('training_date', sa.TIMESTAMP(), nullable=True),
        sa.Column('evaluation_date', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('sample_size', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Index('idx_model_version', 'model_name', 'version')
    )

    # Upsell Opportunities Table
    op.create_table(
        'upsell_opportunities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('opportunity_type', sa.String(50), nullable=False),  # tier_upgrade, seat_expansion, add_on
        sa.Column('estimated_arr_increase', sa.Float(), nullable=True),
        sa.Column('probability', sa.Float(), nullable=False),
        sa.Column('triggers', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('recommended_timing', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='identified'),  # identified, contacted, won, lost
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('closed_at', sa.TIMESTAMP(), nullable=True),
        sa.Index('idx_upsell_customer', 'customer_id', 'status'),
        sa.Index('idx_upsell_status', 'status', 'created_at')
    )

    # Capacity Forecasts Table
    op.create_table(
        'capacity_forecasts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('resource_type', sa.String(50), nullable=False),  # cpu, memory, storage, bandwidth
        sa.Column('forecast_date', sa.Date(), nullable=False, index=True),
        sa.Column('predicted_usage_percent', sa.Float(), nullable=False),
        sa.Column('confidence_lower', sa.Float(), nullable=True),
        sa.Column('confidence_upper', sa.Float(), nullable=True),
        sa.Column('alert_triggered', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Index('idx_capacity_resource_date', 'resource_type', 'forecast_date')
    )

    # Support Volume Forecasts Table
    op.create_table(
        'support_volume_forecasts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('forecast_date', sa.Date(), nullable=False, index=True),
        sa.Column('predicted_tickets', sa.Integer(), nullable=False),
        sa.Column('confidence_lower', sa.Integer(), nullable=True),
        sa.Column('confidence_upper', sa.Integer(), nullable=True),
        sa.Column('recommended_agents', sa.Integer(), nullable=True),
        sa.Column('actual_tickets', sa.Integer(), nullable=True),  # Fill in later
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Index('idx_forecast_date', 'forecast_date')
    )

    # ===================================================================
    # PERSONALIZATION SWARM TABLES (3 tables)
    # ===================================================================

    # Customer Preferences Table (TASK-4022)
    op.create_table(
        'customer_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        # Preferences
        sa.Column('communication_style', sa.String(50), nullable=True),  # formal, casual, technical
        sa.Column('response_depth', sa.String(50), nullable=True),  # brief, moderate, detailed
        sa.Column('content_format', postgresql.JSONB(), nullable=False, server_default='["text"]'),  # ["text", "video", "code"]
        sa.Column('technical_level', sa.String(50), nullable=True),  # beginner, intermediate, expert
        sa.Column('notification_frequency', sa.String(50), nullable=True),  # immediate, daily, weekly
        sa.Column('preferred_channel', sa.String(50), nullable=True),  # email, slack, in_app, phone
        sa.Column('preferred_time', sa.String(50), nullable=True),  # "09:00-17:00"
        sa.Column('timezone', sa.String(50), nullable=True),  # "America/Los_Angeles"
        sa.Column('language', sa.String(10), nullable=True, server_default='en'),  # "en", "es", "fr"
        # Confidence scores (0-1)
        sa.Column('confidence_scores', postgresql.JSONB(), nullable=False, server_default='{}'),
        # Metadata
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Personalization Events Table
    op.create_table(
        'personalization_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('event_type', sa.String(100), nullable=False, index=True),  # email_opened, article_read, etc.
        sa.Column('event_data', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('timestamp', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), index=True),
        sa.Index('idx_customer_events', 'customer_id', 'timestamp'),
        sa.Index('idx_event_type', 'event_type')
    )

    # Customer Personas Table (TASK-4021)
    op.create_table(
        'customer_personas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column('persona', sa.String(50), nullable=False),  # executive, power_user, manager, casual_user, champion
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('signals', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('identified_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # ===================================================================
    # COMPETITIVE INTELLIGENCE SWARM TABLES (4 tables)
    # ===================================================================

    # Competitors Table (TASK-4030)
    op.create_table(
        'competitors',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(200), nullable=False, unique=True, index=True),
        sa.Column('website', sa.String(500), nullable=True),
        sa.Column('target_market', sa.String(100), nullable=True),
        sa.Column('primary_product', sa.String(200), nullable=True),
        # URLs to track
        sa.Column('pricing_page', sa.String(500), nullable=True),
        sa.Column('changelog_url', sa.String(500), nullable=True),
        sa.Column('blog_url', sa.String(500), nullable=True),
        # Latest data
        sa.Column('current_pricing', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('latest_features', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Competitor Changes Table
    op.create_table(
        'competitor_changes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('competitor_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('change_type', sa.String(100), nullable=False, index=True),  # pricing, feature, news, review
        sa.Column('change_description', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(20), nullable=True),  # low, medium, high, critical
        sa.Column('impact', sa.Text(), nullable=True),
        sa.Column('detected_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), index=True),
        sa.Index('idx_competitor_changes', 'competitor_id', 'detected_at')
    )

    # Win/Loss Records Table (TASK-4037)
    op.create_table(
        'win_loss_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('deal_id', sa.String(100), nullable=True),
        sa.Column('outcome', sa.String(20), nullable=False, index=True),  # won or lost
        sa.Column('competitor', sa.String(200), nullable=True, index=True),
        sa.Column('deal_value', sa.Float(), nullable=True),
        sa.Column('decision_factors', postgresql.JSONB(), nullable=False, server_default='[]'),  # Array of factors
        sa.Column('customer_quote', sa.Text(), nullable=True),
        sa.Column('sales_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), index=True),
        sa.Index('idx_win_loss', 'outcome', 'competitor')
    )

    # Battlecards Table (TASK-4039)
    op.create_table(
        'battlecards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('competitor', sa.String(200), nullable=False, unique=True, index=True),
        sa.Column('content', sa.Text(), nullable=False),  # Markdown content
        sa.Column('last_updated', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # ===================================================================
    # CONTENT GENERATION SWARM TABLES (2 tables)
    # ===================================================================

    # Generated Content Table (TASK-4040 to TASK-4049)
    op.create_table(
        'generated_content',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('content_type', sa.String(50), nullable=False, index=True),  # kb_article, blog_post, case_study, etc.
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('review_status', sa.String(50), nullable=False, server_default='pending'),  # pending, approved, rejected
        sa.Column('published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), index=True),
        sa.Column('published_at', sa.TIMESTAMP(), nullable=True),
        sa.Index('idx_content_type_status', 'content_type', 'review_status')
    )

    # Content Performance Table
    op.create_table(
        'content_performance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('views', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('engagement_rate', sa.Float(), nullable=True),
        sa.Column('feedback_positive', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('feedback_negative', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('conversion_rate', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # ===================================================================
    # LEARNING & IMPROVEMENT SWARM TABLES (3 tables)
    # ===================================================================

    # Improvement Insights Table (TASK-4053)
    op.create_table(
        'improvement_insights',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('insight_type', sa.String(100), nullable=False, index=True),  # pattern, gap, mistake, feedback
        sa.Column('insight_description', sa.Text(), nullable=True),
        sa.Column('evidence', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('recommended_action', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(20), nullable=True, index=True),  # low, medium, high, critical
        sa.Column('status', sa.String(50), nullable=False, server_default='new', index=True),  # new, in_progress, completed, dismissed
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), index=True),
        sa.Index('idx_insights_priority', 'priority', 'status')
    )

    # A/B Test Experiments Table (TASK-4055) - Configuration and results
    # Note: Different from 'ab_tests' table which tracks participation
    op.create_table(
        'ab_test_experiments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('test_id', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('hypothesis', sa.Text(), nullable=True),
        sa.Column('variants', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('traffic_split', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('success_metric', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='running', index=True),  # running, completed, cancelled
        sa.Column('results', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('winner', sa.String(50), nullable=True),
        sa.Column('deployed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Index('idx_ab_test_experiments_status', 'status')
    )

    # Prompt Versions Table (TASK-4057)
    op.create_table(
        'prompt_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('agent_name', sa.String(100), nullable=False, index=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('prompt_text', sa.Text(), nullable=False),
        sa.Column('performance_metrics', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Index('idx_prompt_versions', 'agent_name', 'version')
    )


def downgrade() -> None:
    """Drop Tier 4 advanced capabilities tables"""

    # Learning & Improvement tables
    op.drop_table('prompt_versions')
    op.drop_table('ab_test_experiments')
    op.drop_table('improvement_insights')

    # Content Generation tables
    op.drop_table('content_performance')
    op.drop_table('generated_content')

    # Competitive Intelligence tables
    op.drop_table('battlecards')
    op.drop_table('win_loss_records')
    op.drop_table('competitor_changes')
    op.drop_table('competitors')

    # Personalization tables
    op.drop_table('customer_personas')
    op.drop_table('personalization_events')
    op.drop_table('customer_preferences')

    # Predictive Intelligence tables
    op.drop_table('support_volume_forecasts')
    op.drop_table('capacity_forecasts')
    op.drop_table('upsell_opportunities')
    op.drop_table('ml_model_performance')
    op.drop_table('ml_predictions')