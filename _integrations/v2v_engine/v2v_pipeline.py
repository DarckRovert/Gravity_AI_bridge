import cv2
import os
import time
import threading
import logging
import traceback
import queue
import numpy as np
from PIL import Image
from v2v_server import state, start_server_in_background
import onnxruntime as ort
from optimum.onnxruntime import ORTStableDiffusionImg2ImgPipeline
from virtual_cam import VirtualCamera
from segmentor import PersonSegmentor
from background_generator import BackgroundGenerator
from compositor import composite_full_body, add_hud
from scenes_config import get_scene
from motion_driver import MotionDriver

logging.basicConfig(level=logging.INFO, format="[V2V Server] %(message)s")

WIDTH, HEIGHT = 512, 512
CAMERA_INDEX  = 0

# ── Queues ────────────────────────────────────────────────────────────────────
frame_queue   = queue.Queue(maxsize=2)   # exclusivo del inference thread
display_queue = queue.Queue(maxsize=1)   # exclusivo del display thread (último frame)
result_queue  = queue.Queue(maxsize=1)   # resultados de inferencia


def check_directml():
    providers = ort.get_available_providers()
    if 'DmlExecutionProvider' in providers:
        logging.info("DirectML habilitado.")
        return ['DmlExecutionProvider', 'CPUExecutionProvider']
    return ['CPUExecutionProvider']


def camera_thread_func():
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        logging.error(f"No se pudo abrir la cámara {CAMERA_INDEX}.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue

        frame = cv2.flip(frame, 1)
        if frame.shape[0] != HEIGHT or frame.shape[1] != WIDTH:
            frame = cv2.resize(frame, (WIDTH, HEIGHT), interpolation=cv2.INTER_LINEAR)

        frame_copy = frame.copy()

        if frame_queue.full():
            try: frame_queue.get_nowait()
            except queue.Empty: pass
        frame_queue.put(frame_copy)

        if display_queue.full():
            try: display_queue.get_nowait()
            except queue.Empty: pass
        display_queue.put(frame_copy)


def inference_thread_func(pipe, segmentor: PersonSegmentor, bg_gen: BackgroundGenerator, motion_driver: MotionDriver):
    """
    Motor V4.0 (VTuber Architecture):
    - INIT MODE: Genera avatar y fondo una vez usando SD-Turbo (1.7s).
    - LIVE MODE: Usa LivePortrait ONNX para animar a 30+ FPS.
    """
    first_animation_frame = True

    while True:
        if not state.active:
            time.sleep(0.05)
            first_animation_frame = True
            continue

        try:
            frame = frame_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        start_time = time.time()
        scene_cfg  = get_scene(state.preset)

        # ── Fase 1: Generación Única (INIT MODE) ─────────────────────────────
        if state.bg_dirty or state.bg_image is None:
            logging.info(f"Generando fondo: {scene_cfg['name']}...")
            try:
                state.bg_image = bg_gen.generate(
                    bg_prompt=scene_cfg["bg_prompt"],
                    bg_negative=scene_cfg["bg_negative"],
                    seed=42
                )
            except Exception as e:
                logging.error(f"Error fondo: {e}")
                state.bg_image = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
            state.bg_dirty = False

        if state.base_dirty or state.reference_avatar is None:
            logging.info("Generando Avatar Base (SD-Turbo)...")
            custom = state.prompt.strip()
            full_prompt = (
                f"{scene_cfg['face_prompt']}, full body, highly detailed, "
                f"looking directly at camera, front view face"
                + (f", {custom}" if custom else "")
            )
            full_negative = (
                f"{scene_cfg['face_negative']}, {state.negative_prompt}, "
                "profile view, turning away, blurry, deformed"
            )

            init_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            try:
                result = pipe(
                    prompt=full_prompt,
                    negative_prompt=full_negative,
                    image=init_pil,
                    num_inference_steps=3,
                    strength=state.strength,
                    guidance_scale=2.0,
                ).images[0]
                
                state.reference_avatar = cv2.cvtColor(np.array(result), cv2.COLOR_RGB2BGR)
                motion_driver.set_source_image(state.reference_avatar)
                first_animation_frame = True
            except Exception as e:
                logging.error(f"Error SD-Turbo: {e}")
                state.reference_avatar = frame
                
            state.base_dirty = False

        # ── Fase 2: Animación en Tiempo Real (LIVE MODE) ──────────────────────
        # La máscara de segmentación se aplica sobre el frame de la webcam
        # para obtener la silueta de la persona real.
        try:
            person_mask = segmentor.get_mask(frame)
        except Exception:
            person_mask = np.ones((HEIGHT, WIDTH), dtype=np.float32)

        # Si no hay avatar base todavía, mostrar frame de webcam directamente
        if state.reference_avatar is None or not motion_driver.is_prepared:
            animated_bgr = frame.copy()
        else:
            anim_start = time.time()
            try:
                animated_bgr = motion_driver.animate(frame, first_frame=first_animation_frame)
                first_animation_frame = False
                # FPS se calcula solo en LIVE MODE (animación real)
                elapsed_anim = time.time() - anim_start
                state.fps = round(1.0 / elapsed_anim if elapsed_anim > 0 else 0.0, 1)
            except Exception as e:
                logging.error(f"Error Animación: {e}\n{traceback.format_exc()}")
                animated_bgr = state.reference_avatar if state.reference_avatar is not None else frame

            # Guard: asegurarse que el resultado es válido
            if animated_bgr is None:
                animated_bgr = state.reference_avatar if state.reference_avatar is not None else frame

        bg_snap = state.bg_image

        if result_queue.full():
            try: result_queue.get_nowait()
            except queue.Empty: pass
        result_queue.put((frame, animated_bgr, person_mask, bg_snap))


def run_pipeline():
    server_thread = threading.Thread(target=start_server_in_background, daemon=True)
    server_thread.start()

    providers = check_directml()

    # Modelos Base
    logging.info("Cargando SD-Turbo ONNX...")
    try:
        pipe = ORTStableDiffusionImg2ImgPipeline.from_pretrained(
            os.path.join("models", "sd-turbo-onnx"), provider=providers[0]
        )
    except Exception as e:
        logging.error(f"Error SD-Turbo: {e}")
        return

    try:
        segmentor = PersonSegmentor(os.path.join("models", "selfie_segmenter.tflite"))
        bg_gen    = BackgroundGenerator(pipe)
        motion_driver = MotionDriver() # LivePortrait ONNX
    except Exception as e:
        logging.error(f"Error inicializando módulos: {e}")
        return

    # Hilos
    cam_thread = threading.Thread(target=camera_thread_func, daemon=True)
    cam_thread.start()

    inf_thread = threading.Thread(
        target=inference_thread_func,
        args=(pipe, segmentor, bg_gen, motion_driver),
        daemon=True
    )
    inf_thread.start()

    vcam = VirtualCamera(width=WIDTH, height=HEIGHT, fps=30.0)
    last_result = None

    while True:
        try:
            frame = display_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        if state.active:
            try:
                last_result = result_queue.get_nowait()
            except queue.Empty:
                pass

            if last_result is not None:
                orig_frame, transformed_bgr, person_mask, bg_snap = last_result
                scene_cfg = get_scene(state.preset)
                
                if bg_snap is None:
                    bg_snap = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
                    bg_snap[:] = scene_cfg.get("bg_color", (10, 10, 10))

                composite = composite_full_body(
                    transformed_bgr=transformed_bgr,
                    bg_image=bg_snap,
                    person_mask=person_mask,
                )

                mode_label = "GENERANDO AVATAR (INIT)..." if state.base_dirty else "ANIMACION EN VIVO (V4)"
                color      = (0, 165, 255) if state.base_dirty else (0, 255, 100)
                final_frame = add_hud(composite, state.fps, mode_label, scene_cfg["name"], color)
            else:
                final_frame = frame.copy()
                cv2.putText(final_frame, "Iniciando Motor V4...", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
        else:
            final_frame = frame.copy()
            cv2.putText(final_frame, "AI BYPASS", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            last_result = None

        vcam.send(final_frame)
        if vcam.wait_key() == ord('q'):
            break

    segmentor.close()
    vcam.close()


if __name__ == "__main__":
    run_pipeline()
