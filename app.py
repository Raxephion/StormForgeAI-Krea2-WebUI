"""
Krea 2 WebUI - Gradio front-end for the Krea 2 (Turbo) image model.

Uses a headless ComfyUI instance as the inference backend, since ComfyUI
ships native Krea 2 support (UNETLoader + CLIPLoader type=krea2 + VAELoader)
with built-in low-VRAM offloading for fp8 checkpoints.

Run via run.bat, which starts ComfyUI on 127.0.0.1:8188 first, then this app.
"""

import io
import json
import os
import random
import time
import uuid

import gradio as gr
import requests
from PIL import Image

COMFY_HOST = "127.0.0.1"
COMFY_PORT = 8188
COMFY_URL = f"http://{COMFY_HOST}:{COMFY_PORT}"

COMFY_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ComfyUI")
DIFFUSION_MODELS_DIR = os.path.join(COMFY_ROOT, "models", "diffusion_models")
TEXT_ENCODERS_DIR = os.path.join(COMFY_ROOT, "models", "text_encoders")
VAE_DIR = os.path.join(COMFY_ROOT, "models", "vae")

CLIENT_ID = str(uuid.uuid4())


# --------------------------------------------------------------------------
# File discovery
# --------------------------------------------------------------------------

def list_safetensors(folder):
    if not os.path.isdir(folder):
        return []
    files = [f for f in os.listdir(folder) if f.lower().endswith((".safetensors", ".sft", ".gguf"))]
    return sorted(files)


def refresh_file_lists():
    models = list_safetensors(DIFFUSION_MODELS_DIR)
    encoders = list_safetensors(TEXT_ENCODERS_DIR)
    vaes = list_safetensors(VAE_DIR)
    return (
        gr.update(choices=models, value=models[0] if models else None),
        gr.update(choices=encoders, value=encoders[0] if encoders else None),
        gr.update(choices=vaes, value=vaes[0] if vaes else None),
    )


# --------------------------------------------------------------------------
# ComfyUI workflow construction (API format)
# --------------------------------------------------------------------------

def build_workflow(
    model_file,
    encoder_file,
    vae_file,
    prompt,
    negative_prompt,
    width,
    height,
    steps,
    cfg,
    sampler_name,
    scheduler,
    seed,
    batch_size,
    use_tiled_vae,
    tile_size,
):
    workflow = {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": model_file,
                "weight_dtype": "default",
            },
        },
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": encoder_file,
                "type": "krea2",
            },
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": vae_file,
            },
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": prompt,
                "clip": ["2", 0],
            },
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": negative_prompt or "",
                "clip": ["2", 0],
            },
        },
        "6": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {
                "width": int(width),
                "height": int(height),
                "batch_size": int(batch_size),
            },
        },
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "seed": int(seed),
                "steps": int(steps),
                "cfg": float(cfg),
                "sampler_name": sampler_name,
                "scheduler": scheduler,
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["6", 0],
            },
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["8", 0],
                "filename_prefix": "krea2",
            },
        },
    }

    if use_tiled_vae:
        workflow["8"] = {
            "class_type": "VAEDecodeTiled",
            "inputs": {
                "samples": ["7", 0],
                "vae": ["3", 0],
                "tile_size": int(tile_size),
                "overlap": 64,
                "temporal_size": 64,
                "temporal_overlap": 8,
            },
        }
    else:
        workflow["8"] = {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["7", 0],
                "vae": ["3", 0],
            },
        }

    return workflow


# --------------------------------------------------------------------------
# ComfyUI API calls
# --------------------------------------------------------------------------

def queue_prompt(workflow):
    payload = {"prompt": workflow, "client_id": CLIENT_ID}
    resp = requests.post(f"{COMFY_URL}/prompt", json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["prompt_id"]


def get_history(prompt_id):
    resp = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_image(filename, subfolder, folder_type):
    params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    resp = requests.get(f"{COMFY_URL}/view", params=params, timeout=60)
    resp.raise_for_status()
    return Image.open(io.BytesIO(resp.content))


def wait_for_backend(timeout=10):
    try:
        requests.get(f"{COMFY_URL}/system_stats", timeout=timeout)
        return True
    except requests.exceptions.RequestException:
        return False


# --------------------------------------------------------------------------
# Generation
# --------------------------------------------------------------------------

def generate(
    model_file,
    encoder_file,
    vae_file,
    prompt,
    negative_prompt,
    width,
    height,
    steps,
    cfg,
    sampler_name,
    scheduler,
    seed,
    randomize_seed,
    batch_size,
    use_tiled_vae,
    tile_size,
):
    if not model_file or not encoder_file or not vae_file:
        yield None, "Select a model, text encoder, and VAE file first.", seed
        return

    if not prompt or not prompt.strip():
        yield None, "Enter a prompt.", seed
        return

    if not wait_for_backend():
        yield None, "Cannot reach ComfyUI backend at 127.0.0.1:8188. Is run.bat still starting it?", seed
        return

    actual_seed = random.randint(0, 2**32 - 1) if randomize_seed else int(seed)

    workflow = build_workflow(
        model_file, encoder_file, vae_file,
        prompt, negative_prompt,
        width, height, steps, cfg,
        sampler_name, scheduler,
        actual_seed, batch_size,
        use_tiled_vae, tile_size,
    )

    yield None, "Queuing prompt...", actual_seed

    try:
        prompt_id = queue_prompt(workflow)
    except requests.exceptions.RequestException as e:
        yield None, f"Failed to queue prompt: {e}", actual_seed
        return
    except (KeyError, ValueError) as e:
        yield None, f"Backend rejected the workflow: {e}", actual_seed
        return

    start = time.time()
    timeout_s = 600

    while True:
        time.sleep(1)
        elapsed = time.time() - start
        if elapsed > timeout_s:
            yield None, "Timed out waiting for image (10 min). Check the ComfyUI backend window for errors.", actual_seed
            return

        try:
            history = get_history(prompt_id)
        except requests.exceptions.RequestException:
            continue

        if prompt_id not in history:
            yield None, f"Generating... ({int(elapsed)}s)", actual_seed
            continue

        entry = history[prompt_id]
        status = entry.get("status", {})

        if status.get("status_str") == "error":
            yield None, "Generation failed. Check the ComfyUI backend window for the full error.", actual_seed
            return

        outputs = entry.get("outputs", {})
        images_out = outputs.get("9", {}).get("images", [])
        if images_out:
            img_info = images_out[0]
            try:
                image = fetch_image(
                    img_info["filename"], img_info.get("subfolder", ""), img_info.get("type", "output")
                )
            except requests.exceptions.RequestException as e:
                yield None, f"Generated but failed to fetch image: {e}", actual_seed
                return
            yield image, f"Done in {int(elapsed)}s (seed {actual_seed})", actual_seed
            return

        yield None, f"Generating... ({int(elapsed)}s)", actual_seed


# --------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------

CYBERPUNK_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400..900&display=swap');

:root {
    --neon-blue: #00ffff;
    --neon-glow: 0 0 8px #00ffff, 0 0 16px #00ffff;
    --bg-black: #000000;
}

/* GLOBAL */
html, body, .gradio-container,
.gradio-container * {
    font-family: 'Orbitron', sans-serif !important;
}

body, .gradio-container {
    background: var(--bg-black) !important;
    color: var(--neon-blue) !important;
}

/* MAIN TITLE */
#main_title {
    color: var(--neon-blue) !important;
    text-shadow: var(--neon-glow);
    text-align: center;
    font-size: 3em !important;
    border-bottom: 1px solid var(--neon-blue);
    padding-bottom: 8px;
}

/* INPUTS */
textarea,
input[type="text"],
input[type="number"],
.gr-textbox,
.gr-input,
.gradio-dropdown,
.wrap,
.wrap-inner {
    background: var(--bg-black) !important;
    border: 1px solid var(--neon-blue) !important;
    color: var(--neon-blue) !important;
    text-shadow: var(--neon-glow);
    border-radius: 0 !important;
    box-shadow: inset 0 0 12px #003333;
}

/* DROPDOWNS */
.gradio-dropdown,
.gradio-dropdown input,
.gradio-dropdown button,
ul.options,
ul.options li {
    font-family: 'Orbitron', sans-serif !important;
    background: var(--bg-black) !important;
    color: var(--neon-blue) !important;
}

/* IMAGE / GALLERY */
.gradio-gallery,
.gradio-image {
    border: 1px solid var(--neon-blue) !important;
    border-radius: 0 !important;
    background: #001111 !important;
}

/* BUTTONS */
button,
.gr-button {
    background: var(--bg-black) !important;
    border: 1px solid var(--neon-blue) !important;
    color: var(--neon-blue) !important;
    text-shadow: var(--neon-glow);
    border-radius: 0 !important;
    transition: all 0.2s ease-in-out;
}

button:hover,
.gr-button:hover {
    background: var(--neon-blue) !important;
    color: var(--bg-black) !important;
    text-shadow: none !important;
    box-shadow: 0 0 20px #00ffff;
}

/* ACCORDIONS, BOXES, TABS */
.gr-accordion,
.gr-box,
.gradio-tabs > .tab-nav > button {
    background: var(--bg-black) !important;
    border: 1px solid var(--neon-blue) !important;
    color: var(--neon-blue) !important;
    border-radius: 0 !important;
}

.gradio-tabs > .tab-nav > button.selected {
    background: var(--neon-blue) !important;
    color: var(--bg-black) !important;
    text-shadow: none !important;
}

/* SLIDERS */
input[type="range"] {
    -webkit-appearance: none;
    appearance: none;
    background: transparent;
}

input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    height: 16px;
    width: 16px;
    border-radius: 0;
    background: var(--neon-blue);
    cursor: pointer;
    margin-top: -7px;
    box-shadow: var(--neon-glow);
}

input[type="range"]::-webkit-slider-runnable-track {
    width: 100%;
    height: 2px;
    cursor: pointer;
    background: var(--neon-blue) !important;
    border: 1px solid var(--neon-blue);
}

/* LABELS / HEADINGS */
h1, h2, h3, h4,
label,
.gr-checkbox label span,
.gradio-container label span {
    color: var(--neon-blue) !important;
    text-shadow: var(--neon-glow);
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 600;
    text-transform: uppercase;
}

/* MARKDOWN */
.gr-markdown,
.gr-markdown p,
.gr-markdown li,
.gr-markdown code,
.gr-markdown strong {
    font-family: 'Orbitron', sans-serif !important;
    color: var(--neon-blue) !important;
}

/* STATUS */
#status_box textarea {
    font-family: 'Orbitron', sans-serif !important;
}


/* --- STORMFORGE HUD LAYOUT --- */
.gradio-container {
    max-width: 1600px !important;
    margin: 0 auto !important;
    padding: 20px !important;
    background-image:
        linear-gradient(rgba(0,255,255,.018) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,255,255,.018) 1px, transparent 1px),
        radial-gradient(circle at 50% 0%, rgba(0,255,255,.08), transparent 38%) !important;
    background-size: 30px 30px, 30px 30px, auto !important;
}
#hud_header {
    padding: 16px 22px 14px !important;
    margin-bottom: 18px !important;
    border: 1px solid var(--neon-blue) !important;
    background: linear-gradient(90deg, rgba(0,255,255,.13), transparent 20%, transparent 80%, rgba(0,255,255,.13)), #02090b !important;
    box-shadow: 0 0 24px rgba(0,255,255,.12), inset 0 0 22px rgba(0,255,255,.04) !important;
    clip-path: polygon(0 0, calc(100% - 24px) 0, 100% 24px, 100% 100%, 24px 100%, 0 calc(100% - 24px));
}
#hud_subtitle { text-align:center; letter-spacing:.12em; text-transform:uppercase; font-size:.76rem !important; opacity:.78; }
.hud-panel {
    position: relative;
    padding: 16px !important;
    border: 1px solid var(--neon-blue) !important;
    background: linear-gradient(135deg, rgba(0,255,255,.055), transparent 24%), #02090b !important;
    box-shadow: 0 0 24px rgba(0,255,255,.10), inset 0 0 22px rgba(0,255,255,.035) !important;
    border-radius: 0 !important;
}
.hud-panel::before {
    content:""; position:absolute; top:-1px; left:18px; width:72px; height:3px;
    background:var(--neon-blue); box-shadow:var(--neon-glow); pointer-events:none;
}
.hud-title {
    margin: 0 0 14px !important;
    padding: 7px 10px !important;
    border-left: 4px solid var(--neon-blue);
    border-bottom: 1px solid rgba(0,255,255,.32);
    background: linear-gradient(90deg, rgba(0,255,255,.12), transparent);
    letter-spacing:.12em; text-transform:uppercase;
}
#output_panel .gradio-image { min-height: 640px !important; }
#backend_panel { margin-top:18px !important; }
#generate_btn { min-height:56px !important; font-weight:800 !important; letter-spacing:.16em !important; }
#generate_btn button { min-height:56px !important; }
@media (max-width: 900px) {
    .gradio-container { padding:10px !important; }
    #output_panel .gradio-image { min-height:420px !important; }
}

"""

with gr.Blocks(title="StormForgeAI Krea 2 WebUI", css=CYBERPUNK_CSS) as demo:
    with gr.Column(elem_id="hud_header"):
        gr.Markdown("# StormForgeAI Krea 2 WebUI", elem_id="main_title")
        gr.Markdown("Local Krea 2 Turbo inference console // Headless ComfyUI backend", elem_id="hud_subtitle")

    with gr.Row():
        with gr.Column(scale=1, elem_classes=["hud-panel"], elem_id="prompt_panel"):
            gr.Markdown("### Prompt & Generation", elem_classes=["hud-title"])
            prompt_box = gr.Textbox(label="Prompt", lines=6, placeholder="a fox walking in the snow")
            negative_box = gr.Textbox(label="Negative prompt (unused at cfg=1)", lines=2)

            with gr.Row():
                width_slider = gr.Slider(512, 2048, value=1024, step=16, label="Width")
                height_slider = gr.Slider(512, 2048, value=1024, step=16, label="Height")

            with gr.Row():
                steps_slider = gr.Slider(1, 50, value=8, step=1, label="Steps")
                cfg_slider = gr.Slider(0.0, 10.0, value=1.0, step=0.1, label="CFG")

            with gr.Accordion("Advanced", open=False):
                sampler_dropdown = gr.Dropdown(
                    label="Sampler",
                    choices=["euler", "euler_ancestral", "dpmpp_2m", "dpmpp_2m_sde", "res_multistep"],
                    value="euler",
                )
                scheduler_dropdown = gr.Dropdown(
                    label="Scheduler",
                    choices=["simple", "sgm_uniform", "beta", "normal"],
                    value="simple",
                )
                batch_slider = gr.Slider(1, 4, value=1, step=1, label="Batch size")
                with gr.Row():
                    seed_box = gr.Number(label="Seed", value=0, precision=0)
                    randomize_checkbox = gr.Checkbox(label="Randomize seed", value=True)
                with gr.Row():
                    tiled_vae_checkbox = gr.Checkbox(label="Tiled VAE decode (recommended for 6GB VRAM)", value=True)
                    tile_size_slider = gr.Slider(256, 1024, value=512, step=64, label="VAE tile size")

            generate_btn = gr.Button("Initialize Generation", variant="primary", elem_id="generate_btn")

        with gr.Column(scale=1, elem_classes=["hud-panel"], elem_id="output_panel"):
            gr.Markdown("### Output Monitor", elem_classes=["hud-title"])
            output_image = gr.Image(label="Output", type="pil")
            status_box = gr.Textbox(label="Status", interactive=False, elem_id="status_box")

    with gr.Column(elem_classes=["hud-panel"], elem_id="backend_panel"):
        gr.Markdown("## Backend Configuration", elem_classes=["hud-title"])

        with gr.Row():
            init_models, init_encoders, init_vaes = refresh_file_lists()

            model_dropdown = gr.Dropdown(label="Diffusion model (Krea 2 Turbo fp8)", **{k:v for k,v in init_models.items() if k in ("choices","value")})
            encoder_dropdown = gr.Dropdown(label="Text encoder (Qwen3-VL fp8)", **{k:v for k,v in init_encoders.items() if k in ("choices","value")})
            vae_dropdown = gr.Dropdown(label="VAE (Qwen-Image)", **{k:v for k,v in init_vaes.items() if k in ("choices","value")})
            refresh_btn = gr.Button("Refresh file lists")

    refresh_btn.click(
        fn=refresh_file_lists,
        inputs=None,
        outputs=[model_dropdown, encoder_dropdown, vae_dropdown],
    )

    generate_btn.click(
        fn=generate,
        inputs=[
            model_dropdown, encoder_dropdown, vae_dropdown,
            prompt_box, negative_box,
            width_slider, height_slider,
            steps_slider, cfg_slider,
            sampler_dropdown, scheduler_dropdown,
            seed_box, randomize_checkbox, batch_slider,
            tiled_vae_checkbox, tile_size_slider,
        ],
        outputs=[output_image, status_box, seed_box],
    )

if __name__ == "__main__":
    demo.queue().launch(inbrowser=True)
