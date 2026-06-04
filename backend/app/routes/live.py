"""
Live simulation routes + WebSocket endpoint.
Generates synthetic log events and broadcasts via WebSocket.
"""
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, AsyncSessionLocal
from app.routes.auth import get_current_user
from app.models.log_entry import LogEntry
from app.models.alert import Alert
from app.models.prediction import Prediction
from app.ml.predict import predict_batch
from app.ml.alert_rules import apply_alert_rules
from app.utils.log_generator import generate_log_event

router = APIRouter(prefix="/api/live", tags=["live"])

# Global simulation state
_simulation_running = False
_simulation_task = None
_connected_clients: list[WebSocket] = []


async def _broadcast(message: dict):
    disconnected = []
    for ws in _connected_clients:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        _connected_clients.remove(ws)


async def _simulation_loop(interval: float = 1.5):
    global _simulation_running
    while _simulation_running:
        try:
            record = generate_log_event(attack_probability=0.2)

            # Predict
            predictions = predict_batch([record])
            pred = predictions[0] if predictions else {}

            # Convert timestamp to string for JSON
            ts = record.get("timestamp")
            ts_str = ts.isoformat() if ts else ""

            log_data = {
                "type": "log",
                "data": {
                    "timestamp": ts_str,
                    "source": record.get("source"),
                    "source_ip": record.get("source_ip"),
                    "username": record.get("username"),
                    "event_type": record.get("event_type"),
                    "message": record.get("message"),
                    "severity": record.get("severity"),
                    "prediction": pred.get("prediction"),
                    "risk_score": pred.get("risk_score"),
                    "threat_type": pred.get("threat_type"),
                },
            }
            await _broadcast(log_data)

            # Broadcast alert if anomaly
            if pred.get("prediction") == "anomaly":
                alerts = apply_alert_rules([record], [pred])
                for alert in alerts:
                    alert_data = {
                        "type": "alert",
                        "data": {
                            "title": alert["title"],
                            "severity": alert["severity"],
                            "threat_type": alert["threat_type"],
                            "source_ip": alert["source_ip"],
                            "description": alert["description"],
                            "recommendation": alert["recommendation"],
                        },
                    }
                    await _broadcast(alert_data)

                # Persist to DB
                try:
                    async with AsyncSessionLocal() as db:
                        entry = LogEntry(
                            timestamp=record.get("timestamp"),
                            source=record.get("source"),
                            source_ip=record.get("source_ip"),
                            username=record.get("username"),
                            event_type=record.get("event_type"),
                            message=record.get("message"),
                            raw_log=record.get("raw_log", "")[:2000],
                            severity=record.get("severity", "info"),
                        )
                        db.add(entry)
                        await db.flush()

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

                        for alert_data in alerts:
                            a = Alert(**{k: v for k, v in alert_data.items()})
                            db.add(a)

                        await db.commit()
                except Exception:
                    pass   # Don't crash simulation on DB error

        except Exception as e:
            await _broadcast({"type": "error", "message": str(e)})

        await asyncio.sleep(interval)


@router.post("/start")
async def start_simulation(interval: float = 1.5, current_user=Depends(get_current_user)):
    global _simulation_running, _simulation_task
    if _simulation_running:
        return {"message": "Simulation already running", "running": True}
    _simulation_running = True
    _simulation_task = asyncio.create_task(_simulation_loop(interval))
    return {"message": "Live simulation started", "running": True, "interval": interval}


@router.post("/stop")
async def stop_simulation(current_user=Depends(get_current_user)):
    global _simulation_running, _simulation_task
    _simulation_running = False
    if _simulation_task:
        _simulation_task.cancel()
        _simulation_task = None
    return {"message": "Simulation stopped", "running": False}


@router.get("/status")
async def simulation_status(current_user=Depends(get_current_user)):
    return {
        "running": _simulation_running,
        "connected_clients": len(_connected_clients),
    }


@router.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None), db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    if not token:
        await websocket.send_json({"type": "error", "message": "Authentication token missing"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        from app.routes.auth import decode_token, get_user_by_email
        payload = decode_token(token)
        email = payload.get("sub")
        if not email:
            raise Exception("Invalid token structure")
        user = await get_user_by_email(db, email)
        if not user:
            raise Exception("User not found")
    except Exception as e:
        await websocket.send_json({"type": "error", "message": f"Auth failed: {str(e)}"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    _connected_clients.append(websocket)
    try:
        await websocket.send_json({"type": "connected", "message": "ThreatLens AI live feed connected"})
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in _connected_clients:
            _connected_clients.remove(websocket)
