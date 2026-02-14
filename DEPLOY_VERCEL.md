# Cómo se ve la página en Vercel

Tu portfolio es un sitio **estático** (HTML, CSS, JS). En Vercel se ve **igual** que en local: misma estructura, mismos estilos y la demo SIMEL Chile cargando datos desde `sample.json`.

## Desplegar en Vercel

### Opción 1: Desde el dashboard (recomendado)

1. Entra a [vercel.com](https://vercel.com) e inicia sesión (con GitHub).
2. **Add New** → **Project**.
3. Importa el repo `mat1dtsc-portfolio` (o el que uses).
4. **Root Directory**: deja en blanco (raíz del repo).
5. **Framework Preset**: deja **Other** (o **Vite** si lo detecta; no hace falta build).
6. **Build Command**: vacío (o borra el que venga).
7. **Output Directory**: `.` o vacío.
8. **Deploy**.

Tu sitio quedará en una URL como:

- `https://mat1dtsc-portfolio.vercel.app`
- o un dominio que configures.

### Opción 2: CLI

```bash
npm i -g vercel
cd c:\Users\Usuario\mat1dtsc-portfolio
vercel
```

Sigue las preguntas (link a Git, nombre del proyecto, etc.).

---

## Qué verás en la URL de Vercel

- **Raíz** (`/`): tu `index.html` — Hero, About, Skills, Projects, Aprende, **SIMEL Chile** (iframe con la demo), Contact.
- **Demo SIMEL**: el iframe apunta a `/projects/simel-mercado-laboral/demo/index.html`; ese HTML carga `../resultados/sample.json`, así que el gráfico y la tabla se rellenan con los datos que tengas en el repo.
- **Estilos y fuentes**: `style.css` e Inter desde Google Fonts se sirven igual; el aspecto es el mismo que en local.

---

## Importante para que la demo SIMEL funcione

En el repo deben estar estos archivos (ya los tienes):

- `projects/simel-mercado-laboral/demo/index.html`
- `projects/simel-mercado-laboral/resultados/sample.json`

Si actualizas datos (por ejemplo tras `obtener_mercado_actual.py` y `cargar_datos.py`), haz **commit y push** de `resultados/sample.json` para que Vercel sirva la versión nueva.

---

## Resumen

| Dónde        | Cómo se ve |
|-------------|------------|
| **Vercel**  | Igual que en local: mismo diseño, misma navegación por secciones (#about, #projects, #simel, etc.) y la demo SIMEL Chile con gráfico y tabla si `sample.json` está en el repo. |

El `vercel.json` en la raíz solo indica que no hay build; Vercel sirve los archivos estáticos tal cual.
