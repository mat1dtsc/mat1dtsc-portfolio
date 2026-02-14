"""
Obtiene datos del mercado laboral y sociedad actual desde la API del Banco Mundial (Chile).
Usa el contexto de año del proyecto: siempre pide datos hasta el año en que se ejecuta.
Al ejecutar el año que viene, la serie se expande sin cambiar código.
Fuente: https://data.worldbank.org/ | API: api.worldbank.org
"""
import time
from pathlib import Path

import requests

from contexto_anio import ANIO_ACTUAL, ANIO_INICIO_SERIE

DATOS_DIR = Path("datos") / "mercado_actual"
DATOS_DIR.mkdir(parents=True, exist_ok=True)

PAIS = "CL"
BASE_URL = "https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
ANIO_INICIO = ANIO_INICIO_SERIE
ANIO_FIN = ANIO_ACTUAL

# Mercado laboral (ILO)
INDICADORES_LABORAL = {
    "SL.UEM.TOTL.ZS": "Tasa de desempleo (% fuerza de trabajo)",
    "SL.UEM.1524.ZS": "Tasa de desempleo juvenil 15-24 (% fuerza de trabajo 15-24)",
    "SL.TLF.ACTI.ZS": "Tasa de participación laboral (% pop. 15-64)",
    "SL.TLF.CACT.FE.ZS": "Tasa de actividad femenina (% mujeres 15-64)",
    "SL.TLF.CACT.MA.ZS": "Tasa de actividad masculina (% hombres 15-64)",
}

# Sociedad, desigualdad y economía
INDICADORES_SOCIALES = {
    "SI.POV.GINI": "Índice Gini (desigualdad de ingresos)",
    "NY.GDP.PCAP.KD": "PIB per cápita (USD constantes 2015)",
    "SP.POP.TOTL": "Población total",
    "SP.URB.TOTL.IN.ZS": "Población urbana (% del total)",
    "SE.ADT.LITR.ZS": "Tasa de alfabetización adultos (% 15+)",
    "SP.DYN.LE00.IN": "Expectativa de vida al nacer (años)",
}

INDICADORES = {**INDICADORES_LABORAL, **INDICADORES_SOCIALES}


def fetch_indicador(indicator_id: str, indicator_name: str) -> list[dict]:
    """Obtiene serie temporal de un indicador para Chile desde la API."""
    url = (
        BASE_URL.format(country=PAIS, indicator=indicator_id)
        + f"?format=json&date={ANIO_INICIO}:{ANIO_FIN}&per_page=100"
    )
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  Error obteniendo {indicator_id}: {e}")
        return []

    if not isinstance(data, list) or len(data) < 2:
        return []
    observaciones = data[1] or []
    filas = []
    for obs in observaciones:
        if obs.get("value") is None:
            continue
        filas.append({
            "indicador": indicator_name,
            "fecha": obs["date"],
            "valor": round(float(obs["value"]), 2),
            "region": "_T",
        })
    return filas


def main():
    print(f"Obteniendo datos Banco Mundial — Chile (contexto año: {ANIO_ACTUAL}, hasta {ANIO_FIN})...\n")
    todas = []
    for ind_id, ind_nombre in INDICADORES.items():
        print(f"  · {ind_nombre[:60]}...")
        filas = fetch_indicador(ind_id, ind_nombre)
        todas.extend(filas)
        time.sleep(0.25)

    if not todas:
        print("\nNo se obtuvieron datos. Revisa conexión o indicadores.")
        return

    import pandas as pd
    df = pd.DataFrame(todas)
    csv_principal = DATOS_DIR / "mercado_actual_chile.csv"
    df.sort_values(["indicador", "fecha"]).to_csv(csv_principal, index=False)
    print(f"\n  Guardado: {csv_principal} ({len(df)} filas, {df['indicador'].nunique()} indicadores)")
    print("\nEjecuta después: python cargar_datos.py")
    print("  Luego: python calcular_ratios_sociales.py  y  python comportamiento_social.py\n")


if __name__ == "__main__":
    main()
