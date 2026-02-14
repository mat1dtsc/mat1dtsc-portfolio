# Dashboard PGU Chile – Análisis Estadístico

Dashboard interactivo para explorar las estadísticas de la **Pensión Garantizada Universal (PGU)** en Chile: beneficiarios por región y comuna, evolución temporal, análisis de género, mapa geográfico, montos y cobertura sobre población 65+.

## Contenido del dashboard

- **Indicadores (KPIs)**: total beneficiarios, cobertura 65+, gasto total, monto promedio, % mujeres
- **Evolución**: beneficiarios y gasto por mes, crecimiento absoluto y porcentual
- **Regiones**: barras horizontales, concentración regional (pie chart), tabla comparativa
- **Mapa**: mapa de burbujas de Chile con distribución geográfica de beneficiarios
- **Comunas**: ranking top 20, buscador, scatter beneficiarios vs monto, tabla completa (346 comunas)
- **Género**: evolución por sexo, brecha por región, montos por sexo, % mujeres en el tiempo
- **Datos**: tablas descargables de resumen nacional, población INE y datos crudos

## Fuentes de datos

- **PGU**: [Portal de Datos Abiertos – Pensión Garantizada Universal (IPS)](https://datos.gob.cl/dataset/pension-garantizada-universal)
- **Población 65+**: INE Chile (`CL01,DF_NP65MAS_SEXO,1.0+all.csv`)

## Instalación local

```bash
cd "pgu data"
pip install -r requirements.txt
```

## Descargar datos PGU

```bash
python download_pgu_data.py --ultimos 12
```

- `--ultimos N`: descargar los últimos N meses (0 = todos)
- `--force`: re-descargar aunque exista

## Ejecutar localmente

```bash
streamlit run app_dashboard.py
```

Se abre en http://localhost:8501

## Deploy en Streamlit Cloud

1. Sube el proyecto a un repositorio en GitHub
2. Ve a [share.streamlit.io](https://share.streamlit.io)
3. Conecta tu cuenta de GitHub
4. Selecciona el repositorio y apunta al archivo `projects/pgu data/app_dashboard.py`
5. Listo, se despliega automáticamente

## Estructura del proyecto

```
pgu data/
├── app_dashboard.py              # App Streamlit principal
├── data_loader.py                # Carga y análisis de datos
├── download_pgu_data.py          # Descarga CSV desde datos.gob.cl
├── requirements.txt              # Dependencias Python
├── README.md
├── .streamlit/
│   └── config.toml               # Configuración Streamlit
├── data/
│   └── pgu/                      # CSV mensuales (pgu_AAAA_MM.csv)
└── CL01,DF_NP65MAS_SEXO,1.0+all.csv  # Población 65+ INE
```
