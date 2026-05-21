import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


def composite_scene(
    frame_bgr: np.ndarray,
    bg_image: np.ndarray,
    person_mask: np.ndarray,
    driven_face_bgr: np.ndarray | None,
    face_coords: tuple | None,
) -> np.ndarray:
    """
    Compone la escena final en 3 capas:
      1. Fondo AI generado (bg_image escaldo al tamano del frame)
      2. Persona real del webcam recortada con segmentation mask
      3. Cara AI (avatar warpado) sobre la ROI facial

    Args:
        frame_bgr:      Frame BGR del webcam (H, W, 3)
        bg_image:       Fondo AI BGR cualquier tamano (se escala al frame)
        person_mask:    Mascara float32 (H, W) - 1.0=persona, 0.0=fondo
        driven_face_bgr: Avatar warpado BGR (h_roi, w_roi, 3) o None
        face_coords:    (x1, y1, x2, y2) de la ROI facial en coordenadas del frame

    Returns:
        Frame compuesto BGR (H, W, 3) listo para mostrar/enviar a vcam.
    """
    h, w = frame_bgr.shape[:2]

    # --- Capa 1: Escalar fondo AI al tamano del frame ---
    bg_scaled = cv2.resize(bg_image, (w, h), interpolation=cv2.INTER_LINEAR)

    # --- Capa 2: Alpha blend persona sobre fondo ---
    # Suavizar la mascara de la persona para evitar bordes dentados (feathering)
    mask_smoothed = cv2.GaussianBlur(person_mask, (11, 11), 0)
    mask_3c = np.stack([mask_smoothed, mask_smoothed, mask_smoothed], axis=2)
    
    frame_f = frame_bgr.astype(np.float32)
    bg_f = bg_scaled.astype(np.float32)
    composite = (frame_f * mask_3c + bg_f * (1.0 - mask_3c)).astype(np.uint8)

    # --- Capa 3: Pegar cara AI sobre ROI facial (dentro del composite) ---
    if driven_face_bgr is not None and face_coords is not None:
        x1, y1, x2, y2 = face_coords
        h_roi, w_roi = y2 - y1, x2 - x1
        if h_roi > 0 and w_roi > 0 and y2 <= h and x2 <= w:
            face_resized = cv2.resize(driven_face_bgr, (w_roi, h_roi))
            
            # Crear mascara eliptica para difuminar bordes de la cara
            roi_mask = np.zeros((h_roi, w_roi), dtype=np.uint8)
            # Hacemos la mascara un poco mas pequeña y la difuminamos mas agresivamente
            cv2.ellipse(roi_mask, (w_roi // 2, h_roi // 2),
                        (int(w_roi * 0.30), int(h_roi * 0.40)),
                        0, 0, 360, 255, -1)
            
            roi_mask_f32 = cv2.cvtColor(roi_mask, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0
            # Blur mucho mas grande para integracion natural
            roi_mask_f32 = cv2.GaussianBlur(roi_mask_f32, (31, 31), 0)
            
            # Blend suave de la cara sobre el composite
            roi_bg = composite[y1:y2, x1:x2].astype(np.float32)
            face_f32 = face_resized.astype(np.float32)
            
            blended_roi = (face_f32 * roi_mask_f32 + roi_bg * (1.0 - roi_mask_f32)).astype(np.uint8)
            composite[y1:y2, x1:x2] = blended_roi

    return composite


def composite_full_body(
    transformed_bgr: np.ndarray,
    bg_image: np.ndarray,
    person_mask: np.ndarray,
) -> np.ndarray:
    """
    Composita el resultado de la transformacion de cuerpo completo:
      1. Fondo AI (bg_image) como base.
      2. La persona transformada por SD-Turbo sobre el fondo, usando la mascara
         de segmentacion del frame ORIGINAL (no del transformado) para separar
         el cuerpo del fondo.

    Args:
        transformed_bgr: Frame completo transformado por SD-Turbo (H, W, 3).
        bg_image:        Fondo AI generado (cualquier tamano, se escala).
        person_mask:     Mascara float32 (H, W), 1.0=persona, 0.0=fondo.

    Returns:
        Frame compuesto BGR (H, W, 3).
    """
    h, w = transformed_bgr.shape[:2]

    # Escalar fondo AI al tamano del frame
    bg_scaled = cv2.resize(bg_image, (w, h), interpolation=cv2.INTER_LINEAR)

    # Suavizar mascara de la persona (feathering de bordes)
    mask_smooth = cv2.GaussianBlur(person_mask, (15, 15), 0)
    mask_3c = np.stack([mask_smooth, mask_smooth, mask_smooth], axis=2)

    # Blend: persona transformada sobre fondo AI
    person_f = transformed_bgr.astype(np.float32)
    bg_f     = bg_scaled.astype(np.float32)
    result   = (person_f * mask_3c + bg_f * (1.0 - mask_3c)).astype(np.uint8)

    return result


def add_hud(
    frame: np.ndarray,
    fps: float,
    mode_label: str,
    scene_name: str,
    mode_color: tuple,
) -> np.ndarray:
    """
    Superpone un HUD minimalista sobre el frame:
      - Modo actual (DRIVING / GENERANDO AVATAR... / AI BYPASS)
      - Nombre de la escena activa
      - FPS de inferencia

    No modifica el frame in-place — retorna una copia.
    """
    out = frame.copy()
    h, w = out.shape[:2]

    # Barra de estado semitransparente inferior
    overlay = out.copy()
    cv2.rectangle(overlay, (0, h - 45), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, out, 0.5, 0, out)

    # Modo
    cv2.putText(out, mode_label, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, mode_color, 2, cv2.LINE_AA)

    # Escena + FPS en barra inferior
    info_text = f"Escena: {scene_name}  |  AI FPS: {fps}"
    cv2.putText(out, info_text, (10, h - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1, cv2.LINE_AA)

    return out
