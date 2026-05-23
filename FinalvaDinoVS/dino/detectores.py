from abc import ABC, abstractmethod
from dataclasses import dataclass
import cv2


@dataclass
class Obstaculo:
    x: int
    y: int
    w: int
    h: int
    tipo: str
    area: float = 0
    pixeles: int = 0
    porcentaje_area: float = 0
    porcentaje_alto: float = 0
    porcentaje_ancho: float = 0


class ClasificadorObstaculos:
    """
    Clasifica el objeto usando geometría dentro de la ROI.
    No usa machine learning.
    """

    def clasificar(self, x, y, w, h, alto_roi, ancho_roi):
        centro_y = y + h / 2
        parte_baja = y + h

        porcentaje_alto = h / max(alto_roi, 1)
        porcentaje_ancho = w / max(ancho_roi, 1)
        relacion = w / max(h, 1)

        # Ave alta: está muy arriba. No se debe saltar ni agachar.
        if parte_baja < alto_roi * 0.45:
            return "ave_alta"

        # Ave media: está en zona media, no toca el suelo.
        # Esta es la que debe provocar agacharse.
        if (
            y < alto_roi * 0.62 and
            parte_baja < alto_roi * 0.88 and
            porcentaje_alto < 0.45 and
            relacion >= 0.75
        ):
            return "ave_media"

        # Todo lo que está en zona baja normalmente es cactus.
        return "cactus"


class DetectorBase(ABC):
    """
    Base común para DetectorContornos y DetectorPixeles.

    La parte importante es que ambos métodos usan los mismos filtros
    y la misma clasificación para no arruinar la detección de aves.
    """

    def __init__(self):
        self.clasificador = ClasificadorObstaculos()

        # Filtros generales
        self.min_area = 18
        self.min_pixeles = 35

        # Filtros por porcentaje de ROI
        self.min_porcentaje_area = 0.0025
        self.min_porcentaje_alto = 0.10
        self.min_porcentaje_ancho = 0.010

        # Montículos del suelo
        self.zona_suelo = 0.62
        self.max_alto_monticulo = 0.16

        # Nubes o ruido superior
        self.zona_superior_nubes = 0.42

    @abstractmethod
    def detectar(self, binaria):
        pass

    def _crear_obstaculo_si_valido(
        self,
        x,
        y,
        w,
        h,
        area,
        pixeles,
        alto_roi,
        ancho_roi
    ):
        area_roi = alto_roi * ancho_roi

        porcentaje_area = area / max(area_roi, 1)
        porcentaje_alto = h / max(alto_roi, 1)
        porcentaje_ancho = w / max(ancho_roi, 1)
        relacion = w / max(h, 1)
        parte_baja = y + h

        # ===============================
        # 1. Ignorar línea del suelo
        # ===============================

        es_linea_suelo = (
            y > alto_roi * 0.68 and
            h <= 6 and
            w > ancho_roi * 0.08 and
            relacion > 5
        )

        if es_linea_suelo:
            return None

        # ===============================
        # 2. Ignorar montículos del suelo
        # ===============================

        es_monticulo = (
            y > alto_roi * self.zona_suelo and
            porcentaje_alto < self.max_alto_monticulo and
            porcentaje_area < 0.020
        )

        if es_monticulo:
            return None

        # ===============================
        # 3. Ignorar ruido muy pequeño
        # ===============================

        if area < self.min_area and pixeles < self.min_pixeles:
            return None

        if porcentaje_ancho < self.min_porcentaje_ancho:
            return None

        if porcentaje_area < self.min_porcentaje_area and porcentaje_alto < self.min_porcentaje_alto:
            return None

        # ===============================
        # 4. Ignorar nubes superiores
        # ===============================
        # Ojo: no se elimina todo lo que está arriba, porque un ave puede venir alta.
        # Solo se elimina cuando está demasiado arriba, es ancho y no baja al centro.

        es_nube_superior = (
            parte_baja < alto_roi * self.zona_superior_nubes and
            porcentaje_alto < 0.28 and
            porcentaje_ancho > 0.08 and
            relacion > 1.25
        )

        if es_nube_superior:
            return None

        # ===============================
        # 5. Clasificar obstáculo
        # ===============================

        tipo = self.clasificador.clasificar(
            x=x,
            y=y,
            w=w,
            h=h,
            alto_roi=alto_roi,
            ancho_roi=ancho_roi
        )

        return Obstaculo(
            x=int(x),
            y=int(y),
            w=int(w),
            h=int(h),
            tipo=tipo,
            area=float(area),
            pixeles=int(pixeles),
            porcentaje_area=float(porcentaje_area),
            porcentaje_alto=float(porcentaje_alto),
            porcentaje_ancho=float(porcentaje_ancho)
        )

    def _ordenar_candidatos(self, candidatos):
        """
        Se toma el obstáculo más cercano al dinosaurio.
        Como la ROI está delante del dinosaurio, normalmente es el menor x.
        """

        if not candidatos:
            return None

        candidatos.sort(key=lambda obj: obj.x)

        return candidatos[0]


class DetectorContornos(DetectorBase):
    """
    Método 1: detección por contornos.

    Usa la forma del objeto y su caja delimitadora.
    """

    def detectar(self, binaria):
        alto_roi, ancho_roi = binaria.shape

        contornos, _ = cv2.findContours(
            binaria,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        candidatos = []

        for c in contornos:
            x, y, w, h = cv2.boundingRect(c)
            area = cv2.contourArea(c)

            # Pixeles reales dentro del rectángulo del objeto.
            mascara = binaria[y:y + h, x:x + w]
            pixeles = cv2.countNonZero(mascara)

            obstaculo = self._crear_obstaculo_si_valido(
                x=x,
                y=y,
                w=w,
                h=h,
                area=area,
                pixeles=pixeles,
                alto_roi=alto_roi,
                ancho_roi=ancho_roi
            )

            if obstaculo is not None:
                candidatos.append(obstaculo)

        return self._ordenar_candidatos(candidatos)


class DetectorPixeles(DetectorBase):
    """
    Método 2: detección por pixeles.

    Importante:
    No junta todos los pixeles de la ROI en un solo rectángulo.
    Primero separa objetos y luego cuenta pixeles por cada objeto.
    Así no se arruina la clasificación de aves.
    """

    def __init__(self):
        super().__init__()

        # El método de pixeles puede ser más sensible.
        # Por eso se pone un poco más alto el mínimo de pixeles.
        self.min_pixeles = 45

    def detectar(self, binaria):
        alto_roi, ancho_roi = binaria.shape

        contornos, _ = cv2.findContours(
            binaria,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        candidatos = []

        for c in contornos:
            x, y, w, h = cv2.boundingRect(c)

            mascara = binaria[y:y + h, x:x + w]
            pixeles = cv2.countNonZero(mascara)

            if pixeles < self.min_pixeles:
                continue

            # En el método de pixeles el área principal será la cantidad de pixeles.
            area = pixeles

            obstaculo = self._crear_obstaculo_si_valido(
                x=x,
                y=y,
                w=w,
                h=h,
                area=area,
                pixeles=pixeles,
                alto_roi=alto_roi,
                ancho_roi=ancho_roi
            )

            if obstaculo is not None:
                candidatos.append(obstaculo)

        return self._ordenar_candidatos(candidatos)