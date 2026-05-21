import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


class VirtualCamera:
    """
    Salida de video dual:
      - cv2.imshow() siempre activo (modo debug / preview)
      - pyvirtualcam → OBS Virtual Camera si OBS esta instalado y disponible

    Si pyvirtualcam falla (OBS no instalado), cae silenciosamente a solo cv2.
    """

    def __init__(self, width: int, height: int, fps: float = 30.0,
                 window_name: str = "Gravity V2V - Scene Mode"):
        self.width = width
        self.height = height
        self.fps = fps
        self.window_name = window_name
        self._cam = None
        self._vcam_active = False

        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, width, height)

        try:
            import pyvirtualcam
            self._cam = pyvirtualcam.Camera(
                width=width,
                height=height,
                fps=fps,
                fmt=pyvirtualcam.PixelFormat.BGR,
            )
            self._vcam_active = True
            logger.info(f"Virtual Camera activa en: {self._cam.device} "
                        f"({width}x{height} @ {fps}fps)")
        except ImportError:
            logger.warning("pyvirtualcam no instalado. Solo salida cv2.")
        except Exception as e:
            logger.warning(f"Virtual Camera no disponible ({e}). Solo salida cv2.")
            logger.info("Instala OBS Studio y activa 'Start Virtual Camera' una vez para habilitar vcam.")

    def send(self, frame_bgr: np.ndarray) -> None:
        """Envía frame a cv2 window y a la cámara virtual (si disponible)."""
        if frame_bgr.shape[1] != self.width or frame_bgr.shape[0] != self.height:
            frame_bgr = cv2.resize(frame_bgr, (self.width, self.height))

        # Siempre mostrar en ventana local
        cv2.imshow(self.window_name, frame_bgr)

        # Enviar a virtual camera si está activa
        if self._vcam_active and self._cam is not None:
            try:
                self._cam.send(frame_bgr)
                self._cam.sleep_until_next_frame()
            except Exception as e:
                logger.warning(f"Error en vcam.send: {e}")
                self._vcam_active = False

    def wait_key(self) -> int:
        return cv2.waitKey(1) & 0xFF

    @property
    def is_virtual_active(self) -> bool:
        return self._vcam_active

    def close(self) -> None:
        cv2.destroyAllWindows()
        if self._cam is not None:
            try:
                self._cam.close()
            except Exception:
                pass
