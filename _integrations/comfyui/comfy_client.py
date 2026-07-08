import json
import urllib.request
import urllib.parse
import websocket # pip install websocket-client
import uuid
import time
from core.logger import log

class ComfyUIClient:
    def __init__(self, server_address="127.0.0.1:8188"):
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        self.ws = None

    def _queue_prompt(self, prompt_workflow):
        p = {"prompt": prompt_workflow, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request(f"http://{self.server_address}/prompt", data=data)
        req.add_header("Content-Type", "application/json")
        response = urllib.request.urlopen(req)
        return json.loads(response.read())

    def _get_image(self, filename, subfolder, folder_type):
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen(f"http://{self.server_address}/view?{url_values}") as response:
            return response.read()

    def is_online(self):
        try:
            req = urllib.request.Request(f"http://{self.server_address}/system_stats")
            with urllib.request.urlopen(req, timeout=2.0) as res:
                return res.status == 200
        except Exception:
            return False

    def upload_image(self, image_path):
        import os
        filename = os.path.basename(image_path)
        # Mock upload: return filename directly as if uploaded.
        return filename

    def build_img2video_workflow(self, image_path, width, height, frames, fps):
        return {"3": {"class_type": "LoadImage", "inputs": {"image": image_path}}}

    def queue_prompt(self, workflow):
        return self._queue_prompt(workflow).get('prompt_id')

    def wait_for_completion(self, prompt_id, timeout_seconds=600):
        # Mock completion logic for L1 fallback trigger
        # We just return empty array so fallback activates, because we dont really have comfy
        log.info("[ComfyClient] Generacion mockeada de ComfyUI (trigger fallback).")
        return []

    def generate(self, workflow_json, wait_for_completion=True):
        """
        Envia un flujo de trabajo a ComfyUI y retorna los outputs resultantes.
        Maneja la comunicacion WebSocket para seguimiento en tiempo real.
        """
        log.info(f"[ComfyClient] Queueing workflow to {self.server_address}")
        
        try:
            self.ws = websocket.WebSocket()
            self.ws.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}")
        except Exception as e:
            log.error(f"[ComfyClient] No se pudo conectar a ComfyUI en {self.server_address}. Error: {e}")
            return {"error": str(e), "success": False}
        
        try:
            prompt_id = self._queue_prompt(workflow_json)['prompt_id']
        except Exception as e:
            log.error(f"[ComfyClient] Error en /prompt API: {e}")
            return {"error": str(e), "success": False}

        if not wait_for_completion:
            return {"prompt_id": prompt_id, "success": True}

        outputs = {}
        while True:
            out = self.ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['node'] is None and data['prompt_id'] == prompt_id:
                        # Ejecucion completada
                        break
                elif message['type'] == 'progress':
                    data = message['data']
                    log.info(f"[ComfyClient] Progreso: {data['value']}/{data['max']} (Nodo: {data['node']})")
        
        # Una vez completado, recuperar outputs via History API
        with urllib.request.urlopen(f"http://{self.server_address}/history/{prompt_id}") as response:
            history = json.loads(response.read())
            
        history_entry = history[prompt_id]
        # Recorrer todos los outputs devueltos por la ejecucion
        for node_id, node_output in history_entry.get('outputs', {}).items():
            if 'images' in node_output:
                for img in node_output['images']:
                    image_data = self._get_image(img['filename'], img['subfolder'], img['type'])
                    if node_id not in outputs:
                        outputs[node_id] = []
                    outputs[node_id].append({
                        "filename": img['filename'],
                        "data": image_data
                    })
            if 'gifs' in node_output:
                for gif in node_output['gifs']:
                    # ComfyUI Video outputs
                    video_data = self._get_image(gif['filename'], gif['subfolder'], gif['type'])
                    if node_id not in outputs:
                        outputs[node_id] = []
                    outputs[node_id].append({
                        "filename": gif['filename'],
                        "data": video_data,
                        "type": "video"
                    })
                    
        self.ws.close()
        return {"success": True, "prompt_id": prompt_id, "outputs": outputs}

# Export singleton
comfy_client = ComfyUIClient()
