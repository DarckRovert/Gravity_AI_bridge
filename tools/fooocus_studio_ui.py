import sys
import time
import os

# ── sys.path patch: permite lanzar desde la raíz del proyecto ─────────────────
_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

import gradio as gr
from comfyui_client import generate_image, ImageGenRequest

COMFYUI_OUTPUT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "_integrations", "ComfyUI-Zluda", "output")
)

def get_all_images():
    """Retorna paths absolutos de todas las imágenes en el output dir."""
    if not os.path.exists(COMFYUI_OUTPUT_DIR):
        return set()
    imgs = set()
    for f in os.listdir(COMFYUI_OUTPUT_DIR):
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            imgs.add(os.path.abspath(os.path.join(COMFYUI_OUTPUT_DIR, f)))
    return imgs

def get_newest_image(exclude_paths: set) -> str | None:
    """Busca el archivo más nuevo NO presente en exclude_paths."""
    current = get_all_images()
    new_files = current - exclude_paths
    if not new_files:
        return None
    return max(new_files, key=os.path.getmtime)

def on_generate(prompt, aspect_ratio, image_number, output_format, performance):
    if not prompt:
        gr.Warning("Escribe un prompt antes de generar.")
        return None

    # Parsear dimensiones del formato '1152x896 | 9:7'
    width, height = 1024, 1024
    if "x" in aspect_ratio:
        try:
            dims = aspect_ratio.split(" | ")[0].split("x")
            width, height = int(dims[0]), int(dims[1])
        except Exception:
            pass

    req: ImageGenRequest = {
        "prompt": prompt,
        "negative_prompt": "ugly, deformed, blurry, low quality, text, watermark",
        "width": width,
        "height": height,
        "num_images": 1,
        "performance": "Quality" if performance == "Quality" else "Speed",
        "style_selections": [],
        "reference_image_path": None,
    }

    # Snapshot ANTES de generar — así sabemos qué es nuevo
    snapshot_before = get_all_images()
    print(f"[Gravity Studio] Enviando prompt a ComfyUI: {prompt[:60]}...")

    res = generate_image(req)

    if not res.get("success", False):
        err = res.get('error', 'Error desconocido')
        print(f"[Gravity Studio] ERROR: {err}")
        gr.Warning(f"ComfyUI devolvió error: {err}")
        return None

    job_id = res.get('job_id')
    print(f"[Gravity Studio] Job aceptado: {job_id}. Esperando render...")

    # Poll cada 2s hasta 360s buscando archivos NUEVOS
    start = time.time()
    while time.time() - start < 360:
        time.sleep(2.0)
        result = get_newest_image(exclude_paths=snapshot_before)
        if result:
            elapsed = round(time.time() - start)
            print(f"[Gravity Studio] Imagen lista en {elapsed}s → {os.path.basename(result)}")
            return result

    print("[Gravity Studio] Timeout esperando imagen de ComfyUI.")
    gr.Warning("Timeout: ComfyUI tardó más de 6 minutos. Reintenta.")
    return None

def toggle_advanced(advanced_enabled):
    return gr.update(visible=advanced_enabled)

custom_css = """
body {background-color: #1a1b26 !important; color: #ffffff;}
.gradio-container {background-color: #1a1b26 !important;}
"""

with gr.Blocks(title="Fooocus Studio UI") as demo:
    with gr.Row():
        with gr.Column(scale=3):
            output_image = gr.Image(label="Output", interactive=False, height=650, show_label=False)
            
            with gr.Row():
                prompt_box = gr.Textbox(show_label=False, placeholder="Type your prompt here...", scale=4, container=False)
                gen_btn = gr.Button("Generate", variant="primary", scale=1)
                
            with gr.Row():
                inp_cb = gr.Checkbox(label="Input Image", value=False)
                enh_cb = gr.Checkbox(label="Enhance", value=False)
                adv_cb = gr.Checkbox(label="Advanced", value=True)
                
        with gr.Column(scale=1, visible=True) as right_panel:
            with gr.Tabs():
                with gr.TabItem("Settings"):
                    gr.Markdown("### Preset")
                    preset = gr.Dropdown(["Initial"], value="Initial", show_label=False)
                    
                    gr.Markdown("### Performance")
                    perf = gr.Radio(["Quality", "Speed", "Lightning", "Hyper-SD"], show_label=False, value="Quality")
                    
                    gr.Markdown("### Aspect Ratios")
                    ar = gr.Dropdown([
                        "1024x1024 | 1:1", "1152x896 | 9:7", "896x1152 | 7:9",
                        "1216x832 | 19:13", "832x1216 | 13:19", "1344x768 | 7:4",
                        "768x1344 | 4:7", "1536x640 | 12:5", "640x1536 | 5:12"
                    ], show_label=False, value="1152x896 | 9:7")
                    
                    gr.Markdown("### Image Number")
                    img_num = gr.Slider(minimum=1, maximum=4, step=1, value=1, show_label=False)
                    
                    gr.Markdown("### Output Format")
                    out_fmt = gr.Radio(["png", "jpeg", "webp"], show_label=False, value="png")
                    
                    rand_cb = gr.Checkbox(label="Random", value=True)
                    
                with gr.TabItem("Styles"):
                    gr.Markdown("### Image Styles")
                    gr.CheckboxGroup(["Fooocus V2", "Fooocus Enhance", "Fooocus Sharp"], value=["Fooocus V2", "Fooocus Enhance"], label="Selected Styles", interactive=False)
                    gr.Markdown("*Styles are automatically injected by the Gravity Bridge logic.*")
                    
                with gr.TabItem("Models"):
                    gr.Markdown("### Base Model (SDXL)")
                    gr.Dropdown(["juggernautXL_v8Rundiffusion.safetensors"], value="juggernautXL_v8Rundiffusion.safetensors", label="Checkpoint", interactive=False)
                    gr.Markdown("### Refiner / LoRAs")
                    gr.Dropdown(["None"], value="None", label="Refiner", interactive=False)
                    gr.Dropdown(["None"], value="None", label="LoRA 1", interactive=False)
                    gr.Markdown("*Model architecture is locked to ZLUDA optimized presets.*")
                    
                with gr.TabItem("Advanced"):
                    gr.Markdown("### Generation Parameters")
                    gr.Slider(minimum=1.0, maximum=30.0, value=7.0, step=0.5, label="Guidance Scale (CFG)", interactive=False)
                    gr.Slider(minimum=10, maximum=60, value=30, step=1, label="Base Steps", interactive=False)
                    gr.Dropdown(["dpmpp_2m"], value="dpmpp_2m", label="Sampler", interactive=False)
                    gr.Dropdown(["karras"], value="karras", label="Scheduler", interactive=False)
                    gr.Markdown("*Advanced parameters are locked to Diamond-Tier defaults.*")

    adv_cb.change(fn=toggle_advanced, inputs=adv_cb, outputs=right_panel)
    gen_btn.click(fn=on_generate, inputs=[prompt_box, ar, img_num, out_fmt, perf], outputs=output_image)

if __name__ == "__main__":
    # Intentar puerto 7861; si está ocupado GRADIO_SERVER_PORT env lo sobreescribe
    _port = int(os.getenv("GRADIO_SERVER_PORT", "7861"))
    print(f"[Gravity Studio] Iniciando en http://127.0.0.1:{_port}")
    demo.launch(
        server_name="127.0.0.1",
        server_port=_port,
        inbrowser=True,
        quiet=False,
        theme=gr.themes.Base(),
        css=custom_css,
        show_error=True,
    )

