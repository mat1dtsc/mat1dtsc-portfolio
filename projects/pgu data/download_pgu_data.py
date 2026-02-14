"""
Descarga datos de Pensión Garantizada Universal (PGU) desde datos.gob.cl
y los guarda en data/pgu/ para uso en el dashboard.
"""
import os
import re
import requests
import pandas as pd
from pathlib import Path

API_BASE = "https://datos.gob.cl/api/3/action"
PGU_PACKAGE_ID = "pension-garantizada-universal"
DATA_DIR = Path(__file__).parent / "data" / "pgu"


def get_pgu_resources():
    """Obtiene lista de recursos CSV del dataset PGU."""
    url = f"{API_BASE}/package_show?id={PGU_PACKAGE_ID}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        raise RuntimeError("API no devolvió success")
    resources = data["result"].get("resources", [])
    # Solo CSV (evitar xlsx para no depender de openpyxl en descarga)
    csv_resources = [
        res for res in resources
        if (res.get("format") or "").lower() == "csv" and res.get("url")
    ]
    return csv_resources


def parse_month_year(name, url):
    """Extrae año y mes del nombre o URL del recurso."""
    # Ej: PGU_112025, Pens_Garantizada_Universal_112024, pgu_112025.csv, 112024
    name = (name or "") + " " + (url or "")
    # Patrón MMYYYY o MMAAAA (mes 1-12, año 2020-2030)
    m = re.search(r"(\d{1,2})[\-_]?(\d{4})", name)
    if m:
        mes, anio = int(m.group(1)), int(m.group(2))
        if 1 <= mes <= 12 and 2020 <= anio <= 2030:
            return anio, mes
    return None, None


def download_and_save_csv(resource, force=False):
    """Descarga un recurso CSV y lo guarda en data/pgu."""
    url = resource.get("url")
    name = resource.get("name", "pgu")
    if not url:
        return None
    anio, mes = parse_month_year(name, url)
    if anio is None:
        return None
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"pgu_{anio}_{mes:02d}.csv"
    filepath = DATA_DIR / filename
    if filepath.exists() and not force:
        return str(filepath)
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        r.encoding = "utf-8-sig"
        filepath.write_text(r.text, encoding="utf-8")
        return str(filepath)
    except Exception as e:
        print(f"Error descargando {name}: {e}")
        return None


def load_and_aggregate_pgu(data_dir=None):
    """
    Carga todos los CSV de PGU en data/pgu, normaliza columnas y devuelve
    un DataFrame agregado por periodo (año/mes) y por dimensiones (región, sexo, etc.).
    """
    data_dir = data_dir or DATA_DIR
    if not data_dir.exists():
        return pd.DataFrame()

    frames = []
    for path in sorted(Path(data_dir).glob("pgu_*.csv")):
        try:
            df = pd.read_csv(path, encoding="utf-8", sep=";", on_bad_lines="skip")
            if df.empty:
                df = pd.read_csv(path, encoding="utf-8", on_bad_lines="skip")
        except Exception:
            df = pd.read_csv(path, encoding="latin-1", on_bad_lines="skip")
        # Nombre del archivo: pgu_2024_11.csv -> año 2024, mes 11
        parts = path.stem.replace("pgu_", "").split("_")
        if len(parts) >= 2:
            anio, mes = int(parts[0]), int(parts[1])
        else:
            continue
        df["anio"] = anio
        df["mes"] = mes
        df["periodo"] = f"{anio}-{mes:02d}"
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    # Unificar columnas (pueden variar entre archivos)
    all_cols = set()
    for f in frames:
        all_cols.update(f.columns)
    common = list(all_cols & set(frames[0].columns))
    out = pd.concat([f[common + ["anio", "mes", "periodo"]] for f in frames if not f.empty], ignore_index=True)
    return out


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Descargar datos PGU desde datos.gob.cl")
    parser.add_argument("--ultimos", type=int, default=6, help="Número de meses recientes a descargar (0 = todos)")
    parser.add_argument("--force", action="store_true", help="Re-descargar aunque exista archivo")
    args = parser.parse_args()
    resources = get_pgu_resources()
    # Ordenar por nombre para tener los más recientes primero (PGU_112025, etc.)
    resources.sort(key=lambda r: (r.get("name") or ""), reverse=True)
    if args.ultimos > 0:
        resources = resources[: args.ultimos]
    print(f"Descargando {len(resources)} archivos CSV...")
    for res in resources:
        path = download_and_save_csv(res, force=args.force)
        if path:
            print(f"  OK: {path}")
    print("Listo. Ejecuta el dashboard con: streamlit run app_dashboard.py")
