"""
Validador de calidad de imagenes para el dataset BG-Metal.

Revisa una carpeta de imagenes y detecta las que NO son aceptables segun:
  - Archivo corrupto / ilegible
  - Resolucion demasiado baja
  - Imagen desenfocada (poco nitida)
  - Imagen muy oscura o muy quemada (brillo)
  - Archivo demasiado liviano (peso en KB)
  - Duplicados / casi-duplicados (mismo encuadre repetido, ej: "foo (1).heic")

Genera un reporte CSV con la metrica de cada imagen y, opcionalmente,
mueve las imagenes rechazadas a una subcarpeta "_rechazadas" para revision manual.

Uso basico (solo reporte):
    python validar_imagenes.py "C:\\ruta\\a\\fotos"

Mover las rechazadas a _rechazadas:
    python validar_imagenes.py "C:\\ruta\\a\\fotos" --mover

Ajustar umbrales (ejemplos):
    python validar_imagenes.py "C:\\ruta" --min-lado 1000 --nitidez 80 --max-dup 5

No requiere internet. Funciona con .jpg .jpeg .png .heic .heif .webp .bmp .tif
"""

import argparse
import os
import csv
import shutil
import statistics
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

# Habilita lectura de HEIC/HEIF (fotos de iPhone) con Pillow.
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_OK = True
except Exception:
    HEIF_OK = False

EXTENSIONES = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".bmp", ".tif", ".tiff"}

# Kernel Laplaciano 3x3 para medir nitidez (varianza de bordes).
_KERNEL_LAPLACIANO = ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1)


def listar_imagenes(carpeta: Path):
    """Devuelve las rutas de imagenes en la carpeta (no recursivo), ignorando _rechazadas."""
    imgs = []
    for p in sorted(carpeta.iterdir()):
        if p.is_dir():
            continue
        if p.suffix.lower() in EXTENSIONES:
            imgs.append(p)
    return imgs


def metrica_nitidez(gris: Image.Image) -> float:
    """Varianza del Laplaciano: mas alto = mas nitido. Mas bajo = mas borroso."""
    bordes = gris.filter(_KERNEL_LAPLACIANO)
    pixeles = list(bordes.getdata())
    if len(pixeles) < 2:
        return 0.0
    return statistics.pvariance(pixeles)


def metrica_brillo(gris: Image.Image) -> float:
    """Brillo medio 0-255 (0 = negro, 255 = blanco)."""
    pixeles = list(gris.getdata())
    return sum(pixeles) / len(pixeles) if pixeles else 0.0


def hash_perceptual(gris: Image.Image) -> int:
    """dHash de 256 bits (16x16): compara pixeles vecinos en horizontal.

    Es mas discriminativo que el average-hash de 8x8 (evita que placas
    distintas sobre fondos parecidos se confundan) y es robusto al brillo.
    Imagenes casi identicas (ej. la misma foto bajada dos veces) dan
    distancia Hamming ~0; placas realmente distintas dan distancias altas.
    """
    chico = gris.resize((17, 16), Image.BILINEAR)
    pix = list(chico.getdata())
    bits = 0
    for fila in range(16):
        base = fila * 17
        for col in range(16):
            bits = (bits << 1) | (1 if pix[base + col] > pix[base + col + 1] else 0)
    return bits


def distancia_hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def hash_rapido(ruta: Path):
    """Solo calcula el hash perceptual (sin metricas de calidad). Para dedup masivo."""
    try:
        with Image.open(ruta) as im:
            im = ImageOps.exif_transpose(im)
            return hash_perceptual(im.convert("L"))
    except Exception:
        return None


def analizar_imagen(ruta: Path, lado_trabajo: int = 1024):
    """Abre la imagen y calcula sus metricas. Devuelve dict (o marca corrupta)."""
    info = {
        "archivo": ruta.name,
        "ancho": 0,
        "alto": 0,
        "peso_kb": round(ruta.stat().st_size / 1024, 1),
        "nitidez": 0.0,
        "brillo": 0.0,
        "hash": None,
        "corrupta": False,
    }
    try:
        with Image.open(ruta) as im:
            im = ImageOps.exif_transpose(im)  # respeta orientacion del telefono
            info["ancho"], info["alto"] = im.size
            # Trabajamos sobre una version reducida en gris (rapido y estable).
            gris = im.convert("L")
            gris.thumbnail((lado_trabajo, lado_trabajo), Image.BILINEAR)
            info["nitidez"] = round(metrica_nitidez(gris), 1)
            info["brillo"] = round(metrica_brillo(gris), 1)
            info["hash"] = hash_perceptual(gris)
    except Exception as e:
        info["corrupta"] = True
        info["motivo_error"] = str(e)
    return info


def main():
    ap = argparse.ArgumentParser(description="Validador de calidad de imagenes BG-Metal")
    ap.add_argument("carpeta", help="Carpeta con las imagenes a revisar")
    ap.add_argument("--min-lado", type=int, default=800,
                    help="Lado minimo (ancho y alto) en pixeles. Default 800")
    ap.add_argument("--nitidez", type=float, default=120.0,
                    help="Umbral minimo de nitidez (varianza Laplaciano). Default 120. "
                         "Revisa el CSV (ordena por 'nitidez' ascendente) para afinarlo.")
    ap.add_argument("--brillo-min", type=float, default=35.0,
                    help="Brillo minimo aceptable 0-255 (muy oscura). Default 35")
    ap.add_argument("--brillo-max", type=float, default=225.0,
                    help="Brillo maximo aceptable 0-255 (quemada). Default 225")
    ap.add_argument("--min-kb", type=float, default=40.0,
                    help="Peso minimo del archivo en KB. Default 40")
    ap.add_argument("--max-dup", type=int, default=10,
                    help="Distancia Hamming maxima (sobre 256 bits) para duplicado. Default 10")
    ap.add_argument("--mover", action="store_true",
                    help="Mueve las rechazadas a la subcarpeta _rechazadas")
    ap.add_argument("--reporte", default="reporte_calidad.csv",
                    help="Nombre del CSV de salida. Default reporte_calidad.csv")
    args = ap.parse_args()

    carpeta = Path(args.carpeta)
    if not carpeta.is_dir():
        print(f"ERROR: la carpeta no existe: {carpeta}")
        return

    imagenes = listar_imagenes(carpeta)
    if not imagenes:
        print("No se encontraron imagenes en la carpeta.")
        return

    print(f"Analizando {len(imagenes)} imagenes en: {carpeta}")
    if not HEIF_OK:
        print("AVISO: pillow-heif no esta instalado; los .heic se marcaran como corruptos.")

    resultados = []
    for i, ruta in enumerate(imagenes, 1):
        info = analizar_imagen(ruta)
        resultados.append(info)
        if i % 25 == 0:
            print(f"  ...{i}/{len(imagenes)}")

    # Deteccion de duplicados por hash perceptual.
    validos_con_hash = [r for r in resultados if r["hash"] is not None]
    for r in validos_con_hash:
        r["es_duplicado"] = False
        r["duplicado_de"] = ""
    for idx in range(len(validos_con_hash)):
        a = validos_con_hash[idx]
        if a["es_duplicado"]:
            continue
        for jdx in range(idx + 1, len(validos_con_hash)):
            b = validos_con_hash[jdx]
            if b["es_duplicado"]:
                continue
            if distancia_hamming(a["hash"], b["hash"]) <= args.max_dup:
                b["es_duplicado"] = True
                b["duplicado_de"] = a["archivo"]

    # Decision de aceptacion por cada imagen.
    for r in resultados:
        motivos = []
        if r["corrupta"]:
            motivos.append("corrupta")
        else:
            if min(r["ancho"], r["alto"]) < args.min_lado:
                motivos.append(f"baja_resolucion({r['ancho']}x{r['alto']})")
            if r["nitidez"] < args.nitidez:
                motivos.append(f"desenfocada({r['nitidez']})")
            if r["brillo"] < args.brillo_min:
                motivos.append(f"muy_oscura({r['brillo']})")
            if r["brillo"] > args.brillo_max:
                motivos.append(f"quemada({r['brillo']})")
            if r["peso_kb"] < args.min_kb:
                motivos.append(f"peso_bajo({r['peso_kb']}KB)")
            if r.get("es_duplicado"):
                motivos.append(f"duplicada_de({r['duplicado_de']})")
        r["aceptada"] = len(motivos) == 0
        r["motivos"] = "; ".join(motivos)

    # Reporte CSV.
    ruta_reporte = carpeta / args.reporte
    columnas = ["archivo", "aceptada", "motivos", "ancho", "alto",
                "peso_kb", "nitidez", "brillo", "es_duplicado", "duplicado_de"]
    with open(ruta_reporte, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columnas, extrasaction="ignore")
        w.writeheader()
        for r in resultados:
            w.writerow(r)

    aceptadas = [r for r in resultados if r["aceptada"]]
    rechazadas = [r for r in resultados if not r["aceptada"]]

    # Mover rechazadas si se pidio.
    if args.mover and rechazadas:
        destino = carpeta / "_rechazadas"
        destino.mkdir(exist_ok=True)
        for r in rechazadas:
            origen = carpeta / r["archivo"]
            if origen.exists():
                shutil.move(str(origen), str(destino / r["archivo"]))

    # Resumen en consola.
    print("\n" + "=" * 60)
    print("RESUMEN DE VALIDACION")
    print("=" * 60)
    print(f"Total analizadas : {len(resultados)}")
    print(f"Aceptadas        : {len(aceptadas)}")
    print(f"Rechazadas       : {len(rechazadas)}")
    if rechazadas:
        print("-" * 60)
        for r in rechazadas:
            print(f"  [X] {r['archivo']:<45} {r['motivos']}")
    print("-" * 60)
    print(f"Reporte CSV: {ruta_reporte}")
    if args.mover and rechazadas:
        print(f"Rechazadas movidas a: {carpeta / '_rechazadas'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
