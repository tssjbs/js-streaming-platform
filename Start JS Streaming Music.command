#!/bin/bash
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q fastapi uvicorn pydantic
fi
pkill -f "python -m src.server" 2>/dev/null || true
export JS_STREAM_PORT=8790
.venv/bin/python -m src.server &
sleep 2
open "http://127.0.0.1:8790/"