"""
Dashboard interactivo: análisis estadístico de la Pensión Garantizada Universal (PGU) en Chile.
Datos: datos.gob.cl (IPS) y población 65+ (INE).
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pydeck as pdk

# Kepler.gl (opcional - pesado pero potente)
try:
    from keplergl import KeplerGl
    from streamlit_keplergl import keplergl_static
    HAS_KEPLER = True
except ImportError:
    HAS_KEPLER = False

from data_loader import (
    load_poblacion_65_mas,
    load_all_pgu,
    pgu_totales_por_periodo,
    pgu_por_region,
    pgu_por_comuna,
    pgu_crecimiento,
    pgu_concentracion_regional,
    REGIONES_CHILE,
    REGION_COORDS,
    DATA_PGU_DIR,
)

# ── Configuración de colores ──────────────────────────────────────
COLORS = {
    "primary": "#1f77b4",
    "secondary": "#ff7f0e",
    "success": "#2ca02c",
    "danger": "#d62728",
    "purple": "#9467bd",
    "pink": "#e377c2",
    "teal": "#17becf",
    "gray": "#7f7f7f",
    "hombres": "#4e79a7",
    "mujeres": "#e15759",
}
REGION_COLORS = px.colors.qualitative.Set3


def format_clp(val):
    """Formato CLP con separador de miles."""
    if pd.isna(val) or val == 0:
        return "—"
    return f"${int(val):,}".replace(",", ".")


def format_num(val):
    if pd.isna(val):
        return "—"
    return f"{int(val):,}".replace(",", ".")


def main():
    st.set_page_config(
        page_title="PGU Chile – Dashboard Estadístico",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # CSS personalizado
    st.markdown("""
    <style>
    .main .block-container { padding-top: 1rem; max-width: 1200px; }
    div[data-testid="stMetricValue"] { font-size: 1.3rem; }
    div[data-testid="stMetricDelta"] { font-size: 0.9rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 8px 16px; }
    </style>
    """, unsafe_allow_html=True)

    st.title("📊 Pensión Garantizada Universal (PGU)")
    st.caption(
        "Análisis estadístico de beneficiarios PGU en Chile · "
        "Fuentes: Instituto de Previsión Social (IPS) · Instituto Nacional de Estadísticas (INE)"
    )

    # ── Cargar datos ────────────────────────────────────────────
    df_pgu = load_all_pgu()
    df_pob = load_poblacion_65_mas()

    if df_pgu.empty:
        st.error(
            "No hay datos PGU. Ejecuta `python download_pgu_data.py --ultimos 12` "
            "para descargar datos desde datos.gob.cl"
        )
        st.stop()

    totales = pgu_totales_por_periodo(df_pgu)
    periodos = sorted(df_pgu["periodo"].unique())

    # ── Sidebar ─────────────────────────────────────────────────
    with st.sidebar:
        st.header("⚙️ Filtros")
        periodo_sel = st.selectbox("Periodo", periodos, index=len(periodos) - 1)
        region_sel = st.selectbox(
            "Región",
            ["Todas"] + [f"{k} - {v}" for k, v in sorted(REGIONES_CHILE.items(), key=lambda x: int(x[0]))],
        )
        region_code = None
        if region_sel != "Todas":
            region_code = region_sel.split(" - ")[0]

        st.markdown("---")
        st.markdown(
            "**Fuentes de datos**\n\n"
            "- [PGU – datos.gob.cl](https://datos.gob.cl/dataset/pension-garantizada-universal)\n"
            "- Población 65+ – INE Chile\n\n"
            f"📅 Periodos: {periodos[0]} a {periodos[-1]}\n\n"
            f"📍 {df_pgu['cod_comuna'].nunique()} comunas · 16 regiones"
        )

    # ── KPIs principales ────────────────────────────────────────
    ultimo = totales[totales["periodo"] == periodo_sel]
    if ultimo.empty:
        ultimo = totales.iloc[[-1]]
    u = ultimo.iloc[0]

    st.subheader(f"Indicadores · {periodo_sel}")
    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        delta = None
        if len(totales) > 1:
            idx = totales[totales["periodo"] == periodo_sel].index
            if len(idx) > 0 and idx[0] > totales.index[0]:
                prev = totales.iloc[list(totales.index).index(idx[0]) - 1]
                diff = int(u["total_beneficiarios"] - prev["total_beneficiarios"])
                delta = f"{diff:+,}".replace(",", ".")
        st.metric("Total Beneficiarios", format_num(u["total_beneficiarios"]), delta=delta)

    with k2:
        # Cobertura
        if not df_pob.empty:
            pob_t = df_pob[df_pob["sexo"] == "_T"]
            pob_anio = pob_t[pob_t["anio"] == int(u["anio"])]
            if not pob_anio.empty:
                pob_val = pob_anio["poblacion"].iloc[0]
                cob = 100 * u["total_beneficiarios"] / pob_val
                st.metric("Cobertura 65+", f"{cob:.1f}%", delta=f"{pob_val:,.0f} pob. 65+".replace(",", "."))
            else:
                st.metric("Cobertura 65+", "—")
        else:
            st.metric("Cobertura 65+", "—")

    with k3:
        monto_miles = u["total_monto"]
        st.metric("Gasto Total (M$)", f"${format_num(monto_miles)}")

    with k4:
        st.metric("Monto Promedio (M$/benef.)", f"${int(u['monto_promedio']):,}".replace(",", "."))

    with k5:
        st.metric("% Mujeres", f"{u['pct_mujeres']}%",
                  delta=f"{format_num(u['mujeres'])} mujeres")

    st.markdown("---")

    # ── Tabs principales ────────────────────────────────────────
    tab_evol, tab_region, tab_mapa, tab_comuna, tab_sexo, tab_datos = st.tabs([
        "📈 Evolución", "🏛️ Regiones", "🗺️ Mapa", "🏘️ Comunas", "👫 Género", "📋 Datos"
    ])

    # ────────────────────────────────────────────────────────────
    # TAB: Evolución temporal
    # ────────────────────────────────────────────────────────────
    with tab_evol:
        st.subheader("Evolución de beneficiarios PGU")

        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=totales["periodo"], y=totales["total_beneficiarios"],
                mode="lines+markers+text",
                text=[format_num(v) for v in totales["total_beneficiarios"]],
                textposition="top center",
                line=dict(color=COLORS["primary"], width=3),
                marker=dict(size=10),
                name="Beneficiarios",
            ))
            fig.update_layout(
                title="Total beneficiarios por mes",
                xaxis_title="Periodo", yaxis_title="Beneficiarios",
                height=400, showlegend=False,
                yaxis=dict(tickformat=","),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=totales["periodo"], y=totales["total_monto"],
                text=[f"${format_num(v)}" for v in totales["total_monto"]],
                textposition="outside",
                marker_color=COLORS["success"],
                name="Gasto total M$",
            ))
            fig.update_layout(
                title="Gasto total mensual (miles de $)",
                xaxis_title="Periodo", yaxis_title="Monto M$",
                height=400, showlegend=False,
                yaxis=dict(tickformat=","),
            )
            st.plotly_chart(fig, use_container_width=True)

        # Crecimiento
        crec = pgu_crecimiento(df_pgu)
        if not crec.empty and len(crec) > 1:
            col3, col4 = st.columns(2)
            with col3:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=crec["periodo"].iloc[1:], y=crec["crecimiento_abs"].iloc[1:],
                    text=[format_num(v) for v in crec["crecimiento_abs"].iloc[1:]],
                    textposition="outside",
                    marker_color=COLORS["teal"],
                ))
                fig.update_layout(
                    title="Crecimiento absoluto mes a mes",
                    xaxis_title="Periodo", yaxis_title="Nuevos beneficiarios",
                    height=350, showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)

            with col4:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=crec["periodo"].iloc[1:], y=crec["crecimiento"].iloc[1:],
                    text=[f"{v:.2f}%" for v in crec["crecimiento"].iloc[1:]],
                    textposition="outside",
                    marker_color=COLORS["secondary"],
                ))
                fig.update_layout(
                    title="Tasa de crecimiento mensual (%)",
                    xaxis_title="Periodo", yaxis_title="Crecimiento %",
                    height=350, showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)

    # ────────────────────────────────────────────────────────────
    # TAB: Regiones
    # ────────────────────────────────────────────────────────────
    with tab_region:
        st.subheader(f"Distribución regional · {periodo_sel}")
        reg = pgu_por_region(df_pgu, periodo=periodo_sel)
        if reg.empty:
            st.warning("No hay datos para este periodo.")
        else:
            conc = pgu_concentracion_regional(df_pgu, periodo=periodo_sel)

            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(
                    reg.sort_values("beneficiarios", ascending=True),
                    y="region_nombre", x="beneficiarios",
                    orientation="h",
                    title="Beneficiarios por región",
                    text="beneficiarios",
                    color="beneficiarios",
                    color_continuous_scale="Blues",
                )
                fig.update_traces(texttemplate="%{text:,}", textposition="outside")
                fig.update_layout(height=550, showlegend=False, coloraxis_showscale=False,
                                 yaxis_title="", xaxis_title="Beneficiarios")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.pie(
                    conc.head(10),
                    values="pct_nacional", names="region_nombre",
                    title="Concentración regional (% del total)",
                    hole=0.4,
                    color_discrete_sequence=REGION_COLORS,
                )
                fig.update_traces(textposition="inside", textinfo="label+percent")
                fig.update_layout(height=550)
                st.plotly_chart(fig, use_container_width=True)

            # Tabla comparativa
            st.subheader("Tabla comparativa regional")
            tabla_reg = reg[["region_nombre", "beneficiarios", "monto_total", "monto_promedio",
                            "hombres", "mujeres", "pct_mujeres", "n_comunas"]].copy()
            tabla_reg.columns = ["Región", "Beneficiarios", "Monto Total M$", "Monto Prom.",
                                "Hombres", "Mujeres", "% Mujeres", "Comunas"]
            st.dataframe(
                tabla_reg.style.format({
                    "Beneficiarios": "{:,.0f}",
                    "Monto Total M$": "${:,.0f}",
                    "Monto Prom.": "${:,.0f}",
                    "Hombres": "{:,.0f}",
                    "Mujeres": "{:,.0f}",
                    "% Mujeres": "{:.1f}%",
                    "Comunas": "{:,.0f}",
                }),
                use_container_width=True, height=600,
            )

    # ────────────────────────────────────────────────────────────
    # TAB: Mapa
    # ────────────────────────────────────────────────────────────
    with tab_mapa:
        st.subheader(f"Mapa de beneficiarios PGU · {periodo_sel}")
        reg_map = pgu_por_region(df_pgu, periodo=periodo_sel)
        comunas_map = pgu_por_comuna(df_pgu, periodo=periodo_sel)

        if not reg_map.empty:
            # Selector de vista
            opciones_mapa = ["Regiones (columnas 3D)", "Comunas (dispersión)", "Regiones (burbujas)"]
            if HAS_KEPLER:
                opciones_mapa.insert(0, "Kepler.gl (interactivo)")
            vista_mapa = st.radio(
                "Vista del mapa",
                opciones_mapa,
                horizontal=True,
            )

            if HAS_KEPLER and vista_mapa == "Kepler.gl (interactivo)":
                # ── Kepler.gl: mapa interactivo completo ───────
                st.markdown("**Mapa interactivo Kepler.gl** — rotá, hacé zoom, filtrá datos directo en el mapa")

                # Datos de comunas con coordenadas aproximadas
                kp_data = comunas_map.copy()
                kp_data["lat"] = kp_data["region"].map(
                    lambda r: REGION_COORDS.get(r, (-33.45, -70.67))[0]
                )
                kp_data["lon"] = kp_data["region"].map(
                    lambda r: REGION_COORDS.get(r, (-33.45, -70.67))[1]
                )
                np.random.seed(42)
                kp_data["lat"] = kp_data["lat"] + np.random.uniform(-0.3, 0.3, len(kp_data))
                kp_data["lon"] = kp_data["lon"] + np.random.uniform(-0.3, 0.3, len(kp_data))

                kepler_df = kp_data[[
                    "glosa_comuna", "region_nombre", "beneficiarios",
                    "monto_total", "monto_promedio", "hombres", "mujeres",
                    "pct_mujeres", "lat", "lon"
                ]].rename(columns={
                    "glosa_comuna": "Comuna",
                    "region_nombre": "Region",
                    "beneficiarios": "Beneficiarios",
                    "monto_total": "Monto_Total_M",
                    "monto_promedio": "Monto_Promedio",
                    "hombres": "Hombres",
                    "mujeres": "Mujeres",
                    "pct_mujeres": "Pct_Mujeres",
                })

                kepler_reg = reg_map[[
                    "region_nombre", "beneficiarios", "monto_total",
                    "monto_promedio", "pct_mujeres", "lat", "lon"
                ]].rename(columns={
                    "region_nombre": "Region",
                    "beneficiarios": "Beneficiarios",
                    "monto_total": "Monto_Total_M",
                    "monto_promedio": "Monto_Promedio",
                    "pct_mujeres": "Pct_Mujeres",
                })

                kepler_config = {
                    "version": "v1",
                    "config": {
                        "mapState": {
                            "bearing": 0,
                            "latitude": -35.5,
                            "longitude": -71.5,
                            "pitch": 45,
                            "zoom": 4.5,
                        },
                        "mapStyle": {
                            "styleType": "dark",
                        },
                    },
                }

                map_kgl = KeplerGl(height=650, config=kepler_config)
                map_kgl.add_data(data=kepler_reg, name="regiones_pgu")
                map_kgl.add_data(data=kepler_df, name="comunas_pgu")
                keplergl_static(map_kgl, center_map=True, height=650)

                st.caption(
                    "Activa/desactiva capas desde el panel lateral de Kepler.gl. "
                    "Podés cambiar colores, filtrar, agrupar y más."
                )

            elif vista_mapa == "Regiones (columnas 3D)":
                # ── Pydeck: Columnas 3D por región ─────────────
                max_ben = reg_map["beneficiarios"].max()
                reg_deck = reg_map.copy()
                reg_deck["elevation"] = (reg_deck["beneficiarios"] / max_ben * 200000).astype(int)
                reg_deck["color_r"] = (reg_deck["beneficiarios"] / max_ben * 220 + 35).astype(int).clip(0, 255)
                reg_deck["color_g"] = (80 - reg_deck["beneficiarios"] / max_ben * 60).astype(int).clip(0, 255)
                reg_deck["color_b"] = (30).astype(int)

                layer_col = pdk.Layer(
                    "ColumnLayer",
                    data=reg_deck,
                    get_position=["lon", "lat"],
                    get_elevation="elevation",
                    elevation_scale=1,
                    radius=25000,
                    get_fill_color=["color_r", "color_g", "color_b", 200],
                    pickable=True,
                    auto_highlight=True,
                )
                view = pdk.ViewState(
                    latitude=-35.5, longitude=-71.0,
                    zoom=4, pitch=50, bearing=-10,
                )
                tooltip = {
                    "html": "<b>{region_nombre}</b><br/>"
                            "Beneficiarios: {beneficiarios}<br/>"
                            "Monto prom: ${monto_promedio} M$<br/>"
                            "% Mujeres: {pct_mujeres}%",
                    "style": {"backgroundColor": "#1a1a2e", "color": "white",
                              "fontSize": "13px", "padding": "8px"},
                }
                st.pydeck_chart(pdk.Deck(
                    layers=[layer_col],
                    initial_view_state=view,
                    tooltip=tooltip,
                    map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
                ), height=650)

            elif vista_mapa == "Comunas (dispersión)":
                # ── Pydeck: Scatterplot por comuna ─────────────
                com_deck = comunas_map.copy()
                com_deck["lat"] = com_deck["region"].map(
                    lambda r: REGION_COORDS.get(r, (-33.45, -70.67))[0]
                )
                com_deck["lon"] = com_deck["region"].map(
                    lambda r: REGION_COORDS.get(r, (-33.45, -70.67))[1]
                )
                np.random.seed(42)
                com_deck["lat"] = com_deck["lat"] + np.random.uniform(-0.35, 0.35, len(com_deck))
                com_deck["lon"] = com_deck["lon"] + np.random.uniform(-0.35, 0.35, len(com_deck))

                max_ben_c = com_deck["beneficiarios"].max()
                com_deck["radius"] = (com_deck["beneficiarios"] / max_ben_c * 15000 + 2000).astype(int)
                com_deck["color_r"] = (com_deck["beneficiarios"] / max_ben_c * 200 + 55).astype(int).clip(0, 255)
                com_deck["color_g"] = (100 - com_deck["beneficiarios"] / max_ben_c * 70).astype(int).clip(0, 255)
                com_deck["color_b"] = (200 - com_deck["beneficiarios"] / max_ben_c * 150).astype(int).clip(0, 255)

                layer_scatter = pdk.Layer(
                    "ScatterplotLayer",
                    data=com_deck,
                    get_position=["lon", "lat"],
                    get_radius="radius",
                    get_fill_color=["color_r", "color_g", "color_b", 180],
                    pickable=True,
                    auto_highlight=True,
                )
                view = pdk.ViewState(
                    latitude=-35.5, longitude=-71.0,
                    zoom=4, pitch=30, bearing=0,
                )
                tooltip = {
                    "html": "<b>{glosa_comuna}</b> ({region_nombre})<br/>"
                            "Beneficiarios: {beneficiarios}<br/>"
                            "Monto prom: ${monto_promedio} M$<br/>"
                            "% Mujeres: {pct_mujeres}%",
                    "style": {"backgroundColor": "#1a1a2e", "color": "white",
                              "fontSize": "13px", "padding": "8px"},
                }
                st.pydeck_chart(pdk.Deck(
                    layers=[layer_scatter],
                    initial_view_state=view,
                    tooltip=tooltip,
                    map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
                ), height=650)

            else:
                # ── Plotly Scattergeo (burbujas) ───────────────
                fig = go.Figure()
                max_ben = reg_map["beneficiarios"].max()
                for _, row in reg_map.iterrows():
                    size = max(8, 60 * (row["beneficiarios"] / max_ben))
                    fig.add_trace(go.Scattergeo(
                        lat=[row["lat"]],
                        lon=[row["lon"]],
                        text=f"<b>{row['region_nombre']}</b><br>"
                             f"Beneficiarios: {format_num(row['beneficiarios'])}<br>"
                             f"Monto prom: ${int(row['monto_promedio']):,}<br>"
                             f"% Mujeres: {row['pct_mujeres']}%",
                        hoverinfo="text",
                        marker=dict(
                            size=size,
                            color=row["beneficiarios"],
                            colorscale="YlOrRd",
                            cmin=reg_map["beneficiarios"].min(),
                            cmax=max_ben,
                            opacity=0.75,
                            line=dict(width=1, color="white"),
                        ),
                        showlegend=False,
                    ))
                fig.update_geos(
                    scope="south america",
                    center=dict(lat=-35, lon=-71),
                    projection_scale=4.5,
                    showland=True, landcolor="rgb(243, 243, 243)",
                    showocean=True, oceancolor="rgb(204, 224, 245)",
                    showcountries=True, countrycolor="rgb(180, 180, 180)",
                    showcoastlines=True, coastlinecolor="rgb(180, 180, 180)",
                    lonaxis=dict(range=[-76, -66]),
                    lataxis=dict(range=[-56, -17]),
                )
                fig.update_layout(
                    height=700,
                    title="Distribución geográfica de beneficiarios PGU",
                    margin=dict(l=0, r=0, t=40, b=0),
                )
                st.plotly_chart(fig, use_container_width=True)

            st.caption("💡 Podés rotar el mapa 3D arrastrando con click derecho, y hacer zoom con la rueda del mouse.")

            # ── Gráficos complementarios (siempre visibles) ────
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(
                    reg_map.sort_values("monto_promedio", ascending=True),
                    y="region_nombre", x="monto_promedio",
                    orientation="h",
                    title="Monto promedio por beneficiario (M$) por región",
                    text="monto_promedio",
                    color="monto_promedio",
                    color_continuous_scale="Greens",
                )
                fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
                fig.update_layout(height=500, showlegend=False, coloraxis_showscale=False,
                                 yaxis_title="", xaxis_title="Monto promedio M$")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.bar(
                    reg_map.sort_values("pct_mujeres", ascending=True),
                    y="region_nombre", x="pct_mujeres",
                    orientation="h",
                    title="Porcentaje de mujeres beneficiarias por región",
                    text="pct_mujeres",
                    color="pct_mujeres",
                    color_continuous_scale="RdPu",
                )
                fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                fig.update_layout(height=500, showlegend=False, coloraxis_showscale=False,
                                 yaxis_title="", xaxis_title="% Mujeres")
                st.plotly_chart(fig, use_container_width=True)

    # ────────────────────────────────────────────────────────────
    # TAB: Comunas
    # ────────────────────────────────────────────────────────────
    with tab_comuna:
        st.subheader(f"Análisis por comuna · {periodo_sel}")

        comunas = pgu_por_comuna(df_pgu, region=region_code, periodo=periodo_sel)
        if comunas.empty:
            st.warning("No hay datos de comunas para los filtros seleccionados.")
        else:
            # Buscador de comunas
            buscar = st.text_input("🔍 Buscar comuna", placeholder="Ej: Santiago, Maipú, Temuco...")
            if buscar:
                comunas = comunas[comunas["glosa_comuna"].str.contains(buscar.upper(), na=False)]

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Top 20 comunas con más beneficiarios**")
                top20 = comunas.head(20)
                fig = px.bar(
                    top20.sort_values("beneficiarios", ascending=True),
                    y="glosa_comuna", x="beneficiarios",
                    orientation="h",
                    text="beneficiarios",
                    color="region_nombre",
                    color_discrete_sequence=REGION_COLORS,
                    title="",
                )
                fig.update_traces(texttemplate="%{text:,}", textposition="outside")
                fig.update_layout(height=600, yaxis_title="", xaxis_title="Beneficiarios",
                                 legend_title="Región")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("**Top 20 comunas por monto promedio**")
                top_monto = comunas.nlargest(20, "monto_promedio")
                fig = px.bar(
                    top_monto.sort_values("monto_promedio", ascending=True),
                    y="glosa_comuna", x="monto_promedio",
                    orientation="h",
                    text="monto_promedio",
                    color="region_nombre",
                    color_discrete_sequence=REGION_COLORS,
                    title="",
                )
                fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
                fig.update_layout(height=600, yaxis_title="", xaxis_title="Monto Promedio M$",
                                 legend_title="Región")
                st.plotly_chart(fig, use_container_width=True)

            # Scatter: beneficiarios vs monto promedio
            st.subheader("Relación beneficiarios vs monto promedio")
            fig = px.scatter(
                comunas,
                x="beneficiarios", y="monto_promedio",
                size="monto_total", color="region_nombre",
                hover_name="glosa_comuna",
                hover_data={"beneficiarios": ":,", "monto_promedio": ":.0f",
                           "pct_mujeres": ":.1f", "region_nombre": True},
                color_discrete_sequence=REGION_COLORS,
                title="Cada burbuja = 1 comuna (tamaño = gasto total)",
            )
            fig.update_layout(height=500, xaxis_title="Beneficiarios",
                             yaxis_title="Monto Promedio M$", legend_title="Región")
            st.plotly_chart(fig, use_container_width=True)

            # Tabla completa
            with st.expander("📋 Ver tabla completa de comunas"):
                tabla_c = comunas[["glosa_comuna", "region_nombre", "beneficiarios",
                                  "monto_total", "monto_promedio", "hombres", "mujeres", "pct_mujeres"]].copy()
                tabla_c.columns = ["Comuna", "Región", "Beneficiarios", "Monto Total M$",
                                  "Monto Prom.", "Hombres", "Mujeres", "% Mujeres"]
                st.dataframe(
                    tabla_c.style.format({
                        "Beneficiarios": "{:,.0f}",
                        "Monto Total M$": "${:,.0f}",
                        "Monto Prom.": "${:,.0f}",
                        "Hombres": "{:,.0f}",
                        "Mujeres": "{:,.0f}",
                        "% Mujeres": "{:.1f}%",
                    }),
                    use_container_width=True, height=500,
                )

    # ────────────────────────────────────────────────────────────
    # TAB: Género
    # ────────────────────────────────────────────────────────────
    with tab_sexo:
        st.subheader("Análisis por género")

        col1, col2 = st.columns(2)
        with col1:
            # Evolución por sexo
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=totales["periodo"], y=totales["hombres"],
                mode="lines+markers", name="Hombres",
                line=dict(color=COLORS["hombres"], width=2),
                marker=dict(size=8),
            ))
            fig.add_trace(go.Scatter(
                x=totales["periodo"], y=totales["mujeres"],
                mode="lines+markers", name="Mujeres",
                line=dict(color=COLORS["mujeres"], width=2),
                marker=dict(size=8),
            ))
            fig.update_layout(
                title="Evolución por sexo",
                xaxis_title="Periodo", yaxis_title="Beneficiarios",
                height=400, yaxis=dict(tickformat=","),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Proporción último periodo
            u_data = totales[totales["periodo"] == periodo_sel].iloc[0]
            fig = go.Figure(go.Pie(
                labels=["Hombres", "Mujeres"],
                values=[u_data["hombres"], u_data["mujeres"]],
                marker=dict(colors=[COLORS["hombres"], COLORS["mujeres"]]),
                textinfo="label+percent+value",
                texttemplate="%{label}<br>%{value:,}<br>(%{percent})",
                hole=0.45,
            ))
            fig.update_layout(title=f"Distribución por sexo · {periodo_sel}", height=400)
            st.plotly_chart(fig, use_container_width=True)

        # Brecha de género por región
        st.subheader(f"Brecha de género por región · {periodo_sel}")
        reg_genero = pgu_por_region(df_pgu, periodo=periodo_sel)
        if not reg_genero.empty:
            reg_genero = reg_genero.sort_values("pct_mujeres", ascending=True)
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=reg_genero["region_nombre"], x=reg_genero["hombres"],
                name="Hombres", orientation="h",
                marker_color=COLORS["hombres"],
            ))
            fig.add_trace(go.Bar(
                y=reg_genero["region_nombre"], x=reg_genero["mujeres"],
                name="Mujeres", orientation="h",
                marker_color=COLORS["mujeres"],
            ))
            fig.update_layout(
                barmode="group", height=550,
                title="Beneficiarios por sexo y región",
                xaxis_title="Beneficiarios", yaxis_title="",
                xaxis=dict(tickformat=","),
            )
            st.plotly_chart(fig, use_container_width=True)

        # Montos por sexo
        col3, col4 = st.columns(2)
        with col3:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=totales["periodo"], y=totales["monto_hombres"],
                name="Hombres", marker_color=COLORS["hombres"],
            ))
            fig.add_trace(go.Bar(
                x=totales["periodo"], y=totales["monto_mujeres"],
                name="Mujeres", marker_color=COLORS["mujeres"],
            ))
            fig.update_layout(
                barmode="group", title="Gasto total por sexo (M$)",
                xaxis_title="Periodo", yaxis_title="Monto M$",
                height=400, yaxis=dict(tickformat=","),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col4:
            # % mujeres en el tiempo
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=totales["periodo"], y=totales["pct_mujeres"],
                mode="lines+markers+text",
                text=[f"{v}%" for v in totales["pct_mujeres"]],
                textposition="top center",
                line=dict(color=COLORS["mujeres"], width=3),
                marker=dict(size=10),
            ))
            fig.add_hline(y=50, line_dash="dash", line_color="gray",
                         annotation_text="Paridad 50%")
            fig.update_layout(
                title="Porcentaje de mujeres beneficiarias",
                xaxis_title="Periodo", yaxis_title="% Mujeres",
                height=400, yaxis=dict(range=[40, 70]),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

    # ────────────────────────────────────────────────────────────
    # TAB: Datos
    # ────────────────────────────────────────────────────────────
    with tab_datos:
        st.subheader("Explorador de datos")

        subtab1, subtab2, subtab3 = st.tabs(["Resumen nacional", "Población 65+ (INE)", "Datos crudos"])

        with subtab1:
            st.dataframe(
                totales.style.format({
                    "total_beneficiarios": "{:,.0f}",
                    "total_monto": "${:,.0f}",
                    "hombres": "{:,.0f}",
                    "mujeres": "{:,.0f}",
                    "monto_hombres": "${:,.0f}",
                    "monto_mujeres": "${:,.0f}",
                    "monto_promedio": "${:,.0f}",
                    "pct_mujeres": "{:.1f}%",
                    "n_comunas": "{:,.0f}",
                }),
                use_container_width=True,
            )

        with subtab2:
            if not df_pob.empty:
                pob_pivot = df_pob.pivot_table(index="anio", columns="sexo", values="poblacion", aggfunc="sum")
                pob_pivot.columns = [
                    {"M": "Hombres", "F": "Mujeres", "_T": "Total"}.get(c, c) for c in pob_pivot.columns
                ]
                st.dataframe(pob_pivot.style.format("{:,.0f}"), use_container_width=True)

                fig = px.line(
                    df_pob[df_pob["sexo"] != "_T"],
                    x="anio", y="poblacion",
                    color="sexo",
                    color_discrete_map={"M": COLORS["hombres"], "F": COLORS["mujeres"]},
                    title="Proyección población 65+ (INE)",
                    labels={"poblacion": "Población", "anio": "Año", "sexo": "Sexo"},
                )
                fig.update_layout(height=400, yaxis=dict(tickformat=","))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No se encontró archivo de población INE.")

        with subtab3:
            st.caption(f"Datos crudos PGU · {len(df_pgu):,} registros")
            cols_show = ["periodo", "region", "glosa_comuna", "n_hombres", "n_mujeres",
                        "total_n", "total_monto", "monto_hombres", "monto_mujeres"]
            cols_available = [c for c in cols_show if c in df_pgu.columns]
            st.dataframe(df_pgu[cols_available].head(500), use_container_width=True, height=500)

    # ── Footer ──────────────────────────────────────────────────
    st.markdown("---")
    st.caption(
        "Dashboard PGU Chile · Datos abiertos IPS/INE · "
        "Desarrollado con Streamlit + Plotly · "
        f"Última actualización: {periodos[-1]}"
    )


if __name__ == "__main__":
    main()
