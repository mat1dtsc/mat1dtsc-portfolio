"""
Calcula ratios de interés para sociedad, sociología y economía (Chile).
Usa resultados/simel_datos.parquet (generado por cargar_datos.py).
Guarda resultados/ratios_sociales.csv y resultados/ratios_sociales.json.

Contexto de año: toda la lógica usa el año en que se ejecuta el script.
Las series se expanden hasta ese año con el último valor conocido.
Al ejecutar en el próximo año (ej. 2027), las series se expandirán hasta 2027
sin cambiar código — solo vuelve a correr el pipeline.
"""
import json
from pathlib import Path

import pandas as pd

from contexto_anio import ANIO_ACTUAL, ANIO_HASTA_EXPANDIR, obtener_contexto

RESULTADOS = Path("resultados")
PARQUET = RESULTADOS / "simel_datos.parquet"
CONTEXTO_ANIO = obtener_contexto()


def _pivot_anual(df: pd.DataFrame) -> pd.DataFrame:
    """Pivote por año: cada indicador es una columna."""
    if "indicador" not in df.columns or "fecha" not in df.columns or "valor" not in df.columns:
        return pd.DataFrame()
    return df.pivot_table(index="fecha", columns="indicador", values="valor", aggfunc="mean").reset_index()


def _get_serie(df: pd.DataFrame, nombre_parcial: str) -> pd.Series | None:
    """Obtiene la columna que contiene nombre_parcial en el nombre del indicador."""
    for col in df.columns:
        if nombre_parcial.lower() in str(col).lower():
            return df[col]
    return None


def main():
    RESULTADOS.mkdir(exist_ok=True)
    if not PARQUET.exists():
        print("No existe resultados/simel_datos.parquet. Ejecuta antes: python cargar_datos.py")
        return

    df = pd.read_parquet(PARQUET)
    df["fecha"] = df["fecha"].astype(str)
    pivot = _pivot_anual(df)
    if pivot.empty:
        print("No hay datos para calcular ratios.")
        return

    años = pivot["fecha"].astype(int)
    ratios_list = []

    # 1) Brecha de género en actividad laboral (masculina - femenina), en pp
    act_m = _get_serie(pivot, "actividad masculina")
    act_f = _get_serie(pivot, "actividad femenina")
    if act_m is not None and act_f is not None:
        brecha = (act_m - act_f).round(2)
        for i, anio in enumerate(pivot["fecha"]):
            if pd.notna(brecha.iloc[i]):
                ratios_list.append({
                    "fecha": anio,
                    "ratio": "Brecha actividad genero (M-F, pp)",
                    "valor": float(brecha.iloc[i]),
                })
        # Ratio actividad F/M
        ratio_fm = (act_f / act_m.replace(0, float("nan"))).round(4)
        for i, anio in enumerate(pivot["fecha"]):
            if pd.notna(ratio_fm.iloc[i]):
                ratios_list.append({
                    "fecha": anio,
                    "ratio": "Ratio actividad F/M",
                    "valor": float(ratio_fm.iloc[i]),
                })

    # 2) Ratio desempleo juvenil / desempleo total (vulnerabilidad juvenil)
    desemp_joven = _get_serie(pivot, "desempleo juvenil")
    desemp_total = _get_serie(pivot, "Tasa de desempleo (%")
    if desemp_joven is not None and desemp_total is not None:
        ratio_joven = (desemp_joven / desemp_total.replace(0, float("nan"))).round(2)
        for i, anio in enumerate(pivot["fecha"]):
            if pd.notna(ratio_joven.iloc[i]):
                ratios_list.append({
                    "fecha": anio,
                    "ratio": "Ratio desempleo juvenil/total",
                    "valor": float(ratio_joven.iloc[i]),
                })

    # 3) PIB per cápita (miles USD) — solo reetiquetar para el informe
    pib = _get_serie(pivot, "PIB per cápita")
    if pib is not None:
        pib_miles = (pib / 1000).round(2)
        for i, anio in enumerate(pivot["fecha"]):
            if pd.notna(pib_miles.iloc[i]):
                ratios_list.append({
                    "fecha": anio,
                    "ratio": "PIB per cápita (miles USD 2015)",
                    "valor": float(pib_miles.iloc[i]),
                })

    # 4) Índice Gini — desigualdad (ya está en los datos; lo incluimos en ratios para la demo)
    gini = _get_serie(pivot, "Gini")
    if gini is not None:
        for i, anio in enumerate(pivot["fecha"]):
            if pd.notna(gini.iloc[i]):
                ratios_list.append({
                    "fecha": anio,
                    "ratio": "Índice Gini (desigualdad)",
                    "valor": float(round(gini.iloc[i], 2)),
                })

    if not ratios_list:
        print("No se pudieron calcular ratios con los indicadores actuales.")
        print("Asegúrate de haber ejecutado obtener_mercado_actual.py y cargar_datos.py.")
        return

    # Guardar CSV (formato largo: fecha, ratio, valor)
    rdf = pd.DataFrame(ratios_list)
    csv_path = RESULTADOS / "ratios_sociales.csv"
    rdf.to_csv(csv_path, index=False)
    print(f"Guardado: {csv_path}")

    # Construir series por ratio
    por_ratio = {}
    for _, row in rdf.iterrows():
        r = row["ratio"]
        if r not in por_ratio:
            por_ratio[r] = []
        por_ratio[r].append({"fecha": str(row["fecha"]), "valor": row["valor"]})

    # Ordenar por año y extender hasta año actual (último valor conocido) para datos "a la realidad"
    anos_en_datos = set()
    for nombre in list(por_ratio.keys()):
        serie = por_ratio[nombre]
        if not serie:
            continue
        serie = sorted(serie, key=lambda x: int(x["fecha"]))
        por_ratio[nombre] = serie
        anos = [int(p["fecha"]) for p in serie]
        anos_en_datos.update(anos)
        ultimo_valor = serie[-1]["valor"]
        ultimo_ano = max(anos)
        # Expandir hasta el año en contexto (siempre puede crecer al siguiente año al re-ejecutar)
        for anio in range(ultimo_ano + 1, ANIO_HASTA_EXPANDIR + 1):
            por_ratio[nombre].append({"fecha": str(anio), "valor": ultimo_valor})
        por_ratio[nombre] = sorted(por_ratio[nombre], key=lambda x: int(x["fecha"]))

    # Metadatos: contexto de año y rango para la demo
    ano_min = min(anos_en_datos) if anos_en_datos else None
    ano_max = max(anos_en_datos) if anos_en_datos else None
    payload = {
        "ratios": por_ratio,
        "resumen": list(por_ratio.keys()),
        "meta": {
            "contexto_anio": {
                "anio_actual": ANIO_ACTUAL,
                "anio_hasta_expandir": ANIO_HASTA_EXPANDIR,
                "descripcion": "Series extendidas hasta este ano. Al ejecutar el script el proximo ano, se expandiran automaticamente.",
            },
            "ano_minimo_datos": ano_min,
            "ano_maximo_datos_reales": ano_max,
            "actualizado_hasta_ano": ANIO_HASTA_EXPANDIR,
            "nota": "Series extendidas hasta el ano actual con ultimo valor conocido cuando la fuente no publica todos los anos (ej. Gini bienal).",
        },
    }
    json_path = RESULTADOS / "ratios_sociales.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Guardado: {json_path}")
    print("Ratios calculados:", ", ".join(por_ratio.keys()))
    print(f"  Contexto ano: {ANIO_ACTUAL} | Rango en datos: {ano_min}-{ano_max} | Extendido hasta: {ANIO_HASTA_EXPANDIR}")


if __name__ == "__main__":
    main()
