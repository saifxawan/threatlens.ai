"""Pydantic schemas — Logs, Alerts, Predictions, Dashboard"""
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime


# ── Log Schemas ──────────────────────────────────────────────
class LogOut(BaseModel):
    id: int
    timestamp: Optional[datetime]
    source: Optional[str]
    source_ip: Optional[str]
    destination_ip: Optional[str]
    username: Optional[str]
    event_type: Optional[str]
    status_code: Optional[str]
    method: Optional[str]
    path: Optional[str]
    message: Optional[str]
    severity: Optional[str]
    dataset_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class LogStats(BaseModel):
    total: int
    by_severity: Dict[str, int]
    by_source: Dict[str, int]
    recent_24h: int


# ── Alert Schemas ─────────────────────────────────────────────
class AlertOut(BaseModel):
    id: int
    log_id: Optional[int]
    prediction_id: Optional[int]
    title: str
    description: Optional[str]
    severity: Optional[str]
    status: Optional[str]
    assigned_to: Optional[str]
    recommendation: Optional[str]
    source_ip: Optional[str]
    threat_type: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class AlertStatusUpdate(BaseModel):
    status: str
    assigned_to: Optional[str] = None


class AlertStats(BaseModel):
    total: int
    by_severity: Dict[str, int]
    by_status: Dict[str, int]
    by_threat_type: Dict[str, int]


# ── Prediction Schemas ────────────────────────────────────────
class PredictionOut(BaseModel):
    id: int
    log_id: Optional[int]
    model_name: Optional[str]
    prediction: Optional[str]
    anomaly_score: Optional[float]
    risk_score: Optional[float]
    threat_type: Optional[str]
    severity: Optional[str]
    explanation: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Dataset Schemas ───────────────────────────────────────────
class DatasetOut(BaseModel):
    id: int
    file_name: str
    original_name: Optional[str]
    file_type: Optional[str]
    total_rows: int
    processed_rows: int
    upload_status: str
    error_message: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── ModelMetrics Schemas ──────────────────────────────────────
class ModelMetricsOut(BaseModel):
    id: int
    model_name: str
    accuracy: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    false_positive_rate: Optional[float]
    auc_roc: Optional[float]
    training_samples: Optional[int]
    training_date: datetime
    dataset_name: Optional[str]
    is_active: int

    model_config = {"from_attributes": True}


# ── Dashboard Schemas ─────────────────────────────────────────
class DashboardSummary(BaseModel):
    total_logs: int
    threats_detected: int
    critical_alerts: int
    anomaly_rate: float
    active_sources: int
    model_accuracy: Optional[float]
    avg_risk_score: Optional[float]
    logs_last_hour: int
    new_alerts: int
    high_risk_ips: int


class TimeSeriesPoint(BaseModel):
    time: str
    value: int


class ChartData(BaseModel):
    labels: List[str]
    values: List[Any]


# ── Paginated Response ────────────────────────────────────────
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
