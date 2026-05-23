import time
import copy
import pyautogui


class EstimadorVelocidadJuego:
    """Estima la velocidad del juego midiendo cuánto se mueve el obstáculo."""

    def __init__(self, velocidad_inicial=360.0):
        self.velocidad = float(velocidad_inicial)
        self.ultimo_x = None
        self.ultimo_tiempo = None
        self.ultimo_tipo = None
        self.alpha = 0.25

    def actualizar(self, obstaculo):
        ahora = time.time()

        if obstaculo is None:
            return self.velocidad

        x_actual = float(obstaculo.x)

        if self.ultimo_x is not None and self.ultimo_tiempo is not None:
            dt = ahora - self.ultimo_tiempo
            dx = self.ultimo_x - x_actual

            # Si dx es positivo, el obstáculo se movió hacia la izquierda.
            # Si dx es negativo o muy grande, probablemente apareció otro obstáculo.
            if 0 < dt < 0.20 and 0 < dx < 120:
                velocidad_medida = dx / dt

                if 80 <= velocidad_medida <= 1400:
                    self.velocidad = (
                        (1.0 - self.alpha) * self.velocidad +
                        self.alpha * velocidad_medida
                    )

        self.ultimo_x = x_actual
        self.ultimo_tiempo = ahora
        self.ultimo_tipo = obstaculo.tipo

        return self.velocidad

    def obtener_velocidad(self):
        return self.velocidad


class ReglaDecision:
    """
    Decide si se debe saltar, agacharse o no hacer nada.

    Mantiene la lógica de tu versión anterior:
    - estima velocidad del juego
    - usa zona de acción dinámica
    - conserva el último obstáculo unos milisegundos
    - ignora ruido por área
    """

    def __init__(self):
        self.estimador_velocidad = EstimadorVelocidadJuego()
        self.ultimo_obstaculo_valido = None
        self.tiempo_ultimo_obstaculo = 0

        # Ayuda cuando cambia de color y se pierde la detección un momento.
        self.persistencia_obstaculo = 0.14

        self.ultima_zona_accion = 0
        self.ultima_distancia = None

    def decidir(self, obstaculo, ancho_roi, alto_roi):
        ahora = time.time()
        velocidad = self.estimador_velocidad.actualizar(obstaculo)

        obstaculo = self._obtener_obstaculo_estable(
            obstaculo,
            ahora,
            velocidad
        )

        if obstaculo is None:
            self.ultima_distancia = None
            return "nada"

        # Si el ave va alta, no se hace nada.
        if obstaculo.tipo == "ave_alta":
            self.ultima_distancia = obstaculo.x
            return "nada"

        # Ignora montículos, nubes pequeñas o ruido.
        if self._es_ruido_por_area(obstaculo):
            self.ultima_distancia = obstaculo.x
            return "nada"

        zona_accion = self._calcular_zona_accion(
            obstaculo=obstaculo,
            ancho_roi=ancho_roi,
            velocidad=velocidad
        )

        self.ultima_zona_accion = zona_accion
        self.ultima_distancia = obstaculo.x

        # Si todavía está lejos, espera.
        if obstaculo.x > zona_accion:
            return "nada"

        if obstaculo.tipo == "ave_media":
            return "agacharse"

        return "saltar"

    def obtener_estado(self):
        return {
            "velocidad_px_s": round(self.estimador_velocidad.obtener_velocidad(), 1),
            "zona_accion_px": round(self.ultima_zona_accion, 1),
            "distancia_px": self.ultima_distancia
        }

    def _obtener_obstaculo_estable(self, obstaculo, ahora, velocidad):
        if obstaculo is not None:
            if obstaculo.tipo != "ave_alta":
                self.ultimo_obstaculo_valido = copy.copy(obstaculo)
                self.tiempo_ultimo_obstaculo = ahora

            return obstaculo

        # Si se pierde la detección durante el cambio de color,
        # se mantiene un poco el último obstáculo válido.
        if self.ultimo_obstaculo_valido is None:
            return None

        dt = ahora - self.tiempo_ultimo_obstaculo

        if dt > self.persistencia_obstaculo:
            return None

        proyectado = copy.copy(self.ultimo_obstaculo_valido)
        proyectado.x = max(0, int(proyectado.x - velocidad * dt))

        return proyectado

    def _es_ruido_por_area(self, obstaculo):
        """
        Regla para ignorar objetos muy pequeños.
        Sirve para montículos del piso y algunas nubes.
        """

        porcentaje_area = getattr(obstaculo, "porcentaje_area", 0)
        porcentaje_alto = getattr(obstaculo, "porcentaje_alto", 0)

        return (
            porcentaje_area < 0.0035 and
            porcentaje_alto < 0.16
        )

    def _calcular_zona_accion(self, obstaculo, ancho_roi, velocidad):
        """
        Calcula desde qué distancia debe reaccionar.
        Cuando el juego va más rápido, la zona de acción aumenta.
        """

        if obstaculo.tipo == "ave_media":
            tiempo_reaccion = 0.36
            margen = 34
        else:
            tiempo_reaccion = 0.42
            margen = 38

        zona = velocidad * tiempo_reaccion + margen

        zona_minima = ancho_roi * 0.36
        zona_maxima = ancho_roi * 0.90

        return max(zona_minima, min(zona, zona_maxima))


class ControladorTeclado:
    """
    Controla el juego usando el teclado.

    Se mantiene parecido a tu versión anterior, pero con una agachada
    un poco más larga para que no se levante antes de que pase el ave.
    """

    def __init__(self):
        pyautogui.PAUSE = 0.0
        pyautogui.FAILSAFE = True

        self.ultimo_salto = 0
        self.ultima_agachada = 0

        self.saltos = 0
        self.agachadas = 0

    def ejecutar(self, accion):
        ahora = time.time()

        if accion == "saltar":
            self._saltar(ahora)

        elif accion == "agacharse":
            self._agacharse(ahora)

    def _saltar(self, ahora):
        cooldown_salto = 0.12

        if ahora - self.ultimo_salto > cooldown_salto:
            pyautogui.press("space")
            self.ultimo_salto = ahora
            self.saltos += 1

    def _agacharse(self, ahora):
        cooldown_agacharse = 0.26

        if ahora - self.ultima_agachada > cooldown_agacharse:
            pyautogui.keyDown("down")

            # Antes estaba en 0.20.
            # Se sube un poco para que no se levante antes de que pase el ave.
            time.sleep(0.30)

            pyautogui.keyUp("down")

            self.ultima_agachada = ahora
            self.agachadas += 1

    def liberar_todo(self):
        """
        Seguridad para que al cerrar el programa no quede presionada la tecla DOWN.
        """

        pyautogui.keyUp("down")

    def obtener_estado(self):
        return {
            "saltos": self.saltos,
            "agachadas": self.agachadas
        }