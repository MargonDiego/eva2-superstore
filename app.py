"""
EVA2 · Visualización de Datos (TIEL16) — Informe de presentación de datos
Dataset: Sample - Superstore (Kaggle)

Ejecutar en local:  streamlit run app.py
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))

import graficos  # noqa: E402
import limpieza  # noqa: E402
import textos    # noqa: E402

st.set_page_config(page_title="EVA2 · Superstore", page_icon="📊", layout="wide")
graficos.configurar_estilo()

AUTOR = "Diego Martínez González"


@st.cache_data(show_spinner="Limpiando datos…")
def cargar():
    crudo = limpieza.cargar_crudo()
    df, bitacora, resumen = limpieza.limpiar()
    return crudo, df, bitacora, resumen


crudo, df, bitacora, resumen = cargar()


def mostrar(fig):
    st.pyplot(fig, width="stretch")
    plt.close(fig)


def md(texto):
    """Escapa el signo $ para que Streamlit no lo lea como fórmula LaTeX."""
    return texto.replace("$", "\\$")


def fmt_pct(x):
    return graficos._pct(x, 1)


# ---------------------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------------------
SECCIONES = [
    "1. Contexto",
    "2. Preparación de datos",
    "3. Visualizaciones e interpretación",
    "4. Decisiones éticas",
    "5. Conclusiones",
    "Exploración libre",
]
with st.sidebar:
    st.markdown(f"### {textos.CONTEXTO['titulo']}")
    st.caption(f"{textos.CONTEXTO['curso']}\n\n{AUTOR}")
    seccion = st.radio("Sección", SECCIONES, label_visibility="collapsed")
    st.divider()
    informe = RAIZ / "informe" / "Informe_EVA2_Superstore.docx"
    if informe.exists():
        st.download_button("Descargar informe (Word)", informe.read_bytes(), file_name=informe.name,
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           width="stretch")
    st.caption(f"Fuente: [{textos.CONTEXTO['dataset']}]({textos.CONTEXTO['fuente']})")


# ---------------------------------------------------------------------------
# 1. Contexto
# ---------------------------------------------------------------------------
if seccion == SECCIONES[0]:
    st.title(textos.CONTEXTO["titulo"])
    st.caption(f"{textos.CONTEXTO['curso']} · {AUTOR}")
    st.write(md(textos.CONTEXTO["descripcion"]))
    st.info(md(textos.CONTEXTO["pregunta_central"]))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Líneas de pedido", f"{len(df):,}".replace(",", "."))
    c2.metric("Ventas totales", graficos._usd(df["Sales"].sum()))
    c3.metric("Utilidad total", graficos._usd(df["Profit"].sum()))
    c4.metric("Margen", fmt_pct(df["Profit"].sum() / df["Sales"].sum()))

    st.subheader("Preguntas de negocio")
    fichas = textos.ficha_visualizaciones(df)
    st.table(pd.DataFrame({
        "Tipo (tabla U1.4)": [f["tipo"] for f in fichas],
        "Pregunta": [f["pregunta"] for f in fichas],
        "Gráfico": [f["grafico"] for f in fichas],
    }, index=range(1, len(fichas) + 1)))
    st.caption(f"Periodo: {resumen['periodo']} · 4 regiones · 49 estados · 3 categorías · 17 subcategorías.")

# ---------------------------------------------------------------------------
# 2. Preparación de datos
# ---------------------------------------------------------------------------
elif seccion == SECCIONES[1]:
    st.title("Preparación de datos")
    st.write(
        "Antes de graficar se revisó el dataset original en tres dimensiones: **integridad** "
        "(¿están completos y sin duplicar los registros?), **calidad** (¿los valores son correctos y "
        "útiles?) y **homologación** (¿una misma cosa se escribe siempre igual?). Cada problema "
        "encontrado quedó registrado con la decisión tomada y su justificación."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Filas originales", f"{resumen['filas_iniciales']:,}".replace(",", "."))
    c2.metric("Filas finales", f"{resumen['filas_finales']:,}".replace(",", "."),
              delta=resumen["filas_finales"] - resumen["filas_iniciales"])
    c3.metric("Valores nulos", int(crudo.isna().sum().sum()))
    c4.metric("Problemas documentados", len(bitacora))

    st.subheader("Bitácora de limpieza")
    dims = st.multiselect("Filtrar por dimensión", bitacora["Dimensión"].unique().tolist(),
                          default=bitacora["Dimensión"].unique().tolist())
    st.dataframe(bitacora[bitacora["Dimensión"].isin(dims)], width="stretch", hide_index=True)

    st.subheader("Registros por región, antes y después")
    st.write("La limpieza casi no elimina filas, así que ninguna región pierde representación.")
    comp = pd.DataFrame({
        "Antes": crudo["Region"].value_counts(),
        "Después": df["Region"].value_counts(),
    })
    comp["Diferencia"] = comp["Después"] - comp["Antes"]
    st.dataframe(comp, width="stretch")

    with st.expander("Ver el código de limpieza"):
        st.code((RAIZ / "src" / "limpieza.py").read_text(encoding="utf-8"), language="python")

# ---------------------------------------------------------------------------
# 3. Visualizaciones
# ---------------------------------------------------------------------------
elif seccion == SECCIONES[2]:
    st.title("Visualizaciones e interpretación de negocio")
    st.write(
        "Cada gráfico responde una pregunta de negocio distinta y termina en una decisión concreta. "
        "Los gráficos se construyen con matplotlib y seaborn sobre el dataset completo, para que la "
        "interpretación calce siempre con lo que se ve."
    )
    fichas = textos.ficha_visualizaciones(df)
    pestanas = st.tabs([f"{i}. {f['tipo']}" for i, f in enumerate(fichas, 1)])
    for pestana, f in zip(pestanas, fichas):
        with pestana:
            st.subheader(f["pregunta"])
            fig, _ = f["funcion"](df)
            izq, der = st.columns([3, 2], gap="large")
            with izq:
                mostrar(fig)
            with der:
                st.markdown("**Qué muestra**")
                st.write(md(f["lectura"]))
                st.success(md(f"**Decisión que apoya:** {f['decision']}"))
                with st.expander("Por qué este gráfico"):
                    st.write(md(f["por_que"]))
                with st.expander("Configuración de matplotlib/seaborn"):
                    st.write(md(f["configuracion"]))

# ---------------------------------------------------------------------------
# 4. Ética
# ---------------------------------------------------------------------------
elif seccion == SECCIONES[3]:
    st.title("Decisiones con implicancia ética")
    st.write(
        "Limpiar y graficar obliga a decidir qué datos se muestran y cuáles no. Estas son las decisiones "
        "que podían cambiar las conclusiones del informe."
    )
    tabla = limpieza.efecto_eliminar_atipicos(df)
    for i, e in enumerate(textos.reflexion_etica(df, tabla, resumen), 1):
        st.subheader(f"{i}. {e['decision']}")
        st.write(md(f"**Situación.** {e['contexto']}"))
        st.write(md(f"**Consecuencia.** {e['consecuencia']}"))
        if i == 1:
            vista = tabla.copy()
            for c in ["Margen real", "Margen sin atípicos", "% de filas perdidas"]:
                vista[c] = vista[c].map(fmt_pct)
            vista["Diferencia (pp)"] = vista["Diferencia (pp)"].map(lambda x: f"{x:+.1f}".replace(".", ","))
            st.dataframe(vista, width="stretch")
        if i == 2:
            st.dataframe(pd.Series(resumen["estados_muestra_baja"], name="Líneas de pedido"),
                         width="stretch")

# ---------------------------------------------------------------------------
# 5. Conclusiones
# ---------------------------------------------------------------------------
elif seccion == SECCIONES[4]:
    st.title("Conclusiones")
    for c in textos.conclusiones(df):
        st.markdown(md(f"- {c}"))
    st.subheader("Decisiones recomendadas")
    fichas = textos.ficha_visualizaciones(df)
    st.table(pd.DataFrame({
        "Pregunta": [f["pregunta"] for f in fichas],
        "Decisión": [f["decision"] for f in fichas],
    }, index=range(1, len(fichas) + 1)))

# ---------------------------------------------------------------------------
# Exploración libre (fuera de la narrativa evaluada)
# ---------------------------------------------------------------------------
else:
    st.title("Exploración libre")
    st.caption("Esta sección permite filtrar los datos. Las interpretaciones del informe se basan en el dataset completo.")
    c1, c2 = st.columns(2)
    regiones = c1.multiselect("Región", sorted(df["Region"].unique()), default=sorted(df["Region"].unique()))
    anios = c2.multiselect("Año", sorted(df["Año"].unique()), default=sorted(df["Año"].unique()))
    sub = df[df["Region"].isin(regiones) & df["Año"].isin(anios)]
    if sub.empty:
        st.warning("No hay datos con esos filtros.")
    else:
        m1, m2, m3 = st.columns(3)
        m1.metric("Ventas", graficos._usd(sub["Sales"].sum()))
        m2.metric("Utilidad", graficos._usd(sub["Profit"].sum()))
        m3.metric("Margen", fmt_pct(sub["Profit"].sum() / sub["Sales"].sum()))
        izq, der = st.columns(2)
        with izq:
            fig, _ = graficos.g1_utilidad_subcategoria(sub)
            fig.axes[0].set_title("Utilidad por subcategoría")
            mostrar(fig)
        with der:
            fig, _ = graficos.g3_descuento_margen(sub)
            fig.axes[0].set_title("Descuento vs. margen")
            mostrar(fig)
