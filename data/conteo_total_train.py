#!/usr/bin/env python3
"""
Script para contar el total de imágenes en la carpeta train.
"""

import os
from pathlib import Path

def contar_imagenes_train(ruta_train):
    """
    Cuenta el total de imágenes en la carpeta train.
    
    Args:
        ruta_train (str): Ruta de la carpeta train
        
    Returns:
        dict: Diccionario con conteo por extensión y total
    """
    # Extensiones de imagen soportadas (en minúsculas para comparación)
    extensiones_imagen = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    
    conteo_por_extension = {}
    total_imagenes = 0
    
    # Verificar que la carpeta existe
    if not os.path.exists(ruta_train):
        print(f"Error: La carpeta '{ruta_train}' no existe.")
        return None
    
    # Recorrer recursivamente todos los archivos
    for root, dirs, files in os.walk(ruta_train):
        for archivo in files:
            extension = Path(archivo).suffix.lower()
            if extension in extensiones_imagen:
                total_imagenes += 1
                conteo_por_extension[extension] = conteo_por_extension.get(extension, 0) + 1
    
    return {
        'total': total_imagenes,
        'por_extension': conteo_por_extension
    }

def main():
    """
    Función principal del script.
    """
    # Ruta de la carpeta train (relativa al directorio donde está el script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ruta_train = os.path.join(script_dir, "train")
    
    print("=" * 50)
    print("CONTEO TOTAL DE IMÁGENES - CARPETA TRAIN")
    print("=" * 50)
    print(f"\nRuta analizada: {ruta_train}\n")
    
    resultado = contar_imagenes_train(ruta_train)
    
    if resultado is None:
        return
    
    # Mostrar conteo por extensión
    print("Conteo por extensión:")
    print("-" * 30)
    for ext, cantidad in sorted(resultado['por_extension'].items()):
        print(f"  {ext:<10} : {cantidad:>6} imágenes")
    
    print("-" * 30)
    print(f"\n  {'TOTAL':<10} : {resultado['total']:>6} imágenes")
    print("=" * 50)

if __name__ == "__main__":
    main()
