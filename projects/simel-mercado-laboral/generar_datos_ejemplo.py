"""
Genera datos de ejemplo al estilo SIMEL (Oportunidades de empleo).
No requiere scraping; sirve para probar el pipeline y la demo.
"""
import os
import pandas as pd

OUTPUT_DIR = "datos/oportunidades_empleo"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Indicadores típicos SIMEL: tasa de ocupación, desempleo, etc.
indicadores = [
    ("DF_TD_TOTAL", "Tasa de desempleo total", ["region", "sexo"]),
    ("DF_TO_TOTAL", "Tasa de ocupación total", ["region", "sexo"]),
]

regiones = ["_T", "01", "02", "13"]  # Total, Tarapacá, Antofagasta, Metropolitana
sexos = ["_T", "1", "2"]  # Total, Hombre, Mujer
years = [2020, 2021, 2022, 2023]

rows = []
for ind_id, ind_nombre, desag in indicadores:
    for year in years:
        for region in regiones:
            for sexo in sexos:
                # Valores de ejemplo (porcentajes 0-100)
                import random
                random.seed(hash(ind_id + str(year) + region + sexo) % 2**32)
                valor = round(random.uniform(5, 25), 2)
                rows.append({
                    "structure_id": ind_id,
                    "time_period": year,
                    "area_ref": region,
                    "sexo": sexo,
                    "indicador": ind_nombre,
                    "obs_value": valor,
                })

df = pd.DataFrame(rows)
df.columns = [c.replace(" ", "_") for c in df.columns]
path = os.path.join(OUTPUT_DIR, "oportunidades_empleo_ejemplo.csv")
df.to_csv(path, index=False)
print(f"Guardado: {path} ({len(df)} filas)")
