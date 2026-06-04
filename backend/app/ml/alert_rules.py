"""
Alert Rules Engine — converts ML predictions + log patterns into actionable security alerts.
"""
from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime, timezone


SEVERITY_ORDER = {"informational": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def map_ml_severity_to_alert(severity: str) -> str:
    mapping = {
        "low": "low",
        "medium": "medium",
        "high": "high",
        "critical": "critical",
        "info": "informational",
        "warning": "medium",
        "error": "high",
    }
    return mapping.get(severity, "medium")


def get_alert_title(threat_type: str, record: Dict[str, Any]) -> str:
    ip = record.get("source_ip") or "Unknown"
    user = record.get("username") or "Unknown"
    titles = {
        "Brute Force": f"Brute Force Attack from {ip}",
        "SQL Injection / Web Attack": f"SQL Injection / Web Attack from {ip}",
        "Port Scan / Reconnaissance": f"Port Scan Detected from {ip}",
        "Privilege Escalation": f"Privilege Escalation by {user}",
        "Unauthorized Access": f"Unauthorized Access Attempt from {ip}",
        "Malware-like Behavior": f"Malware-like Behavior Detected from {ip}",
        "Web Attack": f"Web Application Attack from {ip}",
        "Suspicious IP Activity": f"Suspicious Activity from {ip}",
        "Suspicious Login": f"Suspicious Login by {user} from {ip}",
        "Unknown Anomaly": f"Anomalous Activity Detected from {ip}",
    }
    return titles.get(threat_type, f"Security Alert: {threat_type}")


def build_alert_from_prediction(
    record: Dict[str, Any],
    prediction: Dict[str, Any],
    log_id: Optional[int] = None,
    prediction_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Build an alert dict from a log record + prediction result."""
    threat_type = prediction.get("threat_type", "Unknown Anomaly")
    severity = map_ml_severity_to_alert(prediction.get("severity", "medium"))
    title = get_alert_title(threat_type, record)

    import json
    try:
        explanation = json.loads(prediction.get("explanation", "{}"))
        factors = explanation.get("contributing_factors", [])
        recommendation = explanation.get("recommendation", "Investigate and monitor.")
        description = explanation.get("narrative") or ("; ".join(factors) if factors else "ML model detected anomalous behavior.")
    except Exception:
        description = "ML model detected anomalous behavior."
        recommendation = "Investigate and monitor."

    return {
        "log_id": log_id,
        "prediction_id": prediction_id,
        "title": title,
        "description": description,
        "severity": severity,
        "status": "new",
        "assigned_to": None,
        "recommendation": recommendation,
        "source_ip": record.get("source_ip"),
        "threat_type": threat_type,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


def apply_alert_rules(
    records: List[Dict[str, Any]],
    predictions: List[Dict[str, Any]],
    log_ids: List[Optional[int]] = None,
    prediction_ids: List[Optional[int]] = None,
) -> List[Dict[str, Any]]:
    """
    Apply alert generation rules to a batch of predictions.
    Only generate alerts for anomalous predictions.
    Suppresses duplicate alerts for same IP + threat_type within batch.
    """
    alerts = []
    seen = set()   # (source_ip, threat_type) dedup key

    if log_ids is None:
        log_ids = [None] * len(records)
    if prediction_ids is None:
        prediction_ids = [None] * len(predictions)

    # Extra batch-level rule: check for IP bursts
    ip_fail_counts: Dict[str, int] = defaultdict(int)
    for rec in records:
        if rec.get("event_type") in ("auth_failure", "access_denied"):
            ip = rec.get("source_ip") or "unknown"
            ip_fail_counts[ip] += 1

    for i, (record, pred, log_id, pred_id) in enumerate(
        zip(records, predictions, log_ids, prediction_ids)
    ):
        if pred.get("prediction") != "anomaly":
            continue

        threat_type = pred.get("threat_type", "Unknown Anomaly")
        ip = record.get("source_ip") or "unknown"
        dedup_key = (ip, threat_type)

        # Skip if we already generated this alert type for this IP in this batch
        # (allow one per unique pair to avoid flooding)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        alert = build_alert_from_prediction(record, pred, log_id, pred_id)
        alerts.append(alert)

    # Extra rule: burst detection — 5+ fails from same IP triggers extra alert
    for ip, count in ip_fail_counts.items():
        if count >= 5:
            dedup_key = (ip, "Brute Force")
            if dedup_key not in seen:
                seen.add(dedup_key)
                alerts.append({
                    "log_id": None,
                    "prediction_id": None,
                    "title": f"Brute Force: {count} Failed Logins from {ip}",
                    "description": f"Detected {count} failed authentication attempts from {ip} in a single batch.",
                    "severity": "critical" if count >= 10 else "high",
                    "status": "new",
                    "assigned_to": None,
                    "recommendation": "Block source IP immediately, enable account lockout, require MFA.",
                    "source_ip": ip,
                    "threat_type": "Brute Force",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                })

    return alerts
