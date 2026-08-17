"""004_add_lawsuit_deadline

Revision ID: 004_add_lawsuit_deadline
Revises: 003_carrier_responses
Create Date: 2026-08-18 00:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004_add_lawsuit_deadline'
down_revision: Union[str, None] = '003_carrier_responses'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column(
        'claims',
        sa.Column('lawsuit_deadline_at', sa.DateTime(timezone=True), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('claims', 'lawsuit_deadline_at')
