import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.orm import sessionmaker

# Locate the database file inside the person_2 directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'agent_storage.db')}"

# Initialize the SQLAlchemy engine and session makers
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TaskModel(Base):
    """SQLAlchemy model representing the persistent tracking table for code audits."""
    __tablename__ = "analysis_tasks"

    task_id = Column(String, primary_key=True, index=True)
    status = Column(String, default="PENDING")
    directory_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    report_file = Column(String, nullable=True)

# Helper function to initialize tables on startup
def init_db():
    Base.metadata.create_all(bind=engine)