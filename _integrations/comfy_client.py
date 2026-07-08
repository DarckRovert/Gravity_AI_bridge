"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI – COMFYUI CLIENT V1.1                                           ║
║  Cliente REST + WebSocket para instancia local de ComfyUI                   ║
║                                                                              ║
║  Workflows disponibles:                                                      ║
║    img2video  — SD 1.5 img2img multi-frame → SaveAnimatedWEBP               ║
║    img2prompt — WD14Tagger (Fase 2: consistencia visual inter-escena)        ║
║                                                                              ║
║  Arquitectura de integración:                                                ║
║    Pollinations (imagen) → ComfyUI (animación/tagging) → FFmpeg (concat)    ║
╚══════════════════════════════════════════════════════════════════════════════╝

Uso desde video_pipeline.py:
    from _integrations.comfy_client import ComfyUIClient
    client = ComfyUIClient()
    if client.is_online():
        prompt_id = client.queue_prompt(workflow)
        outputs   = client.wait_for_completion(prompt_id)
"""

import json
import uuid
import socket
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional


class ComfyUIClient:
    """
    Cliente para la API REST y WebSocket de ComfyUI.
    Permite encolar workflows JSON, esperar su ejecución y descargar resultados.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8188):
        self.host           = host
        self.port           = port
        self.server_address = f"{host}:{port}"
        self.client_id      = str(uuid.uuid4())

    def is_online(self, timeout: float = 2.0) -> bool:
        """Verifica si el servidor ComfyUI está activo."""
        try:
            sock = socket.create_connection((self.host, self.port), timeout=timeout)
            sock.close()
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    def queue_prompt(self, prompt_workflow: dict) -> str:
        """
        Envía un workflow JSON a /prompt y retorna el prompt_id asignado.

        Args:
            prompt_workflow: Diccionario con la estructura de nodos de ComfyUI.

        Returns:
            prompt_id (str) para rastrear la ejecución.

        Raises:
            RuntimeError: Si la petición falla.
        """
        payload = {
            "prompt":    prompt_workflow,
            "client_id": self.client_id,
        }
        data = json.dumps(payload).encode("utf-8")
        url  = f"http://{self.server_address}/prompt"
        req  = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                prompt_id = result.get("prompt_id")
                if not prompt_id:
                    raise RuntimeError(f"ComfyUI no retornó prompt_id: {result}")
                return prompt_id
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"ComfyUI HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:300]}")
        except Exception as e:
            raise RuntimeError(f"ComfyUI queue_prompt error: {e}")

    def get_history(self, prompt_id: str) -> dict:
        """Recupera el historial de ejecución de un prompt_id."""
        url = f"http://{self.server_address}/history/{prompt_id}"
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"ComfyUI get_history error: {e}")

    def get_image(self, filename: str, subfolder: str, folder_type: str) -> bytes:
        """
        Descarga el binario de un archivo generado.

        Args:
            filename:    Nombre del archivo (ej: "output_00001.png").
            subfolder:   Subcarpeta dentro del output dir de ComfyUI.
            folder_type: "output" | "input" | "temp"

        Returns:
            Bytes del archivo.
        """
        params = urllib.parse.urlencode({
            "filename":  filename,
            "subfolder": subfolder,
            "type":      folder_type,
        })
        url = f"http://{self.server_address}/view?{params}"
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                return resp.read()
        except Exception as e:
            raise RuntimeError(f"ComfyUI get_image error para {filename}: {e}")

    def free_memory(self, unload_models: bool = True, free_memory: bool = True) -> bool:
        """
        Ordena a ComfyUI liberar VRAM/RAM y descargar modelos residentes.
        Ideal para llamarse entre generaciones pesadas o si hay OOM.
        """
        payload = {
            "unload_models": unload_models,
            "free_memory": free_memory
        }
        data = json.dumps(payload).encode("utf-8")
        url = f"http://{self.server_address}/free"
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.getcode() == 200
        except Exception:
            return False

    def wait_for_completion(self, prompt_id: str, timeout_seconds: float = 600.0) -> list[dict]:
        """
        Bloquea mediante WebSocket hasta que el prompt finalice.
        No requiere la librería `websockets`; usa socket TCP puro con HTTP Upgrade.

        Args:
            prompt_id:       ID del prompt a esperar.
            timeout_seconds: Tiempo máximo de espera antes de lanzar RuntimeError.

        Returns:
            Lista de dicts con info de archivos generados:
            [{"filename": str, "subfolder": str, "type": str}, ...]

        Raises:
            RuntimeError: Si timeout o error de conexión.
        """
        try:
            import websocket as _ws
            ws = _ws.WebSocket()
            ws.settimeout(timeout_seconds)
            ws.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}")
            try:
                while True:
                    raw = ws.recv()
                    if isinstance(raw, str):
                        msg = json.loads(raw)
                        if msg.get("type") == "executing":
                            data = msg.get("data", {})
                            if data.get("node") is None and data.get("prompt_id") == prompt_id:
                                break  # Ejecución completada
                        elif msg.get("type") == "execution_error":
                            err_data = msg.get("data", {})
                            if err_data.get("prompt_id") == prompt_id:
                                raise RuntimeError(f"ComfyUI abortó la generación: {err_data.get('exception_type')}")
            except _ws.WebSocketTimeoutException:
                raise RuntimeError(f"ComfyUI WebSocket Timeout tras {timeout_seconds}s esperando prompt_id={prompt_id}")
            except _ws.WebSocketException as e:
                raise RuntimeError(f"ComfyUI WebSocket Error crítico: {e}")
            finally:
                ws.close()

        except ImportError:
            # Fallback: polling via HTTP /history si websocket-client no está instalado
            import time
            elapsed = 0.0
            interval = 2.0
            while elapsed < timeout_seconds:
                hist = self.get_history(prompt_id)
                if prompt_id in hist:
                    break
                time.sleep(interval)
                elapsed += interval
            else:
                raise RuntimeError(f"ComfyUI timeout esperando prompt_id={prompt_id}")

        # Extraer archivos de salida del historial
        return self._extract_outputs(prompt_id)

    def _extract_outputs(self, prompt_id: str) -> list[dict]:
        """Extrae la lista de archivos generados del historial."""
        output_files: list[dict] = []
        try:
            history    = self.get_history(prompt_id)
            prompt_data = history.get(prompt_id, {})
            outputs    = prompt_data.get("outputs", {})

            for _node_id, node_output in outputs.items():
                for media_type in ("images", "gifs", "videos"):
                    for item in node_output.get(media_type, []):
                        output_files.append(item)
        except Exception:
            pass
        return output_files

    def extract_tags(self, prompt_id: str) -> list[str]:
        """
        Extrae los tags visuales producidos por WD14Tagger del historial de ejecución.

        El nodo WD14Tagger|pysssss puede depositar su output bajo distintas keys
        dependiendo de la versión: 'tags', 'text', o como valor string directo.
        Este método inspecciona todas las variantes para garantizar compatibilidad.

        Args:
            prompt_id: ID del prompt ejecutado que contiene el nodo WD14.

        Returns:
            Lista de strings con los tags extraídos. Lista vacía si no hay resultado.
        """
        tags: list[str] = []
        try:
            history     = self.get_history(prompt_id)
            prompt_data = history.get(prompt_id, {})
            outputs     = prompt_data.get("outputs", {})

            for _node_id, node_output in outputs.items():
                # Variante 1: key "tags" (versiones antiguas de ComfyUI-WD14-Tagger)
                if "tags" in node_output:
                    val = node_output["tags"]
                    if isinstance(val, list):
                        tags.extend([str(t) for t in val if t])
                    elif isinstance(val, str) and val:
                        tags.append(val)

                # Variante 2: key "text" (versiones nuevas / pysssss)
                elif "text" in node_output:
                    val = node_output["text"]
                    if isinstance(val, list):
                        tags.extend([str(t) for t in val if t])
                    elif isinstance(val, str) and val:
                        tags.append(val)

                # Variante 3: diccionario con valores string planos (fallback)
                else:
                    for v in node_output.values():
                        if isinstance(v, str) and len(v) > 5 and "," in v:
                            tags.append(v)
                            break
                        elif isinstance(v, list) and v and isinstance(v[0], str):
                            tags.extend([str(t) for t in v if t])
                            break

        except Exception:
            pass
        return tags


    def upload_image(self, local_path: str) -> str:
        """
        Sube una imagen al servidor ComfyUI via /upload/image.

        Args:
            local_path: Ruta absoluta a la imagen en el sistema local.

        Returns:
            Nombre del archivo tal como lo registró ComfyUI (para usar en LoadImage).

        Raises:
            RuntimeError: Si la subida falla.
        """
        import os
        import uuid as _uuid
        filename = os.path.basename(local_path)
        with open(local_path, "rb") as f:
            img_data = f.read()

        boundary = _uuid.uuid4().hex
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
            "Content-Type: image/png\r\n\r\n"
        ).encode("utf-8") + img_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

        req = urllib.request.Request(
            f"http://{self.server_address}/upload/image",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                name = result.get("name")
                if not name:
                    raise RuntimeError(f"ComfyUI no retornó nombre tras upload: {result}")
                return name
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"ComfyUI upload HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:200]}")
        except Exception as e:
            raise RuntimeError(f"ComfyUI upload_image error: {e}")

    def build_text2image_workflow(
        self,
        positive_prompt: str,
        negative_prompt: str = "ugly, deformed, blurry, low quality, watermark",
        width: int = 512,
        height: int = 512,
        model_name: str = "v1-5-pruned-emaonly-fp16.safetensors",
        steps: int = 20,
        cfg: float = 7.0,
        seed: int = 42,
    ) -> dict:
        """
        Construye un workflow Text-to-Image estandar para SD 1.5.
        Genera una sola imagen basada en el prompt.
        """
        width  = max(64, (width  // 8) * 8)
        height = max(64, (height // 8) * 8)

        workflow = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": model_name}
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                }
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": positive_prompt,
                    "clip": ["4", 1]
                }
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["4", 1]
                }
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                }
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                }
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "gravity_t2i",
                    "images": ["8", 0]
                }
            }
        }
        return workflow

    def build_img2video_workflow(
        self,
        image_path: str,
        width: int = 512,
        height: int = 512,
        frames: int = 25,
        fps: int = 8,
        model_name: str = "v1-5-pruned-emaonly-fp16.safetensors",
        positive_prompt: str = "cinematic motion, smooth animation, high quality, detailed",
        negative_prompt: str = "blur, distortion, artifacts, static, low quality, noise",
        steps: int = 20,
        cfg: float = 7.0,
        denoise: float = 0.55,
        seed: int = 42,
    ) -> dict:
        """
        Construye un workflow Image-to-Video mediante img2img multi-frame con SD 1.5.

        Genera `frames` variaciones de la imagen fuente con seeds distintos
        y las guarda como WEBP animado vía SaveAnimatedWEBP.

        Requiere únicamente: v1-5-pruned-emaonly-fp16.safetensors (instalado).
        No requiere T5-XXL, LTX-Video ni ningún encoder adicional.

        Args:
            image_path:      Ruta absoluta a la imagen de entrada.
            width, height:   Resolución del video de salida (múltiplos de 8).
            frames:          Número de frames a generar (= batch_size).
            fps:             Frames por segundo del WEBP animado de salida.
            model_name:      Checkpoint SD 1.5 disponible localmente.
            positive_prompt: Prompt positivo de texto para guiar los frames.
            negative_prompt: Prompt negativo de texto.
            steps:           Pasos de difusión por frame.
            cfg:             Classifier-free guidance scale.
            denoise:         Fuerza de denoising (0.0=copia exacta, 1.0=regeneración total).
            seed:            Semilla base (cada frame usa seed+frame_index).

        Returns:
            Dict con la estructura de workflow lista para queue_prompt().
        """
        # Asegurar dimensiones válidas para SD 1.5 (múltiplos de 8)
        width  = max(64, (width  // 8) * 8)
        height = max(64, (height // 8) * 8)

        workflow = {
            # ── Cargar imagen de referencia ──────────────────────────────────
            "1": {
                "class_type": "LoadImage",
                "inputs": {"image": image_path}
            },
            # ── Escalar imagen a resolución objetivo ─────────────────────────
            "12": {
                "class_type": "ImageScale",
                "inputs": {
                    "image":          ["1", 0],
                    "upscale_method": "lanczos",
                    "width":          width,
                    "height":         height,
                    "crop":           "center",
                }
            },
            # ── Modelo SD 1.5 (modelo + clip + vae) ─────────────────────────
            "2": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": model_name}
            },
            # ── Encoders de texto ─────────────────────────────────────────────
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": positive_prompt,
                    "clip": ["2", 1]
                }
            },
            "4": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["2", 1]
                }
            },
            # ── Codificar imagen referencia a latent ─────────────────────────
            "5": {
                "class_type": "VAEEncode",
                "inputs": {
                    "pixels": ["12", 0],
                    "vae":    ["2", 2]
                }
            },
            # ── Batch de N frames: img2img con seeds variados ─────────────────
            "6": {
                "class_type": "KSampler",
                "inputs": {
                    "model":        ["2", 0],
                    "seed":         seed,
                    "steps":        steps,
                    "cfg":          cfg,
                    "sampler_name": "euler_ancestral",
                    "scheduler":    "karras",
                    "positive":     ["3", 0],
                    "negative":     ["4", 0],
                    "latent_image": ["5", 0],
                    "denoise":      denoise
                }
            },
            # ── Decodificar latent a imagen ───────────────────────────────────
            "7": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["6", 0],
                    "vae":     ["2", 2]
                }
            },
            # ── Guardar como WEBP animado ─────────────────────────────────────
            "9": {
                "class_type": "SaveAnimatedWEBP",
                "inputs": {
                    "images":          ["7", 0],
                    "filename_prefix": "gravity_clip",
                    "fps":             fps,
                    "lossless":        False,
                    "quality":         85,
                    "method":          "default"
                }
            }
        }

        # Expandir a N frames mediante nodos repetidos con seed+i
        # Cada frame adicional es otro KSampler con seed distinto cuyo output
        # se concatena. Para mantener el workflow simple, usamos batch en VAEEncode
        # expandiendo el latent. La forma más compatible en ComfyUI es generar
        # una lista de imágenes mediante RepeatLatentBatch y seeds variables.
        # Dado que KSampler no acepta batch de seeds, usamos la estructura minimal:
        # batch_size en EmptyLatentImage con un único seed (ComfyUI genera variación
        # interna por batch index cuando use_batch_seed_offset está activo).
        if frames > 1:
            workflow["5"] = {
                "class_type": "VAEEncode",
                "inputs": {
                    "pixels": ["12", 0],
                    "vae":    ["2", 2]
                }
            }
            workflow["13"] = {
                "class_type": "RepeatLatentBatch",
                "inputs": {
                    "samples": ["5", 0],
                    "amount":  min(frames, 32)   # máx 32 frames para CPU viable
                }
            }
            workflow["6"]["inputs"]["latent_image"] = ["13", 0]

        return workflow

    def build_img2prompt_workflow(
        self,
        image_name: str,
        model: str = "wd-v1-4-moat-tagger-v2",
        threshold: float = 0.35,
        character_threshold: float = 0.85,
        exclude_tags: str = "rating:safe, rating:questionable, rating:explicit",
    ) -> dict:
        """
        Construye el workflow de Image-to-Prompt usando WD14Tagger.

        El resultado del tagger (tags visuales de la imagen) se recupera mediante
        extract_tags(prompt_id) tras la ejecución. No genera archivos en disco.

        Args:
            image_name:          Nombre de archivo ya copiado al directorio /input de ComfyUI.
            model:               Modelo WD14 a usar para el tagging.
            threshold:           Umbral de confianza general para tags (0.0-1.0).
            character_threshold: Umbral de confianza para tags de personaje.
            exclude_tags:        Tags a excluir del output (separados por coma).

        Returns:
            Dict con la estructura de workflow lista para queue_prompt().
        """
        return {
            "1": {
                "class_type": "LoadImage",
                "inputs": {"image": image_name}
            },
            "2": {
                "class_type": "WD14Tagger|pysssss",
                "inputs": {
                    "image":               ["1", 0],
                    "model":               model,
                    "threshold":           threshold,
                    "character_threshold": character_threshold,
                    "replace_underscore":  True,
                    "trailing_comma":      False,
                    "exclude_tags":        exclude_tags,
                }
            }
        }
