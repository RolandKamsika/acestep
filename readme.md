## ACE-Step

On enki, `~/repos/ACE-Step-1.5/acestep.sh up` starts ACE-Step (it stops `llama-swap` and LTX, since they can't share the GPUs). `acestep.sh down` reverses it. Ready after about a minute; log in `~/repos/ACE-Step-1.5/gradio.log`.

A copy of the script is in this folder ([acestep.sh](acestep.sh)). The live one is on enki. After editing the copy here, push it back:

scp acestep.sh 192.168.50.205:repos/ACE-Step-1.5/

From Windows:

ssh 192.168.50.205 '~/repos/ACE-Step-1.5/acestep.sh up'
ssh 192.168.50.205 '~/repos/ACE-Step-1.5/acestep.sh down'

 http://192.168.50.205:7860
  http://enki.local:7860

## LTX-2.5 (video)

LTX-2.5 runs inside ComfyUI at `~/repos/ComfyUI` on enki. `ltx.sh up` starts it (it stops `llama-swap` and ACE-Step). `ltx.sh down` stops it and starts `llama-swap` again. Log in `~/repos/ComfyUI/comfyui.log`.

From Windows:

ssh 192.168.50.205 '~/repos/ComfyUI/ltx.sh up'
ssh 192.168.50.205 '~/repos/ComfyUI/ltx.sh down'

 http://192.168.50.205:8188

In ComfyUI, open Templates > Video > **LTX-2.5 T2V** (or I2V). The models are the int8 builds ComfyUI's docs use; ComfyUI moves weights between the 16GB GPU and system RAM as needed, so expect it to be slow.

The copy of the script here is [ltx.sh](ltx.sh). Push it with:

scp ltx.sh 192.168.50.205:repos/ComfyUI/

### One-time install (on enki)

The weights are gated. First accept the license at https://huggingface.co/Lightricks/LTX-2.5 and create a read token at https://huggingface.co/settings/tokens.

```
cd ~/repos && git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git && cd ComfyUI
~/.local/bin/uv venv --python 3.12
~/.local/bin/uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130
~/.local/bin/uv pip install -r requirements.txt
~/.local/bin/uvx hf auth login
~/.local/bin/uvx hf download Lightricks/LTX-2.5 --local-dir models \
  diffusion_models/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors \
  text_encoders/gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors \
  vae/ltx-2.5-video-vae-bf16.safetensors \
  vae/ltx-2.5-audio-vae-bf16.safetensors \
  latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors
```

Then, from Windows, copy the script over: `scp ltx.sh 192.168.50.205:repos/ComfyUI/` and `ssh 192.168.50.205 chmod +x repos/ComfyUI/ltx.sh`.

The repo's file paths match ComfyUI's model folders, so `--local-dir models` puts each file where the template looks for it.
