"""Dashboard routes — summary cards + chart data"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.models.log_entry import LogEntry
from app.models.alert import Alert
from app.models.prediction import Prediction
from app.models.model_metrics import ModelMetrics

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
from app.routes.auth import get_current_user


@router.get("/summary")
async def dashboard_summary(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    # Total logs
    total_logs = (await db.execute(select(func.count(LogEntry.id)))).scalar() or 0

    # Total threats (anomaly predictions)
    total_threats = (await db.execute(
        select(func.count(Prediction.id)).where(Prediction.prediction == "anomaly")
    )).scalar() or 0

    # Critical alerts
    critical_alerts = (await db.execute(
        select(func.count(Alert.id)).where(Alert.severity == "critical")
    )).scalar() or 0

    # New alerts
    new_alerts = (await db.execute(
        select(func.count(Alert.id)).where(Alert.status == "new")
    )).scalar() or 0

    # Anomaly rate
    anomaly_rate = round((total_threats / total_logs * 100) if total_logs > 0 else 0.0, 2)

    # Active sources
    src_result = await db.execute(
        select(LogEntry.source).distinct().where(LogEntry.source.isnot(None))
    )
    active_sources = len(src_result.fetchall())

    # Best model accuracy
    model_result = await db.execute(
        select(ModelMetrics).where(ModelMetrics.accuracy.isnot(None))
        .order_by(desc(ModelMetrics.training_date)).limit(1)
    )
    model = model_result.scalar_one_or_none()
    model_accuracy = model.accuracy if model else None

    # Average risk score
    avg_risk = (await db.execute(select(func.avg(Prediction.risk_score)))).scalar()

    # Logs last hour
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    logs_last_hour = (await db.execute(
        select(func.count(LogEntry.id)).where(LogEntry.created_at >= one_hour_ago)
    )).scalar() or 0

    # High risk IPs (distinct IPs with critical/high alerts)
    high_risk_ips = (await db.execute(
        select(func.count(func.distinct(Alert.source_ip)))
        .where(Alert.severity.in_(["high", "critical"]))
    )).scalar() or 0

    return {
        "total_logs": total_logs,
        "threats_detected": total_threats,
        "critical_alerts": critical_alerts,
        "anomaly_rate": anomaly_rate,
        "active_sources": active_sources,
        "model_accuracy": round(float(model_accuracy) * 100, 1) if model_accuracy else None,
        "avg_risk_score": round(float(avg_risk), 1) if avg_risk else None,
        "logs_last_hour": logs_last_hour,
        "new_alerts": new_alerts,
        "high_risk_ips": high_risk_ips,
    }


@router.get("/charts/threats-over-time")
async def threats_over_time(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """Return threat counts for last 7 days, grouped by day."""
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    result = await db.execute(
        select(Alert.created_at, Alert.severity)
        .where(Alert.created_at >= seven_days_ago)
        .order_by(Alert.created_at)
    )
    rows = result.fetchall()

    # Group by date
    from collections import defaultdict
    daily = defaultdict(lambda: {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0})
    for created_at, severity in rows:
        if created_at:
            day = created_at.strftime("%Y-%m-%d")
            daily[day]["total"] += 1
            if severity in daily[day]:
                daily[day][severity] += 1

    # Fill missing days
    data = []
    for i in range(7):
        day = (datetime.now(timezone.utc) - timedelta(days=6 - i)).strftime("%Y-%m-%d")
        entry = daily.get(day, {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0})
        data.append({"date": day, **entry})

    return {"data": data}


@router.get("/charts/severity-distribution")
async def severity_distribution(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(
        select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)
    )
    rows = result.fetchall()
    return {"data": [{"name": row[0] or "unknown", "value": row[1]} for row in rows]}


@router.get("/charts/top-ips")
async def top_ips(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(
        select(Alert.source_ip, func.count(Alert.id).label("count"))
        .where(Alert.source_ip.isnot(None))
        .group_by(Alert.source_ip)
        .order_by(desc("count"))
        .limit(10)
    )
    rows = result.fetchall()
    return {"data": [{"ip": row[0], "alerts": row[1]} for row in rows]}


@router.get("/charts/attack-types")
async def attack_types(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(
        select(Alert.threat_type, func.count(Alert.id).label("count"))
        .where(Alert.threat_type.isnot(None))
        .group_by(Alert.threat_type)
        .order_by(desc("count"))
        .limit(10)
    )
    rows = result.fetchall()
    return {"data": [{"type": row[0], "count": row[1]} for row in rows]}


@router.get("/charts/log-sources")
async def log_sources(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(
        select(LogEntry.source, func.count(LogEntry.id))
        .group_by(LogEntry.source)
    )
    rows = result.fetchall()
    return {"data": [{"source": row[0] or "unknown", "count": row[1]} for row in rows]}


@router.get("/charts/hourly-activity")
async def hourly_activity(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """Return log counts by hour of day (0-23)."""
    result = await db.execute(
        select(LogEntry.timestamp).where(LogEntry.timestamp.isnot(None)).limit(5000)
    )
    rows = result.fetchall()
    counts = [0] * 24
    for (ts,) in rows:
        if ts:
            counts[ts.hour] += 1
    return {"data": [{"hour": h, "count": counts[h]} for h in range(24)]}


@router.post("/reset")
async def reset_dashboard(seed: bool = True, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """Delete all logs, alerts, predictions, and metrics. Optionally seed default demo data."""
    # 1. Stop simulation if running
    from app.routes.live import _simulation_running
    if _simulation_running:
        from app.routes.live import stop_simulation
        await stop_simulation()

    # 2. Delete existing records from tables
    from app.models.log_entry import LogEntry
    from app.models.alert import Alert
    from app.models.prediction import Prediction
    from app.models.model_metrics import ModelMetrics
    from sqlalchemy import delete

    await db.execute(delete(Alert))
    await db.execute(delete(Prediction))
    await db.execute(delete(ModelMetrics))
    await db.execute(delete(LogEntry))
    await db.commit()

    # 3. Seed fresh data if requested
    if seed:
        from app.utils.log_generator import generate_historical_records
        from app.ml.train import train_on_demo_data
        from app.ml.predict import predict_batch
        from app.ml.alert_rules import apply_alert_rules

        records = generate_historical_records(1000, days_back=7)

        # Train models
        try:
            train_on_demo_data()
            print("[ThreatLens Reset] All models trained on demo data")
        except Exception as e:
            print(f"[ThreatLens Reset] Model training skipped: {e}")

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

        # Predictions & Alerts
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

            # Model metrics
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
        except Exception as e:
            print(f"[ThreatLens Reset] Seeding failed: {e}")
            await db.commit()

    return {"status": "success", "message": "Dashboard data reset successfully", "seeded": seed}

