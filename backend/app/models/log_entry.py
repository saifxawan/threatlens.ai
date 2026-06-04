"""LogEntry ORM model"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, func
from app.database import Base


class LogEntry(Base):
    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), index=True)
    source = Column(String(100), index=True)          # syslog, apache, hdfs, csv, live
    source_ip = Column(String(50), index=True)
    destination_ip = Column(String(50))
    username = Column(String(100), index=True)
    event_type = Column(String(100), index=True)
    status_code = Column(String(20))
    method = Column(String(20))
    path = Column(Text)
    message = Column(Text)
    raw_log = Column(Text)
    parsed_fields = Column(Text)                       # JSON string
    severity = Column(String(20), index=True, default="info")
    dataset_id = Column(Integer, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
