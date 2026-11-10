#!/usr/bin/env bash
# LTX-2.5 runs in ComfyUI. It can't share the GPUs with ACE-Step or llama-swap: "up" stops both, "down" brings llama-swap back.
set -euo pipefail
cd "$(dirname "$0")"
case "${1:-}" in
  up)   docker stop llama-swap >/dev/null
        pkill -f "acestep --server-name" || true
        pkill -f "main.py --listen 0.0.0.0 --port 8188" || true
        nohup .venv/bin/python main.py --listen 0.0.0.0 --port 8188 > comfyui.log 2>&1 < /dev/null &
        echo "starting, log: $PWD/comfyui.log, http://192.168.50.205:8188" ;;
  down) pkill -f "main.py --listen 0.0.0.0 --port 8188" || true; docker start llama-swap >/dev/null ;;
  *)    echo "usage: $0 up|down" >&2; exit 1 ;;
esac
