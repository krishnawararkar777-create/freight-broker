"""002_multi_tenancy_rls

Revision ID: 002_multi_tenancy_rls
Revises: 001_initial_schema
Create Date: 2026-08-17 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_multi_tenancy_rls'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# All 19 domain tables
DIRECT_SCOPED_TABLES = [
    'organizations',
    'users',
    'customer_policies',
    'shipments',
    'claims',
    'documents',
    'invoices',
    'audit_events'
]

CLAIM_CHILD_TABLES = [
    'claim_facts',
    'claim_requirements',
    'claim_submissions',
    'communications',
    'tasks',
    'recovery_events',
    'fee_events'
]

DOCUMENT_CHILD_TABLES = [
    'document_evidence'
]

REFERENCE_TABLES = [
    'carriers',
    'carrier_rule_sets',
    'carrier_claim_rules'
]

def upgrade() -> None:
    # 1. Enable RLS on all 19 tables
    all_tables = DIRECT_SCOPED_TABLES + CLAIM_CHILD_TABLES + DOCUMENT_CHILD_TABLES + REFERENCE_TABLES
    for table in all_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")

    # 2. RLS Policies for Direct Scoped Tables
    for table in DIRECT_SCOPED_TABLES:
        org_col = 'id' if table == 'organizations' else 'organization_id'
        policy_sql = f"""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policies WHERE tablename = '{table}' AND policyname = 'tenant_isolation_policy_{table}'
                ) THEN
                    CREATE POLICY tenant_isolation_policy_{table} ON {table}
                    FOR ALL TO authenticated
                    USING (
                        {org_col} = COALESCE(
                            NULLIF(current_setting('app.current_org_id', true), ''),
                            (auth.jwt() -> 'app_metadata' ->> 'organization_id')
                        )
                    );
                END IF;
            END $$;
        """
        op.execute(policy_sql)

    # 3. RLS Policies for Claim Child Tables
    for table in CLAIM_CHILD_TABLES:
        policy_sql = f"""
            DO $$ BEGIN
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
            END $$;
        """
        op.execute(policy_sql)

    # 4. RLS Policies for Document Child Tables
    for table in DOCUMENT_CHILD_TABLES:
        policy_sql = f"""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policies WHERE tablename = '{table}' AND policyname = 'tenant_isolation_policy_{table}'
                ) THEN
                    CREATE POLICY tenant_isolation_policy_{table} ON {table}
                    FOR ALL TO authenticated
                    USING (
                        EXISTS (
                            SELECT 1 FROM documents
                            WHERE documents.id = {table}.document_id
                            AND documents.organization_id = COALESCE(
                                NULLIF(current_setting('app.current_org_id', true), ''),
                                (auth.jwt() -> 'app_metadata' ->> 'organization_id')
                            )
                        )
                    );
                END IF;
            END $$;
        """
        op.execute(policy_sql)

    # 5. Shared Reference Tables (Read-Only to All Authenticated Users)
    for table in REFERENCE_TABLES:
        policy_sql = f"""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policies WHERE tablename = '{table}' AND policyname = 'shared_reference_read_policy_{table}'
                ) THEN
                    CREATE POLICY shared_reference_read_policy_{table} ON {table}
                    FOR SELECT TO authenticated
                    USING (true);
                END IF;
            END $$;
        """
        op.execute(policy_sql)

    # 6. Supabase Storage Bucket Policy for claim-documents
    storage_policy_sql = """
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'storage' AND table_name = 'objects') THEN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policies WHERE tablename = 'objects' AND policyname = 'tenant_storage_claim_documents'
                ) THEN
                    CREATE POLICY tenant_storage_claim_documents ON storage.objects
                    FOR ALL TO authenticated
                    USING (
                        bucket_id = 'claim-documents' AND
                        (storage.foldername(name))[1] = COALESCE(
                            NULLIF(current_setting('app.current_org_id', true), ''),
                            (auth.jwt() -> 'app_metadata' ->> 'organization_id')
                        )
                    );
                END IF;
            END IF;
        END $$;
    """
    op.execute(storage_policy_sql)

def downgrade() -> None:
    all_tables = DIRECT_SCOPED_TABLES + CLAIM_CHILD_TABLES + DOCUMENT_CHILD_TABLES + REFERENCE_TABLES
    for table in all_tables:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
