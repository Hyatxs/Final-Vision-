import csv
import os
from statistics import mean

ARCHIVO = os.path.join("resultados_dino", "resumen_pruebas.csv")

CAMPOS_NUMERICOS = [
    "fps_promedio",
    "tiempo_supervivencia",
    "puntaje",
    "detecciones",
    "saltos",
    "agachadas",
    "falsos_positivos",
    "falsos_negativos",
]


def convertir_numero(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def cargar_datos():
    if not os.path.exists(ARCHIVO):
        print("No existe el archivo:", ARCHIVO)
        print("Primero ejecuta pruebas con ambos métodos.")
        return []

    filas = []
    with open(ARCHIVO, "r", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        for fila in lector:
            for campo in CAMPOS_NUMERICOS:
                fila[campo] = convertir_numero(fila.get(campo))
            filas.append(fila)
    return filas


def promedio(filas, campo):
    valores = [f[campo] for f in filas if f.get(campo) is not None]
    if not valores:
        return 0
    return mean(valores)


def maximo(filas, campo):
    valores = [f[campo] for f in filas if f.get(campo) is not None]
    if not valores:
        return 0
    return max(valores)


def minimo(filas, campo):
    valores = [f[campo] for f in filas if f.get(campo) is not None]
    if not valores:
        return 0
    return min(valores)


def imprimir_tabla(resumen):
    encabezado = (
        f"{'Método':<12} {'Pruebas':>7} {'FPS prom':>9} {'Tiempo prom':>12} "
        f"{'Puntaje prom':>13} {'Puntaje máx':>12} {'Detecc prom':>12} "
        f"{'Saltos prom':>12} {'Agach prom':>11} {'FP':>6} {'FN':>6}"
    )
    print("\n=== COMPARACIÓN DE MÉTODOS ===")
    print(encabezado)
    print("-" * len(encabezado))

    for metodo, datos in resumen.items():
        print(
            f"{metodo:<12} "
            f"{datos['pruebas']:>7} "
            f"{datos['fps_promedio']:>9.2f} "
            f"{datos['tiempo_promedio']:>12.2f} "
            f"{datos['puntaje_promedio']:>13.2f} "
            f"{datos['puntaje_maximo']:>12.0f} "
            f"{datos['detecciones_promedio']:>12.2f} "
            f"{datos['saltos_promedio']:>12.2f} "
            f"{datos['agachadas_promedio']:>11.2f} "
            f"{datos['falsos_positivos']:>6.0f} "
            f"{datos['falsos_negativos']:>6.0f}"
        )


def interpretar(resumen):
    print("\n=== INTERPRETACIÓN AUTOMÁTICA ===")

    if "contornos" not in resumen or "pixeles" not in resumen:
        print("Todavía no hay pruebas de ambos métodos en el CSV.")
        print("Ejecuta varias pruebas con:")
        print("  python main.py --metodo contornos")
        print("  python main.py --metodo pixeles")
        return

    c = resumen["contornos"]
    p = resumen["pixeles"]

    mejor_puntaje = "contornos" if c["puntaje_promedio"] > p["puntaje_promedio"] else "pixeles"
    mejor_tiempo = "contornos" if c["tiempo_promedio"] > p["tiempo_promedio"] else "pixeles"
    mejor_fps = "contornos" if c["fps_promedio"] > p["fps_promedio"] else "pixeles"

    print(f"Mejor puntaje promedio: {mejor_puntaje}")
    print(f"Mayor tiempo de supervivencia promedio: {mejor_tiempo}")
    print(f"Mayor FPS promedio: {mejor_fps}")

    if p["detecciones_promedio"] > c["detecciones_promedio"]:
        print("Pixeles detectó más actividad en la ROI. Puede ser más sensible, pero también puede generar más falsos positivos.")
    else:
        print("Contornos detectó más objetos completos. Puede ser mejor cuando la silueta del cactus/ave está bien separada del suelo.")

    if p["agachadas_promedio"] > c["agachadas_promedio"]:
        print("Pixeles produjo más agachadas. Revisa que no esté confundiendo nubes o ruido con aves.")
    elif c["agachadas_promedio"] > p["agachadas_promedio"]:
        print("Contornos produjo más agachadas. Revisa la clasificación geométrica de aves.")


def main():
    filas = cargar_datos()
    if not filas:
        return

    por_metodo = {}
    for fila in filas:
        metodo = fila.get("metodo", "sin_metodo")
        por_metodo.setdefault(metodo, []).append(fila)

    resumen = {}
    for metodo, datos in por_metodo.items():
        resumen[metodo] = {
            "pruebas": len(datos),
            "fps_promedio": promedio(datos, "fps_promedio"),
            "tiempo_promedio": promedio(datos, "tiempo_supervivencia"),
            "puntaje_promedio": promedio(datos, "puntaje"),
            "puntaje_maximo": maximo(datos, "puntaje"),
            "tiempo_maximo": maximo(datos, "tiempo_supervivencia"),
            "detecciones_promedio": promedio(datos, "detecciones"),
            "saltos_promedio": promedio(datos, "saltos"),
            "agachadas_promedio": promedio(datos, "agachadas"),
            "falsos_positivos": sum(f.get("falsos_positivos") or 0 for f in datos),
            "falsos_negativos": sum(f.get("falsos_negativos") or 0 for f in datos),
        }

    imprimir_tabla(resumen)
    interpretar(resumen)


if __name__ == "__main__":
    main()