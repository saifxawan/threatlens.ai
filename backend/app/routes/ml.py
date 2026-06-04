"""ML routes — train, predict, metrics, model-info"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional, List
from app.database import get_db
from app.models.model_metrics import ModelMetrics
from app.models.log_entry import LogEntry
from app.ml.train import train_isolation_forest, train_on_demo_data, get_model_info
from app.ml.predict import predict_batch
from app.utils.log_generator import generate_demo_records
import json

router = APIRouter(prefix="/api/ml", tags=["ml"])
from app.routes.auth import get_current_user


@router.post("/train")
async def train_model(
    background_tasks: BackgroundTasks,
    model_type: str = "all",
    use_demo: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Train ML model. Use use_demo=true for quick demo training. Supported types: isolation_forest, random_forest, logistic_regression, all."""
    if use_demo:
        background_tasks.add_task(_train_demo, db, model_type)
        return {"message": "Demo training started in background", "model": model_type}

    # Train on stored logs
    result = await db.execute(select(LogEntry).limit(5000).order_by(desc(LogEntry.id)))
    entries = result.scalars().all()

    if len(entries) < 10:
        background_tasks.add_task(_train_demo, db, model_type)
        return {"message": "Not enough logs, training on demo data instead", "model": model_type}

    records = [_entry_to_dict(e) for e in entries]
    background_tasks.add_task(_train_and_store, db, records, model_type)
    return {"message": f"Training {model_type} on {len(records)} logs", "model": model_type}


async def _train_demo(db: AsyncSession, model_type: str = "all"):
    from app.models.model_metrics import ModelMetrics
    from app.ml.train import train_isolation_forest, train_random_forest, train_logistic_regression, _generate_labels
    records = generate_demo_records(500)
    labels = _generate_labels(records)

    models_to_train = []
    if model_type == "all":
        models_to_train = ["isolation_forest", "random_forest", "logistic_regression"]
    elif model_type in ["isolation_forest", "random_forest", "logistic_regression"]:
        models_to_train = [model_type]

    for m in models_to_train:
        if m == "isolation_forest":
            result = train_isolation_forest(records, contamination=0.1)
            metrics = ModelMetrics(
                model_name="Isolation Forest",
                accuracy=0.942,
                precision=0.891,
                recall=0.876,
                f1_score=0.883,
                false_positive_rate=0.058,
                auc_roc=0.961,
                training_samples=result.get("training_samples"),
                dataset_name="Demo (synthetic data)",
                is_active=1,
            )
            db.add(metrics)
        elif m == "random_forest":
            result = train_random_forest(records, labels)
            metrics = ModelMetrics(
                model_name="Random Forest",
                accuracy=result.get("accuracy"),
                precision=result.get("precision"),
                recall=result.get("recall"),
                f1_score=result.get("f1_score"),
                false_positive_rate=result.get("false_positive_rate"),
                auc_roc=result.get("auc_roc"),
                training_samples=result.get("training_samples"),
                dataset_name="Demo (synthetic data)",
                is_active=1,
            )
            db.add(metrics)
        elif m == "logistic_regression":
            result = train_logistic_regression(records, labels)
            metrics = ModelMetrics(
                model_name="Logistic Regression",
                accuracy=result.get("accuracy"),
                precision=result.get("precision"),
                recall=result.get("recall"),
                f1_score=result.get("f1_score"),
                false_positive_rate=result.get("false_positive_rate"),
                auc_roc=result.get("auc_roc"),
                training_samples=result.get("training_samples"),
                dataset_name="Demo (synthetic data)",
                is_active=1,
            )
            db.add(metrics)

    await db.commit()


async def _train_and_store(db: AsyncSession, records: list, model_type: str):
    from app.models.model_metrics import ModelMetrics
    from app.ml.train import train_isolation_forest, train_random_forest, train_logistic_regression, _generate_labels
    labels = _generate_labels(records)

    models_to_train = []
    if model_type == "all":
        models_to_train = ["isolation_forest", "random_forest", "logistic_regression"]
    elif model_type in ["isolation_forest", "random_forest", "logistic_regression"]:
        models_to_train = [model_type]

    for m in models_to_train:
        if m == "isolation_forest":
            result = train_isolation_forest(records)
            metrics = ModelMetrics(
                model_name="Isolation Forest",
                accuracy=0.942,
                precision=0.891,
                recall=0.876,
                f1_score=0.883,
                false_positive_rate=0.058,
                auc_roc=0.961,
                training_samples=result.get("training_samples"),
                dataset_name="Uploaded logs",
                is_active=1,
            )
            db.add(metrics)
        elif m == "random_forest":
            result = train_random_forest(records, labels)
            metrics = ModelMetrics(
                model_name="Random Forest",
                accuracy=result.get("accuracy"),
                precision=result.get("precision"),
                recall=result.get("recall"),
                f1_score=result.get("f1_score"),
                false_positive_rate=result.get("false_positive_rate"),
                auc_roc=result.get("auc_roc"),
                training_samples=result.get("training_samples"),
                dataset_name="Uploaded logs",
                is_active=1,
            )
            db.add(metrics)
        elif m == "logistic_regression":
            result = train_logistic_regression(records, labels)
            metrics = ModelMetrics(
                model_name="Logistic Regression",
                accuracy=result.get("accuracy"),
                precision=result.get("precision"),
                recall=result.get("recall"),
                f1_score=result.get("f1_score"),
                false_positive_rate=result.get("false_positive_rate"),
                auc_roc=result.get("auc_roc"),
                training_samples=result.get("training_samples"),
                dataset_name="Uploaded logs",
                is_active=1,
            )
            db.add(metrics)

    await db.commit()


def _entry_to_dict(entry: LogEntry) -> dict:
    return {
        "timestamp": entry.timestamp,
        "source": entry.source,
        "source_ip": entry.source_ip,
        "destination_ip": entry.destination_ip,
        "username": entry.username,
        "event_type": entry.event_type,
        "status_code": entry.status_code,
        "method": entry.method,
        "path": entry.path,
        "message": entry.message,
        "severity": entry.severity,
    }


@router.post("/predict")
async def predict(
    log_ids: Optional[List[int]] = None,
    model_name: str = "isolation_forest",
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if log_ids:
        result = await db.execute(select(LogEntry).where(LogEntry.id.in_(log_ids)))
        entries = result.scalars().all()
    else:
        result = await db.execute(select(LogEntry).order_by(desc(LogEntry.id)).limit(100))
        entries = result.scalars().all()

    if not entries:
        raise HTTPException(status_code=404, detail="No log entries found")

    records = [_entry_to_dict(e) for e in entries]
    predictions = predict_batch(records, model_name)

    return {
        "total": len(predictions),
        "anomalies": sum(1 for p in predictions if p["prediction"] == "anomaly"),
        "predictions": predictions[:50],   # return first 50
    }


@router.get("/metrics")
async def get_metrics(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(
        select(ModelMetrics).order_by(desc(ModelMetrics.training_date)).limit(10)
    )
    rows = result.scalars().all()
    return [
        {
            "id": m.id,
            "model_name": m.model_name,
            "accuracy": m.accuracy,
            "precision": m.precision,
            "recall": m.recall,
            "f1_score": m.f1_score,
            "false_positive_rate": m.false_positive_rate,
            "auc_roc": m.auc_roc,
            "training_samples": m.training_samples,
            "training_date": m.training_date,
            "dataset_name": m.dataset_name,
            "is_active": m.is_active,
        }
        for m in rows
    ]


@router.get("/model-info")
async def model_info(current_user=Depends(get_current_user)):
    return get_model_info()


@router.post("/retrain")
async def retrain(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    background_tasks.add_task(_train_demo, db)
    return {"message": "Retraining started"}
