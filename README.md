# Krea 2 WebUI

Local Gradio UI for Krea 2 Turbo, backed by a headless ComfyUI instance
(ComfyUI ships native Krea 2 support and handles fp8 loading + low-VRAM
offloading).

## Setup

1. Run `install.bat` (creates a venv, installs PyTorch + ComfyUI + this app's dependencies).
2. Copy your files into:
   - `ComfyUI/models/diffusion_models/` — Krea 2 Turbo fp8 model
   - `ComfyUI/models/text_encoders/` — Qwen3-VL fp8 text encoder
   - `ComfyUI/models/vae/` — Qwen-Image VAE
3. Run `run.bat`. This starts ComfyUI in the background (`--lowvram`), then
   opens the Gradio UI in your browser.

## Notes

- Defaults (steps=8, cfg=1.0, sampler=euler, scheduler=simple) match Krea 2
  Turbo's recommended settings. The timestep shift is baked into the model
  config, so no extra sampling node is needed.
- "Tiled VAE decode" is on by default — lowers peak VRAM during decode at a
  small speed cost. Turn it off if you have headroom.
- If generation fails, check the separate "Krea2 Backend - ComfyUI" console
  window — it has the full error/traceback.
- If PyTorch fails to detect your GPU, edit the `--index-url` in
  `install.bat` to match your installed CUDA driver version, then re-run.
- Every time you add/replace files in the model folders, click
  "Refresh file lists" in the UI (or restart the app).
