import argparse
from dino.calibracion import CalibradorDino
from dino.bot import DinoBot
from dino.metricas import GestorMetricas


def main():
    parser = argparse.ArgumentParser(
        description="Bot del dinosaurio de Google usando visión por computadora."
    )

    parser.add_argument(
        "--calibrar",
        action="store_true",
        help="Abrir pantalla de calibración"
    )

    parser.add_argument(
        "--metodo",
        choices=["pixeles", "contornos"],
        default="contornos",
        help="Método de detección"
    )

    parser.add_argument(
        "--sin-control",
        action="store_true",
        help="Detectar sin presionar teclas"
    )

    parser.add_argument(
        "--resumen",
        action="store_true",
        help="Mostrar resultados guardados"
    )

    args = parser.parse_args()

    if args.calibrar:
        calibrador = CalibradorDino()
        calibrador.calibrar()

    elif args.resumen:
        metricas = GestorMetricas()
        metricas.mostrar_resumen()

    else:
        bot = DinoBot(
            metodo=args.metodo,
            sin_control=args.sin_control
        )
        bot.ejecutar()


if __name__ == "__main__":
    main()
