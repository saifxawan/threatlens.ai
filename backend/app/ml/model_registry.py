"""
Model Registry for ThreatLens AI.

Manages all loaded machine learning model instances, serialization checkpoints, 
and algorithm metadata details.
"""
import os
import joblib
from datetime import datetime
from typing import Dict, Any, List, Optional

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")

# Standard model configurations metadata
ALGORITHMS = {
    "isolation_forest": {"name": "Isolation Forest", "type": "Unsupervised Anomaly Detector", "desc": "Detects unknown threat profiles."},
    "logistic_regression": {"name": "Logistic Regression", "type": "Supervised Binary Classifier", "desc": "Fast baseline security scoring."},
    "decision_tree": {"name": "Decision Tree", "type": "Supervised Decision Explainer", "desc": "Human-readable threat logic splits."},
    "random_forest": {"name": "Random Forest", "type": "Supervised Multi-Class Threat Classifier", "desc": "Highly robust incident category tagging."},
    "svm": {"name": "Support Vector Machine", "type": "Supervised Hyperplane Classifier", "desc": "Separates benign logs from malicious attacks."},
    "kmeans": {"name": "K-Means Clustering", "type": "Unsupervised Behavioral Grouper", "desc": "Clusters related log footprints into behavior profiles."},
    "knn": {"name": "K-Nearest Neighbors", "type": "Incident Matcher", "desc": "Finds most similar historic threat records."},
    "naive_bayes": {"name": "Naïve Bayes Text Classifier", "type": "TF-IDF Text Threat Classifier", "desc": "Analyzes raw log payload structures."},
    "linear_regression": {"name": "Linear Regression Forecaster", "type": "Trend Predictor", "desc": "Forecasts next-hour security alert volume."},
    "xgboost": {"name": "XGBoost Stub", "type": "Gradient Booster Hooks", "desc": "Reserved advanced classifier stubs."},
    "deep_learning": {"name": "LogBERT & GNN Hooks", "type": "Neural Network Hooks", "desc": "Extensible Deep Learning stubs."}
}

class ModelRegistry:
    """Central manager for active in-memory models and saved joblib checkpoints."""
    def __init__(self):
        self._loaded_models: Dict[str, Any] = {}
        self.active_model_name: str = "isolation_forest"

    def get_model(self, algo_key: str) -> Optional[Any]:
        """Retrieve model object from cache, load from disk if not loaded."""
        if algo_key in self._loaded_models:
            return self._loaded_models[algo_key]
            
        model = self.load_model_from_disk(algo_key)
        if model:
            self._loaded_models[algo_key] = model
            return model
        return None

    def register_model(self, algo_key: str, model_object: Any):
        """Cache model in memory."""
        self._loaded_models[algo_key] = model_object

    def load_model_from_disk(self, algo_key: str) -> Optional[Any]:
        """Load joblib model file from standard models directory."""
        path = os.path.join(MODEL_DIR, f"{algo_key}_model.joblib")
        if os.path.exists(path):
            try:
                return joblib.load(path)
            except Exception:
                pass
        return None

    def get_all_metadata(self, db_metrics: List[Any] = None) -> List[Dict[str, Any]]:
        """Compiles detailed status list of all algorithms for comparison dashboard."""
        results = []
        metrics_dict = {m.model_name.lower().replace(" ", "_"): m for m in db_metrics} if db_metrics else {}
        
        for key, meta in ALGORITHMS.items():
            path = os.path.join(MODEL_DIR, f"{key}_model.joblib")
            
            # Special check for custom text NB model which has its own path
            if key == "naive_bayes":
                path = os.path.join(MODEL_DIR, "text_nb_classifier.joblib")
            elif key == "kmeans":
                path = os.path.join(MODEL_DIR, "kmeans_clustering.joblib")
            elif key == "knn":
                path = os.path.join(MODEL_DIR, "knn_similarity.joblib")
            elif key == "linear_regression":
                path = os.path.join(MODEL_DIR, "trend_forecaster.joblib")

            is_saved = os.path.exists(path) or key in ("xgboost", "deep_learning")
            
            # Fetch DB metrics if available
            db_metric = metrics_dict.get(key) or metrics_dict.get(meta["name"].lower().replace(" ", "_"))
            
            trained_at = None
            accuracy = None
            precision = None
            recall = None
            f1_score = None
            samples = None

            if db_metric:
                trained_at = db_metric.training_date.isoformat() if db_metric.training_date else None
                accuracy = db_metric.accuracy
                precision = db_metric.precision
                recall = db_metric.recall
                f1_score = db_metric.f1_score
                samples = db_metric.training_samples
            elif is_saved:
                trained_at = datetime.fromtimestamp(os.path.getmtime(path)).isoformat() if os.path.exists(path) else None

            results.append({
                "model_key": key,
                "model_name": meta["name"],
                "model_type": meta["type"],
                "description": meta["desc"],
                "is_active": int(key == self.active_model_name),
                "is_trained": int(is_saved),
                "trained_at": trained_at,
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score,
                "training_samples": samples
            })
            
        return results

# Instantiate global model registry
model_registry = ModelRegistry()
