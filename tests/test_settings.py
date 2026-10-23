from backend.config.settings import BASE_DIR, DB_PATH, MODELS_CFG, VIDEOS_CFG
from pathlib import Path


def test_base_dir_is_project_root():
    assert (BASE_DIR / "backend").is_dir()


def test_db_path():
    assert DB_PATH == BASE_DIR / "data" / "database" / "history.db"


def test_models_cfg():
    assert MODELS_CFG["crowd"] == BASE_DIR / "ml_service" / "models" / "crowd_best.pt"


def test_videos_cfg():
    expected_names = {"crowd_1.mp4", "crowd_2.mp4", "vehicle_1.mp4", "vehicle_2.mp4", "new_p.mp4"}
    assert {Path(v["path"]).name for v in VIDEOS_CFG.values()} == expected_names
    for v in VIDEOS_CFG.values():
        p = Path(v["path"])
        assert p.parent == BASE_DIR / "data" / "videos"
