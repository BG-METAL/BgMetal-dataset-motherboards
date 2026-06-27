"""
Preparador de lote BG-Metal: TODO EN UNO por subtipo.

Reemplaza estos pasos manuales en una sola corrida:
  1. Conversion HEIC/_iOS -> JPG  (ya no necesitas XnConvert)
  2. Validacion de calidad        (descarta borrosas, oscuras, duplicadas, etc.)
  3. Renombrado con el prefijo del subtipo y numeracion continua
  4. Copia al folder del dataset en el repo

Resultado: en data/train/<subtipo> quedan SOLO imagenes nuevas, aceptadas,
en .jpeg, listas para subir a Label Studio y para commitear a git.

Ejemplo (boards tipo 1 -> subtipo12):
    python preparar_lote.py ^
        --origen "C:\\Users\\Matias_Trabajo\\Desktop\\Proyecto_BgMetal\\fotostipo1,2y3\\TIPO 1" ^
        --destino "C:\\Users\\Matias_Trabajo\\Documents\\GitHub\\BgMetal-dataset-motherboards\\data\\train\\subtipo12_boards-tipo1" ^
        --prefijo "2_12_boards-tipo1_"

Modo prueba (no copia nada, solo muestra que pasaria):
    ... --simular

Atajos de subtipo (en vez de --destino y --prefijo):
    python preparar_lote.py --origen "...\\TIPO 1" --subtipo boards-tipo1
"""

import argparse
import csv
import glob
import os
import re
import sys
from pathlib import Path

from PIL import Image, ImageOps

# Reutilizamos la logica de validacion del otro script.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validar_imagenes import (  # noqa: E402
    HEIF_OK,
    analizar_imagen,
    distancia_hamming,
    hash_rapido,
)

# Raiz del dataset (se calcula relativa a este archivo: ../data/train).
RAIZ_REPO = Path(__file__).resolve().parents[1]
TRAIN = RAIZ_REPO / "data" / "train"

# Atajos: nombre corto -> (carpeta destino, prefijo). Numero de subtipo segun el dataset.
SUBTIPOS = {
    "boards-tipo1": ("subtipo12_boards-tipo1", "2_12_boards-tipo1_"),
    "boards-tipo2": ("subtipo16_boards-tipo2", "2_16_boards-tipo2_"),
    "boards-tipo3": ("subtipo18_boards-tipo3", "2_18_boards-tipo3_"),
}


def siguiente_numero(destino: Path, prefijo: str) -> int:
    """Lee el numero mas alto ya usado en destino para continuar la numeracion."""
    max_num = 0
    for archivo in glob.glob(os.path.join(str(destino), f"{prefijo}*.*")):
        m = re.search(rf"{re.escape(prefijo)}(\d+)", os.path.basename(archivo))
        if m:
            max_num = max(max_num, int(m.group(1)))
    return max_num + 1


def hashes_existentes(destino: Path):
    """Hashes perceptuales de lo que ya hay en destino (para no reimportar duplicados)."""
    hashes = []
    if not destino.exists():
        return hashes
    for p in destino.iterdir():
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            h = hash_rapido(p)
            if h is not None:
                hashes.append(h)
    return hashes


def main():
    ap = argparse.ArgumentParser(description="Preparar lote de imagenes BG-Metal (todo en uno)")
    ap.add_argument("--origen", required=True, help="Carpeta con las fotos nuevas (pueden ser .heic)")
    ap.add_argument("--subtipo", choices=sorted(SUBTIPOS.keys()),
                    help="Atajo de subtipo (define destino y prefijo automaticamente)")
    ap.add_argument("--destino", help="Carpeta destino en el dataset (si no usas --subtipo)")
    ap.add_argument("--prefijo", help="Prefijo de nombre (si no usas --subtipo)")
    # Umbrales de calidad (mismos defaults que validar_imagenes.py).
    ap.add_argument("--min-lado", type=int, default=800)
    ap.add_argument("--nitidez", type=float, default=120.0)
    ap.add_argument("--brillo-min", type=float, default=35.0)
    ap.add_argument("--brillo-max", type=float, default=225.0)
    ap.add_argument("--min-kb", type=float, default=40.0)
    ap.add_argument("--max-dup", type=int, default=10,
                    help="Distancia Hamming maxima (sobre 256 bits) para duplicado. Default 10")
    ap.add_argument("--dedup-existentes", action="store_true",
                    help="Tambien compara contra lo ya presente en el destino "
                         "(mas lento; util si reprocesas un lote ya importado).")
    ap.add_argument("--calidad-jpg", type=int, default=95, help="Calidad JPEG de salida (1-100)")
    ap.add_argument("--simular", action="store_true", help="No escribe nada; solo muestra el plan")
    args = ap.parse_args()

    # Resolver destino y prefijo.
    if args.subtipo:
        carpeta, prefijo = SUBTIPOS[args.subtipo]
        destino = TRAIN / carpeta
    else:
        if not args.destino or not args.prefijo:
            ap.error("Debes pasar --subtipo, o bien --destino y --prefijo juntos.")
        destino = Path(args.destino)
        prefijo = args.prefijo

    origen = Path(args.origen)
    if not origen.is_dir():
        print(f"ERROR: la carpeta origen no existe: {origen}")
        return
    if not HEIF_OK:
        print("AVISO: pillow-heif no esta instalado; no se podran leer los .heic.")

    destino.mkdir(parents=True, exist_ok=True)

    extensiones = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".bmp", ".tif", ".tiff"}
    archivos = sorted([p for p in origen.iterdir()
                       if p.is_file() and p.suffix.lower() in extensiones])
    if not archivos:
        print("No se encontraron imagenes en la carpeta origen.")
        return

    print(f"Origen : {origen}  ({len(archivos)} imagenes)")
    print(f"Destino: {destino}")
    print(f"Prefijo: {prefijo}")
    print("-" * 60)

    num = siguiente_numero(destino, prefijo)
    print(f"La numeracion continuara desde: {num:04d}")

    # Anti-duplicado: siempre dentro del propio lote; contra el destino solo si se pide.
    if args.dedup_existentes:
        print("Calculando hashes de lo ya presente en destino (puede tardar)...")
        hashes_acumulados = hashes_existentes(destino)
    else:
        hashes_acumulados = []

    copiadas = 0
    rechazadas = []
    duplicadas = []
    filas = []  # para el CSV de evidencia

    for i, ruta in enumerate(archivos, 1):
        info = analizar_imagen(ruta)
        fila = {
            "archivo_original": ruta.name,
            "nombre_nuevo": "",
            "estado": "",
            "motivos": "",
            "ancho": info["ancho"],
            "alto": info["alto"],
            "peso_kb": info["peso_kb"],
            "nitidez": info["nitidez"],
            "brillo": info["brillo"],
        }

        # Validacion de calidad.
        motivos = []
        if info["corrupta"]:
            motivos.append("corrupta")
        else:
            if min(info["ancho"], info["alto"]) < args.min_lado:
                motivos.append(f"baja_resolucion({info['ancho']}x{info['alto']})")
            if info["nitidez"] < args.nitidez:
                motivos.append(f"desenfocada({info['nitidez']})")
            if info["brillo"] < args.brillo_min:
                motivos.append(f"muy_oscura({info['brillo']})")
            if info["brillo"] > args.brillo_max:
                motivos.append(f"quemada({info['brillo']})")
            if info["peso_kb"] < args.min_kb:
                motivos.append(f"peso_bajo({info['peso_kb']}KB)")

        if motivos:
            rechazadas.append((ruta.name, "; ".join(motivos)))
            fila["estado"] = "rechazada"
            fila["motivos"] = "; ".join(motivos)
            filas.append(fila)
            continue

        # Anti-duplicado contra lo ya aceptado (y, si se pidio, contra el destino).
        dup_de = None
        for h in hashes_acumulados:
            if distancia_hamming(info["hash"], h) <= args.max_dup:
                dup_de = True
                break
        if dup_de:
            duplicadas.append(ruta.name)
            fila["estado"] = "duplicada"
            fila["motivos"] = f"duplicada (Hamming<= {args.max_dup})"
            filas.append(fila)
            continue

        nuevo_nombre = f"{prefijo}{num:04d}.jpeg"
        ruta_destino = destino / nuevo_nombre

        if args.simular:
            print(f"[SIM] {ruta.name}  ->  {nuevo_nombre}")
        else:
            try:
                with Image.open(ruta) as im:
                    im = ImageOps.exif_transpose(im).convert("RGB")
                    im.save(ruta_destino, "JPEG", quality=args.calidad_jpg)
                print(f"OK  {ruta.name}  ->  {nuevo_nombre}")
            except Exception as e:
                rechazadas.append((ruta.name, f"error_guardado: {e}"))
                fila["estado"] = "rechazada"
                fila["motivos"] = f"error_guardado: {e}"
                filas.append(fila)
                continue

        hashes_acumulados.append(info["hash"])
        fila["estado"] = "copiada"
        fila["nombre_nuevo"] = nuevo_nombre
        filas.append(fila)
        copiadas += 1
        num += 1
        if i % 25 == 0:
            print(f"  ...procesadas {i}/{len(archivos)}")

    # Reporte CSV de evidencia (junto a la carpeta origen).
    ruta_reporte = origen / "reporte_lote.csv"
    cols = ["archivo_original", "nombre_nuevo", "estado", "motivos",
            "ancho", "alto", "peso_kb", "nitidez", "brillo"]
    with open(ruta_reporte, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)

    # Resumen.
    print("\n" + "=" * 60)
    print("RESUMEN DEL LOTE" + (" (SIMULACION)" if args.simular else ""))
    print("=" * 60)
    print(f"Imagenes en origen : {len(archivos)}")
    print(f"Aceptadas/copiadas : {copiadas}")
    print(f"Duplicadas omitidas: {len(duplicadas)}")
    print(f"Rechazadas calidad : {len(rechazadas)}")
    if duplicadas:
        print("-" * 60)
        print("Duplicadas (no copiadas):")
        for n in duplicadas:
            print(f"  [=] {n}")
    if rechazadas:
        print("-" * 60)
        print("Rechazadas por calidad (no copiadas):")
        for n, motivo in rechazadas:
            print(f"  [X] {n:<45} {motivo}")
    print("-" * 60)
    print(f"Reporte CSV: {ruta_reporte}")
    print("=" * 60)
    if not args.simular:
        print(f"Siguiente paso: sube las {copiadas} imagenes nuevas de\n  {destino}\na Label Studio, etiqueta con etiquetar_automatico.py, exporta el JSON y commitea.")


if __name__ == "__main__":
    main()
