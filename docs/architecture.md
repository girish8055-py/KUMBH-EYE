# Architecture

## Runtime flow

```text
Local video files ──> OpenCV frame sampling ──> YOLO weights
                                                  │
                                                  v
                                         Detection results
                                          /             \
                                FastAPI WebSockets      SQLite
                                          \             /
                                           Dashboard UI
```

At application startup, `backend.main` initializes the SQLite database, loads the models defined by `MODELS_CFG`, starts one processor thread for each configured video source, and starts the WebSocket broadcaster. Each processor samples a frame at the configured interval, invokes the matching detection function in `ml_service/detection.py`, stores results in memory and SQLite, and checks alert thresholds.

The frontend is served from `frontend/`. Static source videos are served from `data/videos/` when that directory exists. The runtime database is written to `data/database/history.db`.

## Main components

| Path | Responsibility |
| --- | --- |
| `backend/main.py` | FastAPI startup, static files, background tasks |
| `backend/api/routes.py` | REST endpoints and WebSocket connection |
| `backend/config/settings.py` | Video/model paths, thresholds, environment configuration |
| `backend/services/processor.py` | Frame sampling, inference dispatch, result persistence |
| `backend/services/alert.py` | Threshold alerts, email delivery, cooldowns |
| `backend/services/heatmap.py` | Heatmap generation |
| `backend/services/report.py` | Report data and rendering |
| `backend/database/` | SQLite connection and persistence queries |
| `backend/state.py` | In-memory live results and connected clients |
| `ml_service/detector.py` | YOLO weight loading |
| `ml_service/detection.py` | Crowd, vehicle, and parking inference functions |
| `frontend/` | Single-page dashboard and browser assets |

## HTTP and WebSocket API

FastAPI also exposes interactive OpenAPI documentation at `/docs` while the server is running.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/status` | Model, video, processor, and alert status |
| `GET` | `/api/latest/{video_id}` | Latest result for a configured source |
| `GET` | `/api/analytics/{video_id}` | In-memory detection trends |
| `GET` | `/api/heatmap/{video_id}` | Heatmap data/image for a source |
| `GET` | `/api/report/{video_id}` | Report for a source |
| `GET` | `/api/alerts` | Current alert list |
| `POST` | `/api/complaint` | Submit a public complaint |
| `GET` | `/api/complaints` | List complaints |
| `PATCH` | `/api/complaint/{cid}/status` | Update complaint status |
| `GET` | `/api/history/{crowd,vehicle,parking,alerts,complaints}` | Persisted history |
| `PATCH` | `/api/history/complaints/{cid}` | Update persisted complaint |
| WebSocket | `/ws/{video_id}` | Live updates for a configured source |

## Configuration

- `VIDEOS_CFG` maps dashboard source IDs to a local file and detection type.
- `MODELS_CFG` maps `crowd`, `vehicle`, and `parking` to model weight paths.
- `ALERT_THRESHOLDS` contains the built-in crowd, vehicle, and parking thresholds.
- `.env` supplies optional email and RTSP settings; `.env.example` documents the variables.

Changing the source IDs or types may also require matching changes in `frontend/index.html`, which contains the dashboard camera panels.

## Data and deployment notes

- Video files are local inputs and are ignored by Git.
- SQLite history is stored locally and is ignored by Git.
- Docker Compose mounts the host's model and data directories into `/app`.
- The standalone RTSP dashboard in `backend/app.py` is a separate Flask application on port 5000. The main FastAPI dashboard uses port 8000.
- Email delivery requires a reachable SMTP server and valid credentials; the application remains usable when email is not configured.
