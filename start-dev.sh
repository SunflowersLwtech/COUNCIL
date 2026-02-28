#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$ROOT_DIR/.logs"
mkdir -p "$LOG_DIR"

load_conda() {
  if command -v conda >/dev/null 2>&1; then
    local conda_base
    conda_base="$(conda info --base 2>/dev/null || true)"
    if [[ -n "$conda_base" && -f "$conda_base/etc/profile.d/conda.sh" ]]; then
      # shellcheck source=/dev/null
      source "$conda_base/etc/profile.d/conda.sh"
      return 0
    fi
  fi

  if [[ -f "/opt/anaconda3/etc/profile.d/conda.sh" ]]; then
    # shellcheck source=/dev/null
    source "/opt/anaconda3/etc/profile.d/conda.sh"
    return 0
  fi

  return 1
}

if ! load_conda; then
  echo "[ERROR] Cannot load conda. Please install/initialize conda first." >&2
  exit 1
fi

if ! conda activate council; then
  echo "[ERROR] Failed to activate conda environment: council" >&2
  exit 1
fi

pkill -f "next dev|npm run dev|uvicorn|python run.py" >/dev/null 2>&1 || true

cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" >/dev/null 2>&1 || true
}

echo "[INFO] Starting backend..."
(
  cd "$ROOT_DIR"
  conda activate council
  python run.py
) >"$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

echo "[INFO] Starting frontend..."
(
  cd "$ROOT_DIR/frontend"
  npm run dev
) >"$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

trap cleanup INT TERM EXIT

echo "[OK] Backend PID:  $BACKEND_PID"
echo "[OK] Frontend PID: $FRONTEND_PID"
echo "[INFO] Logs:"
echo "  - $LOG_DIR/backend.log"
echo "  - $LOG_DIR/frontend.log"
echo "[INFO] Open http://localhost:3000"
echo "[INFO] Press Ctrl+C to stop both services."

wait "$BACKEND_PID" "$FRONTEND_PID"