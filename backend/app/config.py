"""
ThreatLens AI — Application Configuration
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pathlib import Path
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ThreatLens AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "threatlens-secret-key-change-in-production-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./threatlens.db"

    # Directories
    BASE_DIR: Path = Path(__file__).parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    MODEL_DIR: Path = BASE_DIR / "ml" / "model_store"
    DATASET_DIR: Path = BASE_DIR.parent / "datasets"

    # ML Settings
    ANOMALY_THRESHOLD: float = 0.0      # Isolation Forest: scores < threshold are anomalies
    RISK_SCORE_WEIGHTS: dict = {
        "anomaly_score": 0.4,
        "failed_login_count": 0.15,
        "ip_frequency": 0.1,
        "suspicious_keywords": 0.15,
        "unusual_hour": 0.1,
        "sensitive_path": 0.1,
    }

    # Live Simulation
    SIMULATION_INTERVAL_SECONDS: float = 1.5

    # CORS
    ALLOWED_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            import json
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
settings.DATASET_DIR.mkdir(parents=True, exist_ok=True)
