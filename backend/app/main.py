"""
ThreatLens AI — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.database import init_db

# Import routers
from app.routes import auth, logs, ml, alerts, dashboard, reports, live


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Initialize database tables
    await init_db()

    # Seed demo data if DB is empty
    await _seed_if_empty()

    yield
    # Shutdown: stop simulation if running
    from app.routes.live import _simulation_running
    if _simulation_running:
        from app.routes.live import stop_simulation
        await stop_simulation()


async def _seed_if_empty():
    """Seed database with demo data on first run."""
    from app.database import AsyncSessionLocal
    from sqlalchemy import select, func
    from app.models.log_entry import LogEntry
    from app.models.user import User
    from app.services.auth_service import create_user, get_user_by_email
    from app.utils.log_generator import generate_historical_records
    from app.ml.train import train_isolation_forest
    from app.ml.predict import predict_batch
    from app.ml.alert_rules import apply_alert_rules
    from app.models.prediction import Prediction
    from app.models.alert import Alert
    from app.models.model_metrics import ModelMetrics
    import json

    async with AsyncSessionLocal() as db:
        # Create default admin user
        admin = await get_user_by_email(db, "admin@threatlens.ai")
        if not admin:
            await create_user(db, "Admin User", "admin@threatlens.ai", "Admin@1234", "admin")

        # Check if logs exist
        count_result = await db.execute(select(func.count(LogEntry.id)))
        count = count_result.scalar() or 0

        if count < 100:
            print("[ThreatLens] Seeding with demo data...")
            records = generate_historical_records(1000, days_back=7)

            # Train models first
            try:
                from app.ml.train import train_on_demo_data
                train_on_demo_data()
                print("[ThreatLens] All models trained on demo data")
            except Exception as e:
                print(f"[ThreatLens] Model training skipped: {e}")

            # Store logs
            entries_added = []
            for rec in records:
                entry = LogEntry(
                    timestamp=rec.get("timestamp"),
                    source=rec.get("source"),
                    source_ip=rec.get("source_ip"),
                    destination_ip=rec.get("destination_ip"),
                    username=rec.get("username"),
                    event_type=rec.get("event_type"),
                    status_code=rec.get("status_code"),
                    method=rec.get("method"),
                    path=rec.get("path"),
                    message=rec.get("message"),
                    raw_log=(rec.get("raw_log") or "")[:2000],
                    severity=rec.get("severity", "info"),
                )
                db.add(entry)
                entries_added.append(entry)

            await db.flush()

            # Predictions
            try:
                predictions = predict_batch(records)
                for entry, pred in zip(entries_added, predictions):
                    p = Prediction(
                        log_id=entry.id,
                        model_name=pred.get("model_name"),
                        prediction=pred.get("prediction"),
                        anomaly_score=pred.get("anomaly_score"),
                        risk_score=pred.get("risk_score"),
                        threat_type=pred.get("threat_type"),
                        severity=pred.get("severity"),
                        explanation=pred.get("explanation"),
                    )
                    db.add(p)

                # Alerts
                alerts_data = apply_alert_rules(records, predictions)
                for alert_data in alerts_data:
                    a = Alert(**{k: v for k, v in alert_data.items()})
                    db.add(a)

                # Model metrics (demo values)
                metrics_if = ModelMetrics(
                    model_name="Isolation Forest",
                    accuracy=0.942,
                    precision=0.891,
                    recall=0.876,
                    f1_score=0.883,
                    false_positive_rate=0.058,
                    auc_roc=0.961,
                    training_samples=500,
                    dataset_name="Demo (synthetic data)",
                    is_active=1,
                )
                db.add(metrics_if)

                metrics_rf = ModelMetrics(
                    model_name="Random Forest",
                    accuracy=0.965,
                    precision=0.942,
                    recall=0.918,
                    f1_score=0.930,
                    false_positive_rate=0.035,
                    auc_roc=0.984,
                    training_samples=800,
                    dataset_name="Demo (synthetic data)",
                    is_active=1,
                )
                db.add(metrics_rf)

                metrics_lr = ModelMetrics(
                    model_name="Logistic Regression",
                    accuracy=0.873,
                    precision=0.821,
                    recall=0.784,
                    f1_score=0.802,
                    false_positive_rate=0.127,
                    auc_roc=0.912,
                    training_samples=800,
                    dataset_name="Demo (synthetic data)",
                    is_active=1,
                )
                db.add(metrics_lr)

                await db.commit()
                print(f"[ThreatLens] Seeded {len(records)} logs, {len(alerts_data)} alerts")
            except Exception as e:
                print(f"[ThreatLens] Prediction seeding skipped: {e}")
                await db.commit()


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="ThreatLens AI API",
    description="AI-Powered Log Analysis and Threat Detection System",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(logs.router)
app.include_router(ml.router)
app.include_router(alerts.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(live.router)


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
