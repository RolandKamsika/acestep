#!/bin/sh
set -e
export HF_TOKEN="$(tr -d ' \r\n' < /run/secrets/hf_token)"
# download_weights.py always contacts Hugging Face, so only run it when the checkpoint is missing
[ -f "$MAGENTA_HOME/magenta-rt-v2/checkpoints/mrt2_${MRT_LOAD}.safetensors" ] || python /app/driver/download_weights.py "$MRT_LOAD"
exec python app_local.py
