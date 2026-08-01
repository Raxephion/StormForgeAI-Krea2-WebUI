# StormForgeAI Krea 2 WebUI

A lightweight, local WebUI for **Krea 2 Turbo**, designed for users who want the power of Krea 2 **without having to learn or use ComfyUI**.

StormForgeAI Krea 2 WebUI provides a clean, straightforward interface focused on image generation rather than node graphs and workflows. Under the hood, the application launches a **headless (background) ComfyUI backend** that handles model loading, inference, FP8 support, LoRA application, and low-VRAM optimizations automatically. You never need to interact with ComfyUI directly unless you want to troubleshoot something.

Because the backend is powered by ComfyUI, the application uses the **standard ComfyUI folder structure** for diffusion models, LoRAs, VAEs, text encoders, and other assets. This means you can easily reuse existing ComfyUI model libraries without duplicating files.

Generation time on an **RTX 3060 Laptop GPU (6 GB VRAM)** is approximately **46 seconds** using the default settings.

> **⚠️ APP IS IN ACTIVE DEVELOPMENT ⚠️**

---

# Latest Update: LoRA Support

StormForgeAI Krea 2 WebUI now includes native **Krea 2 LoRA support**.

The app automatically discovers LoRAs stored inside `ComfyUI/models/loras/`, including LoRAs organized in subfolders.

From within the WebUI, you can:

- Select a LoRA or choose `None` to use the base model
- Adjust the LoRA model strength from `-2.0` to `2.0`
- Refresh the file lists after adding, removing, or replacing LoRAs
- Apply a LoRA without editing workflows or interacting with nodes

The selected LoRA is inserted directly into the dynamically generated ComfyUI API graph using `LoraLoaderModelOnly`. This applies the LoRA to the diffusion model while leaving the text encoder unchanged, making it suitable for Krea 2 diffusion-model LoRAs.

When `None` is selected, the application uses the original base-model path without applying a LoRA.

---

# Features

- Clean, beginner-friendly interface
- No node graphs or workflow editing required
- Automatic headless ComfyUI backend
- Native Krea 2 Turbo support
- Native LoRA selection and strength control
- Recursive LoRA discovery, including subfolders
- FP8 model loading
- Low-VRAM optimizations for 6 GB GPUs
- Standard ComfyUI folder structure
- Refreshable model and asset lists
- Simple installation and setup
- Separate backend console for troubleshooting

---

# Setup

1. Run `install.bat`.

   This will:

   - Create a Python virtual environment
   - Install PyTorch
   - Install ComfyUI
   - Install all required dependencies for StormForgeAI Krea 2 WebUI

2. Copy your files into the appropriate folders:

   | File | Folder |
   |---|---|
   | Krea 2 Turbo FP8 model | `ComfyUI/models/diffusion_models/` |
   | Qwen3-VL FP8 text encoder | `ComfyUI/models/text_encoders/` |
   | Qwen-Image VAE | `ComfyUI/models/vae/` |
   | Krea 2 LoRAs | `ComfyUI/models/loras/` |

3. Run `run.bat`.

   This automatically:

   - Starts a **headless ComfyUI backend** using `--lowvram`
   - Launches StormForgeAI Krea 2 WebUI
   - Opens the WebUI in your default browser

No manual ComfyUI configuration is required.

---

# Using LoRAs

Place your Krea 2 LoRA files inside:

```text
ComfyUI/models/loras/
```

You can also organize them into subfolders:

```text
ComfyUI/
└── models/
    └── loras/
        ├── styles/
        │   └── example_style.safetensors
        ├── characters/
        │   └── example_character.safetensors
        └── example_lora.safetensors
```

After adding a LoRA:

1. Launch the application or click **Refresh File Lists**.
2. Select the LoRA from the LoRA dropdown.
3. Adjust its model strength.
4. Generate your image normally.

Select `None` to generate with the base model only.

> LoRA compatibility depends on how the LoRA was trained. Use LoRAs specifically created for Krea 2 or a compatible model architecture.

---

# Model Folder Structure

Since the backend uses ComfyUI internally, all assets follow the standard ComfyUI directory layout.

```text
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

If you have previously used ComfyUI, you can simply copy or reuse your existing model folders.

---

# Notes

- Default settings (`steps=8`, `cfg=1.0`, `sampler=euler`, `scheduler=simple`) match the recommended settings for **Krea 2 Turbo**.
- The required timestep shift is already baked into the model configuration, so no additional sampling node is necessary.
- **Tiled VAE Decode** is enabled by default to reduce peak VRAM usage during decoding. Disable it if your GPU has sufficient memory and you prefer slightly faster decoding.
- If image generation fails, check the separate **Krea2 Backend - ComfyUI** console window. It contains the complete error messages and traceback, making troubleshooting much easier.
- If PyTorch cannot detect your GPU, edit the `--index-url` inside `install.bat` to match your installed CUDA version, then run the installer again.
- Whenever you add, remove, or replace models, LoRAs, VAEs, or other assets, click **Refresh File Lists** inside the UI or restart the application.

---

# Why This Project?

ComfyUI is an incredibly powerful tool, but it can also feel overwhelming if your goal is simply to generate great images.

StormForgeAI Krea 2 WebUI exists to provide a simpler alternative:

- Install.
- Copy your models.
- Launch the app.
- Start creating.

No node graphs.  
No workflow editing.  
No hunting for missing nodes.

Just a straightforward interface that lets you focus on generating images while ComfyUI quietly handles the heavy lifting in the background.
