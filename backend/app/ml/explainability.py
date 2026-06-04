"""
Explainable AI (XAI) Engine for ThreatLens AI.

Interprets model output, extracting:
- Decision path trace from the Decision Tree classifier.
- Feature importance vectors for Random Forest and Decision Tree.
- Natural language security explanations describing threat indicators.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from sklearn.tree import DecisionTreeClassifier
from app.ml.feature_extractor import FEATURE_COLUMNS

def get_dt_decision_path(
    dt_model: DecisionTreeClassifier,
    feature_row: np.ndarray,
    feature_names: List[str]
) -> List[str]:
    """
    Returns a sequence of split conditions traversed by a sample in the Decision Tree.
    Example: ["failed_login_count > 5", "is_auth_fail == 1", "msg_len <= 1500"]
    """
    try:
        # Get decision path indicators
        node_indicator = dt_model.decision_path(feature_row.reshape(1, -1))
        leaf_id = dt_model.apply(feature_row.reshape(1, -1))[0]
        
        # Tree model structure
        tree = dt_model.tree_
        feature = tree.feature
        threshold = tree.threshold
        
        # Traverse nodes from root to leaf
        node_index = node_indicator.indices[node_indicator.indptr[0]:node_indicator.indptr[1]]
        
        path_steps = []
        for node_id in node_index:
            if leaf_id == node_id:
                break
                
            feat_idx = feature[node_id]
            if feat_idx < 0:
                continue
                
            feat_name = feature_names[feat_idx]
            val = float(feature_row[feat_idx])
            thresh = float(threshold[node_id])
            
            # Format comparison operator
            if val <= thresh:
                step = f"{feat_name} <= {round(thresh, 2)}"
            else:
                step = f"{feat_name} > {round(thresh, 2)}"
            path_steps.append(step)
            
        return path_steps
    except Exception as e:
        return [f"Decision tree path traversal unavailable: {e}"]

def generate_analyst_explanation(
    threat_type: str,
    record: Dict[str, Any],
    features_dict: Dict[str, float]
) -> str:
    """
    Compiles numerical feature weights and log message context into a highly 
    descriptive narrative tailored for a security operations center analyst.
    """
    ip = record.get("source_ip") or "unknown source"
    user = record.get("username") or "anonymous"
    
    # 1. Base explanations based on threat class
    if threat_type == "Brute Force":
        fails = int(features_dict.get("failed_login_count", 0))
        ratio = round(float(features_dict.get("failed_login_ratio", 0)) * 100, 1)
        return (
            f"This event was classified as a Brute Force attempt because the source IP {ip} "
            f"generated {fails} failed login attempts, accounting for {ratio}% of its overall request volume. "
            f"Contextual timing flags also indicate unusual system logins by user '{user}' during off-hours."
        )
    elif threat_type == "SQL Injection":
        spec_chars = int(features_dict.get("special_char_count", 0))
        return (
            f"This request was flagged as a SQL Injection attack. The path/message contains "
            f"{spec_chars} special SQL query characters, possesses an abnormally high "
            f"density of command execution signatures, and includes URL query indicators "
            f"associated with database structures."
        )
    elif threat_type == "Privilege Escalation":
        return (
            f"Privilege Escalation warning! User '{user}' requested root administrative resources "
            f"or executed command path modifiers ('{record.get('path', '')}') typically reserved "
            f"for system personnel, which triggered a high risk factor value."
        )
    elif threat_type == "Malware Behavior":
        return (
            f"Malware-like behavior detected! The raw payload indicates connections matching "
            f"command and control reverse shell patterns (e.g. nc, wget, curl) or encoded string signatures "
            f"originating from client IP {ip}."
        )
    elif threat_type == "Unauthorized Access":
        return (
            f"Unauthorized file lookup! The client tried to access sensitive configuration paths "
            f"('{record.get('path', '')}') which triggered an immediate HTTP 401/403 security warning block."
        )
    elif threat_type == "Port Scan":
        freq = int(features_dict.get("ip_frequency", 0))
        return (
            f"Port Scan alert! The host IP {ip} initiated rapid, high-frequency connections ({freq} total) "
            f"probing multiple network paths within a short sequence window."
        )
        
    return "This event is marked anomalous due to structural deviations in request rate, payload size, and off-hour context."
