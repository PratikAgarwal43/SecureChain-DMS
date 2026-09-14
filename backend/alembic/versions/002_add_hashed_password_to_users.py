"""002_add_hashed_password_to_users

Revision ID: 002_add_hashed_password
Revises: 001_initial_schema
Create Date: 2026-09-11 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_hashed_password'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('hashed_password', sa.String(length=255), server_default='', nullable=False)
    )


def downgrade() -> None:
    op.drop_column('users', 'hashed_password')
