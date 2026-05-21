"""
Auditoría completa del entorno para el plan Avatar Reenactment.
"""
import sys
print(f"=== Python {sys.version} ===\n")

# 1. OpenCV + modelos DNN existentes
import cv2
import os
print(f"[OK] OpenCV: {cv2.__version__}")
prototxt = os.path.join("models", "face_dnn", "deploy.prototxt")
caffemodel = os.path.join("models", "face_dnn", "res10_300x300_ssd_iter_140000.caffemodel")
print(f"[{'OK' if os.path.exists(prototxt) else 'FAIL'}] deploy.prototxt: {os.path.exists(prototxt)}")
print(f"[{'OK' if os.path.exists(caffemodel) else 'FAIL'}] caffemodel: {os.path.exists(caffemodel)}")

# 2. Numpy - necesario para TPS
import numpy as np
print(f"[OK] NumPy: {np.__version__}")

# 3. onnxruntime - que proveedor está disponible?
import onnxruntime as ort
providers = ort.get_available_providers()
print(f"[OK] OnnxRuntime: {ort.__version__} | Providers: {providers}")

# 4. OpenCV tiene TPS nativo?
has_tps = hasattr(cv2, 'createThinPlateSplineShapeTransformer')
print(f"[{'OK' if has_tps else 'FAIL'}] OpenCV TPS nativo: {has_tps}")

# 5. OpenCV tiene face landmarks EXTRA?
has_facemark = hasattr(cv2, 'face') and hasattr(cv2.face, 'createFacemarkLBF')
print(f"[{'OK' if has_facemark else 'INFO'}] OpenCV Facemark LBF: {has_facemark}")

# 6. OpenCV contrib?
try:
    facemark = cv2.face.createFacemarkLBF()
    print("[OK] cv2.face.createFacemarkLBF instanciable")
except Exception as e:
    print(f"[INFO] Facemark error: {e}")

# 7. MediaPipe status real
try:
    import mediapipe as mp
    print(f"[OK] MediaPipe importado: {mp.__version__}")
    # Intentar la nueva API tasks (Python 3.13 compatible)
    from mediapipe.tasks import python as mp_tasks
    from mediapipe.tasks.python import vision
    print("[OK] MediaPipe Tasks API disponible (nueva API)")
except ImportError as e:
    print(f"[FAIL] MediaPipe Tasks: {e}")
except Exception as e:
    print(f"[WARN] MediaPipe Tasks: {e}")

# 8. Torch (disponible en el venv?)
try:
    import torch
    print(f"[OK] PyTorch: {torch.__version__}")
except ImportError:
    print("[INFO] PyTorch no en venv")

# 9. PIL
from PIL import Image
print(f"[OK] Pillow disponible")

# 10. Modelo sd-turbo-onnx presente?
import json
model_index = os.path.join("models", "sd-turbo-onnx", "model_index.json")
if os.path.exists(model_index):
    with open(model_index) as f:
        data = json.load(f)
    print(f"[OK] sd-turbo-onnx model_index: {data}")
else:
    print("[FAIL] sd-turbo-onnx model_index.json no encontrado")

# 11. Estado del state object
try:
    from v2v_server import state
    attrs = [a for a in dir(state) if not a.startswith('_')]
    print(f"[OK] V2VState atributos: {attrs}")
except Exception as e:
    print(f"[FAIL] v2v_server: {e}")

print("\n=== Auditoría completa ===")
