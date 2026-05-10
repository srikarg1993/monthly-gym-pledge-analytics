#!/usr/bin/env bash
# Kill any process on port 8501 and start the Monthly Gym Pledge Streamlit app.

set -e
cd "$(dirname "$0")"

PORT=8501

# Try a graceful SIGTERM first, then SIGKILL only if the process is still
# alive. Avoids the kill -9 reflex flagged in the 2026-05-10 adversarial
# review (P2-12).
if lsof -ti :$PORT >/dev/null 2>&1; then
  PIDS=$(lsof -ti :$PORT)
  echo "Killing process on port $PORT (graceful SIGTERM): $PIDS"
  kill $PIDS 2>/dev/null || true
  sleep 2
  if lsof -ti :$PORT >/dev/null 2>&1; then
    echo "Process still alive — escalating to SIGKILL."
    lsof -ti :$PORT | xargs kill -9 2>/dev/null || true
    sleep 1
  fi
fi

echo "Starting app on http://localhost:$PORT"
.venv/bin/streamlit run gym_pledge/dashboard.py --server.port $PORT
