import sys
import os

print(f"Python version: {sys.version}")
try:
    import mediapipe as mp
    print(f"MediaPipe version: {mp.__version__}")
    
    # Try to initialize FaceMesh
    mp_face_mesh = mp.solutions.face_mesh
    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5
    ) as face_mesh:
        print("FaceMesh initialized successfully.")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
