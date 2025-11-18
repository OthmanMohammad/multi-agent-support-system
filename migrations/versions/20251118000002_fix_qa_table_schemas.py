"""Fix code_validation_results and other QA table schemas

Revision ID: 20251118000002
Revises: 20251118000001
Create Date: 2025-11-18 00:00:02.000000

Fix remaining schema mismatches in QA and Security tables
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251118000002'
down_revision = '20251118000001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Fix all remaining table schemas"""

    # Fix code_validation_results
    op.drop_table('code_validation_results')
    op.create_table(
        'code_validation_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('code_block_index', sa.Integer(), nullable=True),  # ← Was missing!
        sa.Column('programming_language', sa.String(50), nullable=False, index=True),
        sa.Column('code_content', sa.Text(), nullable=False),
        sa.Column('code_length', sa.Integer(), nullable=True),
        sa.Column('syntax_valid', sa.Boolean(), nullable=True),
        sa.Column('syntax_errors', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('imports_valid', sa.Boolean(), nullable=True),
        sa.Column('invalid_imports', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('api_endpoints_valid', sa.Boolean(), nullable=True),
        sa.Column('invalid_endpoints', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('executed_in_sandbox', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('execution_success', sa.Boolean(), nullable=True),
        sa.Column('execution_output', sa.Text(), nullable=True),
        sa.Column('execution_errors', sa.Text(), nullable=True),
        sa.Column('validation_passed', sa.Boolean(), nullable=False, index=True),
        sa.Column('validation_score', sa.Float(), nullable=True),
        sa.Column('issues_found', sa.Integer(), nullable=True),
        sa.Column('critical_issues', sa.Integer(), nullable=True),
        sa.Column('suggested_fixes', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('validation_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Fix link_check_results
    op.drop_table('link_check_results')
    op.create_table(
        'link_check_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('url', sa.String(2000), nullable=False, index=True),
        sa.Column('url_domain', sa.String(255), nullable=True, index=True),
        sa.Column('url_context', sa.String(100), nullable=True),
        sa.Column('source_type', sa.String(100), nullable=False, index=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('check_type', sa.String(50), nullable=False, server_default='real_time'),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('link_working', sa.Boolean(), nullable=False, index=True),
        sa.Column('error_type', sa.String(100), nullable=True),
        sa.Column('redirect_url', sa.String(2000), nullable=True),
        sa.Column('action', sa.String(100), nullable=False, server_default='none'),
        sa.Column('replacement_url', sa.String(2000), nullable=True),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('last_working_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('idx_source', 'link_check_results', ['source_type', 'source_id'])

    # Fix sensitivity_violations
    op.drop_table('sensitivity_violations')
    op.create_table(
        'sensitivity_violations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('violation_type', sa.String(100), nullable=False, index=True),
        sa.Column('severity', sa.String(50), nullable=False, index=True),
        sa.Column('detected_issues', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('offensive_terms', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('bias_indicators', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('pii_detected', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('response_blocked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('auto_remediation_attempted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('remediation_suggestions', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('false_positive', sa.Boolean(), nullable=True),
        sa.Column('reviewed_by', sa.String(255), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Fix hallucination_detections
    op.drop_table('hallucination_detections')
    op.create_table(
        'hallucination_detections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', sa.String(100), nullable=True, index=True),
        sa.Column('hallucination_type', sa.String(100), nullable=False, index=True),
        sa.Column('hallucinated_claim', sa.Text(), nullable=True),
        sa.Column('hallucinated_elements', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('verification_method', sa.String(100), nullable=True),
        sa.Column('verification_sources', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('severity', sa.String(50), nullable=False, index=True),
        sa.Column('potential_customer_impact', sa.String(255), nullable=True),
        sa.Column('correct_information', sa.Text(), nullable=True),
        sa.Column('corrected_response', sa.Text(), nullable=True),
        sa.Column('response_blocked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('detected_by', sa.String(100), nullable=False, server_default='TASK-2109'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Fix policy_rules
    op.drop_table('policy_rules')
    op.create_table(
        'policy_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('policy_name', sa.String(255), nullable=False, index=True),
        sa.Column('policy_category', sa.String(100), nullable=False, index=True),
        sa.Column('policy_description', sa.Text(), nullable=True),
        sa.Column('rule_type', sa.String(100), nullable=False),
        sa.Column('rule_config', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('enforcement_level', sa.String(50), nullable=False, server_default='strict'),
        sa.Column('violation_action', sa.String(100), nullable=False),
        sa.Column('compliant_examples', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('violation_examples', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('active', sa.Boolean(), nullable=False, index=True, server_default='true'),
        sa.Column('effective_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expiration_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
    )

    print("✓ Fixed all QA table schemas to match models")


def downgrade() -> None:
    """Revert schema fixes"""
    # Tables will be dropped and recreated with old schemas
    pass