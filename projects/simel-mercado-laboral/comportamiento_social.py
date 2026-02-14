"""
Análisis de comportamiento social — Chile.
Combina indicadores de mercado laboral, sociedad y economía para generar
un informe con tendencias, correlaciones y ratios relevantes en sociología y economía.
"""
from pathlib import Path
from datetime import date

import pandas as pd

RESULTADOS = Path("resultados")
PARQUET = RESULTADOS / "simel_datos.parquet"
RATIOS_CSV = RESULTADOS / "ratios_sociales.csv"
INFORME = RESULTADOS / "informe_comportamiento_social.txt"
INFORME_JSON = RESULTADOS / "informe_resumen.json"


def _get_serie(df: pd.DataFrame, nombre_parcial: str) -> pd.Series | None:
    for col in df.columns:
        if nombre_parcial.lower() in str(col).lower():
            return df[col]
    return None


def main():
    RESULTADOS.mkdir(exist_ok=True)
    if not PARQUET.exists():
        print("Ejecuta antes: python cargar_datos.py")
        return

    df = pd.read_parquet(PARQUET)
    df["fecha"] = df["fecha"].astype(str)
    pivot = df.pivot_table(index="fecha", columns="indicador", values="valor", aggfunc="mean")

    lineas = [
        "=" * 60,
        "  INFORME DE COMPORTAMIENTO SOCIAL — CHILE",
        f"  Generado: {date.today().isoformat()}",
        "=" * 60,
        "",
    ]

    # 1) Tendencias recientes (últimos 5 años)
    años = sorted(pivot.index.astype(int), reverse=True)[:5]
    pivot_reciente = pivot[pivot.index.astype(str).isin(map(str, años))]
    if not pivot_reciente.empty:
        lineas.append("--- Tendencias recientes (últimos años) ---")
        desemp = _get_serie(pivot_reciente, "Tasa de desempleo (%")
        if desemp is not None:
            desemp = desemp.sort_index(ascending=False)
            lineas.append(f"  Desempleo total: {desemp.iloc[0]:.1f}% (mas reciente) -> {desemp.iloc[-1]:.1f}% (5 anos atras)")
        act_f = _get_serie(pivot_reciente, "actividad femenina")
        act_m = _get_serie(pivot_reciente, "actividad masculina")
        if act_f is not None and act_m is not None:
            brecha_ahora = (act_m - act_f).dropna()
            if len(brecha_ahora):
                lineas.append(f"  Brecha actividad genero (M-F): {brecha_ahora.iloc[0]:.1f} pp (ano mas reciente)")
        gini = _get_serie(pivot_reciente, "Gini")
        if gini is not None:
            gini = gini.dropna()
            if len(gini):
                lineas.append(f"  Indice Gini (desigualdad): {gini.iloc[0]:.1f} (ano mas reciente)")
        lineas.append("")

    # 2) Correlaciones economía–sociedad (si hay suficientes años)
    gini = _get_serie(pivot, "Gini")
    pib = _get_serie(pivot, "PIB per cápita")
    if gini is not None and pib is not None:
        valid = gini.notna() & pib.notna()
        if valid.sum() >= 3:
            corr = gini[valid].astype(float).corr(pib[valid].astype(float))
            lineas.append("--- Correlación PIB per cápita vs Gini ---")
            lineas.append(f"  Correlación (Pearson): {corr:.3f}")
            lineas.append("  (Valor negativo: a mas PIB pc, menor desigualdad en la serie)")
            lineas.append("")

    # 3) Desempleo juvenil vs total (vulnerabilidad)
    joven = _get_serie(pivot, "desempleo juvenil")
    total = _get_serie(pivot, "Tasa de desempleo (%")
    if joven is not None and total is not None:
        ratio = (joven / total.replace(0, float("nan"))).dropna()
        if len(ratio):
            lineas.append("--- Ratio desempleo juvenil / total ---")
            lineas.append(f"  Promedio ratio: {ratio.mean():2f} (juveniles sufren ~{ratio.mean():.1f}x mas desempleo)")
            lineas.append("")

    # 4) Resumen de ratios guardados
    if RATIOS_CSV.exists():
        rdf = pd.read_csv(RATIOS_CSV)
        lineas.append("--- Ratios calculados (ver ratios_sociales.csv) ---")
        for r in rdf["ratio"].unique():
            sub = rdf[rdf["ratio"] == r]
            if len(sub):
                v = sub["valor"].dropna()
                if len(v):
                    lineas.append(f"  {r}: min={v.min():.2f}, max={v.max():.2f}, ultimo={v.iloc[-1]:.2f}")
        lineas.append("")

    lineas.extend([
        "=" * 60,
        "  Fuentes: Banco Mundial (Chile), SIMEL/INE. Uso educativo.",
        "=" * 60,
    ])

    texto = "\n".join(lineas)
    with open(INFORME, "w", encoding="utf-8") as f:
        f.write(texto)
    print(texto)
    print(f"\nInforme guardado: {INFORME}")

    # JSON para la app/demo (gráficos y análisis)
    import json
    resumen_json = {
        "fecha_generado": date.today().isoformat(),
        "tendencias": [],
        "correlacion_pib_gini": None,
        "ratio_desempleo_juvenil_promedio": None,
        "resumen_ratios": [],
    }
    if not pivot_reciente.empty:
        if desemp is not None and len(desemp):
            resumen_json["tendencias"].append({
                "indicador": "Desempleo total",
                "actual": round(float(desemp.iloc[0]), 2),
                "hace_5_anos": round(float(desemp.iloc[-1]), 2),
                "unidad": "%",
            })
        if act_f is not None and act_m is not None:
            brecha_ahora = (act_m - act_f).dropna()
            if len(brecha_ahora):
                resumen_json["tendencias"].append({
                    "indicador": "Brecha actividad genero (M-F)",
                    "actual": round(float(brecha_ahora.iloc[0]), 2),
                    "unidad": "pp",
                })
        if gini is not None:
            gini_ = gini.dropna()
            if len(gini_):
                resumen_json["tendencias"].append({
                    "indicador": "Indice Gini",
                    "actual": round(float(gini_.iloc[0]), 2),
                    "unidad": "",
                })
    if gini is not None and pib is not None:
        valid = gini.notna() & pib.notna()
        if valid.sum() >= 3:
            resumen_json["correlacion_pib_gini"] = round(
                float(gini[valid].astype(float).corr(pib[valid].astype(float))), 3
            )
    if joven is not None and total is not None:
        ratio = (joven / total.replace(0, float("nan"))).dropna()
        if len(ratio):
            resumen_json["ratio_desempleo_juvenil_promedio"] = round(float(ratio.mean()), 2)
    if RATIOS_CSV.exists():
        rdf = pd.read_csv(RATIOS_CSV)
        for r in rdf["ratio"].unique():
            sub = rdf[rdf["ratio"] == r]
            v = sub["valor"].dropna()
            if len(v):
                resumen_json["resumen_ratios"].append({
                    "ratio": r,
                    "min": round(float(v.min()), 2),
                    "max": round(float(v.max()), 2),
                    "ultimo": round(float(v.iloc[-1]), 2),
                })
    with open(INFORME_JSON, "w", encoding="utf-8") as f:
        json.dump(resumen_json, f, ensure_ascii=False, indent=2)
    print(f"Resumen JSON para app: {INFORME_JSON}")


if __name__ == "__main__":
    main()
