"""
Test: OpenCV Facemark LBF - requiere un modelo .yaml preentrenado?
Y verificar que MediaPipe Tasks nueva API funciona correctamente para FaceLandmarker.
"""
import cv2
import numpy as np
import mediapipe as mp
import os

print("=== Test Facemark LBF ===")
# LBF necesita un modelo .yaml - verificar si viene embebido
try:
    lbf = cv2.face.createFacemarkLBF()
    # El modelo LBF requiere archivo externo. Sin cargarlo, fit() fallará.
    print(f"[OK] Instanciado, pero requiere archivo de modelo externo (.yaml / .dat)")
    # Verificar si OpenCV contrib incluye el modelo por defecto
    data_dir = cv2.__file__
    print(f"[INFO] cv2 ubicado en: {data_dir}")
except Exception as e:
    print(f"[FAIL] {e}")

print("\n=== Test MediaPipe Tasks FaceLandmarker ===")
try:
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    
    # El nuevo API necesita un archivo .task (modelo descargado aparte)
    # Verificar si hay alguno ya en disco
    model_path = os.path.join("models", "face_landmarker.task")
    print(f"[INFO] Modelo .task esperado en: {model_path}")
    print(f"[INFO] Existe: {os.path.exists(model_path)}")
    
    if not os.path.exists(model_path):
        print("[WARN] No existe. Necesita descargarse de:")
        print("  https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task")
        print(f"  Tamaño aprox: ~6.5 MB")
    else:
        # Intentar inicializar
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(base_options=base_options, num_faces=1)
        detector = vision.FaceLandmarker.create_from_options(options)
        print("[OK] FaceLandmarker inicializado correctamente!")
        detector.close()
except Exception as e:
    print(f"[FAIL] {e}")

print("\n=== Test OpenCV TPS Warping ===")
# Verificar que TPS de OpenCV funciona end-to-end
try:
    tps = cv2.createThinPlateSplineShapeTransformer()
    # Puntos de prueba mínimos
    src = np.array([[[0.0, 0.0]], [[100.0, 0.0]], [[100.0, 100.0]], [[0.0, 100.0]]], dtype=np.float32)
    dst = np.array([[[10.0, 10.0]], [[90.0, 5.0]], [[95.0, 95.0]], [[5.0, 90.0]]], dtype=np.float32)
    matches = [cv2.DMatch(i, i, 0) for i in range(4)]
    tps.estimateTransformation(dst, src, matches)
    
    test_img = np.zeros((100, 100, 3), dtype=np.uint8)
    result = tps.warpImage(test_img)
    print(f"[OK] TPS warpImage funcional. Output shape: {result.shape}")
except Exception as e:
    print(f"[FAIL] TPS: {e}")

print("\n=== Verificar v2v_server import path ===")
import sys
# El fallo del import fue por CWD. Verificar el path correcto
sys.path.insert(0, r"f:\Gravity_AI_bridge\_integrations\v2v_engine")
try:
    from v2v_server import state, V2VState
    print(f"[OK] V2VState atributos: {[a for a in dir(state) if not a.startswith('_')]}")
    print(f"[INFO] state.strength: {state.strength}, state.fps: {state.fps}")
except Exception as e:
    print(f"[FAIL] v2v_server: {e}")
