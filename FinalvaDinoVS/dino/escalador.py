class EscaladorResolucion:
    """
    Escala la calibración cuando cambia la resolución de pantalla.

    Guarda una calibración base y recalcula:
    - zona del juego
    - dinosaurio
    - ROI
    - puntaje
    """

    def __init__(self, config):
        self.config = config

    def escalar(self, ancho_actual, alto_actual):
        if self.config is None:
            return None

        config = dict(self.config)

        if "pantalla" not in config:
            return config

        ancho_base = config["pantalla"]["width"]
        alto_base = config["pantalla"]["height"]

        escala_x = ancho_actual / max(ancho_base, 1)
        escala_y = alto_actual / max(alto_base, 1)

        config["juego"] = self._escalar_juego(
            config["juego"],
            escala_x,
            escala_y
        )

        ancho_juego = config["juego"]["width"]
        alto_juego = config["juego"]["height"]

        if "dinosaurio_rel" in config:
            config["dinosaurio"] = self._desde_relativo(
                config["dinosaurio_rel"],
                ancho_juego,
                alto_juego
            )

        if "roi_rel" in config:
            config["roi"] = self._desde_relativo(
                config["roi_rel"],
                ancho_juego,
                alto_juego
            )

        if "puntaje_rel" in config:
            config["puntaje"] = self._desde_relativo(
                config["puntaje_rel"],
                ancho_juego,
                alto_juego
            )

        return config

    def _escalar_juego(self, region, escala_x, escala_y):
        return {
            "left": int(region["left"] * escala_x),
            "top": int(region["top"] * escala_y),
            "width": int(region["width"] * escala_x),
            "height": int(region["height"] * escala_y)
        }

    def _desde_relativo(self, region_rel, ancho, alto):
        return {
            "x": int(region_rel["x"] * ancho),
            "y": int(region_rel["y"] * alto),
            "w": int(region_rel["w"] * ancho),
            "h": int(region_rel["h"] * alto)
        }


def convertir_a_relativo(region, ancho_base, alto_base):
    return {
        "x": region["x"] / max(ancho_base, 1),
        "y": region["y"] / max(alto_base, 1),
        "w": region["w"] / max(ancho_base, 1),
        "h": region["h"] / max(alto_base, 1)
    }