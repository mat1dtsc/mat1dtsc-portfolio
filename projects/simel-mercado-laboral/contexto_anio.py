"""
Contexto de año — única fuente de verdad para el pipeline SIMEL.
Toda la lógica de "hasta qué año" usa este módulo.
Al ejecutar el script el año que viene, los datos y ratios se expanden
automáticamente hasta ese año sin cambiar código.
"""
from datetime import date


def obtener_contexto():
    """Devuelve el contexto de año actual (año de ejecución)."""
    anio = date.today().year
    return {
        "anio_actual": anio,
        "anio_hasta_expandir": anio,
        "anio_inicio_serie": 2000,  # desde qué año pedir datos (WB, etc.)
    }


# Para importar: from contexto_anio import obtener_contexto, ANIO_ACTUAL
_contexto = obtener_contexto()
ANIO_ACTUAL = _contexto["anio_actual"]
ANIO_HASTA_EXPANDIR = _contexto["anio_hasta_expandir"]
ANIO_INICIO_SERIE = _contexto["anio_inicio_serie"]
