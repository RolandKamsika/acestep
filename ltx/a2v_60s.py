# LTX-2.5 audio-to-video test: T2V template graph with the empty audio latent swapped for an encoded, frozen (noise mask 0) clip.
import json, sys, time, urllib.request

AUDIO, START, SECS, FPS, W, H = "Its-that-sound.mp3", 30.0, 60.0, 24, 1024, 576
FRAMES = int(SECS * FPS) + 1
assert FRAMES % 8 == 1 and W % 64 == 0 and H % 64 == 0  # stage 1 runs at half res, needs /32
PROMPT = ("A charismatic singer performs on a stage, singing passionately into a microphone, "
          "mouth and lips moving precisely in time with the vocals, body moving to the beat, "
          "colorful concert lighting, haze, cinematic close-up, shallow depth of field")
NEG = "pc game, console game, video game, cartoon, childish, ugly"

g = {
  "unet": ("UNETLoader", {"unet_name": "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors", "weight_dtype": "default"}),
  "clip": ("CLIPLoader", {"clip_name": "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors", "type": "ltxv", "device": "default"}),
  "vvae": ("VAELoader", {"vae_name": "ltx-2.5-video-vae-bf16.safetensors"}),
  "avae": ("VAELoader", {"vae_name": "ltx-2.5-audio-vae-bf16.safetensors"}),
  "up":   ("LatentUpscaleModelLoader", {"model_name": "ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors"}),
  "pos":  ("CLIPTextEncode", {"clip": ["clip", 0], "text": PROMPT}),
  "neg":  ("CLIPTextEncode", {"clip": ["clip", 0], "text": NEG}),
  "cond": ("LTXVConditioning", {"positive": ["pos", 0], "negative": ["neg", 0], "frame_rate": FPS}),
  "aud":  ("LoadAudio", {"audio": AUDIO}),
  "trim": ("TrimAudioDuration", {"audio": ["aud", 0], "start_index": START, "duration": SECS}),
  "aenc": ("LTXVAudioVAEEncode", {"audio": ["trim", 0], "audio_vae": ["avae", 0]}),
  "mask": ("SolidMask", {"value": 0.0, "width": 1024, "height": 1024}),
  "alat": ("SetLatentNoiseMask", {"samples": ["aenc", 0], "mask": ["mask", 0]}),
  "vlat": ("EmptyLTXVLatentVideo", {"width": W // 2, "height": H // 2, "length": FRAMES, "batch_size": 1}),
  "av1":  ("LTXVConcatAVLatent", {"video_latent": ["vlat", 0], "audio_latent": ["alat", 0]}),
  "gd1":  ("LTXVDualCFGGuider", {"model": ["unet", 0], "positive": ["cond", 0], "negative": ["cond", 1], "video_cfg": 1.0, "audio_cfg": 1.0}),
  "n1":   ("RandomNoise", {"noise_seed": 42}),
  "ks1":  ("KSamplerSelect", {"sampler_name": "euler_ancestral"}),
  "sg1":  ("ManualSigmas", {"sigmas": "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"}),
  "s1":   ("SamplerCustomAdvanced", {"noise": ["n1", 0], "guider": ["gd1", 0], "sampler": ["ks1", 0], "sigmas": ["sg1", 0], "latent_image": ["av1", 0]}),
  "sep1": ("LTXVSeparateAVLatent", {"av_latent": ["s1", 0]}),
  "ups":  ("LTXVLatentUpsampler", {"samples": ["sep1", 0], "upscale_model": ["up", 0], "vae": ["vvae", 0]}),
  "av2":  ("LTXVConcatAVLatent", {"video_latent": ["ups", 0], "audio_latent": ["alat", 0]}),
  "n2":   ("RandomNoise", {"noise_seed": 42}),
  "ks2":  ("KSamplerSelect", {"sampler_name": "euler_ancestral"}),
  "sg2":  ("ManualSigmas", {"sigmas": "0.85, 0.7250, 0.4219, 0.0"}),
  "s2":   ("SamplerCustomAdvanced", {"noise": ["n2", 0], "guider": ["gd1", 0], "sampler": ["ks2", 0], "sigmas": ["sg2", 0], "latent_image": ["av2", 0]}),
  "sep2": ("LTXVSeparateAVLatent", {"av_latent": ["s2", 0]}),
  "dec":  ("VAEDecodeTiled", {"samples": ["sep2", 0], "vae": ["vvae", 0], "tile_size": 512, "overlap": 64, "temporal_size": 64, "temporal_overlap": 16}),
  # mux the source clip, not the decoded audio latent, so the soundtrack is exactly the input
  "vid":  ("CreateVideo", {"images": ["dec", 0], "audio": ["trim", 0], "fps": FPS}),
  "save": ("SaveVideo", {"video": ["vid", 0], "filename_prefix": "video/ltx25_a2v_60s", "format": "auto", "codec": "auto"}),
}
prompt = {k: {"class_type": t, "inputs": i} for k, (t, i) in g.items()}

def call(path, data=None):
    req = urllib.request.Request("http://localhost:8188" + path, json.dumps(data).encode() if data else None, {"Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        sys.exit(e.read().decode())

pid = call("/prompt", {"prompt": prompt})["prompt_id"]
t0 = time.time()
while True:
    h = call(f"/history/{pid}").get(pid)
    if h and h["status"].get("completed") is not None or (h and h["status"]["status_str"] == "error"):
        break
    time.sleep(5)
print(f"{time.time() - t0:.0f}s", h["status"]["status_str"])
if h["status"]["status_str"] == "error":
    print(json.dumps(h["status"]["messages"])[-3000:])
print(json.dumps(h["outputs"]))
