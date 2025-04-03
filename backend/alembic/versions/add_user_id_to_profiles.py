"""add_user_id_to_profiles

Revision ID: c1d2e3f4g5h6
Revises: b2c3d4e5f6g7
Create Date: 2025-04-03 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1d2e3f4g5h6'
down_revision = 'b2c3d4e5f6g7'
branch_labels = None
depends_on = None


def upgrade():
    # Add user_id column to profiles table
    op.add_column('profiles', sa.Column('user_id', sa.String(36), nullable=True))
    
    # Add an index for faster lookups by user_id
    op.create_index(op.f('ix_profiles_user_id'), 'profiles', ['user_id'], unique=False)


def downgrade():
    # Remove the index
    op.drop_index(op.f('ix_profiles_user_id'), table_name='profiles')
    
    # Remove the user_id column
    op.drop_column('profiles', 'user_id') 