# EVA2 · Rentabilidad y política de descuentos en Superstore

Evaluación académica (EVA2) de **INACAP** — asignatura **Visualización de Datos (TIEL16)**, Unidad 2: informe de presentación de datos.
Autor: Diego Martínez González, Analista Programador, INACAP.
Dataset: [Sample - Superstore (Kaggle)](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final).

El proyecto entrega lo mismo en tres formatos, generados desde el mismo código:

- **App en Streamlit** (`app.py`): presentación interactiva del informe.
- **Informe en Word** (`informe/Informe_EVA2_Superstore.docx`): la entrega formal, con la plantilla institucional de INACAP.
- **Notebook de Google Colab** (`EVA2_Superstore.ipynb`): muestra los datos limpios, los gráficos y su interpretación.

## Estructura

```
├── app.py                  App de Streamlit
├── EVA2_Superstore.ipynb   Notebook para Google Colab
├── generar_informe_word.py Genera el informe en Word (plantilla INACAP)
├── requirements.txt
├── .streamlit/config.toml  Tema claro de la app
├── data/
│   └── Sample - Superstore.csv   CSV original de Kaggle, sin modificar
├── src/
│   ├── limpieza.py         Limpieza + bitácora de decisiones
│   ├── graficos.py         Las 5 visualizaciones (matplotlib/seaborn)
│   └── textos.py           Interpretaciones de negocio y reflexión ética
├── figuras/                PNG de los gráficos
├── plantilla/              Plantilla Word institucional de INACAP
└── informe/                Informe final (.docx)
```

## Cómo cumple la rúbrica

| Criterio | Dónde está |
|---|---|
| 1. Configuración de software y parámetros | `graficos.configurar_estilo()` + bloque "Configuración" de cada gráfico |
| 2. Integridad, calidad y homologación | `limpieza.py`, sección 2 (bitácora de 11 decisiones) |
| 3. Visualizaciones según complejidad | 5 gráficos; avanzados: mapa de calor (G5) y dispersión con 2 dimensiones extra (G3) |
| 4. Interpretación en clave de negocio | "Qué muestra" + "Decisión que apoya" de cada gráfico |
| 5. Decisiones éticas | Sección 4: atípicos, estados sub-representados, uso del dato, jitter |

Requisitos del profesor: limpieza (punto 1) → sección 2 · ≥3 gráficos con preguntas distintas (punto 2) → G1–G5 ·
dimensión adicional (punto 3) → G3 (color = categoría, tamaño = venta) · interpretación en negocio (punto 4) → cada gráfico.

## Ejecutar en local

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
python generar_informe_word.py   # genera el informe en Word
```

## Desplegar en Streamlit Community Cloud

1. Crear un repositorio **público** en GitHub (por ejemplo `eva2-superstore`) y subir esta carpeta completa,
   incluido `data/Sample - Superstore.csv`.
2. Entrar a <https://share.streamlit.io> con la cuenta de GitHub → **Create app** → *Deploy a public app from GitHub*.
3. Elegir el repositorio, la rama `main` y el archivo `app.py`.
4. En **Advanced settings**, elegir Python 3.12 (opcional: el código también funciona con 3.13).
5. **Deploy**. La primera vez tarda unos minutos en instalar las librerías.

App desplegada: <https://eva2-superstore-cf6parf9rmnwtmifgxebqn.streamlit.app/>

Las apps sin visitas se suspenden después de unos días. Antes de la evaluación, abrir el link y,
si aparece "This app has gone to sleep", presionar el botón para despertarla. Por eso el informe en Word y el notebook son las entregas principales.
