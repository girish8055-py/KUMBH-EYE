import json
from datetime import datetime

from backend.database.connection import get_db


def db_save_detection(result: dict):
    try:
        conn = get_db()
        c = conn.cursor()
        vt = result.get("type")
        vid = result.get("video_id", "")
        ts  = result.get("timestamp", datetime.now().isoformat())
        if vt == "crowd":
            c.execute("INSERT INTO crowd_history (video_id,count,density,avg_conf,level,timestamp) VALUES (?,?,?,?,?,?)",
                (vid, result.get("count",0), result.get("density",0),
                 result.get("avg_confidence",0), result.get("density_level","Low"), ts))
        elif vt == "vehicle":
            c.execute("INSERT INTO vehicle_history (video_id,total,density,avg_conf,classes,timestamp) VALUES (?,?,?,?,?,?)",
                (vid, result.get("total_count",0), result.get("density",0),
                 result.get("avg_confidence",0),
                 json.dumps(result.get("class_breakdown",{})), ts))
        elif vt == "parking":
            c.execute("INSERT INTO parking_history (video_id,occupied,available,total,rate,status,timestamp) VALUES (?,?,?,?,?,?,?)",
                (vid, result.get("occupied",0), result.get("available",0),
                 result.get("total_slots",0), result.get("occupancy_rate",0),
                 result.get("status",""), ts))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB] save_detection: {e}")


def db_save_alert(title, video_id, key):
    try:
        conn = get_db()
        conn.execute("INSERT INTO alert_log (title,video_id,alert_key,timestamp) VALUES (?,?,?,?)",
            (title, video_id or "", key or "", datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB] save_alert: {e}")


def db_save_complaint(c: dict):
    try:
        conn = get_db()
        conn.execute("INSERT OR REPLACE INTO complaint_log VALUES (?,?,?,?,?,?,?,?)",
            (c["id"], c["name"], c.get("phone",""), c["location"],
             c["category"], c["description"], c["status"], c["timestamp"]))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB] save_complaint: {e}")
