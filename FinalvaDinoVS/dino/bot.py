import time

from .captura import CapturadorPantalla
from .configuracion import ConfiguracionDino
from .procesamiento import PreprocesadorDino
from .detectores import DetectorPixeles, DetectorContornos
from .control import ControladorTeclado, ReglaDecision
from .metricas import GestorMetricas
from .visualizacion import VisualizadorDino
from .puntaje import DetectorPuntaje
from .escalador import EscaladorResolucion


class DinoBot:
    """
    Clase principal que une:
    - captura de pantalla
    - preprocesamiento
    - detección de obstáculos
    - detección automática del puntaje
    - escalado por resolución
    - regla de decisión
    - control del teclado
    - métricas
    - visualización
    """

    def __init__(
        self,
        metodo="contornos",
        sin_control=False,
        archivo_config="config_dino.json"
    ):
        self.metodo = metodo
        self.sin_control = sin_control

        self.configuracion = ConfiguracionDino(archivo_config)
        self.config = self.configuracion.cargar()

        self.capturador = CapturadorPantalla()

        self.config = self._adaptar_config_a_resolucion_actual()

        self.preprocesador = PreprocesadorDino()
        self.detector = self._crear_detector(metodo)

        self.regla = ReglaDecision()
        self.controlador = ControladorTeclado()
        self.metricas = GestorMetricas()
        self.visualizador = VisualizadorDino()

        self.detector_puntaje = DetectorPuntaje()
        self.puntaje_actual = 0

        self.pausado = False

    def _adaptar_config_a_resolucion_actual(self):
        if self.config is None:
            return None

        frame = self.capturador.capturar_pantalla_completa()

        if frame is None:
            return self.config

        alto_actual, ancho_actual = frame.shape[:2]

        escalador = EscaladorResolucion(self.config)

        config_escalada = escalador.escalar(
            ancho_actual=ancho_actual,
            alto_actual=alto_actual
        )

        print("\nResolución actual:", ancho_actual, "x", alto_actual)

        if "pantalla" in self.config:
            print(
                "Resolución calibrada:",
                self.config["pantalla"]["width"],
                "x",
                self.config["pantalla"]["height"]
            )
        else:
            print("La configuración no tiene datos de resolución base.")

        return config_escalada

    def _crear_detector(self, metodo):
        if metodo == "pixeles":
            return DetectorPixeles()

        return DetectorContornos()

    def ejecutar(self):
        if self.config is None:
            print("No existe archivo de calibración.")
            print("Ejecuta primero: python main.py --calibrar")
            return

        region_juego = self.config["juego"]

        xr = self.config["roi"]["x"]
        yr = self.config["roi"]["y"]
        wr = self.config["roi"]["w"]
        hr = self.config["roi"]["h"]

        print("\n=== BOT DEL DINOSAURIO INICIADO ===")
        print("Método:", self.metodo)

        if self.sin_control:
            print("Modo: sin control de teclado")
        else:
            print("Modo: control automático activado")

        print("q o ESC = salir")
        print("f = registrar falso positivo")
        print("n = registrar falso negativo")
        print("p = pausar/reanudar")
        print()

        try:
            while True:
                inicio_frame = time.time()

                frame_juego = self.capturador.capturar_region(region_juego)

                if frame_juego is None:
                    print("No se pudo capturar el frame del juego.")
                    break

                puntaje_detectado = self.detector_puntaje.detectar(
                    frame_juego,
                    self.config
                )

                if puntaje_detectado is not None:
                    self.puntaje_actual = puntaje_detectado

                roi = frame_juego[yr:yr + hr, xr:xr + wr]

                if roi is None or roi.size == 0:
                    print("La ROI está vacía. Revisa la calibración.")
                    break

                binaria = self.preprocesador.preprocesar(roi)
                obstaculo = self.detector.detectar(binaria)

                self.metricas.registrar_frame(obstaculo)

                accion = self.regla.decidir(
                    obstaculo,
                    ancho_roi=wr,
                    alto_roi=hr
                )

                if not self.sin_control and not self.pausado:
                    self.controlador.ejecutar(accion)

                fps = self.metricas.obtener_fps()

                self._mostrar_visualizacion(
                    frame_juego=frame_juego,
                    roi=roi,
                    binaria=binaria,
                    obstaculo=obstaculo,
                    accion=accion,
                    fps=fps
                )

                tecla = self.visualizador.leer_tecla()

                if self._procesar_tecla(tecla):
                    break

                duracion_frame = time.time() - inicio_frame

                if duracion_frame < 0.005:
                    time.sleep(0.005)

        except KeyboardInterrupt:
            print("\nPrograma detenido con CTRL + C.")

        finally:
            self._finalizar()

    def _mostrar_visualizacion(self, frame_juego, roi, binaria, obstaculo, accion, fps):
        if hasattr(self.regla, "obtener_estado"):
            estado_decision = self.regla.obtener_estado()
        else:
            estado_decision = None

        if hasattr(self.preprocesador, "obtener_estado"):
            estado_color = self.preprocesador.obtener_estado()
        else:
            estado_color = None

        try:
            self.visualizador.mostrar(
                frame_juego=frame_juego,
                roi=roi,
                binaria=binaria,
                obstaculo=obstaculo,
                config=self.config,
                accion=accion,
                metodo=self.metodo,
                fps=fps,
                estado_decision=estado_decision,
                estado_color=estado_color,
                puntaje=self.puntaje_actual,
                detector_puntaje=self.detector_puntaje
            )
            return
        except TypeError:
            pass

        try:
            self.visualizador.mostrar(
                frame_juego=frame_juego,
                roi=roi,
                binaria=binaria,
                obstaculo=obstaculo,
                config=self.config,
                accion=accion,
                metodo=self.metodo,
                fps=fps,
                puntaje=self.puntaje_actual,
                detector_puntaje=self.detector_puntaje
            )
            return
        except TypeError:
            pass

        try:
            self.visualizador.mostrar(
                frame_juego=frame_juego,
                roi=roi,
                binaria=binaria,
                obstaculo=obstaculo,
                config=self.config,
                accion=accion,
                metodo=self.metodo,
                fps=fps,
                estado_decision=estado_decision,
                estado_color=estado_color
            )
            return
        except TypeError:
            pass

        self.visualizador.mostrar(
            frame_juego=frame_juego,
            roi=roi,
            binaria=binaria,
            obstaculo=obstaculo,
            config=self.config,
            accion=accion,
            metodo=self.metodo,
            fps=fps
        )

    def _procesar_tecla(self, tecla):
        if tecla == ord("q") or tecla == 27:
            return True

        if tecla == ord("f"):
            self.metricas.registrar_falso_positivo()
            print("Falso positivo registrado.")

        elif tecla == ord("n"):
            self.metricas.registrar_falso_negativo()
            print("Falso negativo registrado.")

        elif tecla == ord("p"):
            self.pausado = not self.pausado
            print("Pausado." if self.pausado else "Reanudado.")

            if self.pausado and hasattr(self.controlador, "liberar_todo"):
                self.controlador.liberar_todo()

        return False

    def _finalizar(self):
        if hasattr(self.controlador, "liberar_todo"):
            self.controlador.liberar_todo()

        if hasattr(self.visualizador, "cerrar"):
            self.visualizador.cerrar()

        if hasattr(self.capturador, "cerrar"):
            self.capturador.cerrar()

        tiempo = self.metricas.obtener_tiempo_supervivencia()
        fps = self.metricas.obtener_fps()
        estado_control = self.controlador.obtener_estado()

        print("\n=== PRUEBA TERMINADA ===")
        print("Tiempo de supervivencia:", round(tiempo, 2), "s")
        print("FPS promedio:", round(fps, 2))
        print("Detecciones:", self.metricas.detecciones)
        print("Saltos:", estado_control["saltos"])
        print("Agachadas:", estado_control["agachadas"])
        print("Falsos positivos:", self.metricas.falsos_positivos)
        print("Falsos negativos:", self.metricas.falsos_negativos)

        puntaje = self.puntaje_actual

        if puntaje is None:
            puntaje = "no_detectado"

        print("Puntaje detectado:", puntaje)

        self.metricas.guardar(
            metodo=self.metodo,
            estado_control=estado_control,
            puntaje=puntaje
        )