"""
Predictor Engine for ThreatLens AI.

Orchestrates threat evaluation across all loaded hybrid models:
- Isolation Forest
- Logistic Regression
- Decision Tree
- Random Forest
- Support Vector Machine
- Naïve Bayes Text Classifier
- K-Means Cluster Assignment

Standardizes and maps raw class metrics into clean threat vectors.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from app.ml.feature_extractor import extract_features
from app.ml.model_registry import model_registry
from app.ml.text_classifier import text_threat_classifier
from app.ml.clustering import security_clustering
from app.ml.risk_scoring import calculate_adaptive_risk, get_mitre_severity, get_asset_criticality, get_user_sensitivity

CLASSES = ["normal", "brute_force", "sql_injection", "privilege_escalation", "malware_behavior", "unauthorized_access", "port_scan"]
THREAT_LABELS = {
    "normal": "Normal",
    "brute_force": "Brute Force",
    "sql_injection": "SQL Injection",
    "privilege_escalation": "Privilege Escalation",
    "malware_behavior": "Malware Behavior",
    "unauthorized_access": "Unauthorized Access",
    "port_scan": "Port Scan"
}

def predict_single_event(record: Dict[str, Any], model_key: str = None) -> Dict[str, Any]:
    """Runs prediction for a single log event. Standardizes output."""
    batch_results = predict_batch_events([record], model_key)
    return batch_results[0] if batch_results else {}

def predict_batch_events(records: List[Dict[str, Any]], model_key: str = None) -> List[Dict[str, Any]]:
    """Runs threat classification for a batch of log records."""
    if not records:
        return []

    # 1. Extract 29 features
    df_feat = extract_features(records)
    X = df_feat.values
    
    # 2. Identify active model
    algo = model_key or model_registry.active_model_name
    model = model_registry.get_model(algo)
    
    results = []

    # 3. Get behavioral clusters
    clusters = security_clustering.predict(df_feat)
    
    # 4. Predict row by row
    for idx, rec in enumerate(records):
        feat_row = X[idx]
        msg = rec.get("message", "")
        ip = rec.get("source_ip") or "unknown"
        user = rec.get("username") or "unknown"
        path = rec.get("path") or ""

        # Default prediction structure
        pred_label = "normal"
        threat_type = "Normal"
        confidence = 0.95
        anomaly_score = 0.05
        explanation_list = ["Event parameters reside within nominal baseline ranges."]
        
        # Unsupervised Naïve Bayes Text parsing
        text_label, text_conf = text_threat_classifier.predict(msg + " " + path)

        # Apply specific classifier
        if model:
            try:
                # --- Unsupervised Isolation Forest ---
                if algo == "isolation_forest":
                    score = model.decision_function(feat_row.reshape(1, -1))[0]
                    # Convert decision function score to anomaly score (0 to 1 range)
                    anomaly_score = float(0.5 - score)
                    anomaly_score = max(0.0, min(1.0, anomaly_score))
                    
                    if score < 0:
                        pred_label = "anomaly"
                        threat_type = text_label if text_label != "Normal Text" else "Unknown Anomaly"
                        confidence = float(anomaly_score)
                        explanation_list = ["Log attributes flagged as anomalous by unsupervised Isolation Forest."]
                    
                # --- Supervised Logistic Regression ---
                elif algo == "logistic_regression":
                    pred = model.predict(feat_row.reshape(1, -1))[0]
                    probs = model.predict_proba(feat_row.reshape(1, -1))[0]
                    confidence = float(probs[pred])
                    anomaly_score = float(probs[1]) # Probability of anomalous class
                    
                    if pred == 1:
                        pred_label = "anomaly"
                        threat_type = text_label if text_label != "Normal Text" else "Suspicious IP Activity"
                        explanation_list = ["Event characteristics classified as anomalous by Logistic Regression."]

                # --- Supervised Decision Tree ---
                elif algo == "decision_tree":
                    class_idx = model.predict(feat_row.reshape(1, -1))[0]
                    probs = model.predict_proba(feat_row.reshape(1, -1))[0]
                    confidence = float(probs[class_idx])
                    
                    lbl = CLASSES[class_idx]
                    if lbl != "normal":
                        pred_label = "anomaly"
                        threat_type = THREAT_LABELS.get(lbl, "Unknown Anomaly")
                        anomaly_score = 1.0 - float(probs[0])
                        explanation_list = [f"Classified as {threat_type} by Decision Tree model."]

                # --- Supervised Random Forest ---
                elif algo == "random_forest":
                    class_idx = model.predict(feat_row.reshape(1, -1))[0]
                    probs = model.predict_proba(feat_row.reshape(1, -1))[0]
                    confidence = float(probs[class_idx])
                    
                    lbl = CLASSES[class_idx]
                    if lbl != "normal":
                        pred_label = "anomaly"
                        threat_type = THREAT_LABELS.get(lbl, "Unknown Anomaly")
                        anomaly_score = 1.0 - float(probs[0])
                        explanation_list = [f"Incident classified as {threat_type} by Random Forest ensemble."]

                # --- Supervised Support Vector Machine ---
                elif algo == "svm":
                    pred = model.predict(feat_row.reshape(1, -1))[0]
                    probs = model.predict_proba(feat_row.reshape(1, -1))[0]
                    confidence = float(probs[pred])
                    anomaly_score = float(probs[1])
                    
                    if pred == 1:
                        pred_label = "anomaly"
                        threat_type = text_label if text_label != "Normal Text" else "Suspicious Login"
                        explanation_list = ["Security event hyperplane classified as malicious by SVM."]
                        
            except Exception as e:
                # Fallback to simple Naïve Bayes if classifier fails
                if text_label != "Normal Text":
                    pred_label = "anomaly"
                    threat_type = text_label
                    confidence = text_conf
                    anomaly_score = text_conf
                    explanation_list = [f"Text classifier fallback: suspicious payload detected ({text_label})."]

        # If model is absent or normal, let the text classifier overwrite if it detects a high-confidence attack
        if pred_label == "normal" and text_label != "Normal Text" and text_conf >= 0.80:
            pred_label = "anomaly"
            threat_type = text_label
            confidence = text_conf
            anomaly_score = text_conf
            explanation_list = [f"Malicious string payload found: {text_label} ({int(text_conf*100)}% confidence)."]

        # Calculate Adaptive Risk Score
        cluster_info = clusters[idx] if idx < len(clusters) else {}
        cluster_score = cluster_info.get("cluster_risk_score", 10.0)
        
        # Map threat type to severity rules
        rule_severity = 80.0 if "critical" in msg or "sudo" in msg else (60.0 if "fail" in msg else 10.0)
        
        mitre_sev = get_mitre_severity(threat_type)
        asset_crit = get_asset_criticality(ip, path)
        user_sens = get_user_sensitivity(user)
        
        risk = calculate_adaptive_risk(
            model_anomaly_score=anomaly_score,
            rule_severity_score=rule_severity,
            threat_confidence=confidence,
            asset_criticality=asset_crit,
            user_sensitivity=user_sens,
            mitre_severity=mitre_sev,
            time_context_score=40.0 if feat_row[10] > 0 or feat_row[11] > 0 else 10.0
        )
        
        # Triage severity scale
        if risk >= 80.0:
            sev = "critical"
        elif risk >= 60.0:
            sev = "high"
        elif risk >= 35.0:
            sev = "medium"
        else:
            sev = "low"

        results.append({
            "model_name": model_registry.active_model_name if not model_key else model_key,
            "prediction": pred_label,
            "threat_type": threat_type,
            "confidence": round(confidence, 3),
            "anomaly_score": round(anomaly_score, 3),
            "risk_score": risk,
            "severity": sev,
            "explanation": {
                "contributing_factors": explanation_list,
                "recommendation": _get_recommendation(threat_type),
                "cluster_label": cluster_info.get("cluster_label", "Normal Traffic")
            }
        })
        
    return results

def _get_recommendation(threat_type: str) -> str:
    recs = {
        "Brute Force": "Initiate automated source IP firewall blocks, enforce host account lockout, rotate passwords.",
        "SQL Injection": "Review active query parameters, validate database escape signatures, enforce WAF filters.",
        "Privilege Escalation": "Audit sudo group logs, disable administrative credentials, verify identity certificates.",
        "Malware Behavior": "Isolate system host immediately, review active connections, run anti-malware sweeps.",
        "Unauthorized Access": "Update network Access Control Lists (ACLs), expire authorization tokens.",
        "Port Scan": "Verify active port filtering, block scanner IP segments, silence ICMP responses."
    }
    return recs.get(threat_type, "Perform standard security incident investigation procedures.")
