from pathlib import Path

from backend.config.settings import MODELS_CFG
from backend.state import loaded_models


def load_models():
    for name, path in MODELS_CFG.items():
        if Path(path).exists():
            try:
                from ultralytics import YOLO
                loaded_models[name] = YOLO(str(path))
            except Exception as e:
                print(f"[MODEL] {name}: {e}")
        else:
            print(f"[MODEL] Missing: {path}")
