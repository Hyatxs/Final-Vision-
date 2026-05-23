import cv2
import time

from .captura import CapturadorPantalla
from .configuracion import ConfiguracionDino
from .escalador import convertir_a_relativo


class CalibradorDino:
    """
    Calibra:
    1. Zona completa del juego
    2. Dinosaurio
    3. ROI frente al dinosaurio
    4. Zona del puntaje

    También guarda coordenadas relativas para soportar cambios de resolución.
    """

    def __init__(self, archivo_config="config_dino.json"):
        self.configuracion = ConfiguracionDino(archivo_config)
        self.capturador = CapturadorPantalla()

    def calibrar(self):
        print("\n=== CALIBRACIÓN DEL JUEGO ===")
        print("1. Abre el juego del dinosaurio en el navegador.")
        print("2. Deja visible la pantalla del juego.")
        print("3. Se pedirán cuatro selecciones:")
        print("   - Zona completa del juego")
        print("   - Dinosaurio")
        print("   - ROI frente al dinosaurio")
        print("   - Zona del puntaje actual")
        print("\nCuando presiones ENTER tendrás 3 segundos para cambiar al navegador.")

        input("Presiona ENTER para comenzar...")

        for i in range(3, 0, -1):
            print(f"Capturando pantalla en {i}...")
            time.sleep(1)

        frame = self.capturador.capturar_pantalla_completa()
        alto_pantalla, ancho_pantalla = frame.shape[:2]

        # ===============================
        # 1. ZONA COMPLETA DEL JUEGO
        # ===============================

        print("\nSelecciona la zona completa del juego.")
        print("No incluyas la barra de Chrome ni la barra de direcciones.")
        print("Arrastra con el mouse y luego presiona ENTER o SPACE.")

        zona_juego = self._seleccionar_roi(
            "1. Selecciona zona completa del juego",
            frame
        )

        xj, yj, wj, hj = zona_juego

        if wj == 0 or hj == 0:
            print("No seleccionaste la zona del juego.")
            self._cerrar_capturador()
            return

        frame_juego = frame[yj:yj + hj, xj:xj + wj]

        # ===============================
        # 2. DINOSAURIO
        # ===============================

        print("\nSelecciona solamente el dinosaurio.")
        print("Incluye cabeza, cuerpo, patas y cola.")
        print("No selecciones demasiado fondo ni la línea del suelo.")

        zona_dino = self._seleccionar_roi(
            "2. Selecciona al dinosaurio",
            frame_juego
        )

        xd, yd, wd, hd = zona_dino

        if wd == 0 or hd == 0:
            print("No seleccionaste el dinosaurio.")
            self._cerrar_capturador()
            return

        # ===============================
        # 3. ROI DE OBSTÁCULOS
        # ===============================

        print("\nSelecciona la ROI frente al dinosaurio.")
        print("Debe empezar justo delante del dinosaurio.")
        print("Debe cubrir cactus y aves, pero no demasiado arriba para evitar nubes.")

        zona_roi = self._seleccionar_roi(
            "3. Selecciona ROI frente al dinosaurio",
            frame_juego
        )

        xr, yr, wr, hr = zona_roi

        if wr == 0 or hr == 0:
            print("No seleccionaste la ROI.")
            self._cerrar_capturador()
            return

        # ===============================
        # 4. ZONA DEL PUNTAJE
        # ===============================

        print("\nSelecciona la zona del puntaje actual.")
        print("Marca solo los números del puntaje de la derecha.")
        print("Ejemplo: 00713")
        print("No incluyas HI ni el récord.")
        print("Si no quieres calibrar el puntaje, presiona C.")

        zona_puntaje = self._seleccionar_roi(
            "4. Selecciona puntaje actual",
            frame_juego
        )

        xp, yp, wp, hp = zona_puntaje

        usar_puntaje_calibrado = True

        if wp == 0 or hp == 0:
            print("No seleccionaste la zona del puntaje.")
            print("Se usará una zona automática aproximada.")
            usar_puntaje_calibrado = False

        # ===============================
        # GUARDAR CONFIGURACIÓN
        # ===============================

        dinosaurio = {
            "x": int(xd),
            "y": int(yd),
            "w": int(wd),
            "h": int(hd)
        }

        roi = {
            "x": int(xr),
            "y": int(yr),
            "w": int(wr),
            "h": int(hr)
        }

        config = {
            "pantalla": {
                "width": int(ancho_pantalla),
                "height": int(alto_pantalla)
            },
            "juego": {
                "left": int(xj),
                "top": int(yj),
                "width": int(wj),
                "height": int(hj)
            },
            "dinosaurio": dinosaurio,
            "roi": roi,
            "dinosaurio_rel": convertir_a_relativo(
                dinosaurio,
                int(wj),
                int(hj)
            ),
            "roi_rel": convertir_a_relativo(
                roi,
                int(wj),
                int(hj)
            )
        }

        if usar_puntaje_calibrado:
            puntaje = {
                "x": int(xp),
                "y": int(yp),
                "w": int(wp),
                "h": int(hp)
            }

            config["puntaje"] = puntaje
            config["puntaje_rel"] = convertir_a_relativo(
                puntaje,
                int(wj),
                int(hj)
            )

        self.configuracion.guardar(config)
        self._cerrar_capturador()

        print("\nCalibración guardada correctamente.")
        print("Archivo creado:", self.configuracion.archivo)

        print("\nResumen:")
        print("Pantalla:", config["pantalla"])
        print("Juego:", config["juego"])
        print("Dinosaurio:", config["dinosaurio"])
        print("ROI:", config["roi"])

        if "puntaje" in config:
            print("Puntaje:", config["puntaje"])
        else:
            print("Puntaje: zona automática")

    def _seleccionar_roi(self, titulo, frame):
        cv2.namedWindow(titulo, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(titulo, 1000, 600)

        roi = cv2.selectROI(
            titulo,
            frame,
            showCrosshair=True,
            fromCenter=False
        )

        cv2.destroyWindow(titulo)

        return tuple(map(int, roi))

    def _cerrar_capturador(self):
        if hasattr(self.capturador, "cerrar"):
            self.capturador.cerrar()