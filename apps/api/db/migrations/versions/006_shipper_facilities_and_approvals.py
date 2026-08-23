"""add facilities table and shipper columns

Revision ID: 006_shipper_facilities_and_approvals
Revises: 005_api_telemetry_logs
Create Date: 2026-08-23 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '006_shipper_facilities_and_approvals'
down_revision = '005_api_telemetry_logs'
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if 'facilities' not in insp.get_table_names():
        op.create_table(
            'facilities',
            sa.Column('id', sa.String(length=64), nullable=False),
            sa.Column('organization_id', sa.String(length=64), nullable=False),
            sa.Column('facility_code', sa.String(length=64), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('facility_type', sa.String(length=64), server_default='MANUFACTURING_PLANT', nullable=False),
            sa.Column('address', sa.String(length=255), nullable=True),
            sa.Column('city', sa.String(length=128), nullable=True),
            sa.Column('state', sa.String(length=64), nullable=True),
            sa.Column('contact_name', sa.String(length=128), nullable=True),
            sa.Column('contact_email', sa.String(length=128), nullable=True),
            sa.Column('active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_facilities_organization_id', 'facilities', ['organization_id'], unique=False)
        op.create_index('ix_facilities_facility_code', 'facilities', ['facility_code'], unique=False)

def downgrade():
    op.drop_index('ix_facilities_facility_code', table_name='facilities')
    op.drop_index('ix_facilities_organization_id', table_name='facilities')
    op.drop_table('facilities')
