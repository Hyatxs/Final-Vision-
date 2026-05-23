import csv
import os
import time
from datetime import datetime


class GestorMetricas:
    """Mide FPS, tiempo, detecciones y errores registrados manualmente."""

    def __init__(self, carpeta="resultados_dino"):
        self.carpeta = carpeta
        self.reiniciar()

    def reiniciar(self):
        self.tiempo_inicio = time.time()
        self.frames = 0
        self.detecciones = 0
        self.falsos_positivos = 0
        self.falsos_negativos = 0

    def registrar_frame(self, obstaculo):
        self.frames += 1
        if obstaculo is not None:
            self.detecciones += 1

    def registrar_falso_positivo(self):
        self.falsos_positivos += 1

    def registrar_falso_negativo(self):
        self.falsos_negativos += 1

    def obtener_fps(self):
        tiempo_total = time.time() - self.tiempo_inicio
        if tiempo_total <= 0:
            return 0
        return self.frames / tiempo_total

    def obtener_tiempo_supervivencia(self):
        return time.time() - self.tiempo_inicio

    def guardar(self, metodo, estado_control, puntaje):
        os.makedirs(self.carpeta, exist_ok=True)
        archivo = os.path.join(self.carpeta, "resumen_pruebas.csv")
        existe = os.path.exists(archivo)

        datos = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "metodo": metodo,
            "fps_promedio": round(self.obtener_fps(), 2),
            "tiempo_supervivencia": round(self.obtener_tiempo_supervivencia(), 2),
            "puntaje": puntaje,
            "detecciones": self.detecciones,
            "saltos": estado_control["saltos"],
            "agachadas": estado_control["agachadas"],
            "falsos_positivos": self.falsos_positivos,
            "falsos_negativos": self.falsos_negativos
        }

        campos = list(datos.keys())

        with open(archivo, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=campos)
            if not existe:
                writer.writeheader()
            writer.writerow(datos)

        print("\nResultados guardados en:", archivo)
        return datos

    def mostrar_resumen(self):
        archivo = os.path.join(self.carpeta, "resumen_pruebas.csv")

        if not os.path.exists(archivo):
            print("Todavía no hay resultados guardados.")
            return

        print("\n=== RESUMEN DE PRUEBAS ===")

        with open(archivo, "r", encoding="utf-8") as f:
            lector = csv.DictReader(f)
            for fila in lector:
                print(
                    fila["fecha"],
                    "| Método:", fila["metodo"],
                    "| FPS:", fila["fps_promedio"],
                    "| Tiempo:", fila["tiempo_supervivencia"],
                    "| Puntaje:", fila["puntaje"],
                    "| FP:", fila["falsos_positivos"],
                    "| FN:", fila["falsos_negativos"]
                )
