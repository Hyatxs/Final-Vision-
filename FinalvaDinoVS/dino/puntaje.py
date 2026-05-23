import cv2
import numpy as np
import time


class DetectorPuntaje:
    """
    Lee el puntaje del dinosaurio con visión clásica.
    No usa YOLO, OCR entrenado, machine learning ni aprendizaje por refuerzo.

    Correcciones importantes:
    - Solo toma el último grupo de 5 dígitos del marcador.
    - Rechaza lecturas imposibles, por ejemplo 88899 en pocos segundos.
    - Mantiene el último puntaje válido si una lectura sale dudosa.
    """

    def __init__(self):
        self.plantillas = self._crear_plantillas()
        self.ultimo_puntaje = 0
        self.ultimo_texto = "00000"
        self.tiempo_inicio = time.time()
        self.tiempo_ultima_lectura = time.time()
        self.errores_ultima_lectura = []

    def detectar(self, frame_juego, config):
        roi, _ = self._recortar_zona_puntaje(frame_juego, config)

        if roi is None or roi.size == 0:
            return self.ultimo_puntaje

        binaria = self._preprocesar_puntaje(roi)
        cajas_digitos = self._segmentar_digitos(binaria)

        if len(cajas_digitos) < 5:
            return self.ultimo_puntaje

        # Si se seleccionó también HI o récord, tomar el último grupo.
        cajas_digitos = self._tomar_ultimo_grupo(cajas_digitos)

        # El puntaje actual debe estar formado por 5 dígitos.
        if len(cajas_digitos) > 5:
            cajas_digitos = cajas_digitos[-5:]

        if len(cajas_digitos) != 5:
            return self.ultimo_puntaje

        texto = ""
        errores = []

        for x, y, w, h in cajas_digitos:
            digito = binaria[y:y + h, x:x + w]
            numero, error = self._reconocer_digito(digito)
            texto += numero
            errores.append(error)

        if texto == "" or "?" in texto:
            return self.ultimo_puntaje

        try:
            puntaje_leido = int(texto)
        except ValueError:
            return self.ultimo_puntaje

        if self._puntaje_es_valido(puntaje_leido, errores):
            self.ultimo_puntaje = puntaje_leido
            self.ultimo_texto = texto
            self.tiempo_ultima_lectura = time.time()
            self.errores_ultima_lectura = errores

        return self.ultimo_puntaje

    def obtener_caja_puntaje(self, frame_juego, config):
        _, caja = self._recortar_zona_puntaje(frame_juego, config)
        return caja

    def _recortar_zona_puntaje(self, frame_juego, config):
        alto, ancho = frame_juego.shape[:2]

        if "puntaje" in config:
            x = int(config["puntaje"]["x"])
            y = int(config["puntaje"]["y"])
            w = int(config["puntaje"]["w"])
            h = int(config["puntaje"]["h"])
        else:
            # Respaldo si no se calibró puntaje.
            x = int(ancho * 0.72)
            y = int(alto * 0.08)
            w = int(ancho * 0.25)
            h = int(alto * 0.18)

        x = max(0, min(x, ancho - 1))
        y = max(0, min(y, alto - 1))
        w = max(1, min(w, ancho - x))
        h = max(1, min(h, alto - y))

        roi = frame_juego[y:y + h, x:x + w]
        return roi, (x, y, w, h)

    def _preprocesar_puntaje(self, roi):
        gris = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # El marcador puede estar gris sobre fondo blanco o gris claro sobre fondo oscuro.
        # Por eso se mide diferencia contra el fondo dominante.
        fondo = int(np.median(gris))
        diferencia = cv2.absdiff(gris, np.full_like(gris, fondo))

        _, binaria = cv2.threshold(
            diferencia,
            18,
            255,
            cv2.THRESH_BINARY
        )

        kernel = np.ones((2, 2), np.uint8)
        binaria = cv2.morphologyEx(binaria, cv2.MORPH_CLOSE, kernel, iterations=1)
        binaria = cv2.morphologyEx(binaria, cv2.MORPH_OPEN, kernel, iterations=1)

        return binaria

    def _segmentar_digitos(self, binaria):
        alto, ancho = binaria.shape

        num, etiquetas, stats, _ = cv2.connectedComponentsWithStats(
            (binaria > 0).astype(np.uint8),
            8
        )

        cajas = []

        for i in range(1, num):
            x, y, w, h, area = stats[i]

            # Filtros para quedarnos con dígitos del marcador.
            if area < 25:
                continue
            if h < alto * 0.25:
                continue
            if h > alto * 0.95:
                continue
            if w < 4:
                continue
            if w > ancho * 0.30:
                continue

            cajas.append((int(x), int(y), int(w), int(h)))

        cajas.sort(key=lambda c: c[0])
        return cajas

    def _tomar_ultimo_grupo(self, cajas):
        """
        Si la ROI contiene: HI 02058 00713,
        separa por espacios grandes y toma el último grupo: 00713.
        """

        if len(cajas) <= 5:
            return cajas

        anchos = [c[2] for c in cajas]
        ancho_promedio = max(1, sum(anchos) / len(anchos))

        grupos = []
        grupo = [cajas[0]]

        for i in range(1, len(cajas)):
            x_ant, y_ant, w_ant, h_ant = cajas[i - 1]
            x_act, y_act, w_act, h_act = cajas[i]

            espacio = x_act - (x_ant + w_ant)

            if espacio > ancho_promedio * 1.35:
                grupos.append(grupo)
                grupo = [cajas[i]]
            else:
                grupo.append(cajas[i])

        grupos.append(grupo)

        # Se prefiere el último grupo que tenga 5 dígitos.
        for grupo in reversed(grupos):
            if len(grupo) >= 5:
                return grupo[-5:]

        return cajas[-5:]

    def _reconocer_digito(self, imagen_digito):
        if imagen_digito is None or imagen_digito.size == 0:
            return "?", 1.0

        normalizado = cv2.resize(
            imagen_digito,
            (7, 10),
            interpolation=cv2.INTER_AREA
        )

        normalizado = (normalizado > 50).astype(np.uint8)

        mejor_digito = "?"
        mejor_error = 1.0

        for digito, plantilla in self.plantillas.items():
            error = np.mean(normalizado != plantilla)

            if error < mejor_error:
                mejor_error = error
                mejor_digito = digito

        # Si el error es alto, la lectura no es confiable.
        if mejor_error > 0.42:
            return "?", mejor_error

        return mejor_digito, mejor_error

    def _puntaje_es_valido(self, puntaje, errores):
        ahora = time.time()
        tiempo_jugado = ahora - self.tiempo_inicio
        tiempo_desde_ultima = ahora - self.tiempo_ultima_lectura

        # Rechaza lecturas que son demasiado grandes para el tiempo transcurrido.
        # Ejemplo: 88899 a los 72 s no es posible.
        maximo_posible = int(tiempo_jugado * 25 + 400)

        if puntaje > maximo_posible:
            return False

        # Rechaza lecturas de baja confianza.
        if len(errores) == 0:
            return False

        error_promedio = sum(errores) / len(errores)

        if error_promedio > 0.34:
            return False

        # No aceptar bajadas fuertes, porque el puntaje normalmente solo sube.
        if puntaje < self.ultimo_puntaje - 15:
            return False

        # No aceptar saltos enormes de un frame a otro.
        salto_maximo = int(90 + tiempo_desde_ultima * 60)

        if puntaje - self.ultimo_puntaje > salto_maximo:
            return False

        return True

    def _crear_plantillas(self):
        patrones = {
            "0": [
                ".####..",
                ".######",
                "###.###",
                "###..##",
                "###..##",
                "###..##",
                "###..##",
                ".##..##",
                ".#####.",
                ".####..",
            ],
            "1": [
                "..###..",
                ".####..",
                ".####..",
                "..###..",
                "..###..",
                "..###..",
                "..###..",
                "..###..",
                "#######",
                "#######",
            ],
            "2": [
                "#######",
                "#######",
                "##..###",
                "..#####",
                ".######",
                ".#####.",
                "#####..",
                "###....",
                "#######",
                "#######",
            ],
            "3": [
                ".######",
                ".######",
                "...###.",
                "..####.",
                ".######",
                "..#####",
                "###..##",
                "###..##",
                "#######",
                ".######",
            ],
            "4": [
                "###.###",
                "###.###",
                "###.###",
                "###.###",
                "#######",
                "#######",
                "....###",
                "....###",
                "....###",
                "....###",
            ],
            "5": [
                "#######",
                "######.",
                "######.",
                "#######",
                "#######",
                "....###",
                "###.###",
                "###.###",
                "#######",
                "#######",
            ],
            "6": [
                ".######",
                "#######",
                "###....",
                "###....",
                "#######",
                "#######",
                "###.###",
                "###.###",
                "#######",
                ".######",
            ],
            "7": [
                "#######",
                "#######",
                "....###",
                "...###.",
                "..###..",
                "..###..",
                ".###...",
                ".###...",
                "###....",
                "###....",
            ],
            "8": [
                "#####..",
                "#######",
                "###.###",
                "#######",
                "######.",
                "#######",
                "#..####",
                "#...###",
                "#######",
                "#######",
            ],
            "9": [
                ".######",
                "#######",
                "###.###",
                "###.###",
                "#######",
                "#######",
                "....###",
                "....###",
                "#######",
                ".######",
            ],
        }

        plantillas = {}

        for digito, filas in patrones.items():
            matriz = []
            for fila in filas:
                matriz.append([1 if caracter == "#" else 0 for caracter in fila])
            plantillas[digito] = np.array(matriz, dtype=np.uint8)

        return plantillas
