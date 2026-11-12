# ComfyUI for LTX-2.5, from https://github.com/comfyanonymous/ComfyUI (it has no official image).
# torch cu130 builds, the exact versions tested on enki (driver 580 supports CUDA 13.0).
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Pinned to the commit tested on enki; bump to update
ARG COMFY_REF=bbd810e647c64da8212b0d4ab94f1354c9d523f6
WORKDIR /app
RUN git init -q . && git fetch -q --depth 1 https://github.com/comfyanonymous/ComfyUI.git "$COMFY_REF" \
 && git checkout -q FETCH_HEAD \
 && pip install --no-cache-dir torch==2.14.1 torchvision==0.29.1 torchaudio==2.11.0 --index-url https://download.pytorch.org/whl/cu130 \
 && pip install --no-cache-dir -r requirements.txt \
 && python -c "import torch; assert torch.__version__.startswith('2.14.1'), torch.__version__"

# Models, outputs, inputs and saved workflows live under /data (a volume) so they survive rebuilds
RUN for d in models output input user; do rm -rf "/app/$d" && ln -s "/data/$d" "/app/$d"; done

EXPOSE 8188
CMD ["sh", "-c", "mkdir -p /data/models /data/output /data/input /data/user && exec python main.py --listen 0.0.0.0 --port 8188"]
