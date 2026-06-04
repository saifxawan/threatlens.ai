"""
K-Means Clustering Engine for ThreatLens AI.

Unsupervised grouping of similar logs into attack behaviors:
- Cluster 0: Normal Traffic
- Cluster 1: Failed Login-heavy Traffic
- Cluster 2: Exploit & Payload Activity (SQL Injection, Traversal)
- Cluster 3: Suspicious Sudo & Admin command execution
"""
import os
import joblib
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "kmeans_clustering.joblib")

CLUSTER_INFO = {
    0: {"label": "Normal Traffic", "risk_level": "low", "risk_score": 10},
    1: {"label": "Authentication Failure Activity", "risk_level": "medium", "risk_score": 45},
    2: {"label": "Web Exploit & Command Payload", "risk_level": "high", "risk_score": 75},
    3: {"label": "Privileged Admin Operations", "risk_level": "high", "risk_score": 80},
    4: {"label": "Rapid High-Frequency Anomalies", "risk_level": "critical", "risk_score": 90}
}

class SecurityClustering:
    """K-Means behavioral clustering module."""
    def __init__(self):
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=5, random_state=42, n_init='auto')
        self.is_trained = False

    def train(self, df_features: pd.DataFrame):
        """Train K-Means clustering model."""
        if df_features.empty:
            return
        
        # Scale features
        scaled = self.scaler.fit_transform(df_features)
        self.kmeans.fit(scaled)
        self.is_trained = True
        
        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump({"scaler": self.scaler, "kmeans": self.kmeans}, MODEL_PATH)

    def load(self) -> bool:
        """Load K-Means clustering components from checkpoint."""
        if os.path.exists(MODEL_PATH):
            try:
                ckpt = joblib.load(MODEL_PATH)
                self.scaler = ckpt["scaler"]
                self.kmeans = ckpt["kmeans"]
                self.is_trained = True
                return True
            except Exception:
                pass
        return False

    def predict(self, df_features: pd.DataFrame) -> List[Dict[str, Any]]:
        """Assign clusters and distances to a batch of log records."""
        if df_features.empty:
            return []
            
        if not self.is_trained and not self.load():
            # Fallback mock predictions if model is not yet fit
            return self._predict_fallback(df_features)

        try:
            scaled = self.scaler.transform(df_features)
            cluster_ids = self.kmeans.predict(scaled)
            centroids = self.kmeans.cluster_centers_
            
            results = []
            for idx, c_id in enumerate(cluster_ids):
                # Calculate Euclidean distance to centroid
                feat_vec = scaled[idx]
                centroid_vec = centroids[c_id]
                dist = float(np.linalg.norm(feat_vec - centroid_vec))
                
                info = CLUSTER_INFO.get(c_id, {"label": "Unclassified Group", "risk_level": "low", "risk_score": 0})
                
                results.append({
                    "cluster_id": int(c_id),
                    "cluster_label": info["label"],
                    "distance_to_centroid": round(dist, 3),
                    "cluster_risk_level": info["risk_level"],
                    "cluster_risk_score": info["risk_score"]
                })
            return results
        except Exception:
            return self._predict_fallback(df_features)

    def _predict_fallback(self, df_features: pd.DataFrame) -> List[Dict[str, Any]]:
        """Fallback cluster mapping using core feature rules."""
        results = []
        for _, row in df_features.iterrows():
            if row.get("attack_flag", 0) > 0 or row.get("sensitive_path", 0) > 0:
                c_id, label, risk, score = 2, "Web Exploit & Command Payload", "high", 75
            elif row.get("failed_login_count", 0) >= 3 or row.get("is_auth_fail", 0) > 0:
                c_id, label, risk, score = 1, "Authentication Failure Activity", "medium", 45
            elif row.get("priv_flag", 0) > 0 or row.get("is_admin_user", 0) > 0:
                c_id, label, risk, score = 3, "Privileged Admin Operations", "high", 80
            elif row.get("ip_frequency", 0) > 50:
                c_id, label, risk, score = 4, "Rapid High-Frequency Anomalies", "critical", 90
            else:
                c_id, label, risk, score = 0, "Normal Traffic", "low", 10

            results.append({
                "cluster_id": c_id,
                "cluster_label": label,
                "distance_to_centroid": 1.25,
                "cluster_risk_level": risk,
                "cluster_risk_score": score
            })
        return results

# Instantiate global clustering model
security_clustering = SecurityClustering()
