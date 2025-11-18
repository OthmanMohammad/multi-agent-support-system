"""Add missing Tier 3 and KB tables

Revision ID: 20251118000000
Revises: 20251117000000
Create Date: 2025-11-18 00:00:00.000000

This migration adds all missing tables from Tier 3 Operational Excellence
and Knowledge Base that were not created in previous migrations.

Missing tables:
- KB: kb_articles, kb_usage, kb_quality_reports, kb_article_quality
- Analytics: funnel_steps, funnel_analysis, correlation_analysis, nl_queries,
  executive_reports, insights, prediction_explanations
- QA: policy_rules, code_validation_results, link_check_results,
  sensitivity_violations, hallucination_detections
- Automation: automated_tasks, sla_compliance
- Security: pii_detections, access_control_logs, security_incidents, compliance_audits,
  vulnerability_scans, data_retention_policies, consent_records,
  encryption_validations, penetration_tests
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '20251118000000'
down_revision = '20251117000000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all missing tables"""

    # ===================================================================
    # KNOWLEDGE BASE TABLES (3 tables)
    # ===================================================================

    # KB Articles Table
    op.create_table(
        'kb_articles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False, index=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('url', sa.String(500), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('quality_last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('helpful_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('not_helpful_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_resolution_time_seconds', sa.Float(), nullable=True),
        sa.Column('resolution_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_csat', sa.Float(), nullable=True),
        sa.Column('csat_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('needs_update', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('update_priority', sa.String(20), nullable=True),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('idx_kb_articles_category', 'kb_articles', ['category'])
    op.create_index('idx_kb_articles_quality_score', 'kb_articles', ['quality_score'])
    op.create_index('idx_kb_articles_is_active', 'kb_articles', ['is_active'])
    op.create_index('idx_kb_articles_needs_update', 'kb_articles', ['needs_update'])
    op.create_index('idx_kb_articles_not_deleted', 'kb_articles', ['deleted_at'],
                    postgresql_where=sa.text('deleted_at IS NULL'))

    # KB Usage Table
    op.create_table(
        'kb_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('article_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('kb_articles.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('event_type', sa.String(50), nullable=False, index=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('customers.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('resolution_time_seconds', sa.Integer(), nullable=True),
        sa.Column('csat_score', sa.Integer(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('idx_kb_usage_article_id', 'kb_usage', ['article_id'])
    op.create_index('idx_kb_usage_event_type', 'kb_usage', ['event_type'])
    op.create_index('idx_kb_usage_conversation_id', 'kb_usage', ['conversation_id'])
    op.create_index('idx_kb_usage_created_at', 'kb_usage', ['created_at'])

    # KB Quality Reports Table
    op.create_table(
        'kb_quality_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('article_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('kb_articles.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('quality_score', sa.Integer(), nullable=False),
        sa.Column('completeness_score', sa.Integer(), nullable=True),
        sa.Column('clarity_score', sa.Integer(), nullable=True),
        sa.Column('accuracy_score', sa.Integer(), nullable=True),
        sa.Column('examples_score', sa.Integer(), nullable=True),
        sa.Column('formatting_score', sa.Integer(), nullable=True),
        sa.Column('issues', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('strengths', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('needs_update', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('checked_by', sa.String(100), nullable=False, server_default='kb_quality_checker'),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('idx_kb_quality_reports_article_id', 'kb_quality_reports', ['article_id'])
    op.create_index('idx_kb_quality_reports_quality_score', 'kb_quality_reports', ['quality_score'])
    op.create_index('idx_kb_quality_reports_created_at', 'kb_quality_reports', ['created_at'])

    # ===================================================================
    # ANALYTICS & INSIGHTS SWARM (Additional tables - 7 tables)
    # ===================================================================

    # Funnel Steps Table
    op.create_table(
        'funnel_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('funnel_name', sa.String(255), nullable=False, index=True),
        sa.Column('step_order', sa.Integer(), nullable=False),
        sa.Column('step_name', sa.String(255), nullable=False),
        sa.Column('step_type', sa.String(100), nullable=False),
        sa.Column('event_name', sa.String(255), nullable=True),
        sa.Column('url_pattern', sa.String(500), nullable=True),
        sa.Column('required', sa.Boolean(), nullable=False, server_default='true'),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Funnel Analysis Table
    op.create_table(
        'funnel_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('funnel_name', sa.String(255), nullable=False, index=True),
        sa.Column('analysis_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('analysis_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_users', sa.Integer(), nullable=False),
        sa.Column('step_data', postgresql.JSONB(), nullable=False),
        sa.Column('conversion_rate', sa.Float(), nullable=False),
        sa.Column('drop_off_points', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('avg_time_to_convert_minutes', sa.Float(), nullable=True),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Correlation Analysis Table
    op.create_table(
        'correlation_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('metric_a', sa.String(255), nullable=False),
        sa.Column('metric_b', sa.String(255), nullable=False),
        sa.Column('correlation_coefficient', sa.Float(), nullable=False),
        sa.Column('p_value', sa.Float(), nullable=True),
        sa.Column('sample_size', sa.Integer(), nullable=False),
        sa.Column('relationship_strength', sa.String(50), nullable=True),
        sa.Column('causality_direction', sa.String(100), nullable=True),
        sa.Column('analysis_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('analysis_period_end', sa.DateTime(timezone=True), nullable=False),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # NL Queries Table
    op.create_table(
        'nl_queries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(255), nullable=True),
        sa.Column('sql_generated', sa.Text(), nullable=True),
        sa.Column('results_count', sa.Integer(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Executive Reports Table
    op.create_table(
        'executive_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('report_type', sa.String(100), nullable=False, index=True),
        sa.Column('report_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('report_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metrics_summary', postgresql.JSONB(), nullable=False),
        sa.Column('key_insights', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('recommendations', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('report_url', sa.String(500), nullable=True),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Insights Table
    op.create_table(
        'insights',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('insight_type', sa.String(100), nullable=False, index=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('supporting_data', postgresql.JSONB(), nullable=False),
        sa.Column('recommended_actions', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(50), nullable=False, server_default='new'),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Prediction Explanations Table
    op.create_table(
        'prediction_explanations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('prediction_type', sa.String(100), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prediction_value', sa.Float(), nullable=False),
        sa.Column('feature_importances', postgresql.JSONB(), nullable=False),
        sa.Column('explanation_text', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # ===================================================================
    # QUALITY ASSURANCE SWARM (Additional tables - 6 tables)
    # ===================================================================

    # KB Article Quality Table
    op.create_table(
        'kb_article_quality',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('article_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('kb_articles.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('quality_score', sa.Float(), nullable=False),
        sa.Column('accuracy_score', sa.Float(), nullable=True),
        sa.Column('completeness_score', sa.Float(), nullable=True),
        sa.Column('clarity_score', sa.Float(), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('issues_found', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('recommendations', postgresql.JSONB(), nullable=False, server_default='[]'),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Policy Rules Table
    op.create_table(
        'policy_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('rule_name', sa.String(255), nullable=False, unique=True),
        sa.Column('rule_type', sa.String(100), nullable=False),
        sa.Column('rule_category', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('pattern', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Code Validation Results Table
    op.create_table(
        'code_validation_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('code_snippet', sa.Text(), nullable=False),
        sa.Column('language', sa.String(50), nullable=False),
        sa.Column('syntax_valid', sa.Boolean(), nullable=False),
        sa.Column('syntax_errors', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('security_issues', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('best_practice_violations', postgresql.JSONB(), nullable=False, server_default='[]'),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Link Check Results Table
    op.create_table(
        'link_check_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('url', sa.String(2048), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('is_valid', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Sensitivity Violations Table
    op.create_table(
        'sensitivity_violations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('violation_type', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('text_excerpt', sa.Text(), nullable=True),
        sa.Column('recommendation', sa.Text(), nullable=True),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Hallucination Detections Table
    op.create_table(
        'hallucination_detections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('claim', sa.Text(), nullable=False),
        sa.Column('hallucination_type', sa.String(100), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('supporting_evidence', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('contradicting_evidence', postgresql.JSONB(), nullable=False, server_default='{}'),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # ===================================================================
    # AUTOMATION & WORKFLOW SWARM (2 tables)
    # ===================================================================

    # Automated Tasks Table
    op.create_table(
        'automated_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('task_type', sa.String(100), nullable=False, index=True),
        sa.Column('task_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('trigger_type', sa.String(100), nullable=False),
        sa.Column('trigger_config', postgresql.JSONB(), nullable=False),
        sa.Column('action_config', postgresql.JSONB(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('run_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failure_count', sa.Integer(), nullable=False, server_default='0'),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # SLA Compliance Table (CRITICAL - this is blocking API calls!)
    op.create_table(
        'sla_compliance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('sla_type', sa.String(100), nullable=False, index=True),
        sa.Column('sla_tier', sa.String(50), nullable=False),
        sa.Column('sla_target_minutes', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('sla_met', sa.Boolean(), nullable=True),
        sa.Column('sla_buffer_minutes', sa.Integer(), nullable=True),
        sa.Column('sla_breach_severity', sa.String(50), nullable=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('customer_plan', sa.String(100), nullable=True),
        sa.Column('escalated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('compensation_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('compensation_amount', sa.Float(), nullable=True),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Automation Workflow Executions Table
    op.create_table(
        'automation_workflow_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('automated_task_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('automated_tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('result_data', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('error_message', sa.Text(), nullable=True),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # ===================================================================
    # SECURITY & COMPLIANCE SWARM (9 tables)
    # ===================================================================

    # PII Detections Table
    op.create_table(
        'pii_detections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('pii_type', sa.String(100), nullable=False),
        sa.Column('detected_value', sa.String(500), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('masked_value', sa.String(500), nullable=True),
        sa.Column('action_taken', sa.String(100), nullable=False),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Access Control Logs Table
    op.create_table(
        'access_control_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('access_granted', sa.Boolean(), nullable=False),
        sa.Column('denial_reason', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Security Incidents Table
    op.create_table(
        'security_incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('incident_type', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('affected_systems', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(50), nullable=False, server_default='open'),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('remediation_steps', postgresql.JSONB(), nullable=False, server_default='[]'),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Compliance Audits Table
    op.create_table(
        'compliance_audits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('audit_type', sa.String(100), nullable=False),
        sa.Column('framework', sa.String(100), nullable=False),
        sa.Column('audit_date', sa.Date(), nullable=False),
        sa.Column('auditor', sa.String(255), nullable=True),
        sa.Column('findings', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('pass_fail_status', sa.String(50), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('recommendations', postgresql.JSONB(), nullable=False, server_default='[]'),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Vulnerability Scans Table
    op.create_table(
        'vulnerability_scans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('scan_type', sa.String(100), nullable=False),
        sa.Column('target_system', sa.String(255), nullable=False),
        sa.Column('scan_started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('scan_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('vulnerabilities_found', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('critical_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('high_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('medium_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('low_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('findings', postgresql.JSONB(), nullable=False, server_default='[]'),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Data Retention Policies Table
    op.create_table(
        'data_retention_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('policy_name', sa.String(255), nullable=False, unique=True),
        sa.Column('data_type', sa.String(100), nullable=False),
        sa.Column('retention_period_days', sa.Integer(), nullable=False),
        sa.Column('deletion_method', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('legal_basis', sa.Text(), nullable=True),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Consent Records Table
    op.create_table(
        'consent_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('consent_type', sa.String(100), nullable=False),
        sa.Column('consented', sa.Boolean(), nullable=False),
        sa.Column('consent_text', sa.Text(), nullable=True),
        sa.Column('consent_version', sa.String(50), nullable=True),
        sa.Column('consent_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Encryption Validations Table
    op.create_table(
        'encryption_validations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('data_type', sa.String(100), nullable=False),
        sa.Column('encryption_method', sa.String(100), nullable=False),
        sa.Column('key_rotation_date', sa.Date(), nullable=True),
        sa.Column('is_compliant', sa.Boolean(), nullable=False),
        sa.Column('issues_found', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=False),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Penetration Tests Table
    op.create_table(
        'penetration_tests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('test_type', sa.String(100), nullable=False),
        sa.Column('tester', sa.String(255), nullable=True),
        sa.Column('test_date', sa.Date(), nullable=False),
        sa.Column('scope', sa.Text(), nullable=False),
        sa.Column('findings', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('vulnerabilities_found', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('risk_level', sa.String(50), nullable=False),
        sa.Column('report_url', sa.String(500), nullable=True),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    print("Missing Tier 3 and KB tables migration completed")
    print("- KB: 3 tables (kb_articles, kb_usage, kb_quality_reports)")
    print("- Analytics: 7 tables")
    print("- QA: 6 tables")
    print("- Automation: 3 tables (including SLA compliance)")
    print("- Security: 9 tables")
    print("Total: 28 new tables added")


def downgrade() -> None:
    """Drop all missing tables in reverse order"""

    tables_to_drop = [
        # Security tables
        'penetration_tests',
        'encryption_validations',
        'consent_records',
        'data_retention_policies',
        'vulnerability_scans',
        'compliance_audits',
        'security_incidents',
        'access_control_logs',
        'pii_detections',
        # Automation tables
        'automation_workflow_executions',
        'sla_compliance',
        'automated_tasks',
        # QA tables
        'hallucination_detections',
        'sensitivity_violations',
        'link_check_results',
        'code_validation_results',
        'policy_rules',
        'kb_article_quality',
        # Analytics tables
        'prediction_explanations',
        'insights',
        'executive_reports',
        'nl_queries',
        'correlation_analysis',
        'funnel_analysis',
        'funnel_steps',
        # KB tables
        'kb_quality_reports',
        'kb_usage',
        'kb_articles',
    ]

    for table in tables_to_drop:
        op.drop_table(table)

    print("Dropped 28 missing tables")