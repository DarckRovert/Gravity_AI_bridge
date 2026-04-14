"""
Gravity AI Bridge V9.3 PRO -- Vision Studio UI
UI ligera de Gradio que actua como wrapper visual para el motor Fooocus.
Puerto: 7862 (Fooocus corre en 7861, Bridge en 7860)

ARQUITECTURA: Fooocus 2.5.5 no expone API REST (/v1/generation/...).
Solo expone UI Gradio. Este studio NO usa la API REST de Fooocus.
En su lugar:
  1. El usuario lanza la generacion desde aqui O desde http://127.0.0.1:7861
  2. Este studio muestra en tiempo real las imagenes del directorio de salida
  3. La galeria se auto-refresca cada 5s
  4. health_check ve si Fooocus responde en el puerto 7861
"""
import sys
import time
import os
import glob
import threading

# Path setup correcto para importar fooocus_client
_BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TOOLS_DIR = os.path.join(_BASE_DIR, "tools")
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

import gradio as gr
from fooocus_client import health_check, get_latest_outputs, OUTPUT_DIR, FOOOCUS_BASE_URL, trigger_gradio_generation


# ─── Cold-start detection ─────────────────────────────────────────────────────

def wait_for_fooocus(max_retries: int = 20, wait_sec: float = 3.0) -> bool:
    """
    Espera a que Fooocus este disponible (cold-start puede tomar 60-90 seg en CPU).
    """
    for attempt in range(1, max_retries + 1):
        status = health_check()
        if status["online"]:
            print(f"[VisionStudio] Fooocus disponible tras {attempt} intento(s).")
            return True
        print(f"[VisionStudio] Esperando Fooocus... intento {attempt}/{max_retries}")
        time.sleep(wait_sec)
    return False


def get_all_images() -> list:
    """Retorna lista de paths absolutos de todas las imagenes en el output dir, mas nuevas primero."""
    if not os.path.isdir(OUTPUT_DIR):
        return []
    imgs = []
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
        imgs.extend(glob.glob(os.path.join(OUTPUT_DIR, "**", ext), recursive=True))
    imgs.sort(key=os.path.getmtime, reverse=True)
    return imgs


# ─── Galeria de imagenes generadas ────────────────────────────────────────────

def refresh_gallery():
    """Carga las ultimas 20 imagenes del output dir para mostrar en galeria."""
    imgs = get_latest_outputs(20)
    if not imgs:
        return gr.update(value=[])
    return gr.update(value=imgs)


def get_fooocus_status() -> str:
    """Retorna string de estado del motor Fooocus para la UI."""
    st = health_check()
    imgs = get_latest_outputs(1)
    total = len(get_all_images())
    if st["online"]:
        return f"**Motor:** Activo (:7861) | **Imagenes generadas:** {total}"
    return f"**Motor:** OFFLINE — [Abrir motor Fooocus]({FOOOCUS_BASE_URL}) | Inicia INICIAR_TODO.bat"


# ─── Instruccion de generacion (redirige al motor real) ───────────────────────

def on_open_fooocus_and_wait(prompt: str, performance: str, aspect_ratio: str):
    """
    Fooocus 2.5.5 en este build solo expone UI Gradio (no API REST).
    Esta funcion:
      1. Verifica que Fooocus este online
      2. Indica al usuario que abra http://127.0.0.1:7861 con el prompt copiado
      3. Espera activamente archivos nuevos en OUTPUT_DIR (max 15 min)
      4. Retorna la imagen nueva cuando aparece en disco
    """
    if not prompt.strip():
        gr.Warning("Escribe un prompt antes de generar.")
        return None, "Sin prompt"

    # Verificar motor
    status = health_check()
    if not status["online"]:
        gr.Info("Fooocus no responde. Esperando hasta 2 minutos...")
        online = wait_for_fooocus(max_retries=30, wait_sec=4.0)
        if not online:
            gr.Warning("Fooocus offline. Inicia launchers\\INICIAR_TODO.bat.")
            return None, "Motor offline"

    # Snapshot de archivos actuales ANTES de generar
    before_set = set(get_all_images())
    before_count = len(before_set)

    # DISPARO AUTOMÁTICO (V9.3.1 PRO Upgrade)
    gr.Info(f"🎨 Enviando comando de generación al motor (CPU)...")
    trigger_result = trigger_gradio_generation(prompt, performance, aspect_ratio)
    
    if trigger_result["success"]:
        gr.Info("🚀 Motor disparado con éxito. Generación iniciada en segundo plano.")
    else:
        gr.Warning(f"⚠️ No se pudo disparar el motor automáticamente: {trigger_result['error']}")
        gr.Info("Por favor, inicia la generación manualmente en http://127.0.0.1:7861")

    print(f"[VisionStudio] Esperando imagen nueva en {OUTPUT_DIR}...")
    print(f"[VisionStudio] Archivos existentes: {before_count}")

    timeout = 900  # 15 minutos
    start = time.time()

    while time.time() - start < timeout:
        time.sleep(3.0)
        current = get_all_images()
        current_set = set(current)
        new_files = current_set - before_set

        if new_files:
            newest = max(new_files, key=os.path.getmtime)
            elapsed = round(time.time() - start)
            print(f"[VisionStudio] Nueva imagen detectada en {elapsed}s -> {os.path.basename(newest)}")
            return newest, f"Imagen generada en {elapsed}s"

        elapsed = round(time.time() - start)
        if elapsed % 30 == 0 and elapsed > 0:
            print(f"[VisionStudio] Esperando... {elapsed}s transcurridos")

    print(f"[VisionStudio] Timeout tras {timeout}s")
    gr.Warning("Timeout. Si generaste la imagen en Fooocus, usa Actualizar Galeria para verla.")
    return None, "Timeout"


# ─── UI ──────────────────────────────────────────────────────────────────────

custom_css = """
body { background-color: #0d0e17 !important; color: #e8e9f1; }
.gradio-container { background-color: #0d0e17 !important; }
.dark { --color-accent: #7c6af7; }
.status-box { padding: 8px 12px; border-radius: 6px; background: #1a1b2e; border: 1px solid #2a2b4a; margin-bottom: 8px; }
footer { display: none !important; }
"""

with gr.Blocks(title="Gravity Vision Studio V9.3", css=custom_css) as demo:
    gr.Markdown(
        "## Gravity Vision Studio V9.3 PRO\n"
        f"Motor: **Fooocus 2.5.5 (CPU — sin crash)** | Puerto motor: **7861** | "
        f"[**Abrir motor directamente**]({FOOOCUS_BASE_URL}) ← *Genera aqui directamente*\n\n"
        "> **Flujo recomendado**: Escribe el prompt → presiona **Generar** → esta UI detecta la imagen automaticamente. "
        f"O abre directamente [{FOOOCUS_BASE_URL}]({FOOOCUS_BASE_URL}) para control total."
    )

    motor_status = gr.Markdown(get_fooocus_status(), elem_classes=["status-box"])

    with gr.Tabs():
        with gr.TabItem("🎨 Generar"):
            with gr.Row():
                with gr.Column(scale=3):
                    output_image = gr.Image(
                        label="Ultima imagen generada",
                        interactive=False,
                        height=600,
                        show_label=False
                    )
                    gen_status = gr.Markdown("*Escribe un prompt y presiona Generar*")

                    with gr.Row():
                        prompt_box = gr.Textbox(
                            show_label=False,
                            placeholder="Describe la imagen que quieres generar...",
                            scale=4, container=False
                        )
                        gen_btn = gr.Button("🎨 Generar", variant="primary", scale=1)

                    with gr.Row():
                        gr.Markdown(
                            f"> **Nota**: La generacion ocurre en el motor Fooocus ([{FOOOCUS_BASE_URL}]({FOOOCUS_BASE_URL})). "
                            "Esta UI detectara la imagen automaticamente cuando este lista (3-8 min CPU)."
                        )

                with gr.Column(scale=1):
                    with gr.Tabs():
                        with gr.TabItem("Ajustes"):
                            gr.Markdown("### Rendimiento")
                            perf = gr.Radio(
                                ["Quality", "Speed"],
                                show_label=False, value="Speed"
                            )
                            gr.Markdown("*Speed = sampler euler (CPU-safe, recomendado)*")

                            gr.Markdown("### Relacion de aspecto")
                            ar = gr.Dropdown([
                                "832x1216 | 13:19 (Portrait SDXL)",
                                "1024x1024 | 1:1 (Square)",
                                "1216x832 | 19:13 (Landscape)",
                                "1152x896 | 9:7",
                                "896x1152 | 7:9",
                                "1344x768 | 7:4",
                                "768x1344 | 4:7",
                            ], show_label=False, value="832x1216 | 13:19 (Portrait SDXL)")

                        with gr.TabItem("Modelo"):
                            gr.Markdown(
                                "### Base Model (SDXL)\n\n"
                                "**juggernautXL_v8Rundiffusion**\n\n"
                                "**Motor:** Fooocus 2.5.5 (CPU)\n\n"
                                "**Sampler:** euler (CPU-safe)\n\n"
                                "**Steps:** 30\n\n"
                                "**Hardware:** Ryzen 7 8700G (CPU puro)"
                            )

                        with gr.TabItem("Info"):
                            gr.Markdown(
                                "### Estado del Sistema\n\n"
                                "| Componente | URL |\n"
                                "|-----------|-----|\n"
                                f"| Motor Fooocus (generacion) | [{FOOOCUS_BASE_URL}]({FOOOCUS_BASE_URL}) |\n"
                                "| Bridge API | http://127.0.0.1:7860 |\n"
                                "| Vision Studio (esta app) | http://127.0.0.1:7862 |\n\n"
                                "**Output dir:**\n"
                                f"`{OUTPUT_DIR}`"
                            )

        with gr.TabItem("🖼 Galeria"):
            gr.Markdown("### Ultimas imagenes generadas")
            gallery_btn = gr.Button("🔄 Actualizar Galeria", variant="secondary")
            gallery = gr.Gallery(
                label="Imagenes generadas",
                show_label=False,
                columns=3,
                height=600,
                object_fit="cover",
                value=get_all_images()[:20] if get_all_images() else []
            )
            gallery_btn.click(fn=refresh_gallery, outputs=gallery)

    # Wiring de generacion
    gen_btn.click(
        fn=on_open_fooocus_and_wait,
        inputs=[prompt_box, perf, ar],
        outputs=[output_image, gen_status]
    )

    # Refrescar estado del motor al cambiar de tab
    def update_status():
        return get_fooocus_status()


if __name__ == "__main__":
    _port = int(os.getenv("GRADIO_SERVER_PORT", "7862"))
    print(f"[Gravity Vision Studio V9.3] Iniciando en http://127.0.0.1:{_port}")
    print(f"[Gravity Vision Studio V9.3] Motor Fooocus CPU en http://127.0.0.1:7861")
    print(f"[Gravity Vision Studio V9.3] Output dir: {OUTPUT_DIR}")
    demo.launch(
        server_name="0.0.0.0",   # Accesible desde localhost:7862 y 127.0.0.1:7862
        server_port=_port,
        inbrowser=False,
        quiet=False,
        show_error=True,
    )
