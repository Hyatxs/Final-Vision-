import cv2
import numpy as np


class PreprocesadorDino:
    """
    Convierte la ROI en una imagen binaria limpia.

    Correcciones:
    - Detecta modo día/noche con histéresis.
    - Evita alocarse durante el cambio de color.
    - Filtra nubes, montículos y líneas del suelo.
    """

    def __init__(self):
        self.kernel = np.ones((2, 2), np.uint8)

        # Estado del modo de color
        self.modo_noche = False
        self.modo_anterior = False

        # Histéresis:
        # No se cambia de modo con una sola lectura cerca de 127.
        self.umbral_entrar_noche = 105
        self.umbral_salir_noche = 155

        # Cuando cambia de día a noche o de noche a día,
        # se ignoran algunos frames para evitar falsas detecciones.
        self.frames_estabilizacion = 0
        self.frames_estabilizacion_max = 10

        self.media_gris = 0
        self.estado_color = "dia"

    def preprocesar(self, frame):
        gris_original = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        self.media_gris = float(np.mean(gris_original))

        self._actualizar_modo_color(self.media_gris)

        # Si acaba de cambiar el color, se devuelve una imagen vacía.
        # Así el bot no salta ni se agacha por nubes o ruido del cambio.
        if self.frames_estabilizacion > 0:
            self.frames_estabilizacion -= 1
            self.estado_color = "estabilizando"
            return np.zeros_like(gris_original)

        gris = gris_original.copy()

        # En modo noche se invierte para mantener la misma lógica:
        # fondo claro y obstáculos oscuros antes de binarizar.
        if self.modo_noche:
            gris = cv2.bitwise_not(gris)
            self.estado_color = "noche"
        else:
            self.estado_color = "dia"

        # Umbral adaptativo por Otsu.
        # Funciona mejor que un umbral fijo cuando cambia el brillo.
        _, binaria = cv2.threshold(
            gris,
            0,
            255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

        # Limpieza suave
        binaria = cv2.morphologyEx(
            binaria,
            cv2.MORPH_OPEN,
            self.kernel,
            iterations=1
        )

        limpia = self._eliminar_ruido_suelo_y_nubes(binaria)

        return limpia

    def _actualizar_modo_color(self, media):
        """
        Detecta si el juego está en modo día o noche usando histéresis.
        Esto evita cambios falsos cuando el brillo está cerca del límite.
        """

        self.modo_anterior = self.modo_noche

        if not self.modo_noche and media < self.umbral_entrar_noche:
            self.modo_noche = True

        elif self.modo_noche and media > self.umbral_salir_noche:
            self.modo_noche = False

        if self.modo_anterior != self.modo_noche:
            self.frames_estabilizacion = self.frames_estabilizacion_max

    def _eliminar_ruido_suelo_y_nubes(self, binaria):
        contornos, _ = cv2.findContours(
            binaria,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        limpia = np.zeros_like(binaria)
        alto_img, ancho_img = binaria.shape

        for c in contornos:
            x, y, w, h = cv2.boundingRect(c)
            area = cv2.contourArea(c)

            if area < 25:
                continue

            if h < 5 or w < 3:
                continue

            porcentaje_alto = h / max(alto_img, 1)
            porcentaje_ancho = w / max(ancho_img, 1)
            relacion = w / max(h, 1)
            parte_baja = y + h

            # ===============================
            # 1. Eliminar línea del suelo
            # ===============================

            es_linea_suelo = (
                y > alto_img * 0.68 and
                h <= 6 and
                w > ancho_img * 0.08 and
                relacion > 5
            )

            if es_linea_suelo:
                continue

            # ===============================
            # 2. Eliminar montículos del piso
            # ===============================

            es_monticulo = (
                y > alto_img * 0.58 and
                porcentaje_alto < 0.16
            )

            if es_monticulo:
                continue

            # ===============================
            # 3. Eliminar nubes
            # ===============================
            # Las nubes suelen estar arriba, ser anchas y no bajar mucho.
            # Un ave peligrosa normalmente aparece más cerca del centro/bajo
            # de la ROI, no completamente arriba.

            esta_muy_arriba = parte_baja < alto_img * 0.42

            es_nube_por_forma = (
                y < alto_img * 0.48 and
                porcentaje_alto < 0.24 and
                porcentaje_ancho > 0.07 and
                relacion > 1.5
            )

            es_nube_superior = (
                esta_muy_arriba and
                porcentaje_alto < 0.30 and
                relacion > 1.2
            )

            if es_nube_por_forma or es_nube_superior:
                continue

            # ===============================
            # 4. Ignorar cosas demasiado pequeñas
            # ===============================

            area_roi = alto_img * ancho_img
            porcentaje_area = area / max(area_roi, 1)

            es_ruido_pequeno = (
                porcentaje_area < 0.003 and
                porcentaje_alto < 0.16
            )

            if es_ruido_pequeno:
                continue

            cv2.drawContours(
                limpia,
                [c],
                -1,
                255,
                -1
            )

        return limpia

    def obtener_estado(self):
        """
        Regresa información para mostrar en pantalla o depurar.
        """

        return {
            "modo": self.estado_color,
            "media_gris": round(self.media_gris, 2),
            "frames_estabilizacion": self.frames_estabilizacion
        }