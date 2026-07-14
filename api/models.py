from sqlalchemy import Column, Integer, String
from api.database import Base

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True)
    status = Column(String, default="pending")
    primary_language = Column(String, nullable=True)