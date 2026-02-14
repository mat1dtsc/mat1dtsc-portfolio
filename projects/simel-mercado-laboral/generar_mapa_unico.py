import json
import os

# Rutas relativas desde projects/simel-mercado-laboral/
GEO_PATH = 'datos/chile_regiones.geojson'
CSV_PATH = 'resultados/simel_regional.csv'
HTML_OUT = 'demo/mapa.html'

def main():
    print(f"Leyendo {GEO_PATH}...")
    with open(GEO_PATH, 'r', encoding='utf-8') as f:
        geo_content = f.read()

    print(f"Leyendo {CSV_PATH}...")
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        csv_content = f.read().replace('`', '\`') # Escapar backticks si los hubiera

    html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SIMEL Chile — Mapa Interactivo (Kepler.gl)</title>
    <script src="https://unpkg.com/react@16.8.4/umd/react.production.min.js" crossorigin></script>
    <script src="https://unpkg.com/react-dom@16.8.4/umd/react-dom.production.min.js" crossorigin></script>
    <script src="https://unpkg.com/redux@3.7.2/dist/redux.js" crossorigin></script>
    <script src="https://unpkg.com/react-redux@5.0.7/dist/react-redux.min.js" crossorigin></script>
    <script src="https://unpkg.com/styled-components@4.1.3/dist/styled-components.min.js" crossorigin></script>
    <script src="https://unpkg.com/kepler.gl@2.5.5/umd/keplergl.min.js" crossorigin></script>
    <style>
        body {{ margin: 0; padding: 0; overflow: hidden; font-family: 'Inter', sans-serif; }}
        #app {{ width: 100vw; height: 100vh; }}
        .loading {{
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            color: #94a3b8; font-size: 1.2rem; background: #0a0e17; padding: 20px; border-radius: 8px;
            z-index: 100; pointer-events: none;
        }}
    </style>
</head>
<body>
    <div id="app">
        <div class="loading">Cargando mapa...</div>
    </div>

    <script>
        // DATOS INCRUSTADOS
        const GEO_DATA = {geo_content};
        const CSV_DATA = `{csv_content}`;

        const {{ KeplerGl, Reducers, Middleware, processKeplerglJSON }} = keplerGl;
        const {{ createStore, combineReducers, applyMiddleware, compose }} = Redux;
        const {{ Provider }} = ReactRedux;
        const {{ render }} = ReactDOM;

        const mapConfig = {{
            version: 'v1',
            config: {{
                mapState: {{
                    latitude: -35.675147,
                    longitude: -71.542969,
                    zoom: 4,
                    pitch: 0,
                    bearing: 0
                }},
                mapStyle: {{
                    styleType: 'dark'
                }}
            }}
        }};

        const reducers = combineReducers({{ keplerGl: Reducers.keplerGlReducer }});
        const store = createStore(reducers, {{}}, applyMiddleware(Middleware.taskMiddleware));

        class App extends React.Component {{
            componentDidMount() {{
                this.loadData();
            }}

            loadData() {{
                try {{
                    // Procesar CSV
                    const rows = CSV_DATA.split('\\n').map(row => row.split(','));
                    const fields = rows[0].map(name => ({{ name: name.trim(), format: '' }}));
                    const dataRows = rows.slice(1).filter(r => r.length === fields.length);

                    // Despachar a Kepler
                    this.props.dispatch(
                        keplerGl.addDataToMap({{
                            datasets: [
                                {{
                                    info: {{ label: 'Regiones Chile', id: 'regiones_geo' }},
                                    data: {{ 
                                        fields: [{{ name: 'codregion', type: 'integer' }}], 
                                        rows: GEO_DATA.features.map(f => [f.properties.codregion]) 
                                    }}
                                }},
                                {{
                                    info: {{ label: 'Datos Laborales (CSV)', id: 'simel_data' }},
                                    data: {{ fields, rows: dataRows }}
                                }}
                            ],
                            options: {{ centerMap: true, readOnly: false }},
                            config: mapConfig
                        }})
                    );
                    
                    // Ocultar loading (opcional, Kepler lo tapa)
                    document.querySelector('.loading').style.display = 'none';

                }} catch (err) {{
                    console.error("Error cargando datos:", err);
                    alert("Error cargando datos. Ver consola.");
                }}
            }}

            render() {{
                return React.createElement(KeplerGl, {{
                    mapboxApiAccessToken: '',
                    id: "map",
                    width: window.innerWidth,
                    height: window.innerHeight,
                    store: this.props.store
                }});
            }}
        }}

        const mapStateToProps = state => state;
        const dispatchToProps = dispatch => ({{ dispatch }});
        const ConnectedApp = ReactRedux.connect(mapStateToProps, dispatchToProps)(App);

        render(
            React.createElement(Provider, {{ store }}, React.createElement(ConnectedApp)),
            document.getElementById('app')
        );
    </script>
</body>
</html>
"""
    
    print(f"Escribiendo {HTML_OUT}...")
    with open(HTML_OUT, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print("¡Listo! Mapa generado con datos incrustados.")

if __name__ == "__main__":
    main()
