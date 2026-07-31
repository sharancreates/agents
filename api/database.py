from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Hardcoded for local Docker dev as discussed
SQLALCHEMY_DATABASE_URL = "postgresql://admin:password@localhost:5433/submissions_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()