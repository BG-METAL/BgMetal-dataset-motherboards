# Script de Conteo de Dataset de Placas Electrónicas

## Descripción

Este script de Python analiza un dataset estructurado de placas electrónicas y genera un reporte detallado del conteo de imágenes por subtipo.

## Características

- ✅ Recorre automáticamente todas las carpetas de subtipos
- ✅ Cuenta imágenes en formatos: .jpg, .jpeg, .png (mayúsculas y minúsculas)
- ✅ Ignora archivos que no son imágenes
- ✅ Ordena resultados de mayor a menor cantidad
- ✅ Genera reporte en consola y archivo CSV
- ✅ Calcula total global de imágenes
- ✅ Usa solo librerías estándar de Python

## Estructura del Dataset Esperada

```
train/
├── tipo1/
│   ├── subtipo01_bajo-grado-marron/
│   │   ├── imagen1.jpg
│   │   ├── imagen2.jpeg
│   │   └── ...
│   └── subtipo02_bajo-grado-verde/
│       └── ...
├── tipo2/
│   ├── subtipo03_pentium-iii-verde-amarillo/
│   └── ...
└── tipo3/
    └── ...
```

## Uso

### 1. Configuración

Edita la variable `RUTA_BASE_DATASET` en el script según tu estructura:

```python
RUTA_BASE_DATASET = "train"  # Cambiar según la ubicación del dataset
```

### 2. Ejecución

```bash
python3 conteo_dataset.py
```

### 3. Resultados

El script generará:

1. **Reporte en consola**: Muestra los resultados ordenados de mayor a menor
2. **Archivo CSV**: `conteo_dataset.csv` con las columnas:
   - `Subtipo`: Nombre de la carpeta del subtipo
   - `Cantidad`: Número de imágenes encontradas
   - `TOTAL GLOBAL`: Suma total de todas las imágenes

## Ejemplo de Salida

```
============================================================
REPORTE DE CONTEO DE IMÁGENES POR SUBTIPO
============================================================
Subtipo                                  Cantidad  
------------------------------------------------------------
subtipo16_boards-tipo2                   97        
subtipo18_boards-tipo3                   56        
subtipo12_boards-tipo1                   54        
...
------------------------------------------------------------
TOTAL GLOBAL                             1099      
============================================================
```

## Archivo CSV Generado

El archivo `conteo_dataset.csv` contendrá:

```csv
Subtipo,Cantidad
subtipo16_boards-tipo2,97
subtipo18_boards-tipo3,56
subtipo12_boards-tipo1,54
...
TOTAL GLOBAL,1099
```

## Requisitos

- Python 3.x
- Librerías estándar: `os`, `csv`, `glob`, `pathlib`

## Personalización

### Cambiar formatos de imagen soportados

Edita la lista `formatos_imagen` en la función `contar_imagenes_en_carpeta()`:

```python
formatos_imagen = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
```

### Cambiar nombre del archivo de salida

Modifica la variable `ARCHIVO_SALIDA` en la función `main()`:

```python
ARCHIVO_SALIDA = "mi_reporte.csv"
```

## Funciones Principales

- `contar_imagenes_en_carpeta()`: Cuenta imágenes en una carpeta específica
- `obtener_subtipos_con_conteo()`: Recorre todo el dataset y obtiene conteos
- `generar_reporte_csv()`: Crea el archivo CSV con resultados ordenados
- `mostrar_resultados_consola()`: Muestra resultados formateados en consola

## Notas

- El script busca carpetas que contengan "subtipo" en su nombre
- Los resultados se ordenan automáticamente de mayor a menor cantidad
- Se incluye el total global al final del reporte
- El archivo CSV usa codificación UTF-8 para compatibilidad 