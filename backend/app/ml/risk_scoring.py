"""
Adaptive Security Risk Scoring Engine for ThreatLens AI.

Calculates a comprehensive, problem-oriented, and robust risk index (0 - 100) 
for a threat incident using weights mapping directly to SOC assets:

Formula:
risk_score = 
    0.25 * model_anomaly_score +
    0.20 * rule_severity_score +
    0.15 * threat_confidence +
    0.15 * asset_criticality +
    0.10 * user_sensitivity +
    0.10 * MITRE_severity +
    0.05 * time_context_score
"""
from typing import Dict, Any

def calculate_adaptive_risk(
    model_anomaly_score: float,       # 0.0 – 1.0 (unsupervised score)
    rule_severity_score: float,       # 0.0 – 100.0 (rule-based severity mapping)
    threat_confidence: float,         # 0.0 – 1.0 (supervised model confidence)
    asset_criticality: float = 50.0,  # 0.0 – 100.0 (impact risk index of host server/asset)
    user_sensitivity: float = 50.0,   # 0.0 – 100.0 (risk/clearance index of username)
    mitre_severity: float = 50.0,     # 0.0 – 100.0 (severity scale of target MITRE ATT&CK technique)
    time_context_score: float = 20.0  # 0.0 – 100.0 (unusual hour/weekend score)
) -> float:
    """
    Computes weighted threat score index clamped between 0.0 and 100.0.
    Uses robust defaults if factors are missing.
    """
    # Normalize inputs to 0 - 100
    norm_anomaly = float(model_anomaly_score) * 100.0
    norm_confidence = float(threat_confidence) * 100.0

    # Calculate weighted components
    score = (
        0.25 * norm_anomaly +
        0.20 * float(rule_severity_score) +
        0.15 * norm_confidence +
        0.15 * float(asset_criticality) +
        0.10 * float(user_sensitivity) +
        0.10 * float(mitre_severity) +
        0.05 * float(time_context_score)
    )

    # Return clamped value
    return float(max(0.0, min(100.0, round(score, 1))))

def get_asset_criticality(ip: str, path: str) -> float:
    """Returns dynamic asset criticality index based on subnet or path."""
    ip_str = str(ip or "")
    path_str = str(path or "").lower()
    
    # 1. Flag database or backup subnet IPs as highly critical
    if ip_str.startswith("10.0.3") or ip_str.startswith("192.168.3"):
        return 90.0
    # 2. Admin controllers
    elif "admin" in path_str or "config" in path_str or "passwd" in path_str:
        return 85.0
    # 3. Public landing paths
    elif path_str == "/" or path_str == "/index.html":
        return 30.0
    
    return 50.0  # standard server asset default

def get_user_sensitivity(username: str) -> float:
    """Returns dynamic user clearance/sensitivity rating."""
    user = str(username or "").lower()
    if user in ("root", "admin", "administrator", "system"):
        return 95.0
    elif user in ("db_admin", "sec_engineer", "developer"):
        return 75.0
    elif user == "guest" or user == "anonymous":
        return 20.0
    
    return 50.0  # standard user clearance default

def get_mitre_severity(threat_type: str) -> float:
    """Standard severity mapping for MITRE ATT&CK techniques."""
    severities = {
        "Brute Force": 70.0,
        "SQL Injection": 85.0,
        "Privilege Escalation": 95.0,
        "Malware Behavior": 90.0,
        "Unauthorized Access": 80.0,
        "Port Scan": 40.0,
        "Data Exfiltration": 90.0
    }
    return severities.get(threat_type, 50.0)
