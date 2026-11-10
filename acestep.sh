#!/usr/bin/env bash
# ACE-Step and llama-swap can't both fit on the GPUs: "up" swaps llama-swap out, "down" swaps it back.
set -euo pipefail
cd "$(dirname "$0")"
case "${1:-}" in
  up)   docker stop llama-swap >/dev/null
        pkill -f "acestep --server-name" || true
        pkill -f "main.py --listen 0.0.0.0 --port 8188" || true  # LTX/ComfyUI
        nohup ~/.local/bin/uv run acestep --server-name 0.0.0.0 --port 7860 --init_service true > gradio.log 2>&1 < /dev/null &
        echo "starting, log: $PWD/gradio.log, http://192.168.50.205:7860" ;;
  down) pkill -f "acestep --server-name" || true; docker start llama-swap >/dev/null ;;
  *)    echo "usage: $0 up|down" >&2; exit 1 ;;
esac
