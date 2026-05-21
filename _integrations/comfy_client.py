"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI – COMFYUI CLIENT V1.0                                           ║
║  Cliente REST + WebSocket para instancia local de ComfyUI                   ║
║  Permite generar clips animados (Image-to-Video) via LTX-Video              ║
║                                                                              ║
║  Arquitectura de integración:                                                ║
║    Fooocus (imagen estática) → ComfyUI (animación) → ffmpeg (concat)        ║
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
        """Extrae la lista de tags (texto) generados del historial."""
        tags: list[str] = []
        try:
            history    = self.get_history(prompt_id)
            prompt_data = history.get(prompt_id, {})
            outputs    = prompt_data.get("outputs", {})

            for _node_id, node_output in outputs.items():
                if "tags" in node_output:
                    if isinstance(node_output["tags"], list):
                        tags.extend(node_output["tags"])
        except Exception:
            pass
        return tags

    def build_img2video_workflow(
        self,
        image_path: str,
        width: int = 512,
        height: int = 512,
        frames: int = 25,
        fps: int = 8,
        model_name: str = "ltx-video-2b-v0.9.5.safetensors",
    ) -> dict:
        """
        Construye un workflow básico Image-to-Video usando el nodo LTX-Video de ComfyUI.
        Requiere que el modelo LTX-Video esté descargado en ComfyUI/models/video_models/.

        Args:
            image_path:  Ruta absoluta a la imagen de entrada.
            width, height: Resolución del video de salida.
            frames:      Cantidad de frames a generar (25 = ~3s a 8fps).
            fps:         Frames por segundo del clip de salida.
            model_name:  Nombre del archivo del modelo LTX-Video.

        Returns:
            Dict con la estructura de workflow lista para queue_prompt().
        """
        workflow = {
            "1": {
                "class_type": "LoadImage",
                "inputs": {"image": image_path}
            },
            "2": {
                "class_type": "LTXVLoader",
                "inputs": {
                    "ckpt_name": model_name,
                    "dtype": "bfloat16"
                }
            },
            "3": {
                "class_type": "LTXVConditioning",
                "inputs": {
                    "positive": "cinematic motion, smooth, high quality video",
                    "negative": "blur, distortion, artifacts, static, low quality",
                    "model": ["2", 0],
                    "width": width,
                    "height": height,
                    "frame_rate": fps,
                    "length": frames,
                    "batch_size": 1,
                }
            },
            "4": {
                "class_type": "LTXVSampler",
                "inputs": {
                    "model": ["2", 0],
                    "conditioning": ["3", 0],
                    "image": ["1", 0],
                    "sampler": "euler",
                    "scheduler": "linear",
                    "steps": 25,
                    "cfg": 3.0,
                    "seed": 42,
                    "noise_aug_strength": 0.0
                }
            },
            "5": {
                "class_type": "LTXVDecoder",
                "inputs": {
                    "samples": ["4", 0],
                    "model": ["2", 0],
                }
            },
            "6": {
                "class_type": "SaveAnimatedWEBP",
                "inputs": {
                    "images": ["5", 0],
                    "filename_prefix": "gravity_clip",
                    "fps": fps,
                    "lossless": False,
                    "quality": 85,
                    "method": "default",
                }
            }
        }
        return workflow
