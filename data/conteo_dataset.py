#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para contar imágenes en un dataset estructurado por subtipos de placas electrónicas.
Genera un reporte CSV con el conteo ordenado de mayor a menor cantidad de imágenes.
"""

import os
import csv
import glob
from pathlib import Path

def contar_imagenes_en_carpeta(ruta_carpeta):
    """
    Cuenta las imágenes en una carpeta específica.
    
    Args:
        ruta_carpeta (str): Ruta de la carpeta a analizar
        
    Returns:
        int: Cantidad de imágenes encontradas
    """
    # Formatos de imagen soportados
    formatos_imagen = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
    
    total_imagenes = 0
    
    # Buscar archivos de imagen en la carpeta
    for formato in formatos_imagen:
        patron = os.path.join(ruta_carpeta, formato)
        archivos = glob.glob(patron)
        total_imagenes += len(archivos)
    
    return total_imagenes

def obtener_subtipos_con_conteo(ruta_base):
    """
    Obtiene todos los subtipos y cuenta sus imágenes.
    
    Args:
        ruta_base (str): Ruta base del dataset
        
    Returns:
        list: Lista de tuplas (nombre_subtipo, cantidad_imagenes)
    """
    subtipos_conteo = []
    
    # Verificar que la ruta base existe
    if not os.path.exists(ruta_base):
        print(f"Error: La ruta base '{ruta_base}' no existe.")
        return subtipos_conteo
    
    # Recorrer las carpetas principales (tipo1, tipo2, tipo3, etc.)
    for carpeta_tipo in os.listdir(ruta_base):
        ruta_tipo = os.path.join(ruta_base, carpeta_tipo)
        
        # Verificar que es una carpeta
        if not os.path.isdir(ruta_tipo):
            continue
            
        # Recorrer las subcarpetas de subtipos
        for carpeta_subtipo in os.listdir(ruta_tipo):
            ruta_subtipo = os.path.join(ruta_tipo, carpeta_subtipo)
            
            # Verificar que es una carpeta y que contiene "subtipo" en el nombre
            if os.path.isdir(ruta_subtipo) and "subtipo" in carpeta_subtipo.lower():
                cantidad = contar_imagenes_en_carpeta(ruta_subtipo)
                subtipos_conteo.append((carpeta_subtipo, cantidad))
    
    return subtipos_conteo

def generar_reporte_csv(subtipos_conteo, archivo_salida):
    """
    Genera el archivo CSV con el reporte ordenado.
    
    Args:
        subtipos_conteo (list): Lista de tuplas (nombre_subtipo, cantidad_imagenes)
        archivo_salida (str): Nombre del archivo CSV de salida
    """
    # Ordenar por cantidad de imágenes (mayor a menor)
    subtipos_ordenados = sorted(subtipos_conteo, key=lambda x: x[1], reverse=True)
    
    # Calcular total global
    total_global = sum(cantidad for _, cantidad in subtipos_ordenados)
    
    # Escribir archivo CSV
    with open(archivo_salida, 'w', newline='', encoding='utf-8') as archivo_csv:
        writer = csv.writer(archivo_csv)
        
        # Escribir encabezados
        writer.writerow(['Subtipo', 'Cantidad'])
        
        # Escribir datos
        for subtipo, cantidad in subtipos_ordenados:
            writer.writerow([subtipo, cantidad])
        
        # Escribir línea separadora y total
        writer.writerow([])  # Línea en blanco
        writer.writerow(['TOTAL GLOBAL', total_global])
    
    print(f"Reporte generado exitosamente: {archivo_salida}")
    print(f"Total global de imágenes: {total_global}")
    
    return total_global

def mostrar_resultados_consola(subtipos_conteo):
    """
    Muestra los resultados en la consola de forma ordenada.
    
    Args:
        subtipos_conteo (list): Lista de tuplas (nombre_subtipo, cantidad_imagenes)
    """
    # Ordenar por cantidad de imágenes (mayor a menor)
    subtipos_ordenados = sorted(subtipos_conteo, key=lambda x: x[1], reverse=True)
    
    print("\n" + "="*60)
    print("REPORTE DE CONTEO DE IMÁGENES POR SUBTIPO")
    print("="*60)
    print(f"{'Subtipo':<40} {'Cantidad':<10}")
    print("-"*60)
    
    for subtipo, cantidad in subtipos_ordenados:
        print(f"{subtipo:<40} {cantidad:<10}")
    
    total_global = sum(cantidad for _, cantidad in subtipos_ordenados)
    print("-"*60)
    print(f"{'TOTAL GLOBAL':<40} {total_global:<10}")
    print("="*60)

def main():
    """
    Función principal del script.
    """
    # Configuración de rutas
    RUTA_BASE_DATASET = "train"  # Cambiar según la ubicación del dataset
    ARCHIVO_SALIDA = "conteo_dataset.csv"
    
    print("Iniciando análisis del dataset...")
    print(f"Ruta base del dataset: {RUTA_BASE_DATASET}")
    
    # Obtener subtipos y conteos
    subtipos_conteo = obtener_subtipos_con_conteo(RUTA_BASE_DATASET)
    
    if not subtipos_conteo:
        print("No se encontraron subtipos para analizar.")
        return
    
    # Mostrar resultados en consola
    mostrar_resultados_consola(subtipos_conteo)
    
    # Generar archivo CSV
    total_global = generar_reporte_csv(subtipos_conteo, ARCHIVO_SALIDA)
    
    print(f"\nAnálisis completado. Se encontraron {len(subtipos_conteo)} subtipos.")
    print(f"Total de imágenes en el dataset: {total_global}")

if __name__ == "__main__":
    main() 