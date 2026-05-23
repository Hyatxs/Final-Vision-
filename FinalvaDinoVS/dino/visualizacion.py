import cv2


class VisualizadorDino:
    """Muestra el frame original, ROI, binaria, obstáculo y puntaje."""

    def mostrar(self, frame_juego, roi, binaria, obstaculo, config, accion, metodo, fps, puntaje=None, detector_puntaje=None):
        dibujo = frame_juego.copy()

        xr = config["roi"]["x"]
        yr = config["roi"]["y"]
        wr = config["roi"]["w"]
        hr = config["roi"]["h"]

        xd = config["dinosaurio"]["x"]
        yd = config["dinosaurio"]["y"]
        wd = config["dinosaurio"]["w"]
        hd = config["dinosaurio"]["h"]

        cv2.rectangle(dibujo, (xd, yd), (xd + wd, yd + hd), (255, 0, 0), 2)
        cv2.putText(dibujo, "DINO", (xd, max(yd - 5, 15)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

        cv2.rectangle(dibujo, (xr, yr), (xr + wr, yr + hr), (0, 255, 0), 2)
        cv2.putText(dibujo, "ROI", (xr, max(yr - 5, 15)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        if obstaculo is not None:
            ox = xr + obstaculo.x
            oy = yr + obstaculo.y
            ow = obstaculo.w
            oh = obstaculo.h

            cv2.rectangle(dibujo, (ox, oy), (ox + ow, oy + oh), (0, 0, 255), 2)

            porcentaje_alto = getattr(obstaculo, "porcentaje_alto", 0) * 100
            porcentaje_area = getattr(obstaculo, "porcentaje_area", 0) * 100
            texto = f"{obstaculo.tipo} H:{porcentaje_alto:.1f}% A:{porcentaje_area:.1f}%"

            cv2.putText(dibujo, texto, (ox, max(oy - 5, 15)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.putText(dibujo, f"Distancia X: {obstaculo.x}px", (10, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        if detector_puntaje is not None:
            caja_puntaje = detector_puntaje.obtener_caja_puntaje(frame_juego, config)
            if caja_puntaje is not None:
                xp, yp, wp, hp = caja_puntaje
                cv2.rectangle(dibujo, (xp, yp), (xp + wp, yp + hp), (0, 255, 255), 2)
                cv2.putText(dibujo, "PUNTAJE", (xp, max(yp - 5, 15)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        texto_puntaje = "---" if puntaje is None else str(puntaje)

        cv2.putText(dibujo, f"Metodo: {metodo}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(dibujo, f"Accion: {accion}", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(dibujo, f"FPS: {fps:.2f}", (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(dibujo, f"Puntaje: {texto_puntaje}", (10, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        binaria_color = cv2.cvtColor(binaria, cv2.COLOR_GRAY2BGR)

        cv2.imshow("Frame del juego", dibujo)
        cv2.imshow("ROI original", roi)
        cv2.imshow("ROI binaria", binaria_color)

    def leer_tecla(self):
        return cv2.waitKey(1) & 0xFF

    def cerrar(self):
        cv2.destroyAllWindows()
