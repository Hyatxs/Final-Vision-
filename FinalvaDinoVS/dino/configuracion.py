import json
import os


class ConfiguracionDino:
    """Guarda y carga la calibración del juego."""

    def __init__(self, archivo="config_dino.json"):
        self.archivo = archivo

    def existe(self):
        return os.path.exists(self.archivo)

    def guardar(self, datos):
        with open(self.archivo, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4)

    def cargar(self):
        if not self.existe():
            return None

        with open(self.archivo, "r", encoding="utf-8") as f:
            return json.load(f)
