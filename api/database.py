import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://admin:password@localhost:5433/submissions_db"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def run_schema_migrations(target_engine):
    """
    Safely inspects existing database schema and applies ALTER TABLE migrations
    for any missing columns added to the SQLAlchemy models.
    Compatible with PostgreSQL and SQLite.
    """
    try:
        inspector = inspect(target_engine)
        existing_tables = inspector.get_table_names()
        
        from api.models import Base as ModelsBase
        with target_engine.connect() as conn:
            for table_name, table in ModelsBase.metadata.tables.items():
                if table_name in existing_tables:
                    existing_cols = {c["name"] for c in inspector.get_columns(table_name)}
                    for col in table.columns:
                        if col.name not in existing_cols:
                            col_type = col.type.compile(target_engine.dialect)
                            stmt = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}"
                            try:
                                conn.execute(text(stmt))
                                conn.commit()
                            except Exception:
                                pass
    except Exception as e:
        import logging
        logging.getLogger("DatabaseMigration").warning(f"Schema migration skipped or deferred: {e}")
