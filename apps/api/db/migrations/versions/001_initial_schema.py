"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-16 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. organizations
    op.create_table(
        'organizations',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=32), server_default='broker'),
        sa.Column('status', sa.String(length=32), server_default='active'),
        sa.Column('timezone', sa.String(length=64), server_default='America/New_York'),
        sa.Column('currency', sa.String(length=3), server_default='USD'),
        sa.Column('contingency_rate', sa.Float(), server_default='0.20'),
        sa.Column('high_value_threshold', sa.Float(), server_default='5000.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )

    # 2. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('organization_id', sa.String(length=64), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('role', sa.String(length=64), server_default='Claims Manager'),
        sa.Column('status', sa.String(length=32), server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_users_organization_id', 'users', ['organization_id'])
    op.create_index('ix_users_email', 'users', ['email'])

    # 3. customer_policies
    op.create_table(
        'customer_policies',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('organization_id', sa.String(length=64), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('high_value_threshold', sa.Float(), server_default='5000.0'),
        sa.Column('approval_policy_version', sa.String(length=32), server_default='v1.0'),
        sa.Column('contingency_rate', sa.Float(), server_default='0.20'),
        sa.Column('communication_policy', sa.JSON(), nullable=True),
        sa.Column('follow_up_policy', sa.JSON(), nullable=True),
        sa.Column('timezone', sa.String(length=64), server_default='America/New_York'),
        sa.Column('effective_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('ix_customer_policies_organization_id', 'customer_policies', ['organization_id'])

    # 4. carriers
    op.create_table(
        'carriers',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('canonical_name', sa.String(length=255), nullable=False),
        sa.Column('aliases', sa.JSON(), nullable=True),
        sa.Column('mc_number', sa.String(length=64), nullable=True),
        sa.Column('contact_channels', sa.JSON(), nullable=True),
        sa.Column('active', sa.Boolean(), server_default=sa.text('true'))
    )
    op.create_index('ix_carriers_canonical_name', 'carriers', ['canonical_name'])
    op.create_index('ix_carriers_mc_number', 'carriers', ['mc_number'])

    # 5. carrier_rule_sets
    op.create_table(
        'carrier_rule_sets',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('carrier_id', sa.String(length=64), sa.ForeignKey('carriers.id'), nullable=False),
        sa.Column('version', sa.String(length=32), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rule_status', sa.String(length=32), server_default='active'),
        sa.Column('source_reference', sa.Text(), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_by', sa.String(length=64), nullable=True)
    )
    op.create_index('ix_carrier_rule_sets_carrier_id', 'carrier_rule_sets', ['carrier_id'])

    # 6. carrier_claim_rules
    op.create_table(
        'carrier_claim_rules',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('carrier_rule_set_id', sa.String(length=64), sa.ForeignKey('carrier_rule_sets.id'), nullable=False),
        sa.Column('claim_type', sa.String(length=64), server_default='Cargo Damage'),
        sa.Column('filing_window_type', sa.String(length=64), server_default='Carmack'),
        sa.Column('filing_window_value', sa.Integer(), server_default='9'),
        sa.Column('filing_window_unit', sa.String(length=32), server_default='months'),
        sa.Column('required_document_type', sa.JSON(), nullable=True),
        sa.Column('submission_channel', sa.String(length=64), server_default='email'),
        sa.Column('special_rule_json', sa.JSON(), nullable=True)
    )
    op.create_index('ix_carrier_claim_rules_set_id', 'carrier_claim_rules', ['carrier_rule_set_id'])

    # 7. shipments
    op.create_table(
        'shipments',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('organization_id', sa.String(length=64), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('external_reference', sa.String(length=128), nullable=False),
        sa.Column('bol_number', sa.String(length=128), nullable=False),
        sa.Column('carrier_id', sa.String(length=64), sa.ForeignKey('carriers.id'), nullable=False),
        sa.Column('shipper_name', sa.String(length=255), nullable=True),
        sa.Column('consignee_name', sa.String(length=255), nullable=True),
        sa.Column('origin', sa.String(length=255), nullable=True),
        sa.Column('destination', sa.String(length=255), nullable=True),
        sa.Column('pickup_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivery_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('declared_value', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=3), server_default='USD'),
        sa.Column('commodity', sa.String(length=255), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('ix_shipments_org_id', 'shipments', ['organization_id'])
    op.create_index('ix_shipments_ext_ref', 'shipments', ['external_reference'])
    op.create_index('ix_shipments_bol', 'shipments', ['bol_number'])

    # 8. claims
    op.create_table(
        'claims',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('organization_id', sa.String(length=64), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('shipment_id', sa.String(length=64), sa.ForeignKey('shipments.id'), nullable=False),
        sa.Column('claim_type', sa.String(length=64), server_default='Cargo Damage'),
        sa.Column('status', sa.String(length=64), server_default='DRAFT'),
        sa.Column('lifecycle_version', sa.String(length=32), server_default='v1.0'),
        sa.Column('claimed_amount', sa.Float(), server_default='0.0'),
        sa.Column('currency', sa.String(length=3), server_default='USD'),
        sa.Column('approved_claim_amount', sa.Float(), nullable=True),
        sa.Column('deadline_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('concealed_deadline_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('human_threshold_triggered', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('elevated_approval_acknowledged', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('is_approved_by_human', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('approved_by_user_id', sa.String(length=64), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('reimbursement_mode', sa.String(length=64), server_default='CHECK'),
        sa.Column('owner_user_id', sa.String(length=64), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_claims_org_id', 'claims', ['organization_id'])
    op.create_index('ix_claims_status', 'claims', ['status'])

    # 9. documents
    op.create_table(
        'documents',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('organization_id', sa.String(length=64), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('claim_id', sa.String(length=64), sa.ForeignKey('claims.id'), nullable=False),
        sa.Column('shipment_id', sa.String(length=64), sa.ForeignKey('shipments.id'), nullable=True),
        sa.Column('document_type', sa.String(length=64), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=128), server_default='application/pdf'),
        sa.Column('object_key', sa.Text(), nullable=False),
        sa.Column('sha256', sa.String(length=64), nullable=False),
        sa.Column('page_count', sa.Integer(), server_default='1'),
        sa.Column('extraction_status', sa.String(length=32), server_default='uploaded'),
        sa.Column('parser_version', sa.String(length=32), server_default='v1.0'),
        sa.Column('uploaded_by', sa.String(length=64), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('ix_documents_claim_id', 'documents', ['claim_id'])
    op.create_index('ix_documents_sha256', 'documents', ['sha256'])

    # 10. document_evidence
    op.create_table(
        'document_evidence',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('document_id', sa.String(length=64), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('page_number', sa.Integer(), server_default='1'),
        sa.Column('bbox_json', sa.JSON(), nullable=True),
        sa.Column('source_text', sa.Text(), nullable=True),
        sa.Column('field_name', sa.String(length=128), nullable=False),
        sa.Column('normalized_value_json', sa.JSON(), nullable=True),
        sa.Column('extraction_method', sa.String(length=64), server_default='LocalPdfParser'),
        sa.Column('model_version', sa.String(length=32), server_default='v1.0'),
        sa.Column('confidence', sa.Float(), server_default='1.0')
    )
    op.create_index('ix_document_evidence_doc_id', 'document_evidence', ['document_id'])

    # 11. claim_facts
    op.create_table(
        'claim_facts',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('claim_id', sa.String(length=64), sa.ForeignKey('claims.id'), nullable=False),
        sa.Column('field_name', sa.String(length=128), nullable=False),
        sa.Column('value_json', sa.JSON(), nullable=True),
        sa.Column('source_document_id', sa.String(length=64), sa.ForeignKey('documents.id'), nullable=True),
        sa.Column('source_location', sa.String(length=255), nullable=True),
        sa.Column('confidence', sa.Float(), server_default='1.0'),
        sa.Column('verification_status', sa.String(length=32), server_default='extracted'),
        sa.Column('original_value_json', sa.JSON(), nullable=True),
        sa.Column('edited_by_user_id', sa.String(length=64), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('edit_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('ix_claim_facts_claim_id', 'claim_facts', ['claim_id'])

    # 12. claim_requirements
    op.create_table(
        'claim_requirements',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('claim_id', sa.String(length=64), sa.ForeignKey('claims.id'), nullable=False),
        sa.Column('requirement_type', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('source_rule_id', sa.String(length=64), sa.ForeignKey('carrier_claim_rules.id'), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='missing'),
        sa.Column('evidence_document_id', sa.String(length=64), sa.ForeignKey('documents.id'), nullable=True)
    )
    op.create_index('ix_claim_requirements_claim_id', 'claim_requirements', ['claim_id'])

    # 13. claim_submissions
    op.create_table(
        'claim_submissions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('claim_id', sa.String(length=64), sa.ForeignKey('claims.id'), nullable=False),
        sa.Column('submission_channel', sa.String(length=64), server_default='email'),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('external_reference', sa.String(length=128), nullable=True),
        sa.Column('payload_hash', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='SUBMITTED'),
        sa.Column('submitted_by', sa.String(length=64), sa.ForeignKey('users.id'), nullable=False)
    )
    op.create_index('ix_claim_submissions_claim_id', 'claim_submissions', ['claim_id'])

    # 14. communications
    op.create_table(
        'communications',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('claim_id', sa.String(length=64), sa.ForeignKey('claims.id'), nullable=False),
        sa.Column('channel', sa.String(length=32), server_default='email'),
        sa.Column('direction', sa.String(length=32), server_default='outbound'),
        sa.Column('sender', sa.String(length=255), nullable=False),
        sa.Column('recipient', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.Text(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('draft_status', sa.String(length=32), server_default='draft'),
        sa.Column('approved_by', sa.String(length=64), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_document_id', sa.String(length=64), sa.ForeignKey('documents.id'), nullable=True)
    )
    op.create_index('ix_communications_claim_id', 'communications', ['claim_id'])

    # 15. tasks
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('claim_id', sa.String(length=64), sa.ForeignKey('claims.id'), nullable=False),
        sa.Column('type', sa.String(length=64), nullable=False),
        sa.Column('owner_user_id', sa.String(length=64), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='pending'),
        sa.Column('priority', sa.String(length=32), server_default='normal'),
        sa.Column('created_by', sa.String(length=64), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_tasks_claim_id', 'tasks', ['claim_id'])

    # 16. recovery_events
    op.create_table(
        'recovery_events',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('claim_id', sa.String(length=64), sa.ForeignKey('claims.id'), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), server_default='USD'),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('payment_reference', sa.String(length=128), nullable=True),
        sa.Column('payer', sa.String(length=255), nullable=True),
        sa.Column('evidence_document_id', sa.String(length=64), sa.ForeignKey('documents.id'), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='recorded'),
        sa.Column('created_by', sa.String(length=64), sa.ForeignKey('users.id'), nullable=False)
    )
    op.create_index('ix_recovery_events_claim_id', 'recovery_events', ['claim_id'])

    # 17. fee_events
    op.create_table(
        'fee_events',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('claim_id', sa.String(length=64), sa.ForeignKey('claims.id'), nullable=False),
        sa.Column('recovery_event_id', sa.String(length=64), sa.ForeignKey('recovery_events.id'), nullable=False),
        sa.Column('eligible_amount', sa.Float(), nullable=False),
        sa.Column('contingency_rate', sa.Float(), server_default='0.20'),
        sa.Column('fee_amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), server_default='USD'),
        sa.Column('status', sa.String(length=32), server_default='unbilled'),
        sa.Column('invoice_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('ix_fee_events_claim_id', 'fee_events', ['claim_id'])

    # 18. invoices
    op.create_table(
        'invoices',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('organization_id', sa.String(length=64), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('invoice_number', sa.String(length=64), nullable=False, unique=True),
        sa.Column('status', sa.String(length=32), server_default='draft'),
        sa.Column('issue_date', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('currency', sa.String(length=3), server_default='USD'),
        sa.Column('subtotal', sa.Float(), nullable=False),
        sa.Column('tax', sa.Float(), server_default='0.0'),
        sa.Column('total', sa.Float(), nullable=False)
    )
    op.create_index('ix_invoices_organization_id', 'invoices', ['organization_id'])

    # 19. audit_events
    op.create_table(
        'audit_events',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('organization_id', sa.String(length=64), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('actor_type', sa.String(length=32), nullable=False),
        sa.Column('actor_id', sa.String(length=255), nullable=False),
        sa.Column('entity_type', sa.String(length=64), nullable=False),
        sa.Column('entity_id', sa.String(length=64), nullable=False),
        sa.Column('action', sa.String(length=128), nullable=False),
        sa.Column('before_json', sa.JSON(), nullable=True),
        sa.Column('after_json', sa.JSON(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'))
    )
    op.create_index('ix_audit_events_organization_id', 'audit_events', ['organization_id'])


def downgrade() -> None:
    op.drop_table('audit_events')
    op.drop_table('invoices')
    op.drop_table('fee_events')
    op.drop_table('recovery_events')
    op.drop_table('tasks')
    op.drop_table('communications')
    op.drop_table('claim_submissions')
    op.drop_table('claim_requirements')
    op.drop_table('claim_facts')
    op.drop_table('document_evidence')
    op.drop_table('documents')
    op.drop_table('claims')
    op.drop_table('shipments')
    op.drop_table('carrier_claim_rules')
    op.drop_table('carrier_rule_sets')
    op.drop_table('carriers')
    op.drop_table('customer_policies')
    op.drop_table('users')
    op.drop_table('organizations')
