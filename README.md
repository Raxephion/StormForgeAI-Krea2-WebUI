# StormForgeAI Krea 2 WebUI

A lightweight, local WebUI for **Krea 2 Turbo**, designed for users who want the power of Krea 2 **without having to learn or use ComfyUI**.

StormForgeAI Krea 2 WebUI provides a clean, straightforward interface focused on image generation rather than node graphs and workflows. Under the hood, the application launches a **headless (background) ComfyUI backend** that handles model loading, inference, FP8 support, and low-VRAM optimizations automatically. You never need to interact with ComfyUI directly unless you want to troubleshoot something.

Because the backend is powered by ComfyUI, the application uses the **standard ComfyUI folder structure** for models, LoRAs, VAEs, text encoders, and other assets. This means you can easily reuse existing ComfyUI model libraries without duplicating files.

Generation time on an **RTX 3060 Laptop GPU (6 GB VRAM)** is approximately **46 seconds** using the default settings.

> **⚠️ APP IS IN ACTIVE DEVELOPMENT ⚠️**

---

# Features

- Clean, beginner-friendly interface
- No node graphs or workflow editing required
- Automatic headless ComfyUI backend
- Native Krea 2 Turbo support
- FP8 model loading
- Low VRAM optimizations for 6 GB GPUs
- Standard ComfyUI folder structure
- Simple installation and setup

---

# Setup

1. Run `install.bat`.

   This will:
   - Create a Python virtual environment
   - Install PyTorch
   - Install ComfyUI
   - Install all required dependencies for Krea 2 WebUI

2. Copy your model files into the appropriate folders:

| File | Folder |
|------|--------|
| Krea 2 Turbo FP8 model | `ComfyUI/models/diffusion_models/` |
| Qwen3-VL FP8 Text Encoder | `ComfyUI/models/text_encoders/` |
| Qwen-Image VAE | `ComfyUI/models/vae/` |

3. Run `run.bat`.

   This automatically:

   - Starts a **headless ComfyUI backend** using `--lowvram`
   - Launches the Krea 2 WebUI
   - Opens your browser automatically

No manual ComfyUI configuration is required.

---

# Model Folder Structure

Since the backend uses ComfyUI internally, all assets follow the standard ComfyUI directory layout.

Examples:

```
ComfyUI/
└── models/
    ├── diffusion_models/
    ├── text_encoders/
    ├── vae/
    ├── loras/
    ├── clip_vision/
    ├── controlnet/
    └── ...
```

If you've previously used ComfyUI, you can simply copy or reuse your existing model folders.

---

# Notes

- Default settings (`steps=8`, `cfg=1.0`, `sampler=euler`, `scheduler=simple`) match the recommended settings for **Krea 2 Turbo**.
- The required timestep shift is already baked into the model configuration, so no additional sampling node is necessary.
- **Tiled VAE Decode** is enabled by default to reduce peak VRAM usage during decoding. Disable it if your GPU has sufficient memory and you prefer slightly faster decoding.
- If image generation fails, check the separate **"Krea2 Backend - ComfyUI"** console window. It contains the complete error messages and traceback, making troubleshooting much easier.
- If PyTorch cannot detect your GPU, edit the `--index-url` inside `install.bat` to match your installed CUDA version, then run the installer again.
- Whenever you add, remove, or replace models, LoRAs, VAEs, or other assets, click **Refresh File Lists** inside the UI (or simply restart the application).

---

# Why This Project?

ComfyUI is an incredibly powerful tool, but it can also feel overwhelming if your goal is simply to generate great images.

Krea 2 WebUI exists to provide a simpler alternative:

- Install.
- Copy your models.
- Launch the app.
- Start creating.

No node graphs.
No workflow editing.
No hunting for missing nodes.

Just a straightforward interface that lets you focus on generating images while ComfyUI quietly handles the heavy lifting in the background.
