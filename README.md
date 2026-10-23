<div align="center">

# Kumbh Eye

### Real-time vision for safer, smarter public spaces

An AI-assisted surveillance dashboard for crowd density, traffic, and parking monitoring. Bring your own camera footage, run the included YOLO models, and review live results, trends, heatmaps, reports, and alerts from one web interface.

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

</div>

---

## At a glance

- **Crowd monitoring:** person counts, density levels, and confidence summaries.
- **Traffic monitoring:** vehicle totals and model-provided class breakdowns.
- **Parking monitoring:** occupied and available slot counts with occupancy status.
- **Live dashboard:** camera panels, alerts, historical analytics, heatmaps, and reports.
- **Public reporting:** a complaint form and an authority view for complaint status.
- **Local-first data:** video files and the SQLite database stay on the machine running the app.

> Kumbh Eye is a monitoring aid. Model predictions can be wrong and should not replace human judgment or established safety procedures.

## Preview

The dashboard is served by the backend at `http://localhost:8000` after setup. API documentation is available at `http://localhost:8000/docs`.

## How it works

The FastAPI service loads the model weights from `ml_service/models/`, reads the configured video files, and samples frames for detection. Results are sent to the dashboard over WebSockets and saved to a local SQLite database. The browser UI is plain HTML, CSS, and JavaScript in `frontend/`.

See [docs/architecture.md](docs/architecture.md) for the component map and API overview.

## Quick start

### 1. Get the code

After cloning this repository:

```bash
cd Kumbh-Eye-an-Intelligent-vision-system
```

### 2. Create a Python environment

Python 3.10 or newer is required.

**Windows PowerShell**

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The first installation can take a while because computer-vision and model libraries are large.

### 3. Add video files

Put your own video files in `data/videos/`. The default configuration expects these exact names:

| File | Dashboard purpose |
| --- | --- |
| `crowd_1.mp4` | Crowd camera 1 |
| `crowd_2.mp4` | Crowd camera 2 |
| `vehicle_1.mp4` | Vehicle camera 1 |
| `vehicle_2.mp4` | Vehicle camera 2 |
| `new_p.mp4` | Parking camera |

Video files are intentionally excluded from Git. If you have fewer videos, the app can still start, but the corresponding camera panels will have no live results. To use different filenames or add more sources, edit `VIDEOS_CFG` in `backend/config/settings.py` and update the dashboard’s matching camera entries in `frontend/index.html`.

### 4. Check model weights

The repository includes these model files under `ml_service/models/`:

```text
crowd_best.pt       crowd/person detection
vehicle_best.pt     vehicle detection
parking_best.pt     parking-slot detection
```

The files need to retain these names unless you also change `MODELS_CFG` in `backend/config/settings.py`. If you use your own weights, make sure the model classes match the detection logic in `ml_service/detection.py`.

### 5. Configure optional email and RTSP settings

Copy `.env.example` to `.env` in the repository root. Email alerts and the separate laptop RTSP dashboard are optional; leave the values blank to run without them.

```dotenv
EMAIL_SENDER=your-sender@gmail.com
EMAIL_APP_PASSWORD=your-app-password
EMAIL_RECIPIENTS=operator@example.com,team@example.com
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587

RTSP_URL=rtsp://camera-address:554/stream
```

For Gmail, use an app password created for this purpose. Never commit `.env`, passwords, private camera URLs, or private footage. The `.env` file is ignored by Git.

### 6. Start the dashboard

Run this from the repository root with the virtual environment active:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open <http://localhost:8000>. The SQLite database is created automatically at `data/database/history.db`.

On Windows, the same command works in PowerShell. Convenience commands are also available with `make run` on systems with Make installed, or `bash scripts/run.sh` on macOS/Linux.

## Optional: run with Docker

Install Docker Desktop or Docker Engine with Compose, then from the repository root:

```bash
docker compose -f docker/docker-compose.yml up --build
```

The Compose setup mounts `data/videos/`, `data/database/`, and `ml_service/models/` into the container. Add the video and environment files before starting it. On systems where `docker compose` is not available, try `docker-compose`.

## Optional: laptop RTSP dashboard

The standalone Flask dashboard in `backend/app.py` displays an RTSP stream. Set `RTSP_URL` in `.env`, activate the environment, then run:

```bash
python backend/app.py
```

Open <http://localhost:5000>. This is separate from the FastAPI dashboard on port 8000.

## Tests and code quality

Install development dependencies and run the checks from the repository root:

```bash
pip install -r requirements-dev.txt
ruff check backend/ ml_service/ tests/
pytest
```

The settings tests do not require sample video files. For a meaningful end-to-end demo, provide the five videos and the model weights described above.

## Folder structure

```text
.
├── backend/                 FastAPI app, routes, settings, database, services
├── config/                  Development and production YAML examples
├── data/
│   ├── database/            Runtime SQLite database (created automatically)
│   └── videos/               Add local MP4 input videos here
├── docker/                  Dockerfile and Compose configuration
├── docs/                    Architecture and API notes
├── frontend/                Dashboard page and static assets
├── ml_service/
│   ├── detection.py          Crowd, vehicle, and parking inference logic
│   ├── detector.py           YOLO model loading
│   └── models/               Model weight files
├── scripts/                 Convenience launch scripts
├── tests/                   Automated tests
├── .env.example              Environment variable template
├── pyproject.toml            Python project and tool configuration
└── requirements*.txt         Runtime and development dependencies
```

## Configuration map

| Setting | Where to change it |
| --- | --- |
| Video filenames and source types | `backend/config/settings.py` (`VIDEOS_CFG`) |
| Model weight paths | `backend/config/settings.py` (`MODELS_CFG`) |
| Alert thresholds | `backend/config/settings.py` (`ALERT_THRESHOLDS`) |
| Email and RTSP credentials | Repository-root `.env` |
| Detection behavior | `ml_service/detection.py` |
| Dashboard presentation | `frontend/index.html` and `frontend/static/` |

## Troubleshooting

- **Camera panels show no results:** confirm the video files are in `data/videos/` with the exact names above. Check the terminal for `video_missing` or `model_missing` status.
- **A model is missing:** confirm all three `.pt` files exist in `ml_service/models/` and match `MODELS_CFG`.
- **Email alerts do not send:** verify the sender, app password, recipient list, SMTP host, and SMTP port in `.env`. Email is optional.
- **Port 8000 is busy:** start Uvicorn with another port, for example `--port 8001`, then open that port in your browser.
- **Docker cannot find a video:** add local videos before startup; videos are not included in the repository.

## Contributing

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) for the project workflow and checks. Please do not open a pull request containing private camera footage, credentials, or real personal data.

## License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

Built for practical crowd, traffic, and parking visibility. Explore the code, try it with sample footage you are allowed to use, and help improve it.

</div>
