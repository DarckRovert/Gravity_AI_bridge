import os
import subprocess
import logging
import sys

logging.basicConfig(level=logging.INFO, format="[ONNX Exporter] %(message)s")

def export_model():
    model_id = "stabilityai/sd-turbo"
    output_dir = "models/sd-turbo-onnx"
    
    if os.path.exists(output_dir) and len(os.listdir(output_dir)) > 0:
        logging.info(f"El modelo ya parece estar exportado en {output_dir}. Si deseas re-descargarlo, borra la carpeta.")
        return

    logging.info(f"Iniciando descarga y exportación de {model_id} a ONNX FP16...")
    logging.info("Este proceso puede tardar varios minutos y consumirá bastante RAM/Red.")
    
    # Construimos el comando optimum-cli
    cmd = [
        sys.executable, "-m", "optimum.exporters.onnx",
        "--model", model_id,
        "--task", "image-to-image",
        "--dtype", "fp16",
        output_dir
    ]
    
    try:
        subprocess.run(cmd, check=True)
        logging.info(f"Exportación completada exitosamente en: {output_dir}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Fallo en la exportación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    export_model()
