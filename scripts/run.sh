#!/usr/bin/env bash
set -euo pipefail

# Start the SmartVision Backend
echo "Starting SmartVision Surveillance Backend..."
cd "$(dirname "$0")/.."

# Check for virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
