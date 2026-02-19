#!/usr/bin/env bash
# Kill any process on port 8501 and start the Monthly Gym Pledge Streamlit app.

set -e
cd "$(dirname "$0")"

PORT=8501

# Kill process on port 8501 if present
if lsof -ti :$PORT >/dev/null 2>&1; then
  echo "Killing process on port $PORT..."
  lsof -ti :$PORT | xargs kill -9 2>/dev/null || true
  sleep 1
fi

echo "Starting app on http://localhost:$PORT"
.venv/bin/streamlit run gym_pledge/dashboard.py --server.port $PORT
