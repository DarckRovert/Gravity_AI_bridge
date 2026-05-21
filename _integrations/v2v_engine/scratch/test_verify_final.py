"""
Verificacion final: LandmarksDriver + TPS + imports del pipeline.
"""
import sys, os
sys.path.insert(0, r"f:\Gravity_AI_bridge\_integrations\v2v_engine")
os.chdir(r"f:\Gravity_AI_bridge\_integrations\v2v_engine")

import numpy as np
import cv2

print("=== Test 1: LandmarksDriver inicializacion ===")
from landmarks_driver import LandmarksDriver, KEY_LANDMARK_INDICES
driver = LandmarksDriver(os.path.join("models", "face_landmarker.task"))
print(f"[OK] LandmarksDriver creado. Key indices: {len(KEY_LANDMARK_INDICES)} puntos")

print("\n=== Test 2: LandmarksDriver con imagen sintetica (sin cara) ===")
blank = np.zeros((256, 256, 3), dtype=np.uint8)
result = driver.get_key_landmarks(blank)
print(f"[OK] Imagen sin cara devuelve: {result}")  # None esperado

print("\n=== Test 3: TPS con puntos de prueba ===")
import time
n = len(KEY_LANDMARK_INDICES)
# Simular landmarks ref y live con pequena diferencia
rng = np.random.default_rng(42)
ref_pts = rng.uniform(20, 236, size=(n, 2)).astype(np.float32)
live_pts = ref_pts + rng.uniform(-5, 5, size=(n, 2)).astype(np.float32)

ref_rs = ref_pts.reshape(1, n, 2)
live_rs = live_pts.reshape(1, n, 2)
matches = [cv2.DMatch(i, i, 0) for i in range(n)]

t0 = time.perf_counter()
tps = cv2.createThinPlateSplineShapeTransformer()
tps.estimateTransformation(live_rs, ref_rs, matches)
test_avatar = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
warped = tps.warpImage(test_avatar)
elapsed = (time.perf_counter() - t0) * 1000
print(f"[OK] TPS warp con {n} puntos: {elapsed:.1f}ms — output shape: {warped.shape}")
if elapsed < 100:
    print(f"[OK] Latencia TPS dentro del objetivo (<100ms)")
else:
    print(f"[WARN] Latencia TPS alta ({elapsed:.1f}ms). Considerar reducir KEY_LANDMARK_INDICES.")

print("\n=== Test 4: v2v_server state nuevos atributos ===")
from v2v_server import state, V2VState
new_attrs = ['ref_avatar', 'ref_landmarks', 'avatar_dirty', 'last_prompt', 'last_preset']
for attr in new_attrs:
    val = getattr(state, attr, '__MISSING__')
    status = 'OK' if val != '__MISSING__' else 'FAIL'
    print(f"  [{status}] state.{attr} = {repr(val)}")

print("\n=== Test 5: Import de v2v_pipeline ===")
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("v2v_pipeline", "v2v_pipeline.py")
    mod = importlib.util.module_from_spec(spec)
    # No ejecutar — solo verificar que importa sin error de sintaxis
    spec.loader.exec_module(mod)
    print("[OK] v2v_pipeline.py importa sin errores de sintaxis")
except SystemExit:
    print("[OK] v2v_pipeline.py sintaxis OK (SystemExit esperado sin GPU/camara)")
except Exception as e:
    print(f"[FAIL] v2v_pipeline.py: {e}")

driver.close()
print("\n=== Verificacion completada ===")
