import asyncio
import threading
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router
from backend.api.middleware import setup_middleware
from backend.config.settings import VIDEOS_CFG, BASE_DIR
from backend.database.connection import init_db
from backend.services.processor import processor_thread
from backend.services.broadcaster import broadcaster
from ml_service.detector import load_models

app = FastAPI(title="SmartVision Surveillance", version="4.0.0")
setup_middleware(app)
app.include_router(router)


@app.on_event("startup")
async def on_startup():
    init_db()
    load_models()
    for vid_id, cfg in VIDEOS_CFG.items():
        threading.Thread(target=processor_thread, args=(vid_id, cfg), daemon=True).start()
    asyncio.create_task(broadcaster())


videos_dir = BASE_DIR / "data" / "videos"
frontend_dir = BASE_DIR / "frontend"
if videos_dir.exists():
    app.mount("/videos", StaticFiles(directory=str(videos_dir)), name="videos")
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
