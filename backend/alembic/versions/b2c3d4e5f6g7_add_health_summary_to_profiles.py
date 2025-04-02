"""Add health_summary to profiles

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-04-02 23:58:47.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'  # Reference to the previous migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add health_summary as Text column
    op.add_column('profiles', sa.Column('health_summary', sa.Text(), nullable=True))
    # Add summary_last_updated as DateTime column
    op.add_column('profiles', sa.Column('summary_last_updated', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Drop the columns in reverse order
    op.drop_column('profiles', 'summary_last_updated')
    op.drop_column('profiles', 'health_summary') 