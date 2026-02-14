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
    <!-- Updated Dependencies for Kepler.gl 2.5.5 (Requires React 16.8+ and React-Redux 7+) -->
    <script src="https://unpkg.com/react@17.0.2/umd/react.production.min.js" crossorigin></script>
    <script src="https://unpkg.com/react-dom@17.0.2/umd/react-dom.production.min.js" crossorigin></script>
    <script src="https://unpkg.com/redux@4.1.2/dist/redux.js" crossorigin></script>
    <script src="https://unpkg.com/react-redux@7.2.6/dist/react-redux.min.js" crossorigin></script>
    <script src="https://unpkg.com/styled-components@5.3.3/dist/styled-components.min.js" crossorigin></script>
    <script src="https://unpkg.com/kepler.gl@2.5.5/umd/keplergl.min.js" crossorigin></script>
    
    <style>
        body {{ margin: 0; padding: 0; overflow: hidden; font-family: 'Inter', sans-serif; }}
        #app {{ width: 100vw; height: 100vh; background: #0e0e0e; }}
        .loading {{
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            color: #94a3b8; font-size: 1.2rem; background: #1f2937; padding: 20px; border-radius: 8px;
            z-index: 100; pointer-events: none; border: 1px solid #374151;
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

        window.onload = function() {{
            // Ensure global variables are available
            const KeplerGl = window.KeplerGl; // Note: Kepler.gl UMD usually exports as 'KeplerGl' or 'keplerGl'
            const Redux = window.Redux;
            const ReactRedux = window.ReactRedux;
            const ReactDOM = window.ReactDOM;
            const React = window.React;

            if (!KeplerGl) {{
                alert("Error crítico: Kepler.gl no cargó correctamente. Revisa tu conexión a internet.");
                return;
            }}

            const {{ combineReducers, createStore, applyMiddleware, compose }} = Redux;
            const {{ Provider }} = ReactRedux;
            const {{ keplerGlReducer, taskMiddleware, addDataToMap }} = KeplerGl;

            // Configuración del store
            // Kepler.gl reducer debe montarse en 'keplerGl'
            const reducers = combineReducers({{
                keplerGl: keplerGlReducer
            }});

            const store = createStore(
                reducers, 
                {{}}, 
                applyMiddleware(taskMiddleware)
            );

            // Componente App
            function App() {{
                // Cargar datos al montar
                React.useEffect(() => {{
                    try {{
                        // Procesar CSV
                        const rows = CSV_DATA.split('\\n').map(row => row.split(','));
                        if (rows.length < 2) return;
                        
                        const header = rows[0].map(name => ({{ name: name.trim(), format: '' }}));
                        const dataRows = rows.slice(1).filter(r => r.length === header.length);

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
                                mapStyle: {{ styleType: 'dark' }}
                            }}
                        }};

                        // Despachar a Kepler
                        // Usamos GeoJSON + CSV
                        store.dispatch(
                            addDataToMap({{
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
                                        data: {{ fields: header, rows: dataRows }}
                                    }}
                                ],
                                options: {{ centerMap: true, readOnly: false }},
                                config: mapConfig
                            }})
                        );
                        
                        // Ocultar loading
                        const loading = document.querySelector('.loading');
                        if(loading) loading.style.display = 'none';

                    }} catch (err) {{
                        console.error("Error procesando datos:", err);
                    }}
                }}, []);

                return React.createElement(KeplerGl.KeplerGl, {{
                    mapboxApiAccessToken: '',
                    id: "map",
                    width: window.innerWidth,
                    height: window.innerHeight,
                    store: store
                }});
            }}

            // Renderizar
            ReactDOM.render(
                React.createElement(Provider, {{ store }}, React.createElement(App)),
                document.getElementById('app')
            );
        }};
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
