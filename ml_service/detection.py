from collections import defaultdict
from datetime import datetime

import numpy as np


def _centres(boxes, h, w):
    return [
        (float((b.xyxy[0][0] + b.xyxy[0][2]) / 2 / w),
         float((b.xyxy[0][1] + b.xyxy[0][3]) / 2 / h))
        for b in boxes
    ]


def run_crowd(frame, model):
    h, w = frame.shape[:2]
    res = model(frame, verbose=False)[0]
    boxes = res.boxes
    count = len(boxes)
    confs = boxes.conf.cpu().numpy().tolist() if count else []
    avg_c = float(np.mean(confs)) if confs else 0.0
    density = round(count / (h * w / 10_000), 4)
    level = "Low" if count < 10 else "Medium" if count < 30 else "High"
    return {
        "type": "crowd", "count": count, "density": density,
        "avg_confidence": round(avg_c, 3),
        "min_confidence": round(float(min(confs)), 3) if confs else 0.0,
        "max_confidence": round(float(max(confs)), 3) if confs else 0.0,
        "density_level": level, "frame_size": f"{w}x{h}",
        "centers": _centres(boxes, h, w),
        "timestamp": datetime.now().isoformat(),
    }


def run_vehicle(frame, model):
    h, w = frame.shape[:2]
    res = model(frame, verbose=False)[0]
    boxes = res.boxes
    names = model.names
    cls_cnt = defaultdict(int)
    confs = []
    for box in boxes:
        cls_cnt[names.get(int(box.cls[0]), f"cls_{int(box.cls[0])}")] += 1
        confs.append(float(box.conf[0]))
    total = len(boxes)
    avg_c = float(np.mean(confs)) if confs else 0.0
    return {
        "type": "vehicle", "total_count": total,
        "class_breakdown": dict(cls_cnt),
        "avg_confidence": round(avg_c, 3),
        "density": round(total / (h * w / 10_000), 4),
        "frame_size": f"{w}x{h}",
        "centers": _centres(boxes, h, w),
        "timestamp": datetime.now().isoformat(),
    }


def run_parking(frame, model):
    h, w = frame.shape[:2]
    res = model(frame, verbose=False)[0]
    boxes = res.boxes
    names = model.names
    occ = avail = 0
    for box in boxes:
        lbl = names.get(int(box.cls[0]), "").lower()
        if any(k in lbl for k in ("occupied", "car", "filled", "taken")):
            occ += 1
        elif any(k in lbl for k in ("empty", "free", "available", "open")):
            avail += 1
        else:
            occ += 1
    total = occ + avail
    rate = round(occ / total * 100, 1) if total else 0.0
    status = (
        "No slots" if not total else
        "Lot Full" if avail == 0 else
        "Almost Full" if rate > 80 else
        "Mostly Free" if rate < 30 else
        "Available"
    )
    return {
        "type": "parking", "total_slots": total,
        "occupied": occ, "available": avail,
        "occupancy_rate": rate, "status": status,
        "timestamp": datetime.now().isoformat(),
    }


RUNNERS = {"crowd": run_crowd, "vehicle": run_vehicle, "parking": run_parking}
