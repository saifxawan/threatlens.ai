"""
ML Training Pipeline for ThreatLens AI.

Trains:
1. Isolation Forest (unsupervised anomaly detection)
  2. Random Forest Classifier (if labels available)
  3. One-Class SVM (alternative unsupervised)
  4. Logistic Regression (baseline)

Saves models to model_store/ using joblib.
"""
import joblib
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List

from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.svm import OneClassSVM
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix
)

from app.config import settings
from app.ml.feature_engineering import extract_features, FEATURE_COLUMNS

MODEL_STORE = settings.MODEL_DIR


def _save_model(model, name: str, metadata: dict = None):
    path = MODEL_STORE / f"{name}.joblib"
    joblib.dump(model, path)
    if metadata:
        meta_path = MODEL_STORE / f"{name}_meta.json"
        meta_path.write_text(json.dumps(metadata, indent=2, default=str))
    return path


def _load_model(name: str):
    path = MODEL_STORE / f"{name}.joblib"
    if path.exists():
        return joblib.load(path)
    return None


def _load_meta(name: str) -> dict:
    path = MODEL_STORE / f"{name}_meta.json"
    if path.exists():
        return json.loads(path.read_text())
    return {}


# ── Train Isolation Forest (unsupervised) ─────────────────────────────────────
def train_isolation_forest(
    records: List[Dict[str, Any]],
    contamination: float = 0.05,
) -> Dict[str, Any]:
    """Train Isolation Forest and save model."""
    df = extract_features(records)
    X = df[FEATURE_COLUMNS].fillna(0).values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    # Pseudo-evaluation on training data
    preds = model.predict(X_scaled)           # 1=normal, -1=anomaly
    anomaly_count = int((preds == -1).sum())
    scores = model.score_samples(X_scaled)    # raw anomaly scores
    avg_score = float(np.mean(scores))

    _save_model(model, "isolation_forest")
    _save_model(scaler, "isolation_forest_scaler")

    metadata = {
        "model_name": "Isolation Forest",
        "contamination": contamination,
        "training_samples": len(X),
        "anomaly_count_train": anomaly_count,
        "avg_score_train": avg_score,
        "feature_columns": FEATURE_COLUMNS,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_model(model, "isolation_forest")
    meta_path = MODEL_STORE / "isolation_forest_meta.json"
    meta_path.write_text(json.dumps(metadata, indent=2, default=str))

    return {
        "model_name": "Isolation Forest",
        "training_samples": len(X),
        "anomaly_count": anomaly_count,
        "contamination": contamination,
        "avg_score": avg_score,
        "status": "trained",
    }


# ── Train Random Forest (supervised, if labels available) ─────────────────────
def train_random_forest(
    records: List[Dict[str, Any]],
    labels: List[int],          # 0 = normal, 1 = anomaly/attack
) -> Dict[str, Any]:
    """Train Random Forest classifier and save model."""
    df = extract_features(records)
    X = df[FEATURE_COLUMNS].fillna(0).values
    y = np.array(labels)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    model = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train_s, y_train)
    y_pred = model.predict(X_test_s)
    y_prob = model.predict_proba(X_test_s)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    try:
        auc = float(roc_auc_score(y_test, y_prob))
    except Exception:
        auc = 0.0
    cm = confusion_matrix(y_test, y_pred).tolist()
    tn, fp, fn, tp = cm[0][0], cm[0][1], cm[1][0], cm[1][1]
    fpr = fp / (fp + tn + 1e-9)

    _save_model(model, "random_forest")
    _save_model(scaler, "random_forest_scaler")

    metadata = {
        "model_name": "Random Forest",
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "auc_roc": auc,
        "false_positive_rate": fpr,
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "confusion_matrix": cm,
        "feature_columns": FEATURE_COLUMNS,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    meta_path = MODEL_STORE / "random_forest_meta.json"
    meta_path.write_text(json.dumps(metadata, indent=2, default=str))

    return {
        "model_name": "Random Forest",
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "auc_roc": auc,
        "false_positive_rate": fpr,
        "confusion_matrix": cm,
        "training_samples": len(X_train),
        "status": "trained",
    }


# ── Train Logistic Regression (baseline) ──────────────────────────────────────
def train_logistic_regression(
    records: List[Dict[str, Any]],
    labels: List[int],
) -> Dict[str, Any]:
    df = extract_features(records)
    X = df[FEATURE_COLUMNS].fillna(0).values
    y = np.array(labels)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    model = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
    model.fit(X_train_s, y_train)
    y_pred = model.predict(X_test_s)
    try:
        y_prob = model.predict_proba(X_test_s)[:, 1]
        auc = float(roc_auc_score(y_test, y_prob))
    except Exception:
        auc = 0.0

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    cm = confusion_matrix(y_test, y_pred).tolist()
    tn, fp, fn, tp = cm[0][0], cm[0][1], cm[1][0], cm[1][1]
    fpr = fp / (fp + tn + 1e-9)

    _save_model(model, "logistic_regression")
    _save_model(scaler, "logistic_regression_scaler")

    metadata = {
        "model_name": "Logistic Regression",
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "auc_roc": auc,
        "false_positive_rate": fpr,
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "confusion_matrix": cm,
        "feature_columns": FEATURE_COLUMNS,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    meta_path = MODEL_STORE / "logistic_regression_meta.json"
    meta_path.write_text(json.dumps(metadata, indent=2, default=str))

    return {
        "model_name": "Logistic Regression",
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "auc_roc": auc,
        "false_positive_rate": fpr,
        "confusion_matrix": cm,
        "training_samples": len(X_train),
        "status": "trained",
    }


def _generate_labels(records: List[Dict[str, Any]]) -> List[int]:
    """Generate heuristic binary labels for logs based on security indicators."""
    df = extract_features(records)
    labels = []
    for i in range(len(records)):
        feat_row = df.iloc[i].to_dict()
        # Heuristic rules matching security anomalies
        is_attack = (
            feat_row.get("attack_flag", 0) > 0 or
            feat_row.get("failed_login_count", 0) >= 5 or
            (feat_row.get("priv_flag", 0) > 0 and feat_row.get("is_admin_user", 0) > 0) or
            (feat_row.get("sensitive_path", 0) > 0 and feat_row.get("is_auth_fail", 0) > 0) or
            feat_row.get("event_score", 0) >= 70
        )
        labels.append(1 if is_attack else 0)
    
    # Ensure there are at least some positive and negative samples
    if sum(labels) == 0:
        labels[0] = 1
        labels[1] = 1
    elif sum(labels) == len(labels):
        labels[0] = 0
        labels[1] = 0
        
    return labels


# ── Auto train on demo data ───────────────────────────────────────────────────
def train_on_demo_data() -> Dict[str, Any]:
    """Train all models on synthetic demo data so API is ready immediately."""
    from app.utils.log_generator import generate_demo_records
    records = generate_demo_records(1000)
    
    if_res = train_isolation_forest(records, contamination=0.1)
    
    labels = _generate_labels(records)
    rf_res = train_random_forest(records, labels)
    lr_res = train_logistic_regression(records, labels)
    
    return {
        "isolation_forest": if_res,
        "random_forest": rf_res,
        "logistic_regression": lr_res,
    }


def get_model_info() -> List[Dict[str, Any]]:
    """Return info about all saved models."""
    models = ["isolation_forest", "random_forest", "logistic_regression"]
    result = []
    for m in models:
        meta = _load_meta(m)
        exists = (MODEL_STORE / f"{m}.joblib").exists()
        result.append({
            "model_name": meta.get("model_name", m),
            "exists": exists,
            "metadata": meta,
        })
    return result
