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

MIGRATION_STATUS = {
    "completed": True,
    "applied_columns": [],
    "failed_columns": [],
    "error_message": None
}

def run_schema_migrations(target_engine):
    """
    Safely inspects existing database schema and applies ALTER TABLE migrations
    for any missing columns added to the SQLAlchemy models.
    Surfaces migration failures to ensure deployment health correctly reflects incomplete schema.
    """
    global MIGRATION_STATUS
    failed_migrations = []
    applied_migrations = []

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
                                applied_migrations.append(f"{table_name}.{col.name}")
                            except Exception as mig_err:
                                # Re-inspect to check if column was added concurrently by another worker
                                re_inspected = {c["name"] for c in inspect(target_engine).get_columns(table_name)}
                                if col.name not in re_inspected:
                                    failed_migrations.append((f"{table_name}.{col.name}", str(mig_err)))

        if failed_migrations:
            MIGRATION_STATUS["completed"] = False
            MIGRATION_STATUS["failed_columns"] = failed_migrations
            MIGRATION_STATUS["error_message"] = f"Failed migrations: {failed_migrations}"
            raise RuntimeError(f"Database schema migration failed on startup: {failed_migrations}")
        else:
            MIGRATION_STATUS["completed"] = True
            MIGRATION_STATUS["applied_columns"] = applied_migrations
    except Exception as e:
        import logging
        logging.getLogger("DatabaseMigration").error(f"Schema migration error: {e}")
        MIGRATION_STATUS["completed"] = False
        MIGRATION_STATUS["error_message"] = str(e)
        raise
