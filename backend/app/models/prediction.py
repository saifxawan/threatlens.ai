"""Prediction ORM model"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, func
from app.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(Integer, ForeignKey("log_entries.id"), index=True)
    model_name = Column(String(100))
    model_type = Column(String(100), nullable=True)
    prediction = Column(String(50))       # normal | anomaly | attack_type
    confidence = Column(Float, nullable=True)
    anomaly_score = Column(Float)
    risk_score = Column(Float, index=True)
    threat_type = Column(String(100), index=True)
    severity = Column(String(50), index=True)
    explanation = Column(Text)            # JSON: feature contributions
    model_votes = Column(Text, nullable=True) # JSON: ensemble votes dictionary
    created_at = Column(DateTime(timezone=True), server_default=func.now())
