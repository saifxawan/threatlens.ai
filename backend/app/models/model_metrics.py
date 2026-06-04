"""ModelMetrics ORM model"""
from sqlalchemy import Column, Integer, String, Float, DateTime, func
from app.database import Base


class ModelMetrics(Base):
    __tablename__ = "model_metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False, index=True)
    model_type = Column(String(100), nullable=True)
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    false_positive_rate = Column(Float, nullable=True)
    false_negative_rate = Column(Float, nullable=True)
    auc_roc = Column(Float, nullable=True)
    training_samples = Column(Integer, nullable=True)
    training_date = Column(DateTime(timezone=True), server_default=func.now())
    dataset_name = Column(String(255), nullable=True)
    is_active = Column(Integer, default=1)   # 1 = current active model
