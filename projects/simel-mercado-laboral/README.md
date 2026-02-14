# Datos del Sistema de Información del Mercado Laboral (SIMEL) — Python

Recreación en **Python** del proyecto [simel_mercado_laboral](https://github.com/bastianolea/simel_mercado_laboral) de [Bastián Olea](https://bastianolea.rbind.io/). Uso educativo y para practicar web scraping y análisis de datos de mercado laboral.

El [Sistema de Información del Mercado Laboral (SIMEL)](https://www.simel.gob.cl) es una plataforma desarrollada por instituciones chilenas con apoyo de la OIT. Ofrece información actualizada sobre empleo, ingresos, igualdad y estabilidad laboral.

---

## Qué hace este repo

- **Obtener datos**: **mercado actual** (`obtener_mercado_actual.py`) — siempre hasta el **año actual** — Banco Mundial: empleo, desempleo juvenil, participación, Gini, PIB pc, población, urbanización, alfabetización, expectativa de vida. Opcional: **ejemplo** (`generar_datos_ejemplo.py`). **Censo INE** (`obtener_censo_ine.py`): resumen Censo 2024 y enlaces a microdatos.
- **Cargar y limpiar**: `cargar_datos.py` lee CSVs, normaliza columnas y exporta Parquet/JSON.
- **Ratios sociedad/economía**: `calcular_ratios_sociales.py` — brecha de género, ratio desempleo juvenil/total, Gini, PIB pc.
- **Comportamiento social**: `comportamiento_social.py` — tendencias, correlaciones (PIB vs Gini), informe en `resultados/informe_comportamiento_social.txt`.
- **Explorar**: `explorar_datos.py` para análisis y gráficos con Pandas/Matplotlib.
- **Demo en la web**: carpeta `demo/` con vista interactiva para el portfolio.

---

## Estructura

```
simel-mercado-laboral/
├── README.md
├── contexto_anio.py            # Contexto de año (única fuente: año actual)
├── obtener_mercado_actual.py   # Datos Banco Mundial (hasta año en contexto)
├── obtener_censo_ine.py        # Resumen Censo 2024 INE Chile
├── generar_datos_ejemplo.py    # Datos de ejemplo
├── cargar_datos.py             # CSVs → Parquet/JSON
├── calcular_ratios_sociales.py # Ratios; series expandidas hasta año en contexto
├── comportamiento_social.py    # Informe tendencias y correlaciones
├── explorar_datos.py           # Análisis y gráficos
├── datos/                      # CSVs (mercado_actual, censo_ine, ejemplo)
├── resultados/                 # parquet, sample.json, ratios, informe
└── demo/
    └── index.html
```

**Contexto de año:** `contexto_anio.py` define el año actual como única fuente de verdad. Al ejecutar el pipeline el año que viene, los datos y ratios se expanden hasta ese año sin cambiar código.

---

## Cómo ejecutar

### 1. Entorno

```bash
pip install pandas pyarrow requests
```

### 2. Datos del mercado actual (siempre hasta el año actual)

Descarga indicadores reales para Chile (Banco Mundial): empleo, desempleo juvenil, participación por sexo, **Gini**, **PIB per cápita**, población, urbanización, alfabetización, expectativa de vida.

```bash
python obtener_mercado_actual.py
python cargar_datos.py
python calcular_ratios_sociales.py    # ratios sociedad/economía
python comportamiento_social.py       # informe de comportamiento social
```

Opcional — traer resumen del Censo INE 2024:

```bash
python obtener_censo_ine.py
python cargar_datos.py
```

Se actualizan `resultados/simel_datos.parquet`, `resultados/sample.json`, `resultados/ratios_sociales.csv` y `resultados/informe_comportamiento_social.txt`.

### 3. Datos de ejemplo (sin API)

```bash
python generar_datos_ejemplo.py
```

Crea `datos/oportunidades_empleo/` con CSVs de ejemplo al estilo SIMEL.

### 4. Cargar y exportar

```bash
python cargar_datos.py
```

- Lee todos los CSVs en `datos/`
- Limpia y unifica columnas (region, fecha, indicador, valor, desagregaciones)
- Guarda `resultados/simel_datos.parquet` y `resultados/sample.json` (para la demo)

### 5. Explorar

```bash
pip install matplotlib   # opcional, para generar gráficos
python explorar_datos.py
```

Genera en `resultados/`:
- **resumen_exploracion.txt** — estadísticas por indicador y serie temporal.
- **evolucion_indicadores.png** — evolución por año (líneas).
- **indicadores_por_region.png** — barras por región (último año).
- **indicadores_por_sexo.png** — comparación hombre/mujer (último año).

En consola: resumen general, listado de indicadores, estadísticas descriptivas, desagregación por región y sexo, y muestra de datos.

### 6. Ver la aplicación (gráficos, ratios y análisis)

La demo es una **aplicación** que muestra:

- **Indicadores**: gráfico de líneas y tabla con los indicadores de mercado laboral (sample.json).
- **Ratios**: gráfico y tabla de ratios sociedad/economía (brecha género, ratio juvenil/total, Gini, PIB pc) desde ratios_sociales.json.
- **Análisis**: tarjetas con tendencias recientes, correlación PIB–Gini, ratio desempleo juvenil y tabla resumen de ratios (desde informe_resumen.json).

Abre `demo/index.html` en el navegador (o sirve la raíz del repo) y usa las pestañas. Para que aparezcan todos los datos, ejecuta antes: `obtener_mercado_actual.py` → `cargar_datos.py` → `calcular_ratios_sociales.py` → `comportamiento_social.py`. Luego integra la demo en tu portfolio con un iframe a `projects/simel-mercado-laboral/demo/index.html`.

---

## Fuentes de datos

- **Banco Mundial** (siempre hasta año actual): empleo, desempleo juvenil, participación, Gini, PIB pc, población, urbanización, alfabetización, expectativa de vida — [data.worldbank.org](https://data.worldbank.org/).
- **Censo INE Chile**: [censo2024.ine.gob.cl](https://censo2024.ine.gob.cl) — resumen en este repo; microdatos y Redatam en el portal INE.
- **SIMEL Chile**: [simel.gob.cl](https://www.simel.gob.cl) — proyecto original (Bastián Olea) con scraping en [de.ine.gob.cl](https://de.ine.gob.cl).

## Referencia original

- Repositorio original (R): [bastianolea/simel_mercado_laboral](https://github.com/bastianolea/simel_mercado_laboral)
- Sitio SIMEL: [simel.gob.cl](https://www.simel.gob.cl)

---

## Licencia

Uso educativo. Los datos reales de SIMEL siguen los términos del sitio fuente.
