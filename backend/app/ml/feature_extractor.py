"""
Feature Extractor for ThreatLens AI - Hybrid AI Threat Intelligence Engine.

Extracts both the 16 core base features and 13 advanced contextual/network features
from parsed system and security logs.
"""
import re
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Core regular expressions
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
ENCODED_PAYLOADS = re.compile(
    r"(%[0-9a-f]{2}|[a-zA-Z0-9+/]{40,}=*|\b0x[0-9a-fA-F]+\b)", re.I
)
UNUSUAL_HOURS = set(range(0, 6))  # 12 AM to 6 AM

FEATURE_COLUMNS = [
    # Original 16 features
    "fail_flag", "priv_flag", "attack_flag", "sensitive_path",
    "is_4xx", "is_5xx", "is_auth_fail",
    "ip_frequency", "failed_login_count", "user_frequency",
    "unusual_hour", "is_weekend", "msg_len",
    "is_admin_user", "event_score", "status_code_int",
    # Advanced 13 features
    "request_rate_per_ip", "unique_paths_per_ip", "unique_users_per_ip",
    "failed_login_ratio", "admin_path_access_count", "suspicious_keyword_count",
    "path_depth", "query_length", "special_char_count",
    "encoded_payload_flag", "repeated_401_403_count", "time_since_last_event",
    "session_event_count"
]

def extract_features(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Given a list of parsed log records, extracts 29 numerical features.
    Handles empty values gracefully with safe defaults.
    """
    if not records:
        return pd.DataFrame(columns=FEATURE_COLUMNS)

    # 1. Pre-calculate batch aggregations
    ip_stats = {}      # ip -> {total, fails, paths, users, repeated_401_403, last_time, events}
    user_stats = {}    # user -> total_events

    for rec in records:
        ip = rec.get("source_ip") or "unknown"
        user = (rec.get("username") or "unknown").lower()
        msg = (rec.get("message") or "").lower()
        path = (rec.get("path") or "").lower()
        status_code = str(rec.get("status_code") or "0")
        
        # Parse timestamp
        ts = rec.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                ts = datetime.now(timezone.utc)
        elif not isinstance(ts, datetime):
            ts = datetime.now(timezone.utc)

        # Initialize IP stats
        if ip not in ip_stats:
            ip_stats[ip] = {
                "total": 0, "fails": 0, "paths": set(), "users": set(),
                "repeated_401_403": 0, "last_time": ts, "events": []
            }
        
        stats = ip_stats[ip]
        stats["total"] += 1
        stats["paths"].add(path)
        stats["users"].add(user)
        stats["events"].append((ts, path, user, status_code, msg))
        
        if FAIL_KEYWORDS.search(msg) or status_code in ("401", "403"):
            stats["fails"] += 1
            
        if status_code in ("401", "403"):
            stats["repeated_401_403"] += 1

        user_stats[user] = user_stats.get(user, 0) + 1

    # 2. Extract row-level features
    rows = []
    for rec in records:
        ip = rec.get("source_ip") or "unknown"
        msg = (rec.get("message") or "").lower()
        path = (rec.get("path") or "").lower()
        username = (rec.get("username") or "unknown").lower()
        event_type = (rec.get("event_type") or "").lower()
        status = str(rec.get("status_code") or "0")
        
        # Parse row timestamp
        ts = rec.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                ts = datetime.now(timezone.utc)
        elif not isinstance(ts, datetime):
            ts = datetime.now(timezone.utc)

        # --- Base 16 features ---
        fail_flag = int(bool(FAIL_KEYWORDS.search(msg)))
        priv_flag = int(bool(PRIV_KEYWORDS.search(msg + " " + username)))
        attack_flag = int(bool(ATTACK_KEYWORDS.search(msg + " " + path)))
        sensitive_path = int(bool(SENSITIVE_PATHS.search(path + " " + msg)))

        try:
            status_int = int(status)
        except (ValueError, TypeError):
            status_int = 0
            
        is_4xx = int(400 <= status_int < 500)
        is_5xx = int(status_int >= 500)
        is_auth_fail = int(status_int in (401, 403))

        ip_freq = ip_stats[ip]["total"]
        failed_login_count = ip_stats[ip]["fails"]
        user_freq = user_stats.get(username, 0)

        hour = ts.hour if ts else -1
        unusual_hour = int(hour in UNUSUAL_HOURS) if hour >= 0 else 0
        is_weekend = int(ts.weekday() >= 5) if ts else 0
        msg_len = len(msg)
        is_admin_user = int(username in ("root", "admin", "administrator", "system"))

        event_map = {
            "auth_failure": 4, "suspicious_request": 5, "access_denied": 3,
            "not_found": 1, "http_request": 0, "login": 1, "logout": 0,
        }
        event_score = event_map.get(event_type, 0)

        # --- Advanced 13 features ---
        # 17. request_rate_per_ip
        request_rate_per_ip = float(ip_freq) / max(len(records), 1)
        
        # 18. unique_paths_per_ip
        unique_paths_per_ip = len(ip_stats[ip]["paths"])
        
        # 19. unique_users_per_ip
        unique_users_per_ip = len(ip_stats[ip]["users"])
        
        # 20. failed_login_ratio
        failed_login_ratio = float(failed_login_count) / max(ip_freq, 1)
        
        # 21. admin_path_access_count
        admin_path_access_count = sum(1 for p in ip_stats[ip]["paths"] if SENSITIVE_PATHS.search(p))
        
        # 22. suspicious_keyword_count
        suspicious_keyword_count = (
            len(FAIL_KEYWORDS.findall(msg)) + 
            len(PRIV_KEYWORDS.findall(msg + " " + username)) + 
            len(ATTACK_KEYWORDS.findall(msg + " " + path))
        )
        
        # 23. path_depth
        path_depth = path.count("/")
        
        # 24. query_length
        query_parts = path.split("?")
        query_length = len(query_parts[1]) if len(query_parts) > 1 else 0
        
        # 25. special_char_count
        special_char_count = sum(1 for c in (msg + path) if c in ("'", '"', "-", "<", ">", ";", "%", "(", ")"))
        
        # 26. encoded_payload_flag
        encoded_payload_flag = int(bool(ENCODED_PAYLOADS.search(msg + " " + path)))
        
        # 27. repeated_401_403_count
        repeated_401_403_count = ip_stats[ip]["repeated_401_403"]
        
        # 28. time_since_last_event
        # Calculate diff in seconds with previous event in batch for this IP
        ip_events = sorted(ip_stats[ip]["events"], key=lambda x: x[0])
        time_since_last_event = 999.0
        for idx, ev in enumerate(ip_events):
            if ev[0] == ts and idx > 0:
                time_since_last_event = float((ts - ip_events[idx-1][0]).total_seconds())
                break
        
        # 29. session_event_count
        session_event_count = user_freq

        rows.append({
            # Base 16
            "fail_flag": fail_flag,
            "priv_flag": priv_flag,
            "attack_flag": attack_flag,
            "sensitive_path": sensitive_path,
            "is_4xx": is_4xx,
            "is_5xx": is_5xx,
            "is_auth_fail": is_auth_fail,
            "ip_frequency": min(ip_freq, 1000),
            "failed_login_count": min(failed_login_count, 100),
            "user_frequency": min(user_freq, 500),
            "unusual_hour": unusual_hour,
            "is_weekend": is_weekend,
            "msg_len": min(msg_len, 2000),
            "is_admin_user": is_admin_user,
            "event_score": event_score,
            "status_code_int": status_int,
            # Advanced 13
            "request_rate_per_ip": min(request_rate_per_ip, 100.0),
            "unique_paths_per_ip": min(unique_paths_per_ip, 100),
            "unique_users_per_ip": min(unique_users_per_ip, 100),
            "failed_login_ratio": failed_login_ratio,
            "admin_path_access_count": min(admin_path_access_count, 50),
            "suspicious_keyword_count": min(suspicious_keyword_count, 20),
            "path_depth": min(path_depth, 20),
            "query_length": min(query_length, 500),
            "special_char_count": min(special_char_count, 100),
            "encoded_payload_flag": encoded_payload_flag,
            "repeated_401_403_count": min(repeated_401_403_count, 50),
            "time_since_last_event": min(time_since_last_event, 3600.0),
            "session_event_count": min(session_event_count, 1000)
        })

    return pd.DataFrame(rows)[FEATURE_COLUMNS]
