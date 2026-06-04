"""
ML Prediction Engine for ThreatLens AI.

Runs batch predictions using trained models.
Outputs: prediction label, anomaly_score, risk_score (0-100), severity, threat_type, explanation.
"""
import joblib
import json
import numpy as np
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.config import settings
from app.ml.feature_engineering import (
    extract_features, FEATURE_COLUMNS,
    FAIL_KEYWORDS, PRIV_KEYWORDS, ATTACK_KEYWORDS, SENSITIVE_PATHS,
)

MODEL_STORE = settings.MODEL_DIR

# ── Threat type classification rules ─────────────────────────────────────────
def classify_threat_type(record: Dict[str, Any], features: Dict[str, Any]) -> str:
    msg = (record.get("message") or "").lower()
    path = (record.get("path") or "").lower()
    event = (record.get("event_type") or "").lower()

    if features.get("failed_login_count", 0) >= 5 or (
        features.get("fail_flag") and features.get("is_admin_user")
    ):
        return "Brute Force"

    if re.search(r"(union\s+select|' or |xp_cmd|exec\s*\(|select\s+\*)", msg + path, re.I):
        return "SQL Injection / Web Attack"

    if re.search(r"(scan|nmap|masscan|port\s*\d+|syn\s+flood)", msg, re.I):
        return "Port Scan / Reconnaissance"

    if features.get("priv_flag") and features.get("is_admin_user"):
        return "Privilege Escalation"

    if features.get("sensitive_path") and features.get("is_auth_fail"):
        return "Unauthorized Access"

    if re.search(r"(malware|ransomware|trojan|backdoor|shell|wget|curl|base64\s+decode)", msg, re.I):
        return "Malware-like Behavior"

    if features.get("attack_flag"):
        return "Web Attack"

    if features.get("fail_flag") and features.get("ip_frequency", 0) > 10:
        return "Suspicious IP Activity"

    if features.get("unusual_hour") and features.get("is_admin_user"):
        return "Suspicious Login"

    return "Unknown Anomaly"


def severity_from_risk(risk_score: float) -> str:
    if risk_score >= 76:
        return "critical"
    elif risk_score >= 51:
        return "high"
    elif risk_score >= 26:
        return "medium"
    else:
        return "low"


def build_explanation(record: Dict[str, Any], features: Dict[str, Any], risk_score: float, threat_type: str) -> str:
    from app.ml.explainability import generate_analyst_explanation
    reasons = []
    if features.get("failed_login_count", 0) >= 3:
        reasons.append(f"High failed login count ({features['failed_login_count']})")
    if features.get("fail_flag"):
        reasons.append("Authentication failure detected in log message")
    if features.get("priv_flag"):
        reasons.append("Privilege-related keywords detected (root/sudo/admin)")
    if features.get("attack_flag"):
        reasons.append("Attack pattern keywords detected (inject/exploit/scan)")
    if features.get("sensitive_path"):
        reasons.append("Access attempt to sensitive system path")
    if features.get("unusual_hour"):
        reasons.append("Activity at unusual hours (00:00–06:00)")
    if features.get("ip_frequency", 0) > 20:
        reasons.append(f"High request frequency from source IP ({features['ip_frequency']} events)")
    if features.get("is_admin_user"):
        reasons.append("Privileged account (root/admin) involved")
    if features.get("is_auth_fail"):
        reasons.append("HTTP 401/403 authentication/authorization failure")

    if not reasons:
        reasons.append("Statistical anomaly detected by ML model (Isolation Forest)")

    try:
        narrative = generate_analyst_explanation(threat_type, record, features)
    except Exception:
        narrative = "This event is marked anomalous due to structural deviations in request rate, payload size, and off-hour context."

    return json.dumps({
        "threat_type": threat_type,
        "risk_score": round(risk_score, 1),
        "contributing_factors": reasons,
        "recommendation": _get_recommendation(threat_type),
        "narrative": narrative,
        "feature_values": {k: v for k, v in features.items()},
    })


def _get_recommendation(threat_type: str) -> str:
    recs = {
        "Brute Force": "Block source IP, enable account lockout policy, enable MFA.",
        "SQL Injection / Web Attack": "Review WAF rules, sanitize inputs, patch web application.",
        "Port Scan / Reconnaissance": "Firewall the source IP, investigate potential follow-up attacks.",
        "Privilege Escalation": "Audit sudo logs, review user privileges, rotate credentials.",
        "Unauthorized Access": "Revoke session, audit access logs, change affected passwords.",
        "Malware-like Behavior": "Isolate host, run full AV scan, check process list.",
        "Web Attack": "Enable WAF, review suspicious requests, patch known CVEs.",
        "Suspicious IP Activity": "Geo-block if international, add to watchlist.",
        "Suspicious Login": "Require MFA, notify account owner, review session.",
        "Unknown Anomaly": "Investigate manually, correlate with other events.",
    }
    return recs.get(threat_type, "Investigate and monitor.")


def predict_batch(
    records: List[Dict[str, Any]],
    model_name: str = "isolation_forest",
    threshold: float = None,
) -> List[Dict[str, Any]]:
    """
    Run batch prediction on a list of parsed log records.
    Returns a list of prediction dicts, one per record.
    """
    threshold = threshold if threshold is not None else settings.ANOMALY_THRESHOLD

    df = extract_features(records)
    X = df[FEATURE_COLUMNS].fillna(0).values

    # Load model + scaler
    model_path = MODEL_STORE / f"{model_name}.joblib"
    scaler_path = MODEL_STORE / f"{model_name}_scaler.joblib"

    if not model_path.exists():
        # No model trained yet — fallback to rule-based only
        return _rule_based_predictions(records, df)

    model = joblib.load(model_path)
    if scaler_path.exists():
        scaler = joblib.load(scaler_path)
        X_scaled = scaler.transform(X)
    else:
        X_scaled = X

    if model_name == "isolation_forest":
        raw_scores = model.score_samples(X_scaled)    # lower = more anomalous
        preds = model.predict(X_scaled)               # -1 = anomaly, 1 = normal
    else:
        preds = model.predict(X_scaled)               # 0 = normal, 1 = attack
        try:
            raw_scores = model.predict_proba(X_scaled)[:, 1]
        except Exception:
            raw_scores = preds.astype(float)

    results = []
    for i, record in enumerate(records):
        feat_row = df.iloc[i].to_dict()
        raw_score = float(raw_scores[i])
        pred_label = int(preds[i])

        if model_name == "isolation_forest":
            # Score range: typically [-0.5, 0.2]. Normalize to [0, 100] risk
            # More negative = more anomalous = higher risk
            # Clip to [-0.6, 0.1]
            clipped = max(-0.6, min(0.1, raw_score))
            normalized = (clipped - 0.1) / (-0.6 - 0.1)  # 0 (normal) to 1 (anomaly)
            base_risk = normalized * 100.0
            is_anomaly = pred_label == -1
        else:
            base_risk = raw_score * 100.0
            is_anomaly = pred_label == 1

        # Boost risk score based on rule-based features
        boost = 0.0
        if feat_row.get("fail_flag"):
            boost += 5
        if feat_row.get("priv_flag"):
            boost += 10
        if feat_row.get("attack_flag"):
            boost += 15
        if feat_row.get("sensitive_path"):
            boost += 10
        if feat_row.get("unusual_hour"):
            boost += 5
        if feat_row.get("failed_login_count", 0) >= 5:
            boost += 15
        if feat_row.get("is_admin_user"):
            boost += 5
        if feat_row.get("is_auth_fail"):
            boost += 8

        risk_score = min(100.0, base_risk + boost)
        if not is_anomaly and risk_score < 30:
            risk_score = max(0.0, risk_score)

        prediction = "anomaly" if is_anomaly or risk_score >= 40 else "normal"
        threat_type = classify_threat_type(record, feat_row) if prediction == "anomaly" else "Normal"
        severity = severity_from_risk(risk_score)
        explanation = build_explanation(record, feat_row, risk_score, threat_type)

        results.append({
            "prediction": prediction,
            "anomaly_score": round(raw_score, 4),
            "risk_score": round(risk_score, 2),
            "threat_type": threat_type,
            "severity": severity,
            "explanation": explanation,
            "model_name": model_name,
        })

    return results


def _rule_based_predictions(
    records: List[Dict[str, Any]],
    df,
) -> List[Dict[str, Any]]:
    """Fallback: pure rule-based detection when no model is trained."""
    results = []
    for i, record in enumerate(records):
        feat_row = df.iloc[i].to_dict()
        risk = 0.0
        if feat_row.get("attack_flag"):
            risk += 40
        if feat_row.get("priv_flag"):
            risk += 20
        if feat_row.get("fail_flag"):
            risk += 15
        if feat_row.get("sensitive_path"):
            risk += 15
        if feat_row.get("unusual_hour"):
            risk += 10
        if feat_row.get("failed_login_count", 0) >= 5:
            risk += 25
        risk = min(100.0, risk)

        prediction = "anomaly" if risk >= 30 else "normal"
        threat_type = classify_threat_type(record, feat_row) if prediction == "anomaly" else "Normal"

        results.append({
            "prediction": prediction,
            "anomaly_score": 0.0,
            "risk_score": round(risk, 2),
            "threat_type": threat_type,
            "severity": severity_from_risk(risk),
            "explanation": build_explanation(record, feat_row, risk, threat_type),
            "model_name": "rule_based",
        })
    return results
