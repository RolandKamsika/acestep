#!/usr/bin/env bash
# Video generation with lip-sync: LTX-2.5 in ComfyUI.
# It can't share the GPUs with ACE-Step or llama-swap: "up" stops them, "down" brings llama-swap back.
#~/docker/ltx/stack/ltx.sh up     # http://192.168.50.205:8188
#~/docker/ltx/stack/ltx.sh down
set -euo pipefail
cd "$(dirname "$0")"
case "${1:-}" in
  up)   docker stop llama-swap acestep magenta >/dev/null 2>&1 || true
        docker compose -f ltx.yaml up -d --build
        echo "starting, logs: docker logs -f ltx, http://192.168.50.205:8188" ;;
  down) docker compose -f ltx.yaml down; docker start llama-swap >/dev/null ;;
  *)    echo "usage: $0 up|down" >&2; exit 1 ;;
esac
