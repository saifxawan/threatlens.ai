"""
Feature Engineering for ThreatLens AI ML Pipeline.

Extracts security-relevant numerical features from parsed log records.
"""
import re
import json
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime


# ── Keyword dictionaries ──────────────────────────────────────────────────────
FAIL_KEYWORDS = re.compile(
    r"\b(fail|failed|failure|invalid|denied|unauthorized|refused|"
    r"blocked|rejected|forbidden|error|timeout|banned)\b", re.I
)
PRIV_KEYWORDS = re.compile(
    r"\b(root|admin|sudo|su\b|privilege|escalat|setuid|chmod\s+[74]|"
    r"passwd|shadow|visudo|wheel|sudoers)\b", re.I
)
ATTACK_KEYWORDS = re.compile(
    r"\b(scan|brute.?force|exploit|payload|inject|xss|sqli|"
    r"union\s+select|malware|ransomware|trojan|backdoor|shell|"
    r"exec\(|eval\(|base64|wget\s+http|curl\s+http|nc\s+-[el])\b", re.I
)
SENSITIVE_PATHS = re.compile(
    r"(/etc/passwd|/etc/shadow|/root/|/admin|/wp-admin|"
    r"/login|/.env|/config|/secret|/backup|/database)", re.I
)
UNUSUAL_HOURS = set(range(0, 6))  # midnight – 6am


def extract_features(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Given parsed log records, returns a DataFrame of numerical features.
    Each row = one log event.
    """
    rows = []
    # Pre-compute IP frequency and failed-login counts across the batch
    ip_counts: Dict[str, int] = {}
    fail_ip_counts: Dict[str, int] = {}
    user_counts: Dict[str, int] = {}

    for rec in records:
        ip = rec.get("source_ip") or ""
        msg = (rec.get("message") or "").lower()
        ip_counts[ip] = ip_counts.get(ip, 0) + 1
        if FAIL_KEYWORDS.search(msg):
            fail_ip_counts[ip] = fail_ip_counts.get(ip, 0) + 1
        user = rec.get("username") or ""
        user_counts[user] = user_counts.get(user, 0) + 1

    for rec in records:
        ip = rec.get("source_ip") or ""
        msg = (rec.get("message") or "").lower()
        path = (rec.get("path") or "").lower()
        username = (rec.get("username") or "").lower()
        event_type = (rec.get("event_type") or "").lower()
        status = rec.get("status_code") or "0"
        ts: Optional[datetime] = rec.get("timestamp")

        # 1. keyword flags
        fail_flag = int(bool(FAIL_KEYWORDS.search(msg)))
        priv_flag = int(bool(PRIV_KEYWORDS.search(msg + " " + username)))
        attack_flag = int(bool(ATTACK_KEYWORDS.search(msg + " " + path)))
        sensitive_path = int(bool(SENSITIVE_PATHS.search(path + " " + msg)))

        # 2. Status code
        try:
            status_int = int(status)
        except (ValueError, TypeError):
            status_int = 0
        is_4xx = int(400 <= status_int < 500)
        is_5xx = int(status_int >= 500)
        is_auth_fail = int(status_int in (401, 403))

        # 3. IP/user frequency
        ip_freq = ip_counts.get(ip, 0)
        fail_count = fail_ip_counts.get(ip, 0)
        user_freq = user_counts.get(username, 0)

        # 4. Time features
        hour = ts.hour if ts else -1
        unusual_hour = int(hour in UNUSUAL_HOURS) if hour >= 0 else 0
        is_weekend = int(ts.weekday() >= 5) if ts else 0

        # 5. Message features
        msg_len = len(msg)

        # 6. Known admin user
        is_admin_user = int(username in ("root", "admin", "administrator", "system"))

        # 7. Event type encoding
        event_map = {
            "auth_failure": 4, "suspicious_request": 5, "access_denied": 3,
            "not_found": 1, "http_request": 0, "login": 1, "logout": 0,
        }
        event_score = event_map.get(event_type, 0)

        rows.append({
            "fail_flag": fail_flag,
            "priv_flag": priv_flag,
            "attack_flag": attack_flag,
            "sensitive_path": sensitive_path,
            "is_4xx": is_4xx,
            "is_5xx": is_5xx,
            "is_auth_fail": is_auth_fail,
            "ip_frequency": min(ip_freq, 1000),
            "failed_login_count": min(fail_count, 100),
            "user_frequency": min(user_freq, 500),
            "unusual_hour": unusual_hour,
            "is_weekend": is_weekend,
            "msg_len": min(msg_len, 2000),
            "is_admin_user": is_admin_user,
            "event_score": event_score,
            "status_code_int": status_int,
        })

    return pd.DataFrame(rows)


FEATURE_COLUMNS = [
    "fail_flag", "priv_flag", "attack_flag", "sensitive_path",
    "is_4xx", "is_5xx", "is_auth_fail",
    "ip_frequency", "failed_login_count", "user_frequency",
    "unusual_hour", "is_weekend", "msg_len",
    "is_admin_user", "event_score", "status_code_int",
]
