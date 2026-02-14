"""
Obtiene y documenta datos del Censo de Población y Vivienda (INE Chile).
- Censo 2024: síntesis y enlaces oficiales.
- Censo 2017: referencia para series históricas.
Los microdatos completos se descargan desde los portales INE/Redatam; este script
guarda un resumen numérico y opcionalmente la síntesis en PDF.
"""
from pathlib import Path
import csv

import requests

DATOS_DIR = Path("datos") / "censo_ine"
RESULTADOS_DIR = Path("resultados")
RESULTADOS_DIR.mkdir(exist_ok=True)
DATOS_DIR.mkdir(parents=True, exist_ok=True)

# Censo 2024 — cifras oficiales publicadas por el INE (dic 2025)
CENSO_2024_RESUMEN = [
    {"censo": "2024", "concepto": "Población censada", "valor": 18480432, "unidad": "personas"},
    {"censo": "2024", "concepto": "Viviendas censadas", "valor": 7642716, "unidad": "viviendas"},
    {"censo": "2024", "concepto": "Hogares censados", "valor": 6596527, "unidad": "hogares"},
]

# URL pública de la síntesis en PDF (Censo 2024)
URL_SINTESIS_PDF = "https://censo2024.ine.gob.cl/wp-content/uploads/2025/12/sintesis_resultados_censo2024.pdf"
# Portales oficiales
URL_CENSO_2024 = "https://censo2024.ine.gob.cl"
URL_INE_CENSOS = "https://www.ine.gob.cl/estadisticas/sociales/censos-de-poblacion-y-vivienda"


def guardar_resumen_csv():
    """Guarda resumen numérico del Censo 2024 en resultados/ y datos/ (formato pipeline)."""
    path_resultados = RESULTADOS_DIR / "censo_ine_resumen.csv"
    path_datos = DATOS_DIR / "censo_2024_resumen.csv"
    with open(path_resultados, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["censo", "concepto", "valor", "unidad"])
        w.writeheader()
        w.writerows(CENSO_2024_RESUMEN)
    with open(path_datos, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["censo", "concepto", "valor", "unidad"])
        w.writeheader()
        w.writerows(CENSO_2024_RESUMEN)
    # Versión compatible con cargar_datos.py (indicador, fecha, valor, region)
    path_indicadores = DATOS_DIR / "indicadores_censo_2024.csv"
    with open(path_indicadores, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["indicador", "fecha", "valor", "region"])
        w.writeheader()
        for row in CENSO_2024_RESUMEN:
            w.writerow({
                "indicador": f"Censo 2024 — {row['concepto']}",
                "fecha": row["censo"],
                "valor": row["valor"],
                "region": "_T",
            })
    print(f"  Guardado: {path_resultados}")
    print(f"  Guardado: {path_datos}")
    print(f"  Guardado: {path_indicadores} (para pipeline)")
    return path_resultados


def descargar_sintesis_pdf():
    """Descarga la síntesis de resultados Censo 2024 (PDF) si está disponible."""
    out = DATOS_DIR / "sintesis_resultados_censo2024.pdf"
    try:
        r = requests.get(URL_SINTESIS_PDF, timeout=30, stream=True)
        if r.status_code == 200:
            with open(out, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"  Descargado: {out}")
        else:
            print(f"  Síntesis PDF no disponible (HTTP {r.status_code}). Descarga manual: {URL_SINTESIS_PDF}")
    except Exception as e:
        print(f"  No se pudo descargar PDF: {e}")
        print(f"  Descarga manual: {URL_SINTESIS_PDF}")


def guardar_lectura_ine():
    """Guarda un archivo de texto con instrucciones para acceder a microdatos INE."""
    path = DATOS_DIR / "LECTURA_CENSO_INE.txt"
    texto = f"""
Datos del Censo — INE Chile
===========================

Censo 2024 (Población y Vivienda)
  Portal: {URL_CENSO_2024}
  Síntesis PDF: {URL_SINTESIS_PDF}
  Base de datos (microdatos): ver portal → Publicaciones → Base de datos
  Redatam Web: para tabulados y gráficos en línea

Censo 2017
  Estadísticas: {URL_INE_CENSOS}
  INE.Stat y geodatos: www.ine.gob.cl

Para descargar microdatos completos (personas, hogares, viviendas por comuna/manzana):
  1. Entra a censo2024.ine.gob.cl o ine.gob.cl
  2. Busca "Base de datos" / "Microdatos" / "Descargas"
  3. Usa Redatam o el formato que publique el INE (CSV, SPSS, etc.)
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(texto.strip())
    print(f"  Guardado: {path}")


def main():
    print("Obteniendo datos del Censo — INE Chile...\n")
    guardar_resumen_csv()
    descargar_sintesis_pdf()
    guardar_lectura_ine()
    print("\nResumen Censo 2024:")
    for row in CENSO_2024_RESUMEN:
        print(f"  {row['concepto']}: {row['valor']:,} {row['unidad']}")
    print("\nPara análisis con SIMEL/mercado laboral, puedes cruzar población censada")
    print("con indicadores de empleo (Banco Mundial) en comportamiento_social.py.\n")


if __name__ == "__main__":
    main()
