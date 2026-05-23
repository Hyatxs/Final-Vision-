import cv2
import numpy as np
import mss


class CapturadorPantalla:
    """Captura pantalla completa o una región específica."""

    def __init__(self):
        self.sct = mss.mss()

    def capturar_pantalla_completa(self):
        monitor = self.sct.monitors[1]
        captura = np.array(self.sct.grab(monitor))
        frame = cv2.cvtColor(captura, cv2.COLOR_BGRA2BGR)
        return frame

    def capturar_region(self, region):
        region_mss = {
            "left": int(region["left"]),
            "top": int(region["top"]),
            "width": int(region["width"]),
            "height": int(region["height"])
        }

        captura = np.array(self.sct.grab(region_mss))
        frame = cv2.cvtColor(captura, cv2.COLOR_BGRA2BGR)
        return frame

    def cerrar(self):
        self.sct.close()