## ACE-Step

ACE-Step runs in Docker on enki. The image is built from ACE-Step's own Dockerfile, pinned to a commit in [acestep/acestep.yaml](acestep/acestep.yaml); to update, change the `#ref` there. The stack is in `~/docker/acestep/stack`, and the checkpoints and outputs are in `~/docker/acestep/data`. `acestep.sh up` stops `llama-swap`, LTX and Magenta, since they can't share the GPUs. `acestep.sh down` reverses it. It's ready after about a minute; see the log with `docker logs -f acestep`.

From Windows:

ssh 192.168.50.205 '~/docker/acestep/stack/acestep.sh up'
ssh 192.168.50.205 '~/docker/acestep/stack/acestep.sh down'

After editing the copies in [acestep/](acestep/), push them back:

scp acestep/acestep.yaml acestep/acestep.sh 192.168.50.205:docker/acestep/stack/

 http://192.168.50.205:7860
  http://enki.local:7860

## Back to llama-swap

ACE-Step, LTX and `llama-swap` take turns on the GPUs. To get `llama-swap` back, run `down` for whichever one is up. That stops it and starts `llama-swap`:

ssh 192.168.50.205 '~/docker/acestep/stack/acestep.sh down'
ssh 192.168.50.205 '~/docker/ltx/stack/ltx.sh down'

If you're not sure which is running, run both; it's safe. To check: `ssh 192.168.50.205 'docker ps --filter name=llama-swap'`.

## UVR5 (stem splitting)

[UVR5-UI](https://github.com/Eddycrack864/UVR5-UI) runs in Docker on enki. The stack is in `~/docker/uvr5/stack`. Models, outputs and settings are in `~/docker/uvr5/data`. `uvr5.sh up` stops `llama-swap` and builds and starts the container. `uvr5.sh down` reverses it.

ssh 192.168.50.205 '~/docker/uvr5/stack/uvr5.sh up'
ssh 192.168.50.205 '~/docker/uvr5/stack/uvr5.sh down'

 http://192.168.50.205:7861

The copies here are in [uvr5/](uvr5/). Push them with:

scp uvr5/uvr5.yaml uvr5/uvr5.sh 192.168.50.205:docker/uvr5/stack/ && scp uvr5/Dockerfile 192.168.50.205:docker/uvr5/stack/uvr5/

To update UVR5-UI, change `UVR5_REF` in the Dockerfile to a newer commit, then run `up` again.

## LTX-2.5 (video)

LTX-2.5 runs inside ComfyUI, in Docker on enki. ComfyUI has no official image, so [ltx/Dockerfile](ltx/Dockerfile) builds one pinned to a commit (`COMFY_REF`). The stack is in `~/docker/ltx/stack`. Models, output, input and saved workflows are in `~/docker/ltx/data`. `ltx.sh up` stops `llama-swap`, ACE-Step and Magenta, then starts it. `ltx.sh down` stops it and starts `llama-swap` again. See the log with `docker logs -f ltx`.

From Windows:

ssh 192.168.50.205 '~/docker/ltx/stack/ltx.sh up'
ssh 192.168.50.205 '~/docker/ltx/stack/ltx.sh down'

 http://192.168.50.205:8188

In ComfyUI, open Templates > Video > **LTX-2.5 T2V** (or I2V). The models are the int8 builds ComfyUI's docs use; ComfyUI moves weights between the 16GB GPU and system RAM as needed, so expect it to be slow.

After editing the copies in [ltx/](ltx/), push them back:

scp ltx/ltx.yaml ltx/ltx.sh 192.168.50.205:docker/ltx/stack/ && scp ltx/Dockerfile 192.168.50.205:docker/ltx/stack/ltx/

### Downloading the models (on enki)

The models are already in `~/docker/ltx/data/models`. To download them again, note that the weights are gated: first accept the license at https://huggingface.co/Lightricks/LTX-2.5 and create a read token at https://huggingface.co/settings/tokens.

```
~/.local/bin/uvx hf auth login
~/.local/bin/uvx hf download Lightricks/LTX-2.5 --local-dir ~/docker/ltx/data/models \
  diffusion_models/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors \
  text_encoders/gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors \
  vae/ltx-2.5-video-vae-bf16.safetensors \
  vae/ltx-2.5-audio-vae-bf16.safetensors \
  latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors
```

The repo's file paths match ComfyUI's model folders, so `--local-dir` puts each file where the template looks for it.
