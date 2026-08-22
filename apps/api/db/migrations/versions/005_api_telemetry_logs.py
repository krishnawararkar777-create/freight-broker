"""add api_telemetry_logs table

Revision ID: 005_api_telemetry_logs
Revises: 004_add_lawsuit_deadline
Create Date: 2026-08-22 17:42:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_api_telemetry_logs'
down_revision = '004_add_lawsuit_deadline'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'api_telemetry_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=True),
        sa.Column('endpoint_path', sa.String(length=255), nullable=False),
        sa.Column('http_method', sa.String(length=10), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('latency_ms', sa.Float(), nullable=False),
        sa.Column('request_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('response_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_api_telemetry_logs_organization_id', 'api_telemetry_logs', ['organization_id'], unique=False)
    op.create_index('ix_api_telemetry_logs_endpoint_path', 'api_telemetry_logs', ['endpoint_path'], unique=False)
    op.create_index('ix_api_telemetry_logs_status_code', 'api_telemetry_logs', ['status_code'], unique=False)
    op.create_index('ix_api_telemetry_logs_created_at', 'api_telemetry_logs', ['created_at'], unique=False)


def downgrade():
    op.drop_index('ix_api_telemetry_logs_created_at', table_name='api_telemetry_logs')
    op.drop_index('ix_api_telemetry_logs_status_code', table_name='api_telemetry_logs')
    op.drop_index('ix_api_telemetry_logs_endpoint_path', table_name='api_telemetry_logs')
    op.drop_index('ix_api_telemetry_logs_organization_id', table_name='api_telemetry_logs')
    op.drop_table('api_telemetry_logs')
