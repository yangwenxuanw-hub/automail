#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! python -c "import fastapi, uvicorn" >/dev/null 2>&1; then
  python -m pip install -e "$ROOT_DIR"
fi

if [ ! -d "$ROOT_DIR/web/node_modules" ]; then
  (cd "$ROOT_DIR/web" && npm install)
fi

cleanup() {
  kill 0 >/dev/null 2>&1 || true
}

trap cleanup INT TERM EXIT

(cd "$ROOT_DIR" && python -m automail.web_api) &
(cd "$ROOT_DIR/web" && npm run dev -- --host 0.0.0.0 --port 5173) &

wait
