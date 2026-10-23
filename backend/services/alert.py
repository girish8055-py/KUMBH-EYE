import smtplib
import threading
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from backend.config.settings import EMAIL_CFG, EMAIL_RECIPIENTS, ALERT_THRESHOLDS, ALERT_COOLDOWN_MIN
from backend.state import alert_cooldowns, alert_history
from backend.database.queries import db_save_alert


def _email_html(title, details, vid_id, vtype, accent="#00c9a7"):
    rows = "".join(
        f'<tr><td style="padding:7px 14px;color:#8b949e;font-size:13px;border-bottom:1px solid #21262d">{k}</td>'
        f'<td style="padding:7px 14px;color:#e6edf3;font-size:13px;font-weight:600;border-bottom:1px solid #21262d">{v}</td></tr>'
        for k, v in details.items()
    )
    ts = datetime.now().strftime("%d %b %Y, %I:%M %p")
    r, g, b = int(accent[1:3], 16), int(accent[3:5], 16), int(accent[5:7], 16)
    return f"""<html><body style="margin:0;padding:0;background:#0d1117;font-family:'Segoe UI',sans-serif">
<div style="max-width:580px;margin:30px auto;background:#161b22;border-radius:12px;overflow:hidden;border:1px solid #30363d">
  <div style="background:{accent};padding:4px 0"></div>
  <div style="padding:28px 32px">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:18px">
      <span style="font-size:26px">🚨</span>
      <div>
        <div style="font-size:10px;letter-spacing:2px;color:#484f58;text-transform:uppercase;font-weight:600">SMARTVISION ALERT</div>
        <div style="font-size:19px;font-weight:700;color:#e6edf3;margin-top:2px">{title}</div>
      </div>
    </div>
    <div style="background:#0d1117;border-radius:8px;overflow:hidden;margin-bottom:18px;border:1px solid #21262d">
      <table style="width:100%;border-collapse:collapse">{rows}</table>
    </div>
    <div style="background:rgba({r},{g},{b},.08);border-left:3px solid {accent};padding:11px 15px;border-radius:0 6px 6px 0;margin-bottom:18px">
      <div style="color:#e6edf3;font-size:13px;font-weight:600">📍 Camera: {vid_id.replace("_"," ").title()}</div>
      <div style="color:#8b949e;font-size:12px;margin-top:3px">Detected at {ts}</div>
    </div>
    <div style="color:#484f58;font-size:11px;border-top:1px solid #21262d;padding-top:14px">
      SmartVision AI Surveillance · Auto-generated alert · {ALERT_COOLDOWN_MIN}-min cooldown active
    </div>
  </div>
</div></body></html>"""


def _complaint_email_html(c):
    return f"""<html><body style="margin:0;padding:0;background:#0d1117;font-family:'Segoe UI',sans-serif">
<div style="max-width:580px;margin:30px auto;background:#161b22;border-radius:12px;overflow:hidden;border:1px solid #30363d">
  <div style="background:#f59e0b;padding:4px 0"></div>
  <div style="padding:28px 32px">
    <div style="margin-bottom:16px">
      <div style="font-size:10px;letter-spacing:2px;color:#484f58;text-transform:uppercase;margin-bottom:4px">NEW COMPLAINT SUBMITTED</div>
      <div style="font-size:19px;font-weight:700;color:#e6edf3">Public Complaint — #{c["id"][:8].upper()}</div>
    </div>
    <div style="background:#0d1117;border-radius:8px;overflow:hidden;margin-bottom:16px;border:1px solid #21262d">
      <table style="width:100%;border-collapse:collapse">
        <tr><td style="padding:7px 14px;color:#8b949e;font-size:13px;border-bottom:1px solid #21262d">Name</td><td style="padding:7px 14px;color:#e6edf3;font-size:13px;font-weight:600;border-bottom:1px solid #21262d">{c["name"]}</td></tr>
        <tr><td style="padding:7px 14px;color:#8b949e;font-size:13px;border-bottom:1px solid #21262d">Location</td><td style="padding:7px 14px;color:#e6edf3;font-size:13px;font-weight:600;border-bottom:1px solid #21262d">{c["location"]}</td></tr>
        <tr><td style="padding:7px 14px;color:#8b949e;font-size:13px;border-bottom:1px solid #21262d">Category</td><td style="padding:7px 14px;color:#e6edf3;font-size:13px;font-weight:600;border-bottom:1px solid #21262d">{c["category"]}</td></tr>
        <tr><td style="padding:7px 14px;color:#8b949e;font-size:13px">Submitted</td><td style="padding:7px 14px;color:#e6edf3;font-size:13px;font-weight:600">{c["timestamp"]}</td></tr>
      </table>
    </div>
    <div style="background:rgba(245,158,11,.08);border-left:3px solid #f59e0b;padding:12px 15px;border-radius:0 6px 6px 0;margin-bottom:16px">
      <div style="color:#fcd34d;font-size:12px;font-weight:600;margin-bottom:5px">📝 Description</div>
      <div style="color:#e6edf3;font-size:13px;line-height:1.6">{c["description"]}</div>
    </div>
    <div style="color:#484f58;font-size:11px;border-top:1px solid #21262d;padding-top:14px">
      SmartVision Public Portal · Please review and take appropriate action.
    </div>
  </div>
</div></body></html>"""


def send_email(subject, body_html, vid_id=None, alert_key=None):
    now = datetime.now()
    if alert_key:
        ck = f"{vid_id}:{alert_key}"
        if ck in alert_cooldowns:
            elapsed = (now - alert_cooldowns[ck]).total_seconds() / 60
            if elapsed < ALERT_COOLDOWN_MIN:
                return
        alert_cooldowns[ck] = now

    if alert_key:
        db_save_alert(subject, vid_id, alert_key)

    if EMAIL_CFG["sender"] and EMAIL_CFG["app_password"]:
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"SmartVision <{EMAIL_CFG['sender']}>"
            msg["To"] = ", ".join(EMAIL_RECIPIENTS)
            msg["Subject"] = f"🚨 SmartVision: {subject}"
            msg.attach(MIMEText(body_html, "html"))
            with smtplib.SMTP(EMAIL_CFG["smtp_host"], EMAIL_CFG["smtp_port"]) as s:
                s.ehlo()
                s.starttls()
                s.ehlo()
                s.login(EMAIL_CFG["sender"], EMAIL_CFG["app_password"])
                s.send_message(msg)
        except Exception as exc:
            print(f"[EMAIL] Failed: {exc}")
    else:
        print(f"[EMAIL] Not configured — skipping: {subject}")

    if alert_key:
        alert_history.append({
            "id": len(alert_history),
            "title": subject,
            "video_id": vid_id or "system",
            "timestamp": now.isoformat(),
            "key": alert_key,
        })
        if len(alert_history) > 100:
            alert_history.pop(0)


def check_alerts(vid_id, result):
    vtype = result.get("type")
    ts = datetime.now().strftime("%I:%M %p")
    accent_map = {"crowd": "#00c9a7", "vehicle": "#f59e0b", "parking": "#a78bfa"}
    accent = accent_map.get(vtype, "#3b82f6")
    if vtype == "crowd":
        cnt = result.get("count", 0)
        lvl = result.get("density_level", "Low")
        if cnt >= ALERT_THRESHOLDS["crowd_count"] or lvl == "High":
            send_email(
                f"High Crowd — {vid_id.replace('_',' ').title()}",
                _email_html("High Crowd Density Detected",
                    {"Camera": vid_id, "Count": cnt, "Level": lvl,
                     "Confidence": f"{result.get('avg_confidence',0)*100:.1f}%", "Time": ts},
                    vid_id, "crowd", accent),
                vid_id, "crowd_high")
    elif vtype == "vehicle":
        cnt = result.get("total_count", 0)
        if cnt >= ALERT_THRESHOLDS["vehicle_count"]:
            send_email(
                f"Heavy Traffic — {vid_id.replace('_',' ').title()}",
                _email_html("Heavy Vehicle Traffic",
                    {"Camera": vid_id, "Vehicles": cnt,
                     "Density": f"{result.get('density',0):.3f}", "Time": ts},
                    vid_id, "vehicle", accent),
                vid_id, "vehicle_high")
    elif vtype == "parking":
        rate = result.get("occupancy_rate", 0)
        if rate >= ALERT_THRESHOLDS["parking_occupancy"]:
            send_email(
                f"Parking {result.get('status','Full')}",
                _email_html("Parking Lot Critical",
                    {"Occupied": result.get("occupied", 0),
                     "Available": result.get("available", 0),
                     "Rate": f"{rate}%", "Status": result.get("status", ""), "Time": ts},
                    vid_id, "parking", accent),
                vid_id, "parking_full")
