import asyncio
import io
import json
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse

from backend.config.settings import VIDEOS_CFG
from backend.state import (
    latest_results, detection_history, heatmap_points, path_history,
    ws_clients, processor_status, alert_history, complaints, loaded_models,
)
from backend.database.connection import get_db
from backend.database.queries import db_save_complaint
from backend.schemas import ComplaintIn
from backend.services.alert import send_email, _complaint_email_html, check_alerts
from backend.services.heatmap import build_heatmap
from backend.services.report import build_report

router = APIRouter()


@router.get("/api/status")
async def api_status():
    return {
        "models_loaded": list(loaded_models.keys()),
        "videos_configured": list(VIDEOS_CFG.keys()),
        "results_available": list(latest_results.keys()),
        "processor_status": processor_status,
        "alert_count": len(alert_history),
    }


@router.get("/api/latest/{video_id}")
async def api_latest(video_id: str):
    r = latest_results.get(video_id)
    if not r:
        return JSONResponse({"error": "No data yet", "video_id": video_id}, status_code=202)
    return r


@router.get("/api/analytics/{video_id}")
async def api_analytics(video_id: str):
    hist = list(detection_history.get(video_id, []))
    if not hist:
        return JSONResponse({"error": "No history yet"}, status_code=202)
    vtype = VIDEOS_CFG.get(video_id, {}).get("type", "unknown")
    ts = [h["timestamp"] for h in hist]
    if vtype == "crowd":
        counts = [h["count"] for h in hist]
        densities = [h["density"] for h in hist]
        confs = [h["avg_confidence"] for h in hist]
        levels = [h.get("density_level", "Low") for h in hist]
        return {
            "type": "crowd", "timestamps": ts, "counts": counts,
            "densities": densities, "confidences": confs,
            "level_distribution": {
                "Low": levels.count("Low"),
                "Medium": levels.count("Medium"),
                "High": levels.count("High"),
            },
        }
    elif vtype == "vehicle":
        totals = [h["total_count"] for h in hist]
        dens = [h["density"] for h in hist]
        confs = [h["avg_confidence"] for h in hist]
        ac = defaultdict(int)
        for h in hist:
            for k, v in h.get("class_breakdown", {}).items():
                ac[k] += v
        return {
            "type": "vehicle", "timestamps": ts, "totals": totals,
            "densities": dens, "confidences": confs,
            "class_totals": dict(ac),
        }
    elif vtype == "parking":
        return {
            "type": "parking", "timestamps": ts,
            "occupied": [h["occupied"] for h in hist],
            "available": [h["available"] for h in hist],
            "occupancy_rates": [h["occupancy_rate"] for h in hist],
        }
    return JSONResponse({"error": "Unknown type"}, status_code=400)


@router.get("/api/heatmap/{video_id}")
async def api_heatmap(video_id: str):
    if video_id not in VIDEOS_CFG:
        return JSONResponse({"error": "Unknown"}, status_code=404)
    img = build_heatmap(video_id)
    return StreamingResponse(
        io.BytesIO(img), media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="heatmap_{video_id}.png"'},
    )


@router.get("/api/report/{video_id}")
async def api_report(video_id: str):
    if video_id not in VIDEOS_CFG:
        return JSONResponse({"error": "Unknown"}, status_code=404)
    return HTMLResponse(content=build_report(video_id))


@router.get("/api/alerts")
async def api_alerts():
    return {"alerts": list(reversed(alert_history[-50:]))}


@router.post("/api/complaint")
async def post_complaint(c: ComplaintIn):
    complaint = {
        "id": str(uuid.uuid4()),
        "name": c.name,
        "phone": c.phone,
        "location": c.location,
        "category": c.category,
        "description": c.description,
        "photo_b64": c.photo_b64,
        "status": "Open",
        "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "timestamp_iso": datetime.now().isoformat(),
    }
    complaints.append(complaint)
    db_save_complaint(complaint)
    import threading
    threading.Thread(target=send_email,
        args=(f"New Complaint — {c.category} at {c.location}", _complaint_email_html(complaint)),
        daemon=True).start()
    return {"success": True, "complaint_id": complaint["id"]}


@router.get("/api/complaints")
async def get_complaints():
    return {"complaints": list(reversed(complaints))}


@router.patch("/api/complaint/{cid}/status")
async def update_complaint_status(cid: str, body: dict):
    for c in complaints:
        if c["id"] == cid:
            c["status"] = body.get("status", c["status"])
            return {"success": True}
    return JSONResponse({"error": "Not found"}, status_code=404)


@router.get("/api/history/crowd")
async def history_crowd(limit: int = 500):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM crowd_history ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return {"data": [dict(r) for r in rows]}


@router.get("/api/history/vehicle")
async def history_vehicle(limit: int = 500):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM vehicle_history ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return {"data": [dict(r) for r in rows]}


@router.get("/api/history/parking")
async def history_parking(limit: int = 500):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM parking_history ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return {"data": [dict(r) for r in rows]}


@router.get("/api/history/alerts")
async def history_alerts(limit: int = 500):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM alert_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return {"data": [dict(r) for r in rows]}


@router.get("/api/history/complaints")
async def history_complaints():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM complaint_log ORDER BY timestamp DESC"
    ).fetchall()
    conn.close()
    return {"data": [dict(r) for r in rows]}


@router.patch("/api/history/complaints/{cid}")
async def update_complaint_db(cid: str, body: dict):
    conn = get_db()
    conn.execute("UPDATE complaint_log SET status=? WHERE id=?",
                 (body.get("status", "Open"), cid))
    conn.commit()
    conn.close()
    for c in complaints:
        if c["id"] == cid:
            c["status"] = body.get("status", c["status"])
    return {"success": True}


@router.websocket("/ws/{video_id}")
async def ws_endpoint(websocket: WebSocket, video_id: str):
    await websocket.accept()
    ws_clients[video_id].append(websocket)
    try:
        if video_id in latest_results:
            await websocket.send_json(latest_results[video_id])
        while True:
            await asyncio.sleep(60)
    except Exception:
        pass
    finally:
        if websocket in ws_clients[video_id]:
            ws_clients[video_id].remove(websocket)
