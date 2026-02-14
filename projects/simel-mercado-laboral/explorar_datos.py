"""
Exploración de los datos SIMEL cargados.
Lee resultados/simel_datos.parquet (generado por cargar_datos.py), genera
estadísticas, tablas resumen y gráficos en resultados/.
"""
from pathlib import Path
import sys

RESULTADOS = Path("resultados")
PARQUET = RESULTADOS / "simel_datos.parquet"


def asegurar_resultados():
    RESULTADOS.mkdir(exist_ok=True)


def resumen_general(df):
    """Imprime y retorna resumen general del dataset."""
    print("\n" + "=" * 60)
    print("  RESUMEN GENERAL")
    print("=" * 60)
    print(f"  Total de filas:      {len(df):,}")
    print(f"  Indicadores:         {df['indicador'].nunique()}")
    print(f"  Años:                {df['fecha'].nunique()} ({sorted(df['fecha'].unique().tolist())})")
    print("=" * 60)
    return {"filas": len(df), "indicadores": df["indicador"].nunique(), "años": df["fecha"].nunique()}


def listar_indicadores(df):
    """Lista indicadores con conteo de registros."""
    print("\n--- Indicadores ---")
    conteo = df.groupby("indicador").agg(registros=("valor", "count")).sort_values("registros", ascending=False)
    for ind, row in conteo.iterrows():
        print(f"  · {ind}: {int(row['registros'])} registros")
    return conteo


def estadisticas_por_indicador(df):
    """Estadísticas descriptivas del valor por indicador."""
    print("\n--- Estadísticas por indicador (valor) ---")
    stats = df.groupby("indicador")["valor"].agg(["count", "min", "max", "mean", "std"]).round(2)
    stats = stats.fillna(0)
    print(stats.to_string())
    return stats


def desagregacion(df, columna, etiquetas=None):
    """Tabla resumen por una columna de desagregación (region, sexo, etc.)."""
    if columna not in df.columns:
        return None
    print(f"\n--- Valores por {columna} (promedio por indicador y año) ---")
    pivot = df.pivot_table(values="valor", index=columna, columns=["indicador", "fecha"], aggfunc="mean").round(2)
    print(pivot.to_string())
    return pivot


def serie_temporal_promedio(df):
    """Promedio por indicador y año (serie temporal)."""
    print("\n--- Serie temporal (promedio por indicador y año) ---")
    ser = df.groupby(["indicador", "fecha"])["valor"].mean().unstack(level=0).round(2)
    print(ser.to_string())
    return ser


def guardar_graficos(df, serie_temporal):
    """Genera y guarda gráficos en resultados/."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n(Matplotlib no instalado; omitiendo gráficos. pip install matplotlib para generarlos.)")
        return

    asegurar_resultados()
    plt.rcParams["figure.figsize"] = (10, 5)
    plt.rcParams["font.size"] = 10

    # 1) Evolución por indicador (líneas)
    fig, ax = plt.subplots(figsize=(9, 4))
    for col in serie_temporal.columns:
        ax.plot(serie_temporal.index.astype(str), serie_temporal[col], marker="o", label=col, linewidth=2)
    ax.set_xlabel("Año")
    ax.set_ylabel("Valor (%)")
    ax.set_title("Evolución de indicadores SIMEL (promedio)")
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_facecolor("#f8f9fa")
    fig.tight_layout()
    fig.savefig(RESULTADOS / "evolucion_indicadores.png", dpi=120, bbox_inches="tight")
    plt.close()
    print(f"\n  Gráfico guardado: {RESULTADOS / 'evolucion_indicadores.png'}")

    # 2) Si hay región, barras del último año por indicador y región
    if "region" in df.columns:
        ultimo_año = df["fecha"].max()
        sub = df[df["fecha"] == ultimo_año].copy()
        if len(sub) > 0:
            pivot_region = sub.pivot_table(values="valor", index="region", columns="indicador", aggfunc="mean")
            fig2, ax2 = plt.subplots(figsize=(8, 4))
            pivot_region.plot(kind="bar", ax=ax2, width=0.8)
            ax2.set_xlabel("Región")
            ax2.set_ylabel("Valor (%)")
            ax2.set_title(f"Indicadores por región ({ultimo_año})")
            ax2.legend(loc="upper right", fontsize=8)
            ax2.tick_params(axis="x", rotation=45)
            ax2.set_facecolor("#f8f9fa")
            fig2.tight_layout()
            fig2.savefig(RESULTADOS / "indicadores_por_region.png", dpi=120, bbox_inches="tight")
            plt.close()
            print(f"  Gráfico guardado: {RESULTADOS / 'indicadores_por_region.png'}")

    # 3) Si hay sexo, comparación hombre/mujer (último año)
    if "sexo" in df.columns:
        ultimo_año = df["fecha"].max()
        sub = df[(df["fecha"] == ultimo_año) & (df["sexo"].isin(["1", "2"]))].copy()
        if len(sub) > 0:
            sub["sexo_label"] = sub["sexo"].map({"1": "Hombre", "2": "Mujer"})
            pivot_sexo = sub.pivot_table(values="valor", index="indicador", columns="sexo_label", aggfunc="mean")
            fig3, ax3 = plt.subplots(figsize=(7, 4))
            pivot_sexo.plot(kind="bar", ax=ax3, width=0.7)
            ax3.set_xlabel("Indicador")
            ax3.set_ylabel("Valor (%)")
            ax3.set_title(f"Comparación por sexo ({ultimo_año})")
            ax3.legend(loc="upper right", fontsize=8)
            ax3.tick_params(axis="x", rotation=15)
            ax3.set_facecolor("#f8f9fa")
            fig3.tight_layout()
            fig3.savefig(RESULTADOS / "indicadores_por_sexo.png", dpi=120, bbox_inches="tight")
            plt.close()
            print(f"  Gráfico guardado: {RESULTADOS / 'indicadores_por_sexo.png'}")


def guardar_resumen_txt(df, stats, serie_temporal):
    """Guarda un resumen en texto en resultados/."""
    asegurar_resultados()
    out = RESULTADOS / "resumen_exploracion.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write("EXPLORACIÓN DE DATOS SIMEL\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total filas: {len(df)}\n")
        f.write(f"Indicadores: {df['indicador'].nunique()}\n")
        f.write(f"Años: {df['fecha'].unique().tolist()}\n\n")
        f.write("Estadísticas por indicador:\n")
        f.write(stats.to_string() + "\n\n")
        f.write("Serie temporal (promedio por indicador y año):\n")
        f.write(serie_temporal.to_string() + "\n")
    print(f"  Resumen guardado: {out}")


def main():
    if not PARQUET.exists():
        print("No existe resultados/simel_datos.parquet. Ejecuta antes: python cargar_datos.py")
        sys.exit(1)

    import pandas as pd

    df = pd.read_parquet(PARQUET)
    df["fecha"] = df["fecha"].astype(str)

    resumen_general(df)
    listar_indicadores(df)
    stats = estadisticas_por_indicador(df)
    serie_temporal = serie_temporal_promedio(df)

    for col in ["region", "sexo"]:
        desagregacion(df, col)

    print("\n--- Muestra (primeras 8 filas) ---")
    columnas_mostrar = [c for c in ["id", "fecha", "indicador", "valor", "region", "sexo"] if c in df.columns]
    print(df[columnas_mostrar].head(8).to_string())

    asegurar_resultados()
    guardar_resumen_txt(df, stats, serie_temporal)
    guardar_graficos(df, serie_temporal)

    print("\n" + "=" * 60)
    print("  Exploración terminada.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
