"""Alert ORM model"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func
from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(Integer, ForeignKey("log_entries.id"), nullable=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    severity = Column(String(20), index=True)         # informational|low|medium|high|critical
    status = Column(String(50), index=True, default="new")  # new|investigating|resolved|false_positive
    assigned_to = Column(String(100), nullable=True)
    recommendation = Column(Text)
    source_ip = Column(String(50), index=True, nullable=True)
    threat_type = Column(String(100), index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
