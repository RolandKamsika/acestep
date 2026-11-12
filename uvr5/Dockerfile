# UVR5 UI (Gradio front end for python-audio-separator) from https://github.com/Eddycrack864/UVR5-UI.
# torch 2.7.1+cu128: the RTX 5060 Ti (sm_120) needs CUDA 12.8, and it's the version UVR5-UI's installer pins.
FROM pytorch/pytorch:2.7.1-cuda12.8-cudnn9-runtime

# gcc/g++: diffq has no prebuilt wheel and compiles during pip install. ffmpeg: audio decoding/encoding
RUN apt-get update && apt-get install -y --no-install-recommends git gcc g++ ffmpeg && rm -rf /var/lib/apt/lists/*

# Pinned to the commit tested on enki; bump to update
ARG UVR5_REF=3df6c6456ed959808a0ae000e4d3801feeb02381
WORKDIR /app
RUN git init -q . && git fetch -q --depth 1 https://github.com/Eddycrack864/UVR5-UI.git "$UVR5_REF" \
 && git checkout -q FETCH_HEAD \
 && pip install --no-cache-dir -r requirements.txt \
 && python -c "import torch, audio_separator.separator, gradio; assert torch.__version__.startswith('2.7.1'), torch.__version__"

# Models, outputs and settings live under /data (a volume) so they survive rebuilds
RUN for d in models outputs user_data ytdl; do rm -rf "/app/$d" && ln -s "/data/$d" "/app/$d"; done

EXPOSE 7861
CMD ["sh", "-c", "mkdir -p /data/models /data/outputs /data/user_data /data/ytdl && exec python app.py --server-name 0.0.0.0 --listen-port 7861"]
