"""
dashboard_laptop.py  —  Run on Laptop
=======================================
Smooth dashboard improvements:
  1. Count animates smoothly (JS interpolation, not instant jumps)
  2. History logs only when count actually changes (no duplicate spam)
  3. Shows raw vs smoothed count
  4. Peak tracking per session
  5. Live RTSP feed with bounding boxes + track IDs

HOW TO RUN:
    pip install flask opencv-python requests
    python3 dashboard_laptop.py
    open http://localhost:5000
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, render_template_string, jsonify, request
import cv2
import threading
import time
from collections import deque
from datetime import datetime

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = Flask(__name__)

# ===================== CONFIG =====================
RTSP_URL     = os.getenv("RTSP_URL", "")
HISTORY_SIZE = 200
# ==================================================

_lock  = threading.Lock()
_state = {
    "count":     0,
    "raw_count": 0,
    "detections": [],
    "fps":       0.0,
    "timestamp": 0.0,
}
_history      = deque(maxlen=HISTORY_SIZE)
_last_logged_count = -1   # only log when count changes

_frame_lock   = threading.Lock()
_latest_frame = None


# ── video thread ──────────────────────────────────
def video_thread():
    global _latest_frame

    if not RTSP_URL:
        print("RTSP_URL is not configured; video streaming is disabled.")
        return

    def open_cap():
        while True:
            print(f"📡 Connecting RTSP: {RTSP_URL}")
            cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if cap.isOpened():
                print("  ✅ RTSP connected!")
                return cap
            print("  ❌ Retrying in 3s")
            cap.release()
            time.sleep(3)

    cap = open_cap()

    while True:
        ok, frame = cap.read()
        if not ok:
            print("⚠️  RTSP dropped — reconnecting")
            cap.release()
            time.sleep(1)
            cap = open_cap()
            continue

        with _lock:
            dets  = list(_state["detections"])
            count = _state["count"]

        fh, fw = frame.shape[:2]
        sx = fw / 640
        sy = fh / 360

        for d in dets:
            x1 = int(d["x1"] * sx);  y1 = int(d["y1"] * sy)
            x2 = int(d["x2"] * sx);  y2 = int(d["y2"] * sy)
            cf = d.get("conf", 0)
            lb = d.get("label", "person")
            tid = d.get("track_id", "")

            # box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 220, 80), 2)

            # label: "person #3  0.87"
            tag = f"{lb} #{tid}  {cf:.2f}" if tid != "" else f"{lb} {cf:.2f}"
            (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
            ty = max(y1 - 4, th + 4)
            cv2.rectangle(frame, (x1, ty - th - 4), (x1 + tw + 6, ty + 2), (0, 220, 80), -1)
            cv2.putText(frame, tag, (x1 + 3, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0,0,0), 1)

        # count overlay
        ct = f"People: {count}"
        (ctw, cth), _ = cv2.getTextSize(ct, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
        cv2.rectangle(frame, (6, 6), (ctw + 20, cth + 20), (0,0,0), -1)
        cv2.putText(frame, ct, (12, cth + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 100), 2)

        with _frame_lock:
            _latest_frame = frame


def generate_mjpeg():
    while True:
        with _frame_lock:
            frame = _latest_frame.copy() if _latest_frame is not None else None
        if frame is None:
            time.sleep(0.05)
            continue
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ok:
            continue
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n"
               + buf.tobytes()
               + b"\r\n")
        time.sleep(0.033)


# ── Dashboard HTML ─────────────────────────────────
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Crowd Monitor</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #090c13; color: #d1d5db;
    font-family: 'Segoe UI', system-ui, sans-serif;
    min-height: 100vh;
    padding: 24px 16px 48px;
    display: flex; flex-direction: column; align-items: center; gap: 18px;
  }
  .header h1 { font-size: 1.45rem; color: #38d9ff; text-align: center; }
  .header p  { font-size: 0.78rem; color: #4b5563; text-align: center; margin-top: 4px; }

  /* stat cards */
  .stats { display: flex; gap: 14px; width: 100%; max-width: 860px; }
  .card  {
    flex: 1; background: #111827; border: 1px solid #1f2937;
    border-radius: 16px; padding: 16px 18px; text-align: center;
  }
  .card-label { font-size: 0.62rem; text-transform: uppercase;
                letter-spacing: 0.1em; color: #4b5563; margin-bottom: 8px; }
  .card-value { font-size: 2.8rem; font-weight: 700; color: #00ff88;
                line-height: 1; transition: color 0.3s; }
  .card-value.blue   { font-size: 1.6rem; color: #38d9ff; }
  .card-value.yellow { font-size: 1.6rem; color: #fbbf24; }
  .card-value.dim    { font-size: 1.3rem; color: #6b7280; }
  .card-sub { font-size: 0.68rem; color: #374151; margin-top: 6px; }

  /* main layout */
  .main {
    display: flex; gap: 16px;
    width: 100%; max-width: 860px;
    align-items: flex-start;
  }

  /* video */
  .video-panel {
    flex: 0 0 560px; background: #0d111a;
    border: 1px solid #1f2937; border-radius: 14px; overflow: hidden;
  }
  .video-panel img { display: block; width: 100%; height: auto; }
  .video-footer {
    display: flex; justify-content: space-between;
    padding: 7px 12px; font-size: 0.68rem; color: #374151;
    border-top: 1px solid #1a2333;
  }
  #live-dot {
    display: inline-block; width: 7px; height: 7px; border-radius: 50%;
    background: #374151; margin-right: 5px; vertical-align: middle;
  }
  #live-dot.on { background: #00ff88; box-shadow: 0 0 6px #00ff88; }

  /* history panel */
  .history-panel {
    flex: 1; background: #111827; border: 1px solid #1f2937;
    border-radius: 14px; display: flex; flex-direction: column;
    min-height: 380px; max-height: 480px;
  }
  .history-header {
    padding: 10px 14px; font-size: 0.68rem; text-transform: uppercase;
    letter-spacing: 0.1em; color: #4b5563;
    border-bottom: 1px solid #1f2937;
    display: flex; justify-content: space-between; align-items: center;
  }
  .badge {
    background: #1f2937; color: #6b7280;
    border-radius: 99px; padding: 2px 8px; font-size: 0.62rem;
  }
  .history-list { overflow-y: auto; flex: 1; }
  .history-list::-webkit-scrollbar { width: 4px; }
  .history-list::-webkit-scrollbar-thumb { background: #1f2937; border-radius: 4px; }

  .log-row {
    display: grid;
    grid-template-columns: 64px 36px 1fr 44px;
    align-items: center; gap: 8px;
    padding: 7px 14px;
    border-bottom: 1px solid #141c2a;
    font-size: 0.72rem;
  }
  .log-row.new { background: #0a1a0f; }
  .log-time  { color: #4b5563; font-size: 0.65rem; }
  .log-num   { font-weight: 700; font-size: 0.95rem; color: #00ff88; text-align:center; }
  .log-num.zero { color: #374151; }
  .bar-wrap  { background: #1f2937; border-radius: 3px; height: 4px; }
  .bar-fill  { height: 4px; border-radius: 3px; background: #00ff88;
               transition: width 0.4s ease; }
  .log-fps   { color: #4b5563; font-size: 0.62rem; text-align: right; }

  /* smooth counter animation */
  #count { transition: color 0.3s; }

  @media (max-width: 700px) {
    .main { flex-direction: column; }
    .video-panel { flex: none; width: 100%; }
    .stats { flex-wrap: wrap; }
    .card { min-width: 45%; }
  }
</style>
</head>
<body>
  <div class="header">
    <h1>🎥 Crowd Monitoring Dashboard</h1>
    <p>ByteTrack + rolling median smoothing</p>
  </div>

  <div class="stats">
    <div class="card">
      <div class="card-label">People (smoothed)</div>
      <div class="card-value" id="count">—</div>
      <div class="card-sub" id="last-update">Waiting for Pi...</div>
    </div>
    <div class="card">
      <div class="card-label">Raw count</div>
      <div class="card-value dim" id="raw">—</div>
      <div class="card-sub">before smoothing</div>
    </div>
    <div class="card">
      <div class="card-label">Detection FPS</div>
      <div class="card-value blue" id="fps">—</div>
      <div class="card-sub">frames / second</div>
    </div>
    <div class="card">
      <div class="card-label">Session peak</div>
      <div class="card-value yellow" id="peak">—</div>
      <div class="card-sub" id="peak-time">—</div>
    </div>
  </div>

  <div class="main">
    <div class="video-panel">
      <img src="/video_feed" alt="Live feed">
      <div class="video-footer">
        <span><span id="live-dot"></span><span id="live-status">Connecting...</span></span>
        <span>ByteTrack · smooth window: 5 frames</span>
      </div>
    </div>

    <div class="history-panel">
      <div class="history-header">
        Change log <span class="badge" id="badge">0</span>
      </div>
      <div class="history-list" id="history-list">
        <div style="padding:20px;text-align:center;color:#374151;font-size:0.72rem;">
          Logs only when count changes...
        </div>
      </div>
    </div>
  </div>

<script>
  // ── smooth number counter ───────────────────────
  let displayedCount = 0;
  let targetCount    = 0;
  let peakCount      = 0;
  let peakTime       = '—';
  let maxPeak        = 1;
  let renderedLen    = 0;

  function animateCount() {
    if (displayedCount !== targetCount) {
      const step = targetCount > displayedCount ? 1 : -1;
      displayedCount += step;
      document.getElementById('count').textContent = displayedCount;

      // flash green if increasing, amber if decreasing
      document.getElementById('count').style.color =
        step > 0 ? '#00ff88' : '#fbbf24';
      setTimeout(() => {
        document.getElementById('count').style.color = '#00ff88';
      }, 600);
    }
    requestAnimationFrame(animateCount);
  }
  requestAnimationFrame(animateCount);

  // ── polling ─────────────────────────────────────
  function poll() {
    fetch('/get_state')
      .then(r => r.json())
      .then(d => {
        targetCount = d.count;
        document.getElementById('raw').textContent  = d.raw_count;
        document.getElementById('fps').textContent  = d.fps;

        const age  = (Date.now() / 1000) - d.timestamp;
        const live = age < 5;
        document.getElementById('live-dot').className = live ? 'on' : '';
        document.getElementById('live-status').textContent =
          live ? 'Live' : 'Delayed (' + Math.round(age) + 's)';
        document.getElementById('last-update').textContent =
          'Updated ' + Math.round(age) + 's ago';

        if (d.count > peakCount) {
          peakCount = d.count;
          peakTime  = new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit', second:'2-digit'});
          document.getElementById('peak').textContent     = peakCount;
          document.getElementById('peak-time').textContent = 'at ' + peakTime;
          maxPeak = peakCount;
        }
      })
      .catch(() => {
        document.getElementById('live-status').textContent = 'Lost connection';
        document.getElementById('live-dot').className = '';
      });

    // history (only changes, so usually short)
    fetch('/get_history')
      .then(r => r.json())
      .then(entries => {
        if (entries.length === renderedLen) return;  // nothing new
        renderedLen = entries.length;
        document.getElementById('badge').textContent = entries.length;

        const list = document.getElementById('history-list');
        list.innerHTML = entries.slice().reverse().map((e, i) => {
          const pct = Math.min(100, Math.round((e.count / Math.max(maxPeak, 1)) * 100));
          const numCls = e.count === 0 ? 'log-num zero' : 'log-num';
          const rowCls = i === 0 ? 'log-row new' : 'log-row';
          const arrow  = e.delta > 0 ? '▲' : e.delta < 0 ? '▼' : '·';
          const arrowColor = e.delta > 0 ? '#00ff88' : e.delta < 0 ? '#f87171' : '#4b5563';
          return `<div class="${rowCls}">
            <span class="log-time">${e.time_str}</span>
            <span class="${numCls}">${e.count} <span style="font-size:0.6rem;color:${arrowColor}">${arrow}</span></span>
            <div class="bar-wrap"><div class="bar-fill" style="width:${pct}%"></div></div>
            <span class="log-fps">${e.fps} fps</span>
          </div>`;
        }).join('');
      });
  }

  poll();
  setInterval(poll, 500);
</script>
</body>
</html>
"""


# ── Flask routes ───────────────────────────────────
@app.route("/")
def home():
    return render_template_string(DASHBOARD_HTML)

@app.route("/video_feed")
def video_feed():
    return Response(generate_mjpeg(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/update", methods=["POST"])
def update():
    global _last_logged_count
    data  = request.get_json(force=True) or {}
    now   = time.time()
    count = data.get("count", 0)
    fps   = data.get("fps", 0.0)
    ts    = data.get("timestamp", now)

    with _lock:
        _state["count"]      = count
        _state["raw_count"]  = data.get("raw_count", count)
        _state["detections"] = data.get("detections", [])
        _state["fps"]        = round(fps, 1)
        _state["timestamp"]  = ts

        # ── only log when count changes ──────────
        if count != _last_logged_count:
            delta = count - _last_logged_count if _last_logged_count >= 0 else 0
            _history.append({
                "time_str": datetime.fromtimestamp(ts).strftime("%H:%M:%S"),
                "count":    count,
                "fps":      round(fps, 1),
                "delta":    delta,
                "ts":       ts,
            })
            _last_logged_count = count

    return {"status": "ok"}

@app.route("/get_state")
def get_state():
    with _lock:
        return jsonify({
            "count":     _state["count"],
            "raw_count": _state["raw_count"],
            "fps":       _state["fps"],
            "timestamp": _state["timestamp"],
        })

@app.route("/get_history")
def get_history():
    with _lock:
        return jsonify(list(_history))


# ── start ──────────────────────────────────────────
if __name__ == "__main__":
    t = threading.Thread(target=video_thread, daemon=True)
    t.start()
    print("=" * 52)
    print("  🌐 Dashboard  →  http://localhost:5000")
    print(f"  📡 RTSP       →  {RTSP_URL}")
    print("  📬 Pi posts   →  /update")
    print("=" * 52 + "\n")
    app.run(host="0.0.0.0", port=5000, threaded=True)
