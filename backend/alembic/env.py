from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from urllib.parse import urlparse

# Import the Base model and other models
from app.db.database import Base
from app.models.profile_model import Profile
from app.models.pdf_model import PDF
from app.models.biomarker_model import Biomarker

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Get the database URL from environment variable with SQLite as default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vein_diagram.db")

# If using Supabase, modify the URL to use the standard PostgreSQL port
if 'supabase' in DATABASE_URL:
    parsed = urlparse(DATABASE_URL)
    host = parsed.hostname.replace('db.', '')
    DATABASE_URL = f"postgresql://{parsed.username}:{parsed.password}@{host}:5432/{parsed.path[1:]}?sslmode=require"

# Determine if we're using SQLite
is_sqlite = DATABASE_URL.startswith("sqlite")

# Override sqlalchemy.url from alembic.ini with environment variable
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Add compare_type=True to detect column type changes
        compare_type=True,
        # Add compare_server_default=True to detect default value changes
        compare_server_default=True,
        # Add render_as_batch=True for SQLite support of ALTER
        render_as_batch=is_sqlite
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Configure the database connection
    engine_config = config.get_section(config.config_ini_section)
    
    if is_sqlite:
        # SQLite-specific configuration
        engine_config.update({
            'sqlalchemy.url': DATABASE_URL,
            'sqlalchemy.connect_args': {'check_same_thread': False}
        })
    else:
        # PostgreSQL-specific configuration
        engine_config.update({
            'sqlalchemy.url': DATABASE_URL,
            'sqlalchemy.connect_args': {
                'connect_timeout': 30,
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 10,
                'keepalives_count': 5,
                'application_name': 'vein-diagram-alembic'
            }
        })

    connectable = engine_from_config(
        engine_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Add compare_type=True to detect column type changes
            compare_type=True,
            # Add compare_server_default=True to detect default value changes
            compare_server_default=True,
            # Add render_as_batch=True for SQLite support of ALTER
            render_as_batch=is_sqlite,
            # Add transaction_per_migration=True for better error handling
            transaction_per_migration=True,
            # Add include_schemas=True to support schema-based migrations
            include_schemas=True if not is_sqlite else False
        )

        try:
            with context.begin_transaction():
                context.run_migrations()
        except Exception as e:
            # Log the error and re-raise
            import logging
            logging.error(f"Error during migration: {str(e)}")
            raise

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
