# Magenta RealTime 2 jam app from https://huggingface.co/babakarto/magenta-rt-local-windows, on Linux.
# torch 2.7.1+cu128 instead of the guide's 2.6.0+cu124: the RTX 5060 Ti (sm_120) needs CUDA 12.8.
FROM pytorch/pytorch:2.7.1-cuda12.8-cudnn9-runtime

# gcc: torch.compile (Triton) builds its kernels at startup
RUN apt-get update && apt-get install -y --no-install-recommends git gcc g++ && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# transformers: imported by the Space's magenta_rt package but missing from requirements-local.txt
RUN git clone --depth 1 https://huggingface.co/spaces/magenta-community/magenta-rt-jam jam \
 && git clone --depth 1 https://huggingface.co/babakarto/magenta-rt-local-windows driver \
 && pip install --no-cache-dir -r driver/requirements-local.txt transformers \
 && cp driver/app_local.py jam/app_local.py \
 && python -c "import torch; assert torch.__version__.startswith('2.7.1'), torch.__version__"

COPY entrypoint.sh /entrypoint.sh
WORKDIR /app/jam
ENTRYPOINT ["sh", "/entrypoint.sh"]
