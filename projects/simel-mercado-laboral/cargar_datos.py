"""
Carga CSVs de datos SIMEL (o de ejemplo), limpia y exporta Parquet + JSON para demo.
Equivalente en Python a cargar_datos.R del repo original.
"""
import os
import json
import pandas as pd
from pathlib import Path

DATOS_DIR = Path("datos")
RESULTADOS_DIR = Path("resultados")
RESULTADOS_DIR.mkdir(exist_ok=True)

def main():
    archivos = list(DATOS_DIR.rglob("*.csv"))
    if not archivos:
        print("No hay CSVs en datos/. Ejecuta primero: python generar_datos_ejemplo.py")
        return

    dfs = []
    for path in archivos:
        df = pd.read_csv(path)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        if "obs_value" in df.columns:
            df = df.rename(columns={"obs_value": "valor"})
        if "time_period" in df.columns:
            df = df.rename(columns={"time_period": "fecha"})
        if "area_ref" in df.columns:
            df = df.rename(columns={"area_ref": "region"})
        if "region" not in df.columns:
            df["region"] = "_T"
        df["id"] = path.stem
        dfs.append(df)

    simel = pd.concat(dfs, ignore_index=True)
    simel["fecha"] = simel["fecha"].astype(str)

    # Exportar Parquet
    out_parquet = RESULTADOS_DIR / "simel_datos.parquet"
    simel.to_parquet(out_parquet, index=False)
    print(f"Guardado: {out_parquet}")

    # Exportar JSON para la demo (agregado por indicador y año)
    agg = simel.groupby(["indicador", "fecha"], as_index=False).agg(
        valor=("valor", "mean"),
        registros=("valor", "count")
    ).round(2)
    sample = {
        "indicadores": agg["indicador"].unique().tolist(),
        "por_indicador_año": agg.to_dict(orient="records"),
        "resumen": {"total_filas": int(len(simel)), "indicadores": int(simel["indicador"].nunique())}
    }
    out_json = RESULTADOS_DIR / "sample.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)
    print(f"Guardado: {out_json}")

    # --- Exportar CSV para Kepler.gl (solo regiones) ---
    # Filtrar solo datos regionales (excluir _T o tot)
    # Asumimos que region != "_T" son las regiones
    regional = simel[simel["region"] != "_T"].copy()
    
    # Mapeo simple de codigos si es necesario. 
    # El GeoJSON usa codregion (int): 1, 2, ... 15.
    # Tus datos CSV usan '01', '02', '13', etc.
    # Vamos a crear una columna 'codregion' entero para el join en Kepler
    try:
        regional["codregion"] = regional["region"].astype(int)
    except:
        regional["codregion"] = 0 # Fallback
        
    # Seleccionar columnas relevantes para el mapa
    cols_mapa = ["codregion", "region", "fecha", "indicador", "valor"]
    out_csv_map = RESULTADOS_DIR / "simel_regional.csv"
    regional[cols_mapa].to_csv(out_csv_map, index=False)
    print(f"Guardado: {out_csv_map} (para Kepler.gl)")

if __name__ == "__main__":
    main()
