import sys, os
sys.path.insert(0, r'f:\Gravity_AI_bridge\_integrations\v2v_engine')
os.chdir(r'f:\Gravity_AI_bridge\_integrations\v2v_engine')

print('=== 1. ORTStableDiffusionPipeline (txt2img) ===')
try:
    from optimum.onnxruntime import ORTStableDiffusionPipeline
    print('[OK] ORTStableDiffusionPipeline importable')
except Exception as e:
    print(f'[FAIL] {e}')

print()
print('=== 2. pyvirtualcam ===')
try:
    import pyvirtualcam
    print(f'[OK] pyvirtualcam {pyvirtualcam.__version__}')
except ImportError:
    print('[MISSING] pyvirtualcam no instalado')
except Exception as e:
    print(f'[ERROR] {e}')

print()
print('=== 3. MediaPipe ImageSegmenter (Tasks) ===')
try:
    from mediapipe.tasks.python import vision
    has_seg = hasattr(vision, 'ImageSegmenter')
    status = 'OK' if has_seg else 'FAIL'
    print(f'[{status}] ImageSegmenter disponible: {has_seg}')
    model_path = os.path.join('models', 'selfie_segmenter.tflite')
    print(f'  Modelo existe: {os.path.exists(model_path)}')
except Exception as e:
    print(f'[FAIL] {e}')

print()
print('=== 4. sd-turbo-onnx estructura ===')
import json
with open('models/sd-turbo-onnx/model_index.json') as f:
    idx = json.load(f)
print(f'  _class_name: {idx["_class_name"]}')
print(f'  vae_encoder: {os.path.exists("models/sd-turbo-onnx/vae_encoder")}')
print(f'  unet: {os.path.exists("models/sd-turbo-onnx/unet")}')
print(f'  vae_decoder: {os.path.exists("models/sd-turbo-onnx/vae_decoder")}')
# txt2img no necesita vae_encoder
unet_dir = 'models/sd-turbo-onnx/unet'
unet_files = os.listdir(unet_dir) if os.path.exists(unet_dir) else []
print(f'  unet files: {unet_files}')

print()
print('=== 5. OBS instalado ===')
obs_paths = [
    r'C:\Program Files\obs-studio\bin\64bit\obs64.exe',
    r'C:\Program Files (x86)\obs-studio\bin\32bit\obs32.exe',
]
found = [p for p in obs_paths if os.path.exists(p)]
print(f'  OBS: {found if found else "No encontrado"}')

print()
print('=== 6. Pillow txt2img test (tamanio 512x512) ===')
from PIL import Image
import numpy as np
blank = Image.fromarray(np.zeros((512, 512, 3), dtype=np.uint8))
print(f'  Imagen 512x512 creada OK: {blank.size}')

print()
print('=== Auditoria completa ===')
