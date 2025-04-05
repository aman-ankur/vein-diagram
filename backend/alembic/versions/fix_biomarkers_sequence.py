"""fix_biomarkers_sequence

Revision ID: fix_biomarkers_sequence
Revises: fix_pdfs_sequence
Create Date: 2025-04-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import os

# revision identifiers, used by Alembic.
revision = 'fix_biomarkers_sequence'
down_revision = 'fix_pdfs_sequence'
branch_labels = None
depends_on = None


def upgrade():
    # Get database URL to determine if SQLite or PostgreSQL
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vein_diagram.db")
    
    # SQLite specific sequence fix
    if DATABASE_URL.startswith("sqlite"):
        conn = op.get_bind()
        conn.execute(text("UPDATE sqlite_sequence SET seq = (SELECT MAX(id) FROM biomarkers) WHERE name = 'biomarkers'"))
        conn.execute(text("UPDATE sqlite_sequence SET seq = (SELECT MAX(id) FROM biomarker_dictionary) WHERE name = 'biomarker_dictionary'"))
    else:
        # PostgreSQL specific sequence fix
        op.execute("""
        DO $$
        DECLARE
            max_id INTEGER;
        BEGIN
            -- Get the maximum id from the biomarkers table
            SELECT COALESCE(MAX(id), 0) INTO max_id FROM biomarkers;
            
            -- Drop the existing sequence
            EXECUTE 'DROP SEQUENCE IF EXISTS biomarkers_id_seq CASCADE';
            
            -- Create a new sequence starting from max_id + 1
            EXECUTE 'CREATE SEQUENCE biomarkers_id_seq START WITH ' || (max_id + 1);
            
            -- Set the sequence as the default for the id column
            EXECUTE 'ALTER TABLE biomarkers ALTER COLUMN id SET DEFAULT nextval(''biomarkers_id_seq'')';
            
            -- Set the sequence ownership to the biomarkers.id column
            EXECUTE 'ALTER SEQUENCE biomarkers_id_seq OWNED BY biomarkers.id';
            
            RAISE NOTICE 'Reset biomarkers_id_seq to start from %', (max_id + 1);
            
            -- Also fix the biomarker_dictionary sequence
            SELECT COALESCE(MAX(id), 0) INTO max_id FROM biomarker_dictionary;
            
            -- Drop the existing sequence
            EXECUTE 'DROP SEQUENCE IF EXISTS biomarker_dictionary_id_seq CASCADE';
            
            -- Create a new sequence starting from max_id + 1
            EXECUTE 'CREATE SEQUENCE biomarker_dictionary_id_seq START WITH ' || (max_id + 1);
            
            -- Set the sequence as the default for the id column
            EXECUTE 'ALTER TABLE biomarker_dictionary ALTER COLUMN id SET DEFAULT nextval(''biomarker_dictionary_id_seq'')';
            
            -- Set the sequence ownership to the biomarker_dictionary.id column
            EXECUTE 'ALTER SEQUENCE biomarker_dictionary_id_seq OWNED BY biomarker_dictionary.id';
            
            RAISE NOTICE 'Reset biomarker_dictionary_id_seq to start from %', (max_id + 1);
        END $$;
        """)


def downgrade():
    # No downgrade needed for sequence reset
    pass 