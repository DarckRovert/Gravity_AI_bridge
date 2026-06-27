import asyncio
import json
import logging
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# We will implement V2VPipeline in v2v_pipeline.py
from v2v_pipeline import V2VPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("v2v_server")

app = FastAPI(title="Gravity V2V Engine (DirectML)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline: Optional[V2VPipeline] = None
pipeline_task: Optional[asyncio.Task] = None

@app.on_event("startup")
async def startup_event():
    global pipeline
    logger.info("Inicializando V2V Pipeline (ONNX DirectML)...")
    try:
        pipeline = V2VPipeline()
        # Start the camera capture and engine loop in background
        pipeline.start()
        logger.info("V2V Pipeline iniciado correctamente.")
    except Exception as e:
        logger.error(f"Error al iniciar el V2V Pipeline: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    global pipeline
    logger.info("Apagando V2V Pipeline...")
    if pipeline:
        pipeline.stop()

@app.get("/status")
async def get_status():
    global pipeline
    return {
        "online": True,
        "active": pipeline.running if pipeline else False,
        "fps": 0,
        "bg_ready": True
    }

@app.websocket("/ws/v2v")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Cliente conectado al streaming V2V.")
    
    if not pipeline:
        await websocket.close(code=1011, reason="El pipeline no esta iniciado.")
        return

    # Registrar el cliente para recibir los frames codificados
    pipeline.add_client(websocket)

    try:
        while True:
            # Recibir comandos de estilo y configuraciones desde el frontend en vivo
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                action = msg.get("action")
                
                if action == "update_config":
                    config = msg.get("config", {})
                    pipeline.update_config(config)
                    logger.info(f"Configuracion V2V actualizada: {config}")
                
                # Tambien soportar comandos del frontend
                command = msg.get("command")
                if command == "toggle_active":
                    pipeline.ai_active = msg.get("active", False)
                    logger.info(f"V2V AI Active: {pipeline.ai_active}")
                elif command == "get_status":
                    # Status is sent back directly by broadcast or ping
                    pass
                elif command == "generate_base" or command == "refresh_bg":
                    # For now just trigger an AI frame if paused
                    pass
                    
                elif action == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                logger.warning("Recibido payload no-JSON en WebSocket")
                
    except WebSocketDisconnect:
        logger.info("Cliente desconectado.")
        pipeline.remove_client(websocket)
    except Exception as e:
        logger.error(f"Error en websocket: {e}")
        pipeline.remove_client(websocket)

if __name__ == "__main__":
    uvicorn.run("v2v_server:app", host="0.0.0.0", port=7861, log_level="info")
