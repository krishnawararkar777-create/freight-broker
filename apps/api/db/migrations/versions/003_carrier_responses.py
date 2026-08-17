"""003_carrier_responses

Revision ID: 003_carrier_responses
Revises: 002_multi_tenancy_rls
Create Date: 2026-08-17 18:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_carrier_responses'
down_revision: Union[str, None] = '002_multi_tenancy_rls'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'carrier_responses',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('claim_id', sa.String(length=64), sa.ForeignKey('claims.id'), nullable=False, index=True),
        sa.Column('document_id', sa.String(length=64), sa.ForeignKey('documents.id'), nullable=False, index=True),
        sa.Column('decision_type', sa.String(length=64), nullable=False),
        sa.Column('carrier_claim_reference', sa.String(length=128), nullable=True),
        sa.Column('offer_amount', sa.Float(), default=0.0),
        sa.Column('disputed_amount', sa.Float(), default=0.0),
        sa.Column('denial_reasons_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    # Enable RLS on carrier_responses
    op.execute("ALTER TABLE carrier_responses ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies WHERE tablename = 'carrier_responses' AND policyname = 'tenant_isolation_policy_carrier_responses'
            ) THEN
                CREATE POLICY tenant_isolation_policy_carrier_responses ON carrier_responses
                FOR ALL TO authenticated
                USING (
                    EXISTS (
                        SELECT 1 FROM claims
                        WHERE claims.id = carrier_responses.claim_id
                        AND claims.organization_id = COALESCE(
                            NULLIF(current_setting('app.current_org_id', true), ''),
                            (auth.jwt() -> 'app_metadata' ->> 'organization_id')
                        )
                    )
                );
            END IF;
        END $$;
    """)

def downgrade() -> None:
    op.drop_table('carrier_responses')
