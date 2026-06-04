"""
Log Parsers — supports syslog, Apache, HDFS, and generic CSV/structured logs.
Each parser returns a list of dicts with a common schema.
"""
import re
import csv
import json
import io
from datetime import datetime
from typing import List, Dict, Any, Optional


COMMON_FIELDS = [
    "timestamp", "source", "source_ip", "destination_ip",
    "username", "event_type", "status_code", "method",
    "path", "message", "severity", "raw_log",
]


def _empty_record() -> Dict[str, Any]:
    return {f: None for f in COMMON_FIELDS}


# ── Syslog Parser ─────────────────────────────────────────────────────────────
# Format: Jan 15 12:34:56 hostname process[pid]: message
SYSLOG_PATTERN = re.compile(
    r"(?P<month>\w+)\s+(?P<day>\d+)\s+(?P<time>[\d:]+)\s+"
    r"(?P<host>\S+)\s+(?P<process>\S+?)(?:\[(?P<pid>\d+)\])?:\s+(?P<message>.+)"
)
SYSLOG_FAIL_PATTERN = re.compile(r"(failed|failure|invalid|denied|unauthorized)", re.I)
SYSLOG_IP_PATTERN = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b")
SYSLOG_USER_PATTERN = re.compile(r"(?:user|for|from)\s+(\w+)", re.I)


def parse_syslog_line(line: str, year: int = None) -> Optional[Dict[str, Any]]:
    m = SYSLOG_PATTERN.match(line.strip())
    if not m:
        return None
    year = year or datetime.now().year
    try:
        ts = datetime.strptime(
            f"{m.group('month')} {int(m.group('day'))} {m.group('time')} {year}",
            "%b %d %H:%M:%S %Y"
        )
    except ValueError:
        ts = None

    record = _empty_record()
    record["timestamp"] = ts
    record["source"] = "syslog"
    record["message"] = m.group("message")
    record["raw_log"] = line.strip()
    record["event_type"] = m.group("process").split("/")[-1]

    msg = m.group("message")
    ips = SYSLOG_IP_PATTERN.findall(msg)
    record["source_ip"] = ips[0] if ips else None

    user_m = SYSLOG_USER_PATTERN.search(msg)
    record["username"] = user_m.group(1) if user_m else None

    if SYSLOG_FAIL_PATTERN.search(msg):
        record["severity"] = "warning"
        record["event_type"] = "auth_failure"
    else:
        record["severity"] = "info"

    return record


def parse_syslog(content: str) -> List[Dict[str, Any]]:
    records = []
    for line in content.splitlines():
        if not line.strip():
            continue
        r = parse_syslog_line(line)
        if r:
            records.append(r)
    return records


# ── Apache / Nginx Access Log Parser ─────────────────────────────────────────
# Combined Log Format: 127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /index.html HTTP/1.1" 200 2326
APACHE_PATTERN = re.compile(
    r'(?P<ip>\S+)\s+-\s+(?P<user>\S+)\s+\[(?P<time>[^\]]+)\]\s+'
    r'"(?P<method>\w+)\s+(?P<path>\S+)\s+\S+"\s+(?P<status>\d+)\s+(?P<size>\S+)'
    r'(?:\s+"(?P<referrer>[^"]*)"\s+"(?P<agent>[^"]*)")?'
)
SUSPICIOUS_PATHS = re.compile(
    r"(/admin|/etc/passwd|/wp-login|\.php\?|union\s+select|script>|"
    r"/\.env|/config|exec\(|eval\(|/shell|/cmd|base64)", re.I
)


def parse_apache_line(line: str) -> Optional[Dict[str, Any]]:
    m = APACHE_PATTERN.match(line.strip())
    if not m:
        return None

    try:
        ts = datetime.strptime(m.group("time"), "%d/%b/%Y:%H:%M:%S %z")
    except ValueError:
        ts = None

    record = _empty_record()
    record["timestamp"] = ts
    record["source"] = "apache"
    record["source_ip"] = m.group("ip")
    record["username"] = m.group("user") if m.group("user") != "-" else None
    record["method"] = m.group("method")
    record["path"] = m.group("path")
    record["status_code"] = m.group("status")
    record["raw_log"] = line.strip()
    record["message"] = f"{m.group('method')} {m.group('path')} [{m.group('status')}]"
    record["event_type"] = "http_request"

    status = int(m.group("status"))
    if status >= 500:
        record["severity"] = "error"
    elif status in (401, 403):
        record["severity"] = "warning"
        record["event_type"] = "access_denied"
    elif status == 404:
        record["severity"] = "info"
        record["event_type"] = "not_found"
    else:
        record["severity"] = "info"

    if SUSPICIOUS_PATHS.search(m.group("path")):
        record["severity"] = "high"
        record["event_type"] = "suspicious_request"

    return record


def parse_apache(content: str) -> List[Dict[str, Any]]:
    records = []
    for line in content.splitlines():
        if not line.strip():
            continue
        r = parse_apache_line(line)
        if r:
            records.append(r)
    return records


# ── HDFS Log Parser ───────────────────────────────────────────────────────────
# Format: 081109 203518 3 INFO dfs.DataNode$DataXceiver: Receiving block ...
HDFS_PATTERN = re.compile(
    r"(?P<date>\d{6})\s+(?P<time>\d{6})\s+(?P<pid>\d+)\s+"
    r"(?P<level>\w+)\s+(?P<component>\S+):\s+(?P<message>.+)"
)
HDFS_IP_PATTERN = re.compile(r"(?:from|to)\s+(/\S+:\d+)")


def parse_hdfs_line(line: str) -> Optional[Dict[str, Any]]:
    m = HDFS_PATTERN.match(line.strip())
    if not m:
        return None

    try:
        ts = datetime.strptime(m.group("date") + " " + m.group("time"), "%y%m%d %H%M%S")
    except ValueError:
        ts = None

    record = _empty_record()
    record["timestamp"] = ts
    record["source"] = "hdfs"
    record["event_type"] = m.group("component").split(".")[-1]
    record["message"] = m.group("message")
    record["raw_log"] = line.strip()
    level = m.group("level").upper()
    severity_map = {"INFO": "info", "WARN": "warning", "ERROR": "error", "FATAL": "critical"}
    record["severity"] = severity_map.get(level, "info")

    return record


def parse_hdfs(content: str) -> List[Dict[str, Any]]:
    records = []
    for line in content.splitlines():
        if not line.strip():
            continue
        r = parse_hdfs_line(line)
        if r:
            records.append(r)
    return records


# ── Generic CSV Parser ────────────────────────────────────────────────────────
TIMESTAMP_COLS = ["timestamp", "time", "datetime", "date", "@timestamp", "ts"]
IP_COLS = ["source_ip", "src_ip", "ip", "srcip", "src", "client_ip", "remote_addr"]
USER_COLS = ["username", "user", "uid", "account"]
MSG_COLS = ["message", "msg", "log", "description", "content", "text"]
SEV_COLS = ["severity", "level", "priority", "risk", "log_level"]
EVENT_COLS = ["event_type", "event", "action", "type", "category"]
STATUS_COLS = ["status_code", "status", "response_code", "http_status"]


def _find_col(headers: List[str], candidates: List[str]) -> Optional[str]:
    lower_headers = [h.lower() for h in headers]
    for c in candidates:
        if c in lower_headers:
            return headers[lower_headers.index(c)]
    return None


def parse_csv(content: str) -> List[Dict[str, Any]]:
    records = []
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        return records

    headers = list(reader.fieldnames)
    ts_col = _find_col(headers, TIMESTAMP_COLS)
    ip_col = _find_col(headers, IP_COLS)
    user_col = _find_col(headers, USER_COLS)
    msg_col = _find_col(headers, MSG_COLS)
    sev_col = _find_col(headers, SEV_COLS)
    event_col = _find_col(headers, EVENT_COLS)
    status_col = _find_col(headers, STATUS_COLS)

    for row in reader:
        record = _empty_record()
        record["source"] = "csv"
        record["raw_log"] = json.dumps(row)
        record["parsed_fields"] = json.dumps(row)

        # Timestamp
        if ts_col and row.get(ts_col):
            try:
                record["timestamp"] = datetime.fromisoformat(str(row[ts_col]).replace("Z", "+00:00"))
            except (ValueError, TypeError):
                record["timestamp"] = None

        record["source_ip"] = row.get(ip_col) if ip_col else None
        record["username"] = row.get(user_col) if user_col else None
        record["message"] = row.get(msg_col) if msg_col else None
        record["event_type"] = row.get(event_col) if event_col else None
        record["status_code"] = str(row.get(status_col, "")) if status_col else None

        sev_raw = str(row.get(sev_col, "")).lower() if sev_col else ""
        if "crit" in sev_raw or "alert" in sev_raw or "fatal" in sev_raw:
            record["severity"] = "critical"
        elif "high" in sev_raw or "error" in sev_raw or "err" == sev_raw:
            record["severity"] = "high"
        elif "warn" in sev_raw or "medium" in sev_raw:
            record["severity"] = "warning"
        elif "low" in sev_raw or "info" in sev_raw:
            record["severity"] = "info"
        else:
            record["severity"] = "info"

        records.append(record)

    return records


# ── Auto Dispatcher ───────────────────────────────────────────────────────────
def detect_format(content: str, filename: str = "") -> str:
    fn = filename.lower()
    if fn.endswith(".csv"):
        return "csv"
    if fn.endswith(".json"):
        return "json"

    lines = [l for l in content.splitlines() if l.strip()]
    if not lines:
        return "unknown"

    sample = lines[0]
    if SYSLOG_PATTERN.match(sample):
        return "syslog"
    if APACHE_PATTERN.match(sample):
        return "apache"
    if HDFS_PATTERN.match(sample):
        return "hdfs"
    if "," in sample and any(k in sample.lower() for k in ["timestamp", "ip", "event"]):
        return "csv"
    return "syslog"   # default fallback


def parse_logs(content: str, filename: str = "", fmt: str = None) -> List[Dict[str, Any]]:
    """Main entry point — auto-detect format and parse."""
    fmt = fmt or detect_format(content, filename)
    parsers = {
        "syslog": parse_syslog,
        "apache": parse_apache,
        "hdfs": parse_hdfs,
        "csv": parse_csv,
    }
    parser = parsers.get(fmt, parse_syslog)
    return parser(content)
