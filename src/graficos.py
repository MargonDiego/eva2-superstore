"""
Visualizaciones del informe, construidas con matplotlib y seaborn.

Cada función recibe el DataFrame limpio y devuelve (figura, datos), donde
`datos` contiene las cifras que usa la interpretación de negocio. Así el texto
del informe siempre calza con lo que muestra el gráfico.
"""
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

# ---------------------------------------------------------------------------
# Configuración global (criterio 1: parámetros ajustados a la problemática)
# ---------------------------------------------------------------------------
SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
GRILLA = "#e4e3df"

# Categorías: 3 tonos fijos, validados para daltonismo como trío
COLOR_CATEGORIA = {
    "Furniture": "#2a78d6",        # azul
    "Office Supplies": "#eb6834",  # naranjo
    "Technology": "#1baf7a",       # aqua
}
NOMBRE_CATEGORIA = {
    "Furniture": "Muebles",
    "Office Supplies": "Artículos de oficina",
    "Technology": "Tecnología",
}
# Polaridad (ganancia / pérdida): azul vs rojo, con gris neutro al centro
POSITIVO, NEGATIVO, NEUTRO = "#2a78d6", "#e34948", "#f0efec"
# Secuencial (tramos ordenados de menor a mayor): un solo tono, claro a oscuro
SECUENCIAL = ["#cde2fb", "#86b6ef", "#2a78d6", "#104281"]
SECUENCIAL_ANIOS = ["#b7d3f6", "#6da7ec", "#256abf", "#0d366b"]

TRAD_REGION = {"Central": "Central", "East": "Este", "South": "Sur", "West": "Oeste"}
TRAD_SUBCAT = {
    "Accessories": "Accesorios", "Appliances": "Electrodomésticos", "Art": "Arte",
    "Binders": "Carpetas", "Bookcases": "Libreros", "Chairs": "Sillas",
    "Copiers": "Copiadoras", "Envelopes": "Sobres", "Fasteners": "Sujetadores",
    "Furnishings": "Decoración", "Labels": "Etiquetas", "Machines": "Máquinas",
    "Paper": "Papel", "Phones": "Teléfonos", "Storage": "Almacenaje",
    "Supplies": "Insumos", "Tables": "Mesas",
}
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def configurar_estilo():
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update({
        "figure.facecolor": SUPERFICIE,
        "axes.facecolor": SUPERFICIE,
        "savefig.facecolor": SUPERFICIE,
        "figure.dpi": 110,
        "savefig.dpi": 160,
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlepad": 26,
        "axes.labelsize": 10,
        "axes.labelcolor": TINTA_2,
        "axes.edgecolor": GRILLA,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.color": GRILLA,
        "grid.linewidth": 0.8,
        "xtick.color": TINTA_2,
        "ytick.color": TINTA_2,
        "text.color": TINTA,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "legend.title_fontsize": 9,
    })


def _usd(x, _=None):
    """Formato de miles al estilo chileno: US$ 12.345."""
    signo = "−" if x < 0 else ""
    return f"{signo}US$ {abs(x):,.0f}".replace(",", ".")


def _pct(x, decimales=1):
    """Porcentaje con coma decimal: −8,6 %."""
    texto = f"{abs(x) * 100:.{decimales}f}".replace(".", ",")
    return f"{'−' if x < 0 else ''}{texto} %"


def _subtitulo(ax, texto):
    ax.text(0, 1.02, texto, transform=ax.transAxes, fontsize=9.5, color=TINTA_2, va="bottom")


# ---------------------------------------------------------------------------
# 1. COMPARACIÓN — ¿Qué subcategorías venden pero no dejan utilidad?
# ---------------------------------------------------------------------------
def g1_utilidad_subcategoria(df):
    datos = (df.groupby("Sub-Category")[["Sales", "Profit"]].sum()
               .assign(Margen=lambda x: x.Profit / x.Sales)
               .sort_values("Profit"))
    datos.index = datos.index.map(TRAD_SUBCAT)

    fig, ax = plt.subplots(figsize=(9, 6.2))
    colores = [NEGATIVO if p < 0 else POSITIVO for p in datos["Profit"]]
    ax.barh(datos.index, datos["Profit"], color=colores, height=0.68)
    ax.axvline(0, color=TINTA_2, linewidth=1)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(20000))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_usd))
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Utilidad acumulada 2014–2017")
    ax.set_ylabel("")

    # Etiquetas solo en las que pierden: es ahí donde está la decisión
    for nombre, fila in datos[datos["Profit"] < 0].iterrows():
        ax.text(900, nombre,
                f"ventas {_usd(fila.Sales)} · margen {_pct(fila.Margen)}",
                va="center", ha="left", fontsize=8.5, color=TINTA)
    ax.set_xlim(datos["Profit"].min() * 1.25, datos["Profit"].max() * 1.08)

    ax.set_title("Mesas, libreros e insumos venden, pero pierden dinero")
    _subtitulo(ax, "Utilidad total por subcategoría. En rojo, las que generan pérdida.")
    fig.tight_layout()
    return fig, datos


# ---------------------------------------------------------------------------
# 2. TENDENCIA — ¿Cómo evolucionan las ventas y cuándo se concentran?
# ---------------------------------------------------------------------------
def g2_estacionalidad(df):
    mensual = df.groupby(["Año", df["Order Date"].dt.month])["Sales"].sum().reset_index()
    mensual.columns = ["Año", "Mes", "Ventas"]
    anual = df.groupby("Año")["Sales"].sum()
    trimestre = df.groupby(df["Order Date"].dt.quarter)["Sales"].sum() / df["Sales"].sum()

    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.axvspan(8.5, 12.5, color=NEUTRO, zorder=0)
    ax.text(10.5, 0.985, "Sep – Dic", transform=ax.get_xaxis_transform(),
            ha="center", va="top", fontsize=9, color=TINTA_2)
    sns.lineplot(data=mensual, x="Mes", y="Ventas", hue="Año",
                 palette=SECUENCIAL_ANIOS, linewidth=2, marker="o", markersize=5, ax=ax)
    ax.set_xticks(range(1, 13), MESES)
    ax.set_xlim(0.6, 12.4)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_usd))
    ax.set_xlabel("")
    ax.set_ylabel("Ventas del mes")
    ax.grid(axis="x", visible=False)

    # Rotular directo cada año al final de su línea, con su crecimiento
    for i, (anio, color) in enumerate(zip(anual.index, SECUENCIAL_ANIOS)):
        y_fin = mensual.query("Año == @anio and Mes == 12")["Ventas"].iloc[0]
        ax.annotate(f"{anio}", (12, y_fin), xytext=(6, 0), textcoords="offset points",
                    va="center", fontsize=9, color=TINTA_2)
    ax.legend(title=None, loc="upper left", ncol=4)

    ax.set_title("Ventas al alza, concentradas entre septiembre y diciembre")
    _subtitulo(ax, "Ventas mensuales, una línea por año (más oscuro = más reciente).")
    fig.tight_layout()
    sep_dic = df.loc[df["Order Date"].dt.month >= 9, "Sales"].sum() / df["Sales"].sum()
    datos = {"anual": anual, "trimestre": trimestre, "mensual": mensual, "sep_dic": sep_dic}
    return fig, datos


# ---------------------------------------------------------------------------
# 3. RELACIÓN + DIMENSIONES ADICIONALES — ¿El descuento destruye el margen?
#    Color = categoría, tamaño = monto de la venta (sección 2.4)
# ---------------------------------------------------------------------------
def g3_descuento_margen(df):
    rng = np.random.default_rng(42)
    d = df[["Discount", "Margen", "Sales", "Category"]].copy()
    d["Descuento"] = d["Discount"] + rng.uniform(-0.012, 0.012, len(d))  # jitter: hay solo 12 niveles
    d["Categoría"] = d["Category"].map(NOMBRE_CATEGORIA)
    paleta = {NOMBRE_CATEGORIA[k]: v for k, v in COLOR_CATEGORIA.items()}

    fig, ax = plt.subplots(figsize=(9, 5.8))
    ax.axhspan(-3, 0, color="#fbeaea", zorder=0)
    ax.axhline(0, color=TINTA_2, linewidth=1)
    ax.axvline(0.2, color=TINTA_2, linewidth=1, linestyle="--")
    # Tamaño proporcional a la venta, acotado para que las ventas grandes no tapen todo
    def area(ventas):
        return 10 + 250 * np.clip(np.asarray(ventas, dtype=float) / 5000, 0, 1)

    for cat, color in paleta.items():
        sub = d[d["Categoría"] == cat]
        ax.scatter(sub["Descuento"], sub["Margen"], s=area(sub["Sales"]), color=color,
                   alpha=0.55, edgecolors=SUPERFICIE, linewidths=0.5)

    # Margen agregado por nivel de descuento: la tendencia que guía la decisión
    prom = df.groupby("Discount").apply(lambda g: g.Profit.sum() / g.Sales.sum(), include_groups=False)
    ax.plot(prom.index, prom.values, color=TINTA, linewidth=2, marker="D", markersize=5, zorder=5)

    ax.text(0.21, 0.6, "umbral 20 %", fontsize=9, color=TINTA_2)
    ax.text(0.79, -0.06, "zona de pérdida", fontsize=9, color=NEGATIVO, ha="right", va="top")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(1, decimals=0))
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1, decimals=0))
    ax.set_xlim(-0.03, 0.83)
    ax.set_ylim(-2.85, 0.72)
    ax.set_xlabel("Descuento aplicado")
    ax.set_ylabel("Margen de la línea (utilidad / venta)")

    # Dos leyendas: una por dimensión (color y tamaño), para que se lean por separado
    from matplotlib.lines import Line2D
    h_color = [Line2D([], [], marker="o", linestyle="", markersize=8, color=c, label=k)
               for k, c in paleta.items()]
    h_color.append(Line2D([], [], color=TINTA, marker="D", markersize=5, linewidth=2,
                          label="Margen agregado"))
    ley1 = ax.legend(handles=h_color, title="Categoría (color)", loc="lower left",
                     bbox_to_anchor=(0.0, 0.0), alignment="left")
    ax.add_artist(ley1)
    h_tam = [ax.scatter([], [], s=area(v), color="#9a9994", label=f"{_usd(v)}{' o más' if v == 5000 else ''}")
             for v in (100, 1000, 5000)]
    ax.legend(handles=h_tam, title="Venta (tamaño)", loc="lower left",
              bbox_to_anchor=(0.27, 0.0), alignment="left", labelspacing=1.1)

    ax.set_title("Sobre 20 % de descuento, la venta deja de ser rentable")
    _subtitulo(ax, "Cada punto es una línea de pedido. Línea negra: margen agregado por nivel de descuento.")
    fig.tight_layout()

    tramos = (df.groupby("Tramo descuento", observed=True)
                .agg(Lineas=("Sales", "size"), Ventas=("Sales", "sum"), Utilidad=("Profit", "sum"),
                     Con_perdida=("Profit", lambda x: (x < 0).mean()))
                .assign(Margen=lambda x: x.Utilidad / x.Ventas))
    return fig, {"tramos": tramos, "por_nivel": prom}


# ---------------------------------------------------------------------------
# 4. COMPOSICIÓN — ¿Cómo se componen las ventas de cada región según descuento?
# ---------------------------------------------------------------------------
def g4_composicion_descuento(df):
    tabla = df.pivot_table(index="Region", columns="Tramo descuento", values="Sales",
                           aggfunc="sum", observed=False, fill_value=0)
    pct = tabla.div(tabla.sum(axis=1), axis=0)
    alto = pct[["21–40%", "41–80%"]].sum(axis=1)
    pct = pct.loc[alto.sort_values().index]           # orden: menos a más descuento alto
    pct.index = pct.index.map(TRAD_REGION)

    fig, ax = plt.subplots(figsize=(9, 4.4))
    izquierda = np.zeros(len(pct))
    for tramo, color in zip(pct.columns, SECUENCIAL):
        valores = pct[tramo].values
        ax.barh(pct.index, valores, left=izquierda, color=color, height=0.62,
                edgecolor=SUPERFICIE, linewidth=2, label=tramo)
        for y, (v, x0) in enumerate(zip(valores, izquierda)):
            if v >= 0.05:
                ax.text(x0 + v / 2, y, f"{v:.0%}", ha="center", va="center", fontsize=9,
                        color=TINTA if color in SECUENCIAL[:2] else "white")
        izquierda += valores

    ax.xaxis.set_major_formatter(mticker.PercentFormatter(1, decimals=0))
    ax.set_xlim(0, 1)
    ax.grid(visible=False)
    ax.set_xlabel("Participación en las ventas de la región")
    ax.legend(title="Tramo de descuento", loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=4)
    ax.set_title("Central es la que más vende con descuentos sobre 20 %")
    _subtitulo(ax, "Composición de las ventas de cada región por tramo de descuento.")
    fig.tight_layout()
    alto.index = alto.index.map(TRAD_REGION)
    return fig, {"composicion": pct, "descuento_alto": alto.sort_values(ascending=False)}


# ---------------------------------------------------------------------------
# 5. AVANZADA — Mapa de calor del margen región × subcategoría
# ---------------------------------------------------------------------------
def g5_mapa_margen(df):
    g = df.groupby(["Sub-Category", "Region"])[["Sales", "Profit"]].sum()
    margen = (g.Profit / g.Sales).unstack()
    margen = margen.loc[margen.mean(axis=1).sort_values().index]
    margen = margen[["West", "East", "South", "Central"]]
    margen.index = margen.index.map(TRAD_SUBCAT)
    margen.columns = margen.columns.map(TRAD_REGION)

    divergente = LinearSegmentedColormap.from_list("perdida_ganancia", [NEGATIVO, NEUTRO, POSITIVO])
    fig, ax = plt.subplots(figsize=(7.8, 7.2))
    sns.heatmap(margen, cmap=divergente, center=0, vmin=-0.3, vmax=0.3,
                annot=True, fmt=".0%", annot_kws={"fontsize": 9},
                linewidths=2, linecolor=SUPERFICIE,
                cbar_kws={"format": mticker.PercentFormatter(1, decimals=0),
                          "label": "Margen (utilidad / venta)", "shrink": 0.7}, ax=ax)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="x", labeltop=True, labelbottom=False, length=0)
    ax.tick_params(axis="y", length=0)
    ax.set_title("Central pierde donde las demás regiones ganan", pad=34)
    fig.tight_layout()

    # Celdas donde Central pierde pero el resto de las regiones gana
    otras = margen.drop(columns="Central")
    solo_central = margen[(margen["Central"] < 0) & (otras > 0).all(axis=1)]
    return fig, {"margen": margen, "solo_central": solo_central}


TODOS = [g1_utilidad_subcategoria, g2_estacionalidad, g3_descuento_margen,
         g4_composicion_descuento, g5_mapa_margen]
