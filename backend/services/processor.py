import threading
import time
from datetime import datetime
from pathlib import Path

import cv2

from backend.config.settings import VIDEOS_CFG, PROCESS_INTERVAL, HEATMAP_POINTS_MAX
from backend.state import (
    loaded_models, latest_results, detection_history,
    heatmap_points, path_history, processor_status,
)
from backend.database.queries import db_save_detection
from backend.services.alert import check_alerts
from ml_service.detection import RUNNERS


def processor_thread(vid_id, cfg):
    path = str(cfg["path"])
    vtype = cfg["type"]
    if not Path(path).exists():
        processor_status[vid_id] = "error:video_missing"
        return
    model = loaded_models.get(vtype)
    if not model:
        processor_status[vid_id] = "error:model_missing"
        return
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    total_f = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_f / fps
    runner = RUNNERS[vtype]
    frame_idx = 0
    processor_status[vid_id] = "running"
    while True:
        target_sec = (frame_idx * PROCESS_INTERVAL) % max(duration, 1)
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(target_sec * fps))
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            frame_idx = 0
            time.sleep(PROCESS_INTERVAL)
            continue
        try:
            result = runner(frame, model)
            result.update({"video_id": vid_id, "video_time": target_sec, "duration": duration})
            latest_results[vid_id] = result
            db_save_detection(result)
            detection_history[vid_id].append(result)
            centres = result.get("centers", [])
            heatmap_points[vid_id].extend(centres)
            if len(heatmap_points[vid_id]) > HEATMAP_POINTS_MAX:
                heatmap_points[vid_id] = heatmap_points[vid_id][-HEATMAP_POINTS_MAX:]
            if centres:
                cx = sum(c[0] for c in centres) / len(centres)
                cy = sum(c[1] for c in centres) / len(centres)
                path_history[vid_id].append((cx, cy, datetime.now().isoformat()))
            check_alerts(vid_id, result)
        except Exception as e:
            print(f"[PROC] {vid_id}: {e}")
        frame_idx += 1
        time.sleep(PROCESS_INTERVAL)
