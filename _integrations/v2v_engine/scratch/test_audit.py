"""
Auditoria profunda post-implementacion:
1. KEY_LANDMARK_INDICES duplicados?
2. torch importado pero innecesario?
3. Thread-safety: ref_avatar puede ser None mientras inference lo lee?
4. TPS: matches se crea con DMatch() sin query/train size validation
5. EMA smoothing ausente
6. get_status no expone modo avatar
7. seamlessClone center fuera de bounds?
8. face_roi puede ser non-contiguous (slice de array) -> cv2 issue?
9. warpImage output puede tener dtype incorrecto para seamlessClone?
"""
import sys, os
sys.path.insert(0, r"f:\Gravity_AI_bridge\_integrations\v2v_engine")
os.chdir(r"f:\Gravity_AI_bridge\_integrations\v2v_engine")

import numpy as np
import cv2

print("=== 1. KEY_LANDMARK_INDICES: duplicados y rango ===")
from landmarks_driver import KEY_LANDMARK_INDICES
indices = list(KEY_LANDMARK_INDICES)
print(f"Total indices: {len(indices)}")
print(f"Unicos: {len(set(indices))}")
out_of_range = [i for i in indices if i < 0 or i > 477]
print(f"Fuera de rango [0-477]: {out_of_range}")
dups = [i for i in indices if indices.count(i) > 1]
print(f"Duplicados: {list(set(dups))}")

print("\n=== 2. torch: se usa para algo real? ===")
# torch.manual_seed no afecta ONNX runtime - es codigo muerto
print("HALLAZGO: 'import torch' y 'torch.manual_seed(42)' son codigo muerto.")
print("SD-Turbo usa ONNX Runtime, no PyTorch. Eliminar para reducir tiempo de arranque.")

print("\n=== 3. Thread-safety: ref_avatar puede ser None mid-read? ===")
# El WS server puede ejecutar state.ref_avatar = None en su thread asyncio
# mientras inference_thread esta en Phase B ejecutando:
#   tps.warpImage(state.ref_avatar)  <- puede recibir None aqui
# HALLAZGO: Race condition real. Necesita snapshot local.
print("HALLAZGO: race condition en Phase B - state.ref_avatar puede volverse None")
print("durante tps.warpImage(state.ref_avatar) por comando refresh_avatar del WS server.")

print("\n=== 4. seamlessClone center bounds ===")
# El centro (cX, cY) viene de moments del roi_mask, siempre dentro de la imagen.
# Pero seamlessClone requiere que la mascara NO toque el borde del dst (face_roi).
# El ellipse se dibuja con axes (w*0.35, h*0.45) centrado en el centro del ROI.
# Con ROI pequeno (ej: 50x50), la elipse puede tocar bordes.
test_sizes = [(50, 50), (80, 80), (120, 120), (200, 200)]
for w, h in test_sizes:
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.ellipse(mask, (w//2, h//2), (int(w*0.35), int(h*0.45)), 0, 0, 360, 255, -1)
    # Revisar si toca bordes
    touches = (mask[0,:].any() or mask[-1,:].any() or mask[:,0].any() or mask[:,-1].any())
    print(f"  ROI {w}x{h}: mascara toca borde = {touches}")

print("\n=== 5. warpImage output dtype ===")
test_img = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
n = 10
src_pts = np.random.uniform(20, 236, (1, n, 2)).astype(np.float32)
dst_pts = src_pts + np.random.uniform(-3, 3, (1, n, 2)).astype(np.float32)
matches = [cv2.DMatch(i, i, 0) for i in range(n)]
tps = cv2.createThinPlateSplineShapeTransformer()
tps.estimateTransformation(dst_pts, src_pts, matches)
warped = tps.warpImage(test_img)
print(f"warpImage dtype: {warped.dtype}, shape: {warped.shape}")
print(f"seamlessClone requiere uint8: {warped.dtype == np.uint8}")
# Verificar si hay pixeles negros en bordes (artefacto TPS)
black_border = (warped[0,:,:].sum() == 0 or warped[-1,:,:].sum() == 0 or
                warped[:,0,:].sum() == 0 or warped[:,-1,:].sum() == 0)
print(f"Bordes negros en warpImage output: {black_border}")

print("\n=== 6. face_roi como slice: es contiguous? ===")
frame = np.zeros((512, 512, 3), dtype=np.uint8)
face_roi = frame[100:300, 150:350]
print(f"face_roi es C-contiguous: {face_roi.flags['C_CONTIGUOUS']}")
# cv2.resize sobre arrays no-contiguous puede fallar en algunos builds
try:
    resized = cv2.resize(face_roi, (256, 256))
    print(f"cv2.resize sobre slice: OK ({resized.shape})")
except Exception as e:
    print(f"cv2.resize sobre slice: FALLO - {e}")

print("\n=== 7. EMA smoothing ausente ===")
print("HALLAZGO: Sin EMA en landmarks, TPS tendrá jitter por ruido del detector.")
print("Solución: suavizado exponencial con alpha=0.6 entre frames.")

print("\n=== 8. get_status no expone modo avatar ===")
print("HALLAZGO: el panel de control no sabe si el sistema está en DRIVING o GENERANDO.")
print("Añadir: 'avatar_ready': bool, 'driving_mode': bool al status WS.")

print("\n=== Auditoria completada ===")
