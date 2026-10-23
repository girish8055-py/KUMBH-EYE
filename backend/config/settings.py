import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

DB_PATH = BASE_DIR / "data" / "database" / "history.db"

MODELS_CFG = {
    "crowd":   BASE_DIR / "ml_service" / "models" / "crowd_best.pt",
    "vehicle": BASE_DIR / "ml_service" / "models" / "vehicle_best.pt",
    "parking": BASE_DIR / "ml_service" / "models" / "parking_best.pt",
}

VIDEOS_CFG = {
    "crowd_1":   {"path": BASE_DIR / "data" / "videos" / "crowd_1.mp4",   "type": "crowd"},
    "crowd_2":   {"path": BASE_DIR / "data" / "videos" / "crowd_2.mp4",   "type": "crowd"},
    "vehicle_1": {"path": BASE_DIR / "data" / "videos" / "vehicle_1.mp4", "type": "vehicle"},
    "vehicle_2": {"path": BASE_DIR / "data" / "videos" / "vehicle_2.mp4", "type": "vehicle"},
    "parking_1": {"path": BASE_DIR / "data" / "videos" / "new_p.mp4",     "type": "parking"},
}

PROCESS_INTERVAL   = 4
HISTORY_MAX        = 200
HEATMAP_POINTS_MAX = 8000
PATH_HISTORY_MAX   = 300

EMAIL_RECIPIENTS = [
    address.strip()
    for address in os.getenv("EMAIL_RECIPIENTS", "").split(",")
    if address.strip()
]

EMAIL_CFG = {
    "enabled":      True,
    "sender": os.getenv("EMAIL_SENDER", ""),
    "app_password": os.getenv("EMAIL_APP_PASSWORD", ""),
    "smtp_host": os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("EMAIL_SMTP_PORT", "587")),
}

ALERT_THRESHOLDS = {
    "crowd_count": 30,
    "vehicle_count": 25,
    "parking_occupancy": 85,
}

ALERT_COOLDOWN_MIN = 10
