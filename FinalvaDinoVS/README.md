# Dino CV Bot dividido en clases

Este proyecto controla el juego del dinosaurio de Google usando visión por computadora. No usa machine learning ni aprendizaje por refuerzo.

## Estructura

```text
dino_cv_clases/
├─ main.py
├─ requirements.txt
├─ README.md
└─ dino/
   ├─ __init__.py
   ├─ bot.py
   ├─ calibracion.py
   ├─ captura.py
   ├─ configuracion.py
   ├─ control.py
   ├─ detectores.py
   ├─ metricas.py
   ├─ procesamiento.py
   └─ visualizacion.py
```

## Instalación

```bash
pip install -r requirements.txt
```

## Calibrar

Abre el juego del dinosaurio y ejecuta:

```bash
python main.py --calibrar
```

Selecciona:

1. Zona completa del juego.
2. Dinosaurio.
3. ROI frente al dinosaurio.
4. Zona del puntaje actual, solo los números de la derecha.

## Probar sin controlar el teclado

```bash
python main.py --metodo contornos --sin-control
```

## Ejecutar con control automático

```bash
python main.py --metodo contornos
```

## Comparar métodos

Método por contornos:

```bash
python main.py --metodo contornos
```

Método por conteo de píxeles:

```bash
python main.py --metodo pixeles
```

## Ver resultados

```bash
python main.py --resumen
```

El puntaje se detecta automáticamente con visión por computadora clásica, usando segmentación de dígitos y comparación con plantillas binarias. No usa YOLO, OCR entrenado ni machine learning.

Los resultados se guardan en:

```text
resultados_dino/resumen_pruebas.csv
```

## Teclas durante la ejecución

```text
q o ESC = terminar prueba
f       = registrar falso positivo
n       = registrar falso negativo
p       = pausar/reanudar
```

## Explicación corta para reporte

El sistema se dividió en clases para separar responsabilidades. La clase `CapturadorPantalla` obtiene frames del juego desde la pantalla. La clase `PreprocesadorDino` convierte la ROI a escala de grises, corrige modo noche, aplica umbralización y elimina ruido. Los detectores `DetectorPixeles` y `DetectorContornos` implementan los dos métodos de visión por computadora solicitados. `ReglaDecision` decide si saltar, agacharse o no actuar, mientras que `ControladorTeclado` ejecuta la acción mediante el teclado. Finalmente, `GestorMetricas` guarda FPS, tiempo de supervivencia, puntaje, falsos positivos y falsos negativos.

## Nota sobre montículos del suelo

Esta versión agrega filtros por porcentaje de ocupación de la ROI. Los objetos que ocupan muy poca altura o poca área dentro de la ROI se ignoran para evitar que los pequeños montículos del suelo activen saltos falsos.

Los valores principales están en `dino/detectores.py`:

```python
self.min_porcentaje_area = 0.006
self.min_alto_obstaculo = 0.18
self.max_alto_monticulo = 0.16
```

Si detecta montículos, sube `min_alto_obstaculo` a `0.20`. Si deja de detectar cactus pequeños, bájalo a `0.15`.

## Corrección añadida

Esta versión corrige dos problemas:

1. Puntaje automático: el lector rechaza lecturas imposibles como 88899 cuando el tiempo de juego es bajo y toma solo el último grupo de 5 dígitos del marcador.
2. Nubes en cambio de color: el preprocesamiento y los detectores filtran objetos altos, delgados y alargados que corresponden a nubes, además de montículos del suelo.

Después de copiar los archivos corregidos, borra `config_dino.json` y calibra de nuevo. En la zona del puntaje selecciona solo los cinco números actuales, por ejemplo `00713`, no incluyas `HI` ni el récord.
