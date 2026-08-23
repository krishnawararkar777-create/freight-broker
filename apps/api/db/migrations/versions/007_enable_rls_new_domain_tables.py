"""007_enable_rls_new_domain_tables

Revision ID: 007_enable_rls_new_domain_tables
Revises: 006_shipper_facilities_and_approvals
Create Date: 2026-08-23 11:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '007_enable_rls_new_domain_tables'
down_revision: Union[str, None] = '006_shipper_facilities_and_approvals'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DIRECT_SCOPED_NEW_TABLES = ['facilities', 'api_telemetry']
CLAIM_CHILD_NEW_TABLES = ['salvage_records', 'legal_escalation_records']
REFERENCE_NEW_TABLES = ['carrier_risk_facts', 'carrier_contract_clauses']
ALL_NEW_TABLES = DIRECT_SCOPED_NEW_TABLES + CLAIM_CHILD_NEW_TABLES + REFERENCE_NEW_TABLES

def upgrade() -> None:
    for table in ALL_NEW_TABLES:
        op.execute(f"ALTER TABLE IF EXISTS {table} ENABLE ROW LEVEL SECURITY;")

    for table in DIRECT_SCOPED_NEW_TABLES:
        policy_sql = f"""
            DO $$ BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '{table}') THEN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_policies WHERE tablename = '{table}' AND policyname = 'tenant_isolation_policy_{table}'
                    ) THEN
                        CREATE POLICY tenant_isolation_policy_{table} ON {table}
                        FOR ALL TO authenticated
                        USING (
                            organization_id = COALESCE(
                                NULLIF(current_setting('app.current_org_id', true), ''),
                                (auth.jwt() -> 'app_metadata' ->> 'organization_id')
                            )
                        );
                    END IF;
                END IF;
            END $$;
        """
        op.execute(policy_sql)

    for table in CLAIM_CHILD_NEW_TABLES:
        policy_sql = f"""
            DO $$ BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '{table}') THEN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_policies WHERE tablename = '{table}' AND policyname = 'tenant_isolation_policy_{table}'
                    ) THEN
                        CREATE POLICY tenant_isolation_policy_{table} ON {table}
                        FOR ALL TO authenticated
                        USING (
                            EXISTS (
                                SELECT 1 FROM claims
                                WHERE claims.id = {table}.claim_id
                                AND claims.organization_id = COALESCE(
                                    NULLIF(current_setting('app.current_org_id', true), ''),
                                    (auth.jwt() -> 'app_metadata' ->> 'organization_id')
                                )
                            )
                        );
                    END IF;
                END IF;
            END $$;
        """
        op.execute(policy_sql)

    for table in REFERENCE_NEW_TABLES:
        policy_sql = f"""
            DO $$ BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '{table}') THEN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_policies WHERE tablename = '{table}' AND policyname = 'shared_reference_read_policy_{table}'
                    ) THEN
                        CREATE POLICY shared_reference_read_policy_{table} ON {table}
                        FOR SELECT TO authenticated
                        USING (true);
                    END IF;
                END IF;
            END $$;
        """
        op.execute(policy_sql)

def downgrade() -> None:
    for table in ALL_NEW_TABLES:
        op.execute(f"ALTER TABLE IF EXISTS {table} DISABLE ROW LEVEL SECURITY;")
