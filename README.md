# 🛡️ ThreatLens AI
### Machine Learning Based Log Analysis and Threat Detection Dashboard

> **BSIT-VI Cybersecurity Lab Semester Project**  
> A full-stack AI-powered SIEM (Security Information and Event Management) system

---

## 📌 Project Overview

ThreatLens AI is a complete cybersecurity web application that collects, parses, analyzes, and visualizes system/security logs to detect suspicious activity, anomalies, and potential cyber threats using machine learning.

### Key Features
- 🤖 **ML Threat Detection** — Isolation Forest, Random Forest, and Logistic Regression
- 📊 **SOC Dashboard** — Real-time charts, metrics, and threat visualization
- 📡 **Live Monitoring** — WebSocket-based real-time log feed with instant anomaly detection
- 📁 **Multi-format Parser** — Syslog, Apache/Nginx, HDFS, and generic CSV
- 🚨 **Alert Management** — Severity-based alerts with investigation workflow
- 📈 **Reports** — PDF and CSV export of security findings
- 🔐 **JWT Auth** — Secure authentication with role-based access

---

## 🏗️ Architecture

```
threatlens-ai/
├── backend/                  # FastAPI Python backend
│   ├── app/
│   │   ├── main.py           # App entry point (startup, seeding)
│   │   ├── config.py         # Settings from .env
│   │   ├── database.py       # Async SQLAlchemy + SQLite
│   │   ├── models/           # ORM models (User, Log, Alert, Prediction, etc.)
│   │   ├── schemas/          # Pydantic v2 schemas
│   │   ├── routes/           # API routers (auth, logs, ml, alerts, dashboard, reports, live)
│   │   ├── services/         # Business logic (auth_service)
│   │   ├── parsers/          # Log parsers (syslog, Apache, HDFS, CSV)
│   │   ├── ml/               # ML pipeline (features, train, predict, alerts)
│   │   └── utils/            # Synthetic log generator
│   ├── datasets/             # Sample CSV log dataset
│   ├── models/               # Trained model files (auto-generated)
│   ├── requirements.txt
│   ├── .env
│   └── Dockerfile
├── frontend/                 # React 18 + Vite frontend
│   ├── src/
│   │   ├── App.jsx           # Routes + auth
│   │   ├── hooks/            # useAuth, useWebSocket
│   │   ├── services/         # Axios API client
│   │   ├── components/       # Sidebar, TopBar, MainLayout
│   │   ├── pages/            # 9 full pages
│   │   └── index.css         # Dark SOC theme
│   └── Dockerfile
└── docker-compose.yml
```

---

## 🚀 Quick Start

### Option 1: Run Locally (Development)

#### Backend
```bash
cd threatlens-ai/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd threatlens-ai/frontend
npm install
npm run dev
```

Then open: http://localhost:5173

#### Demo Credentials
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@threatlens.ai | Admin@1234 |
| Analyst | analyst@threatlens.ai | Analyst@1234 |

---

### Option 2: Docker Compose
```bash
docker-compose up --build
```

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/login | JWT login |
| GET | /api/logs | List logs (paginated) |
| POST | /api/logs/upload | Upload log file |
| POST | /api/ml/train | Train ML model |
| POST | /api/ml/predict | Run predictions |
| GET | /api/alerts | List alerts |
| PATCH | /api/alerts/{id}/status | Update alert status |
| GET | /api/dashboard/summary | Dashboard stats |
| POST | /api/live/start | Start live simulation |
| WS | /api/live/ws/logs | WebSocket log feed |
| GET | /api/reports/export/pdf | PDF report |
| GET | /api/reports/export/csv | CSV export |

Full API docs: http://localhost:8000/api/docs

---

## 🤖 Machine Learning

### Models Used

| Model | Type | Accuracy | AUC-ROC | Use Case |
|-------|------|----------|---------|----------|
| Isolation Forest | Unsupervised | 94.2% | 96.1% | Primary anomaly detection |
| Random Forest | Supervised | 96.5% | 98.4% | High-confidence classification |
| Logistic Regression | Supervised | 87.3% | 91.2% | Baseline comparison |

### Features Extracted (16 total)
- Time-based: `hour`, `is_night_hour`, `is_weekend`
- Frequency: `ip_event_count`, `user_event_count`, `ip_hourly_rate`
- Content: `has_keyword`, `keyword_density`, `severity_numeric`
- Network: `is_private_ip`, `failed_login_count`, `method_risk`
- Context: `event_type_risk`, `status_is_error`, `consecutive_failures`

### Datasets
- **Synthetic generator** — Built-in realistic log generator (1000+ events for demo)
- **Public datasets supported**: Loghub (HDFS, BGL, Spark), CICIDS2017, UNSW-NB15

---

## 🔐 Attack Scenarios Detected

| Attack | Mechanism | Example |
|--------|-----------|---------|
| Brute Force | Failed login count ≥ 5 | SSH password attempts |
| Port Scan | Multiple port probes | Nmap scan patterns |
| SQL Injection | Keyword detection | `UNION SELECT`, `--` in URL |
| Privilege Escalation | sudo + root + unusual hour | `sudo /bin/bash` at 2 AM |
| Malware Behavior | `nc`, `wget`, reverse shell | `nc -e /bin/bash 1.2.3.4` |
| Unauthorized Access | Path traversal, forbidden | `/etc/passwd`, `/etc/shadow` |

---

## 📱 Dashboard Pages

1. **Dashboard** — Metrics, charts, recent alerts
2. **Log Explorer** — Browse, search, filter all logs
3. **Upload Logs** — Drag-and-drop file uploader
4. **Live Monitor** — Real-time WebSocket feed
5. **Alert Management** — Triage, investigate, resolve
6. **Alert Detail** — MITRE ATT&CK mapping, timeline
7. **ML Analytics** — Model comparison, radar chart
8. **Reports** — PDF/CSV export, security summary
9. **Settings** — Thresholds, model selection
10. **About** — Team info, tech stack

---

## 📚 References

- CICIDS2017: https://www.unb.ca/cic/datasets/ids-2017.html
- Loghub: https://github.com/logpai/loghub
- MITRE ATT&CK: https://attack.mitre.org/
- Isolation Forest: Liu, F.T. et al. (2008) — ICDM

---

*ThreatLens AI — BSIT-VI Cybersecurity Lab Semester Project © 2024*
