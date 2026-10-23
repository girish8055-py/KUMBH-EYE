#!/usr/bin/env bash
set -euo pipefail

# Start the Laptop RTSP Dashboard
echo "Starting KumbhEye Laptop Dashboard..."
cd "$(dirname "$0")/.."

if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

python backend/app.py
