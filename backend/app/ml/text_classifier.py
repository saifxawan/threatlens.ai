"""
Text Threat Classifier using TF-IDF + Multinomial Naïve Bayes.

Classifies log text (message, path, raw log) into specific attack types:
- SQL Injection
- Malware Command
- Directory Traversal
- Brute Force Message
- Normal Text
"""
import joblib
import os
import pandas as pd
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "text_nb_classifier.joblib")

CLASSES = [
    "Normal Text",
    "SQL Injection",
    "Malware Command",
    "Directory Traversal",
    "Brute Force Message"
]

class LogTextClassifier:
    """TF-IDF Vectorizer + Naïve Bayes log classifier."""
    def __init__(self):
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=5000, token_pattern=r'(?u)\b\w+\b', ngram_range=(1, 2))),
            ('nb', MultinomialNB(alpha=0.1))
        ])
        self.is_trained = False

    def train(self, texts: List[str], labels: List[str]):
        """Train Naïve Bayes classifier on labeled text streams."""
        if not texts or not labels:
            return
        self.pipeline.fit(texts, labels)
        self.is_trained = True
        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(self.pipeline, MODEL_PATH)

    def load(self) -> bool:
        """Load trained model weights if they exist."""
        if os.path.exists(MODEL_PATH):
            try:
                self.pipeline = joblib.load(MODEL_PATH)
                self.is_trained = True
                return True
            except Exception:
                pass
        return False

    def predict(self, text: str) -> Tuple[str, float]:
        """Classify single log text and return threat label + confidence score."""
        if not self.is_trained and not self.load():
            # If not trained yet, use simple heuristic rules
            return self._predict_heuristic(text)
        
        try:
            pred = self.pipeline.predict([text])[0]
            probs = self.pipeline.predict_proba([text])[0]
            class_idx = list(self.pipeline.classes_).index(pred)
            confidence = float(probs[class_idx])
            
            # Map back standard threat class name
            return pred, confidence
        except Exception:
            return self._predict_heuristic(text)

    def _predict_heuristic(self, text: str) -> Tuple[str, float]:
        """Rule-based text parser fallback."""
        text_lower = text.lower()
        if "union select" in text_lower or "select " in text_lower and "from " in text_lower or "' or " in text_lower:
            return "SQL Injection", 0.85
        elif "etc/passwd" in text_lower or "etc/shadow" in text_lower or "../" in text_lower or "..\\" in text_lower:
            return "Directory Traversal", 0.90
        elif "wget " in text_lower or "curl " in text_lower or "nc -e" in text_lower or "eval(" in text_lower or "exec(" in text_lower:
            return "Malware Command", 0.88
        elif "fail" in text_lower and ("login" in text_lower or "password" in text_lower or "auth" in text_lower):
            return "Brute Force Message", 0.80
        return "Normal Text", 0.95

# Instantiate global singleton log text classifier
text_threat_classifier = LogTextClassifier()
