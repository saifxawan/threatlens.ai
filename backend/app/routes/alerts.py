"""Alerts routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
from app.database import get_db
from app.models.alert import Alert
from app.schemas.schemas import AlertOut, AlertStatusUpdate

router = APIRouter(prefix="/api/alerts", tags=["alerts"])
from app.routes.auth import get_current_user


@router.get("", response_model=dict)
async def list_alerts(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    threat_type: Optional[str] = None,
    source_ip: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = select(Alert).order_by(desc(Alert.created_at))

    if severity:
        query = query.where(Alert.severity == severity)
    if status:
        query = query.where(Alert.status == status)
    if threat_type:
        query = query.where(Alert.threat_type.contains(threat_type))
    if source_ip:
        query = query.where(Alert.source_ip.contains(source_ip))

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0

    offset = (page - 1) * size
    result = await db.execute(query.offset(offset).limit(size))
    alerts = result.scalars().all()

    return {
        "items": [AlertOut.model_validate(a) for a in alerts],
        "total": total,
        "page": page,
        "size": size,
        "pages": max(1, (total + size - 1) // size),
    }


@router.get("/stats")
async def alert_stats(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    total_result = await db.execute(select(func.count(Alert.id)))
    total = total_result.scalar() or 0

    sev_result = await db.execute(
        select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)
    )
    by_sev = {row[0] or "unknown": row[1] for row in sev_result}

    status_result = await db.execute(
        select(Alert.status, func.count(Alert.id)).group_by(Alert.status)
    )
    by_status = {row[0] or "unknown": row[1] for row in status_result}

    type_result = await db.execute(
        select(Alert.threat_type, func.count(Alert.id)).group_by(Alert.threat_type).limit(10)
    )
    by_type = {row[0] or "Unknown": row[1] for row in type_result}

    return {
        "total": total,
        "by_severity": by_sev,
        "by_status": by_status,
        "by_threat_type": by_type,
    }


@router.get("/{alert_id}", response_model=AlertOut)
async def get_alert(alert_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertOut.model_validate(alert)


@router.patch("/{alert_id}/status", response_model=AlertOut)
async def update_alert_status(
    alert_id: int,
    body: AlertStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    valid_statuses = {"new", "investigating", "resolved", "false_positive"}
    if body.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {valid_statuses}")

    alert.status = body.status
    if body.assigned_to:
        alert.assigned_to = body.assigned_to
    await db.commit()
    await db.refresh(alert)
    return AlertOut.model_validate(alert)
