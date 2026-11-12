
#!/usr/bin/env bash
# Magenta and llama-swap can't both fit on the GPUs: "up" swaps llama-swap out, "down" swaps it back.
#~/docker/magenta/stack/magenta.sh up     # stops llama-swap, starts Magenta
#~/docker/magenta/stack/magenta.sh down   # stops Magenta, starts llama-swap again

set -euo pipefail
cd "$(dirname "$0")"
case "${1:-}" in
  up)   docker stop llama-swap >/dev/null; docker compose -f magenta.yaml up -d --build ;;
  down) docker compose -f magenta.yaml down; docker start llama-swap >/dev/null ;;
  *)    echo "usage: $0 up|down" >&2; exit 1 ;;
esac
