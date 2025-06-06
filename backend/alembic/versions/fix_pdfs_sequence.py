"""fix_pdfs_sequence

Revision ID: fix_pdfs_sequence
Revises: c1d2e3f4g5h6
Create Date: 2025-04-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import os

# revision identifiers, used by Alembic.
revision = 'fix_pdfs_sequence'
down_revision = 'c1d2e3f4g5h6'
branch_labels = None
depends_on = None


def upgrade():
    # Get database URL to determine if SQLite or PostgreSQL
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vein_diagram.db")
    
    # SQLite specific sequence fix
    if DATABASE_URL.startswith("sqlite"):
        conn = op.get_bind()
        conn.execute(text("UPDATE sqlite_sequence SET seq = (SELECT MAX(id) FROM pdfs) WHERE name = 'pdfs'"))
    else:
        # PostgreSQL specific sequence fix
        op.execute("""
        DO $$
        DECLARE
            max_id INTEGER;
        BEGIN
            -- Get the maximum id from the pdfs table
            SELECT COALESCE(MAX(id), 0) INTO max_id FROM pdfs;
            
            -- Drop the existing sequence
            EXECUTE 'DROP SEQUENCE IF EXISTS pdfs_id_seq CASCADE';
            
            -- Create a new sequence starting from max_id + 1
            EXECUTE 'CREATE SEQUENCE pdfs_id_seq START WITH ' || (max_id + 1);
            
            -- Set the sequence as the default for the id column
            EXECUTE 'ALTER TABLE pdfs ALTER COLUMN id SET DEFAULT nextval(''pdfs_id_seq'')';
            
            -- Set the sequence ownership to the pdfs.id column
            EXECUTE 'ALTER SEQUENCE pdfs_id_seq OWNED BY pdfs.id';
            
            RAISE NOTICE 'Reset pdfs_id_seq to start from %', (max_id + 1);
        END $$;
        """)


def downgrade():
    # No downgrade needed for sequence reset
    pass 