# LTX-2.5 long audio-to-video (DFR): renders CHUNK-second pieces (each fits a 16GB card), each one image-conditioned on the
# previous piece's last frame for continuity, then concatenates and muxes the untouched source audio.
# usage (on enki, ComfyUI running): python3 a2v_long.py AUDIO START SECS [PREFIX]
import json, os, subprocess, sys, time, urllib.request

COMFY = os.path.expanduser("~/docker/ltx/data")  # the ltx container's /data (input/, output/)
AUDIO, START, SECS = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
PREFIX = sys.argv[4] if len(sys.argv) > 4 else "ltx25_a2v_long"
CHUNK, FPS, W, H = 10.0, 24, 1024, 576
FRAMES = int(CHUNK * FPS) + 1  # 241; last frame is dropped on concat so each piece is exactly CHUNK seconds
assert FRAMES % 8 == 1 and W % 64 == 0 and H % 64 == 0 and SECS % CHUNK == 0
PROMPT = ("A charismatic singer performs on a stage, singing passionately into a microphone, "
          "mouth and lips moving precisely in time with the vocals, body moving to the beat, "
          "colorful concert lighting, haze, cinematic close-up, shallow depth of field")
NEG = ("pc game, console game, video game, cartoon, childish, ugly, deformed hands, extra fingers, fused fingers, "
       "blurry hands, morphing, warping, distorted face, changing face, flicker, artifacts, low quality")
CFG = 2.0  # stage-1 video CFG; >1 is what makes NEG count (CFG 1 ignores it). Stage 2 stays at 1, as the DFR template has it.

# DFR (Lightricks' production path): distilled transformer; stage 1 adds generated keyframes every 24 frames, stage 2 is
# the pixel-spatial IC-LoRA detailing pass at full res, guided by the stage-1 latent as its x2 reference. Graph follows
# ComfyUI's video_ltx2_5_dfr_i2v template minus its optional 48fps temporal stage; audio is our frozen clip in both stages.
def graph(start, prefix, init_image, ref_image):
    g = {
      "unet": ("UNETLoader", {"unet_name": "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors", "weight_dtype": "default"}),
      "lora": ("LoraLoaderModelOnly", {"model": ["unet", 0], "lora_name": "ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors", "strength_model": 1.0}),
      "clip": ("CLIPLoader", {"clip_name": "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors", "type": "ltxv", "device": "default"}),
      "vvae": ("VAELoader", {"vae_name": "ltx-2.5-video-vae-bf16.safetensors"}),
      "avae": ("VAELoader", {"vae_name": "ltx-2.5-audio-vae-bf16.safetensors"}),
      "up":   ("LatentUpscaleModelLoader", {"model_name": "ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors"}),
      "pos":  ("CLIPTextEncode", {"clip": ["clip", 0], "text": PROMPT}),
      "neg":  ("CLIPTextEncode", {"clip": ["clip", 0], "text": NEG}),
      "cond": ("LTXVConditioning", {"positive": ["pos", 0], "negative": ["neg", 0], "frame_rate": FPS}),
      "aud":  ("LoadAudio", {"audio": AUDIO}),
      "trim": ("TrimAudioDuration", {"audio": ["aud", 0], "start_index": start, "duration": CHUNK}),
      "aenc": ("LTXVAudioVAEEncode", {"audio": ["trim", 0], "audio_vae": ["avae", 0]}),
      "alat": ("LTXVFreezeLatent", {"latent": ["aenc", 0]}),  # audio only steers via cross-attention, never denoised
      "vlat": ("EmptyLTXVLatentVideo", {"width": W // 2, "height": H // 2, "length": FRAMES, "batch_size": 1}),
      "ks":   ("KSamplerSelect", {"sampler_name": "euler"}),
      "n1":   ("RandomNoise", {"noise_seed": 42}),
      "n2":   ("RandomNoise", {"noise_seed": 142}),
      "sg1":  ("ManualSigmas", {"sigmas": "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"}),
      "sg2":  ("ManualSigmas", {"sigmas": "0.909375, 0.725, 0.421875, 0.0"}),
    }
    # stage 1: half res
    v, c = ["vlat", 0], (["cond", 0], ["cond", 1])
    if init_image:  # continuity: previous chunk's last frame pinned at frame 0
        g["img"] = ("LoadImage", {"image": init_image})
        g["pre"] = ("LTXVPreprocess", {"image": ["img", 0], "img_compression": 18})
        g["i1"] = ("LTXVImgToVideoInplace", {"vae": ["vvae", 0], "image": ["pre", 0], "latent": v, "strength": 1.0, "bypass": False})
        v = ["i1", 0]
    g["k1"] = ("LTXVAddGeneratedKeyframes", {"positive": c[0], "negative": c[1], "vae": ["vvae", 0], "latent": v, "interval_frames": 24, "frame_indices": ""})
    v, c = ["k1", 2], (["k1", 0], ["k1", 1])
    if ref_image:  # after the keyframes: the node requires all keyframes before any guides  # identity: chunk 0's first frame as a guide placed before the clip, so it isn't shown but anchors the face
        g["ref"] = ("LoadImage", {"image": ref_image})
        g["rs"] = ("ImageScale", {"image": ["ref", 0], "upscale_method": "lanczos", "width": W // 2, "height": H // 2, "crop": "disabled"})
        g["re"] = ("VAEEncode", {"pixels": ["rs", 0], "vae": ["vvae", 0]})
        g["g1"] = ("LTXVAddLatentGuide", {"positive": c[0], "negative": c[1], "vae": ["vvae", 0], "latent": v,
                                         "guiding_latent": ["re", 0], "latent_idx": -1, "strength": 1.0})
        v, c = ["g1", 2], (["g1", 0], ["g1", 1])
    g["gd1"] = ("LTXVDualCFGGuider", {"model": ["unet", 0], "positive": c[0], "negative": c[1], "video_cfg": CFG, "audio_cfg": 1.0})
    g["av1"] = ("LTXVConcatAVLatent", {"video_latent": v, "audio_latent": ["alat", 0]})
    g["s1"] = ("SamplerCustomAdvanced", {"noise": ["n1", 0], "guider": ["gd1", 0], "sampler": ["ks", 0], "sigmas": ["sg1", 0], "latent_image": ["av1", 0]})
    g["sep1"] = ("LTXVSeparateAVLatent", {"av_latent": ["s1", 0]})
    g["sk1"] = ("LTXVSeparateGeneratedKeyframes", {"positive": c[0], "negative": c[1], "latent": ["sep1", 0], "keyframes_to_batch": False})
    g["crop1"] = ("LTXVCropGuides", {"positive": ["sk1", 0], "negative": ["sk1", 1], "latent": ["sk1", 2]})
    # stage 2: x2 upsample, IC-LoRA detailing at full res
    g["ups"] = ("LTXVLatentUpsampler", {"samples": ["crop1", 2], "upscale_model": ["up", 0], "vae": ["vvae", 0]})
    g["kup"] = ("LTXVLatentUpsampler", {"samples": ["sk1", 3], "upscale_model": ["up", 0], "vae": ["vvae", 0]})
    # Stage 2 needs a frame-0 pin as in the template: LTXVAddGeneratedKeyframes treats a mask-less latent as fully occupied.
    if init_image:
        img2, strength2 = ["img", 0], 1.0
    else:  # chunk 0 has no input image: pin stage 1's own first frame at strength 0 (near no-op, just supplies the mask)
        g["dec1"] = ("VAEDecodeTiled", {"samples": ["crop1", 2], "vae": ["vvae", 0], "tile_size": 512, "overlap": 64, "temporal_size": 64, "temporal_overlap": 8})
        g["f0"] = ("ImageFromBatch", {"image": ["dec1", 0], "batch_index": 0, "length": 1})
        img2, strength2 = ["f0", 0], 0.0
    g["is"] = ("ImageScale", {"image": img2, "upscale_method": "lanczos", "width": W, "height": H, "crop": "center"})
    g["i2"] = ("LTXVImgToVideoInplace", {"vae": ["vvae", 0], "image": ["is", 0], "latent": ["ups", 0], "strength": strength2, "bypass": False})
    v = ["i2", 0]
    g["k2"] = ("LTXVAddGeneratedKeyframes", {"positive": ["crop1", 0], "negative": ["crop1", 1], "vae": ["vvae", 0], "latent": v,
                                            "interval_frames": 24, "keyframes": ["kup", 0], "frame_indices": ""})
    g["ic"] = ("LTXVAddLatentGuide", {"positive": ["k2", 0], "negative": ["k2", 1], "vae": ["vvae", 0], "latent": ["k2", 2],
                                     "guiding_latent": ["crop1", 2], "latent_idx": 0, "strength": 1.0})  # half-size -> x2 IC-LoRA reference
    g["gd2"] = ("CFGGuider", {"model": ["lora", 0], "positive": ["ic", 0], "negative": ["ic", 1], "cfg": 1.0})
    g["av2"] = ("LTXVConcatAVLatent", {"video_latent": ["ic", 2], "audio_latent": ["alat", 0]})
    g["s2"] = ("SamplerCustomAdvanced", {"noise": ["n2", 0], "guider": ["gd2", 0], "sampler": ["ks", 0], "sigmas": ["sg2", 0], "latent_image": ["av2", 0]})
    g["sep2"] = ("LTXVSeparateAVLatent", {"av_latent": ["s2", 0]})
    g["sk2"] = ("LTXVSeparateGeneratedKeyframes", {"positive": ["ic", 0], "negative": ["ic", 1], "latent": ["sep2", 0], "keyframes_to_batch": False})
    g["crop2"] = ("LTXVCropGuides", {"positive": ["sk2", 0], "negative": ["sk2", 1], "latent": ["sk2", 2]})
    g["dec"] = ("VAEDecodeTiled", {"samples": ["crop2", 2], "vae": ["vvae", 0], "tile_size": 512, "overlap": 64, "temporal_size": 64, "temporal_overlap": 8})
    g["vid"] = ("CreateVideo", {"images": ["dec", 0], "fps": FPS})
    g["save"] = ("SaveVideo", {"video": ["vid", 0], "filename_prefix": prefix, "format": "auto", "codec": "auto"})
    return {k: {"class_type": t, "inputs": i} for k, (t, i) in g.items()}

def call(path, data=None):
    req = urllib.request.Request("http://localhost:8188" + path, json.dumps(data).encode() if data else None, {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))

def run(prompt):
    pid = call("/prompt", {"prompt": prompt})["prompt_id"]
    while True:
        h = call(f"/history/{pid}").get(pid)
        if h and h["status"]["status_str"] == "error":
            sys.exit("chunk failed: " + json.dumps(h["status"]["messages"])[-1500:])
        if h and h["status"].get("completed"):
            f = h["outputs"]["save"]["images"][0]
            return os.path.join(COMFY, "output", f["subfolder"], f["filename"])
        time.sleep(5)

if __name__ == "__main__":
    parts, init, ref = [], None, None
    for i in range(int(SECS // CHUNK)):
        t0 = time.time()
        path = run(graph(START + i * CHUNK, f"video/{PREFIX}_part{i:02d}", init, ref))
        parts.append(path)
        if i == 0:
            ref = f"{PREFIX}_ref.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-frames:v", "1", os.path.join(COMFY, "input", ref)], check=True)
        init = f"{PREFIX}_last{i:02d}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-sseof", "-0.1", "-i", path, "-update", "1", "-frames:v", "1",
                        os.path.join(COMFY, "input", init)], check=True)
        print(f"part {i} done in {time.time() - t0:.0f}s", flush=True)

    lst = os.path.join(COMFY, "output", "video", f"{PREFIX}_parts.txt")
    with open(lst, "w") as f:
        for p in parts:
            f.write(f"file '{p}'\noutpoint {CHUNK}\n")  # drop each part's extra (241st) frame
    out = os.path.join(COMFY, "output", "video", f"{PREFIX}.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-ss", str(START), "-t", str(SECS), "-i", os.path.join(COMFY, "input", AUDIO),
                    "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", out], check=True)
    print(out)
