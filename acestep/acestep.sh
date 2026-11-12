#!/usr/bin/env bash
# Music generation based on an input track.
# ACE-Step and llama-swap can't both fit on the GPUs: "up" swaps llama-swap out (and LTX/Magenta), "down" swaps it back.
#~/docker/acestep/stack/acestep.sh up     # http://192.168.50.205:7860, ready after a minute or two
#~/docker/acestep/stack/acestep.sh down
set -euo pipefail
cd "$(dirname "$0")"
case "${1:-}" in
  up)   docker stop llama-swap ltx magenta >/dev/null 2>&1 || true
        docker compose -f acestep.yaml up -d --build
        echo "starting, logs: docker logs -f acestep, http://192.168.50.205:7860" ;;
  down) docker compose -f acestep.yaml down; docker start llama-swap >/dev/null ;;
  *)    echo "usage: $0 up|down" >&2; exit 1 ;;
esac
