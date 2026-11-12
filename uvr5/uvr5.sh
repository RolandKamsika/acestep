#!/usr/bin/env bash
# UVR5 and llama-swap share the GPUs: "up" swaps llama-swap out, "down" swaps it back.
#~/docker/uvr5/stack/uvr5.sh up     # stops llama-swap, starts UVR5 on :7861
#~/docker/uvr5/stack/uvr5.sh down   # stops UVR5, starts llama-swap again

set -euo pipefail
cd "$(dirname "$0")"
case "${1:-}" in
  up)   docker stop llama-swap >/dev/null 2>&1 || true; docker compose -f uvr5.yaml up -d --build ;;
  down) docker compose -f uvr5.yaml down; docker start llama-swap >/dev/null ;;
  *)    echo "usage: $0 up|down" >&2; exit 1 ;;
esac
