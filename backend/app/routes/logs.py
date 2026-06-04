"""Logs routes — upload, list, get, stats, delete"""
import json
import aiofiles
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, delete
from app.database import get_db
from app.models.log_entry import LogEntry
from app.models.dataset import Dataset
from app.models.prediction import Prediction
from app.models.alert import Alert
from app.schemas.schemas import LogOut, DatasetOut
from app.parsers.log_parser import parse_logs, detect_format
from app.ml.predict import predict_batch
from app.ml.alert_rules import apply_alert_rules
from app.config import settings
from datetime import datetime, timezone

router = APIRouter(prefix="/api/logs", tags=["logs"])
from app.routes.auth import get_current_user

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_TYPES = {".csv", ".txt", ".log", ".json"}


async def _process_upload(dataset_id: int, content: str, filename: str):
    """Background task: parse, store, predict — opens its own DB session."""
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            # Update status
            result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
            dataset = result.scalar_one_or_none()
            if not dataset:
                return

            dataset.upload_status = "processing"
            await db.commit()

            # Parse
            fmt = detect_format(content, filename)
            records = parse_logs(content, filename, fmt)

            if not records:
                dataset.upload_status = "failed"
                dataset.error_message = "No parseable log entries found. Check file format."
                await db.commit()
                return

            dataset.total_rows = len(records)

            # Store log entries in chunks
            chunk_size = 500
            log_ids = []
            for chunk_start in range(0, len(records), chunk_size):
                chunk = records[chunk_start: chunk_start + chunk_size]
                for rec in chunk:
                    entry = LogEntry(
                        timestamp=rec.get("timestamp"),
                        source=rec.get("source") or fmt,
                        source_ip=rec.get("source_ip"),
                        destination_ip=rec.get("destination_ip"),
                        username=rec.get("username"),
                        event_type=rec.get("event_type"),
                        status_code=rec.get("status_code"),
                        method=rec.get("method"),
                        path=rec.get("path"),
                        message=rec.get("message"),
                        raw_log=rec.get("raw_log", "")[:2000],
                        parsed_fields=json.dumps(rec.get("parsed_fields") or {}),
                        severity=rec.get("severity", "info"),
                        dataset_id=dataset_id,
                    )
                    db.add(entry)
                await db.flush()
                # Collect IDs
                result2 = await db.execute(
                    select(LogEntry.id)
                    .where(LogEntry.dataset_id == dataset_id)
                    .order_by(desc(LogEntry.id))
                    .limit(len(chunk))
                )
                ids = [r[0] for r in result2.fetchall()]
                log_ids.extend(ids)
                dataset.processed_rows = chunk_start + len(chunk)
                await db.commit()

            # Run ML predictions on all records
            predictions = predict_batch(records)

            # Save predictions + generate alerts
            alerts_to_add = apply_alert_rules(records, predictions)
            for i, (pred, log_id) in enumerate(zip(predictions, log_ids[:len(predictions)])):
                p = Prediction(
                    log_id=log_id,
                    model_name=pred.get("model_name"),
                    prediction=pred.get("prediction"),
                    anomaly_score=pred.get("anomaly_score"),
                    risk_score=pred.get("risk_score"),
                    threat_type=pred.get("threat_type"),
                    severity=pred.get("severity"),
                    explanation=pred.get("explanation"),
                )
                db.add(p)
            await db.flush()

            for alert_data in alerts_to_add:
                alert = Alert(**{k: v for k, v in alert_data.items()})
                db.add(alert)

            dataset.upload_status = "completed"
            dataset.processed_rows = len(records)
            await db.commit()
            print(f"[Upload] Processed {filename}: {len(records)} logs, {len(alerts_to_add)} alerts")

        except Exception as e:
            print(f"[Upload ERROR] {filename}: {e}")
            try:
                result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
                dataset = result.scalar_one_or_none()
                if dataset:
                    dataset.upload_status = "failed"
                    dataset.error_message = str(e)[:500]
                    await db.commit()
            except Exception:
                pass


@router.post("/upload", response_model=DatasetOut)
async def upload_logs(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Validate
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"File type {suffix} not supported. Use: {ALLOWED_TYPES}")

    content_bytes = await file.read()
    if len(content_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 50MB.")

    content = content_bytes.decode("utf-8", errors="replace")

    # Save file
    save_path = settings.UPLOAD_DIR / (file.filename or "upload.log")
    async with aiofiles.open(save_path, "w", encoding="utf-8") as f:
        await f.write(content)

    # Create dataset record
    dataset = Dataset(
        file_name=str(save_path),
        original_name=file.filename,
        file_type=suffix.lstrip("."),
        upload_status="pending",
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)

    # FIX: Pass dataset_id (not db session) — background task opens its own session
    background_tasks.add_task(_process_upload, dataset.id, content, file.filename or "")

    return DatasetOut.model_validate(dataset)



@router.get("", response_model=dict)
async def list_logs(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
    severity: Optional[str] = None,
    source: Optional[str] = None,
    source_ip: Optional[str] = None,
    event_type: Optional[str] = None,
    search: Optional[str] = None,
    dataset_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = select(LogEntry).order_by(desc(LogEntry.created_at))

    if severity:
        query = query.where(LogEntry.severity == severity)
    if source:
        query = query.where(LogEntry.source == source)
    if source_ip:
        query = query.where(LogEntry.source_ip.contains(source_ip))
    if event_type:
        query = query.where(LogEntry.event_type.contains(event_type))
    if dataset_id:
        query = query.where(LogEntry.dataset_id == dataset_id)
    if search:
        query = query.where(
            (LogEntry.message.contains(search)) |
            (LogEntry.source_ip.contains(search)) |
            (LogEntry.username.contains(search))
        )

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * size
    result = await db.execute(query.offset(offset).limit(size))
    entries = result.scalars().all()

    return {
        "items": [LogOut.model_validate(e) for e in entries],
        "total": total,
        "page": page,
        "size": size,
        "pages": max(1, (total + size - 1) // size),
    }


@router.get("/stats")
async def log_stats(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    total_result = await db.execute(select(func.count(LogEntry.id)))
    total = total_result.scalar() or 0

    sev_result = await db.execute(
        select(LogEntry.severity, func.count(LogEntry.id)).group_by(LogEntry.severity)
    )
    by_sev = {row[0] or "unknown": row[1] for row in sev_result}

    src_result = await db.execute(
        select(LogEntry.source, func.count(LogEntry.id)).group_by(LogEntry.source)
    )
    by_src = {row[0] or "unknown": row[1] for row in src_result}

    return {"total": total, "by_severity": by_sev, "by_source": by_src}


@router.get("/datasets", response_model=list)
async def list_datasets(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(select(Dataset).order_by(desc(Dataset.created_at)))
    return [DatasetOut.model_validate(d) for d in result.scalars().all()]


@router.get("/{log_id}", response_model=LogOut)
async def get_log(log_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(select(LogEntry).where(LogEntry.id == log_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Log not found")
    return LogOut.model_validate(entry)


@router.delete("/{log_id}")
async def delete_log(log_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(select(LogEntry).where(LogEntry.id == log_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Log not found")
    await db.delete(entry)
    await db.commit()
    return {"message": "Log deleted"}
