"""
Carga y normaliza datos de PGU (data/pgu/*.csv) y población 65+ (INE).
Incluye funciones de análisis por comuna, región, montos y tasas de crecimiento.
"""
import re
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).parent
DATA_PGU_DIR = PROJECT_ROOT / "data" / "pgu"
POPULATION_GLOB = "CL01*NP65MAS*all.csv"

# Mapeo de regiones
REGIONES_CHILE = {
    "1": "Tarapacá", "2": "Antofagasta", "3": "Atacama", "4": "Coquimbo",
    "5": "Valparaíso", "6": "O'Higgins", "7": "Maule", "8": "Biobío",
    "9": "La Araucanía", "10": "Los Lagos", "11": "Aysén", "12": "Magallanes",
    "13": "Metropolitana", "14": "Los Ríos", "15": "Arica y Parinacota", "16": "Ñuble",
}

# ISO 3166-2:CL codes para mapa
REGION_ISO = {
    "15": "CL-AP", "1": "CL-TA", "2": "CL-AN", "3": "CL-AT", "4": "CL-CO",
    "5": "CL-VS", "6": "CL-LI", "7": "CL-ML", "8": "CL-BI", "9": "CL-AR",
    "10": "CL-LL", "11": "CL-AI", "12": "CL-MA", "13": "CL-RM", "14": "CL-LR",
    "16": "CL-NB",
}

# Latitudes aproximadas para mapa de burbujas
REGION_COORDS = {
    "15": (-18.48, -70.31), "1": (-20.21, -70.14), "2": (-23.65, -70.40),
    "3": (-27.37, -70.33), "4": (-30.47, -71.25), "5": (-33.05, -71.63),
    "6": (-34.17, -70.74), "7": (-35.43, -71.66), "8": (-36.83, -73.05),
    "9": (-38.74, -72.60), "10": (-41.47, -72.94), "11": (-45.57, -72.07),
    "12": (-53.15, -70.92), "13": (-33.45, -70.67), "14": (-39.81, -73.24),
    "16": (-36.62, -72.10),
}


def _find_population_file():
    for f in PROJECT_ROOT.glob(POPULATION_GLOB):
        return f
    return None


def load_poblacion_65_mas():
    """Carga población 65+ por sexo y año (INE)."""
    path = _find_population_file()
    if not path or not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, encoding="utf-8", sep=";", on_bad_lines="skip")
    if df.empty:
        df = pd.read_csv(path, encoding="utf-8", on_bad_lines="skip")
    rename = {}
    for c in df.columns:
        cu = c.upper()
        if "TIME_PERIOD" in cu or ("TIME" in cu and "PERIOD" in cu):
            rename[c] = "anio"
        elif "OBS_VALUE" in cu:
            rename[c] = "poblacion"
        elif "SEXO" in cu:
            rename[c] = "sexo"
    df = df.rename(columns=rename)
    need = ["anio", "poblacion", "sexo"]
    for n in need:
        if n not in df.columns:
            return pd.DataFrame()
    df["poblacion"] = pd.to_numeric(df["poblacion"], errors="coerce")
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce")
    df = df.dropna(subset=["poblacion", "anio"])
    return df[["anio", "sexo", "poblacion"]].copy()


def _parse_number(s):
    """Parsea número con formato chileno (punto como separador de miles)."""
    if pd.isna(s):
        return 0
    s = str(s).strip().replace(".", "").replace(",", ".")
    try:
        return int(float(s))
    except ValueError:
        return 0


def load_one_pgu_csv(path):
    """Carga un CSV de PGU (IPS). Maneja formatos de 9 o 21+ columnas."""
    path = Path(path)
    text = path.read_text(encoding="utf-8-sig")
    text = text.replace("\r\r\n", "\n").replace("\r\n", "\n").replace("\r", "\n")
    lines = [l for l in text.split("\n") if l.strip()]
    if len(lines) < 5:
        return pd.DataFrame()

    # Buscar fila header
    header_idx = None
    for i, line in enumerate(lines):
        if "Regi" in line and "Comuna" in line:
            header_idx = i
            break
    if header_idx is None:
        return pd.DataFrame()

    # Columnas base siempre son: Región, Cód. Comuna, Glosa Comuna, Nº Hombre, Monto m$ Hombre, Nº Mujer, Monto m$ Mujer, Total Nº, Total Mto. m$
    base_cols = [
        "region", "cod_comuna", "glosa_comuna",
        "n_hombres", "monto_hombres", "n_mujeres", "monto_mujeres",
        "total_n", "total_monto"
    ]

    rows = []
    for line in lines[header_idx + 1:]:
        parts = line.split(";")
        non_empty = [p.strip() for p in parts if p.strip()]
        if len(non_empty) < 5:
            continue
        region = parts[0].strip()
        if not region.isdigit():
            continue

        row = {
            "region": region,
            "cod_comuna": parts[1].strip() if len(parts) > 1 else "",
            "glosa_comuna": parts[2].strip() if len(parts) > 2 else "",
        }

        # Detectar si es formato extendido (21 campos) o simple (9 campos)
        numeric_parts = [p.strip() for p in parts[3:] if p.strip()]
        if len(numeric_parts) >= 18:
            # Formato extendido: 3 grupos de 6 (PGU básica, complemento, total)
            # Usamos el grupo 3 (total) que está en posiciones 12-17 desde col 3
            # = cols 15-20 absolutas
            row["n_hombres"] = _parse_number(parts[15].strip() if len(parts) > 15 else "0")
            row["monto_hombres"] = _parse_number(parts[16].strip() if len(parts) > 16 else "0")
            row["n_mujeres"] = _parse_number(parts[17].strip() if len(parts) > 17 else "0")
            row["monto_mujeres"] = _parse_number(parts[18].strip() if len(parts) > 18 else "0")
            row["total_n"] = _parse_number(parts[19].strip() if len(parts) > 19 else "0")
            row["total_monto"] = _parse_number(parts[20].strip() if len(parts) > 20 else "0")
            # También guardar PGU básica (grupo 1)
            row["pgu_basica_n"] = _parse_number(parts[3].strip() if len(parts) > 3 else "0")
            row["pgu_basica_monto"] = _parse_number(parts[8].strip() if len(parts) > 8 else "0")
            # Complemento (grupo 2)
            row["pgu_complemento_n"] = _parse_number(parts[9].strip() if len(parts) > 9 else "0")
            row["pgu_complemento_monto"] = _parse_number(parts[14].strip() if len(parts) > 14 else "0")
        else:
            # Formato simple: 6 valores numéricos
            row["n_hombres"] = _parse_number(parts[3].strip() if len(parts) > 3 else "0")
            row["monto_hombres"] = _parse_number(parts[4].strip() if len(parts) > 4 else "0")
            row["n_mujeres"] = _parse_number(parts[5].strip() if len(parts) > 5 else "0")
            row["monto_mujeres"] = _parse_number(parts[6].strip() if len(parts) > 6 else "0")
            row["total_n"] = _parse_number(parts[7].strip() if len(parts) > 7 else "0")
            row["total_monto"] = _parse_number(parts[8].strip() if len(parts) > 8 else "0")

        rows.append(row)

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def load_all_pgu(data_dir=None):
    """Carga todos los CSV de PGU y devuelve DataFrame unificado con columnas normalizadas."""
    data_dir = data_dir or DATA_PGU_DIR
    if not data_dir.exists():
        return pd.DataFrame()
    frames = []
    for path in sorted(Path(data_dir).glob("pgu_*.csv")):
        stem = path.stem.replace("pgu_", "")
        parts = stem.split("_")
        if len(parts) < 2:
            continue
        try:
            anio, mes = int(parts[0]), int(parts[1])
        except ValueError:
            continue
        df = load_one_pgu_csv(path)
        if df.empty:
            continue
        df["anio"] = anio
        df["mes"] = mes
        df["periodo"] = f"{anio}-{mes:02d}"
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


# ── Funciones de análisis ──────────────────────────────────────────

def pgu_totales_por_periodo(df):
    """Totales nacionales por periodo."""
    if df.empty:
        return pd.DataFrame()
    agg = df.groupby(["periodo", "anio", "mes"]).agg(
        total_beneficiarios=("total_n", "sum"),
        total_monto=("total_monto", "sum"),
        hombres=("n_hombres", "sum"),
        mujeres=("n_mujeres", "sum"),
        monto_hombres=("monto_hombres", "sum"),
        monto_mujeres=("monto_mujeres", "sum"),
        n_comunas=("cod_comuna", "nunique"),
    ).reset_index().sort_values("periodo")
    agg["monto_promedio"] = (agg["total_monto"] / agg["total_beneficiarios"].replace(0, np.nan)).round(0)
    agg["pct_mujeres"] = (100 * agg["mujeres"] / agg["total_beneficiarios"].replace(0, np.nan)).round(1)
    return agg


def pgu_por_region(df, periodo=None, anio=None):
    """Agrega beneficiarios y montos por región."""
    if df.empty:
        return pd.DataFrame()
    d = df.copy()
    if periodo:
        d = d[d["periodo"] == periodo]
    elif anio:
        last_per = d[d["anio"] == anio]["periodo"].max()
        d = d[d["periodo"] == last_per]
    else:
        d = d[d["periodo"] == d["periodo"].max()]

    agg = d.groupby("region").agg(
        beneficiarios=("total_n", "sum"),
        monto_total=("total_monto", "sum"),
        hombres=("n_hombres", "sum"),
        mujeres=("n_mujeres", "sum"),
        n_comunas=("cod_comuna", "nunique"),
    ).reset_index()
    agg["region_nombre"] = agg["region"].map(REGIONES_CHILE).fillna("Otro")
    agg["monto_promedio"] = (agg["monto_total"] / agg["beneficiarios"].replace(0, np.nan)).round(0)
    agg["pct_mujeres"] = (100 * agg["mujeres"] / agg["beneficiarios"].replace(0, np.nan)).round(1)
    agg["lat"] = agg["region"].map(lambda r: REGION_COORDS.get(r, (0, 0))[0])
    agg["lon"] = agg["region"].map(lambda r: REGION_COORDS.get(r, (0, 0))[1])
    return agg.sort_values("beneficiarios", ascending=False)


def pgu_por_comuna(df, region=None, periodo=None, top_n=None):
    """Agrega beneficiarios por comuna, con filtro opcional por región."""
    if df.empty:
        return pd.DataFrame()
    d = df.copy()
    if periodo:
        d = d[d["periodo"] == periodo]
    else:
        d = d[d["periodo"] == d["periodo"].max()]
    if region:
        d = d[d["region"] == str(region)]

    agg = d.groupby(["cod_comuna", "glosa_comuna", "region"]).agg(
        beneficiarios=("total_n", "sum"),
        monto_total=("total_monto", "sum"),
        hombres=("n_hombres", "sum"),
        mujeres=("n_mujeres", "sum"),
    ).reset_index()
    agg["region_nombre"] = agg["region"].map(REGIONES_CHILE).fillna("Otro")
    agg["monto_promedio"] = (agg["monto_total"] / agg["beneficiarios"].replace(0, np.nan)).round(0)
    agg["pct_mujeres"] = (100 * agg["mujeres"] / agg["beneficiarios"].replace(0, np.nan)).round(1)
    agg = agg.sort_values("beneficiarios", ascending=False)
    if top_n:
        agg = agg.head(top_n)
    return agg


def pgu_crecimiento(df):
    """Calcula tasa de crecimiento mes a mes de beneficiarios."""
    totales = pgu_totales_por_periodo(df)
    if totales.empty or len(totales) < 2:
        return pd.DataFrame()
    totales = totales.sort_values("periodo")
    totales["crecimiento"] = totales["total_beneficiarios"].pct_change() * 100
    totales["crecimiento_abs"] = totales["total_beneficiarios"].diff()
    return totales


def pgu_concentracion_regional(df, periodo=None):
    """Calcula índices de concentración regional (% del total nacional)."""
    reg = pgu_por_region(df, periodo=periodo)
    if reg.empty:
        return pd.DataFrame()
    total = reg["beneficiarios"].sum()
    reg["pct_nacional"] = (100 * reg["beneficiarios"] / total).round(2)
    reg["pct_monto_nacional"] = (100 * reg["monto_total"] / reg["monto_total"].sum()).round(2)
    return reg.sort_values("pct_nacional", ascending=False)
