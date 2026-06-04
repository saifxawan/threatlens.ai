"""Dataset ORM model"""
from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    original_name = Column(String(255))
    file_type = Column(String(50))   # csv | txt | json | log
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    upload_status = Column(String(50), default="pending")  # pending|processing|completed|failed
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
