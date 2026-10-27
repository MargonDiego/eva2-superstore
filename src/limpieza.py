"""
Preparación de datos del dataset Sample - Superstore (Kaggle).

Cada paso deja un registro en la bitácora con: problema detectado, filas
afectadas, decisión tomada, justificación e implicancia (incluida la ética).
La bitácora alimenta la sección de limpieza de la app y del informe.
"""
from pathlib import Path

import numpy as np
import pandas as pd

RUTA_DATOS = Path(__file__).resolve().parent.parent / "data" / "Sample - Superstore.csv"

# Umbral bajo el cual un estado no tiene datos suficientes para concluir algo
MIN_FILAS_ESTADO = 30


def _registrar(bitacora, dimension, problema, filas, decision, justificacion, implicancia):
    bitacora.append({
        "Dimensión": dimension,
        "Problema detectado": problema,
        "Filas afectadas": filas,
        "Decisión": decision,
        "Justificación": justificacion,
        "Implicancia": implicancia,
    })


def cargar_crudo(ruta=RUTA_DATOS):
    """Lee el CSV original. El archivo publicado en Kaggle no está en UTF-8."""
    return pd.read_csv(ruta, encoding="latin-1", dtype={"Postal Code": str})


def limpiar(ruta=RUTA_DATOS):
    """Devuelve (df_limpio, bitacora, resumen) a partir del CSV original."""
    bitacora = []
    df = cargar_crudo(ruta)
    filas_iniciales = len(df)

    # 1. Codificación ------------------------------------------------------
    con_nbsp = df["Product Name"].str.contains("\xa0", regex=False).sum()
    _registrar(
        bitacora, "Integridad",
        "El CSV viene en Latin-1, no en UTF-8: leerlo con la configuración por defecto de pandas falla "
        "(UnicodeDecodeError). Además hay espacios no separables (\\xa0) en nombres de producto.",
        int(con_nbsp),
        "Leer con encoding='latin-1' y reemplazar \\xa0 por un espacio normal.",
        "Sin esto el archivo no carga, y los nombres con \\xa0 no coinciden al buscar o agrupar por texto.",
        "Ninguna pérdida de datos; solo se normaliza el texto.",
    )
    for col in ["Product Name", "Customer Name", "City", "State"]:
        df[col] = df[col].str.replace("\xa0", " ", regex=False)

    # 2. Espacios sobrantes ------------------------------------------------
    texto = df.select_dtypes(include=["object", "string"]).columns
    con_espacios = sum((df[c] != df[c].str.strip()).sum() for c in texto)
    df[texto] = df[texto].apply(lambda s: s.str.strip())
    _registrar(
        bitacora, "Homologación",
        "Nombres de producto con espacios al final (ej. 'Iceberg Mobile Mega Data/Printer Cart ').",
        int(con_espacios),
        "Aplicar strip() a todas las columnas de texto.",
        "Dos escrituras del mismo producto se contarían como productos distintos.",
        "Ninguna pérdida de datos.",
    )

    # 3. Códigos postales sin cero inicial ----------------------------------
    cp_cortos = (df["Postal Code"].str.len() == 4)
    estados_cp = ", ".join(df.loc[cp_cortos, "State"].value_counts().head(3).index)
    df["Postal Code"] = df["Postal Code"].str.zfill(5)
    _registrar(
        bitacora, "Calidad",
        f"Códigos postales de 4 dígitos: perdieron el 0 inicial al guardarse como número "
        f"(estados del noreste: {estados_cp}, entre otros).",
        int(cp_cortos.sum()),
        "Tratar el código postal como texto y completarlo a 5 dígitos con zfill(5).",
        "Un código postal es un identificador, no una cantidad. Mal formado, no cruza con fuentes externas.",
        "Afecta solo a la región East: si no se corrige, cualquier cruce geográfico la sub-representa.",
    )

    # 4. Fechas --------------------------------------------------------------
    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%m/%d/%Y")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%m/%d/%Y")
    envio_invalido = (df["Ship Date"] < df["Order Date"]).sum()
    _registrar(
        bitacora, "Integridad",
        "Fechas guardadas como texto en formato mes/día/año (estadounidense).",
        len(df),
        "Convertir a datetime con formato explícito '%m/%d/%Y' y validar que la fecha de envío "
        f"no sea anterior a la de pedido (casos inválidos encontrados: {envio_invalido}).",
        "Con formato implícito, '11/8/2016' podría leerse como 11 de agosto (formato chileno). "
        "El formato explícito evita esa ambigüedad.",
        "Ninguna pérdida de datos.",
    )

    # 5. Duplicados ----------------------------------------------------------
    dup_exactos = df.drop(columns="Row ID").duplicated()
    df = df.loc[~dup_exactos].copy()
    lineas_repetidas = df.duplicated(["Order ID", "Product ID"], keep=False)
    _registrar(
        bitacora, "Integridad",
        "Una fila idéntica a otra en todos los campos salvo el Row ID (pedido US-2014-150119).",
        int(dup_exactos.sum()),
        "Eliminar la copia.",
        "Es el mismo registro cargado dos veces: duplicaría su venta y su pérdida.",
        "Se elimina 1 fila (0,01%).",
    )
    _registrar(
        bitacora, "Integridad",
        "Mismo pedido y producto en dos líneas, pero con cantidades distintas.",
        int(lineas_repetidas.sum()),
        "Conservar ambas líneas.",
        "No son duplicados: difieren en cantidad y venta, y son compatibles con dos líneas reales de un mismo pedido.",
        "Eliminarlas borraría ventas reales.",
    )

    # 6. Product ID con varios nombres ---------------------------------------
    nombres_por_id = df.groupby("Product ID")["Product Name"].nunique()
    ids_ambiguos = nombres_por_id[nombres_por_id > 1].index
    df["ID ambiguo"] = df["Product ID"].isin(ids_ambiguos)
    _registrar(
        bitacora, "Homologación",
        "Un mismo Product ID aparece con nombres de producto distintos.",
        int(len(ids_ambiguos)),
        "No usar Product ID como llave de producto; el análisis se hace a nivel de subcategoría. "
        "Se marcan las filas con la columna 'ID ambiguo'.",
        "Agrupar por ID mezclaría productos distintos; agrupar por nombre partiría un ID. "
        "La subcategoría no tiene esta ambigüedad.",
        "Las conclusiones no bajan a nivel de producto individual.",
    )

    # 7. Columnas sin información -------------------------------------------
    _registrar(
        bitacora, "Calidad",
        "'Country' tiene un solo valor (United States) en todas las filas.",
        len(df),
        "Eliminar la columna.",
        "Una columna constante no aporta información.",
        "Ninguna.",
    )
    df = df.drop(columns=["Country"])

    # 8. Valores atípicos ------------------------------------------------------
    q1, q3 = df["Profit"].quantile([0.25, 0.75])
    iqr = q3 - q1
    df["Atípico IQR"] = (df["Profit"] < q1 - 1.5 * iqr) | (df["Profit"] > q3 + 1.5 * iqr)
    atipicos_neg = df["Atípico IQR"] & (df["Profit"] < 0)
    perdida_total = df.loc[df["Profit"] < 0, "Profit"].sum()
    perdida_atipica = df.loc[atipicos_neg, "Profit"].sum()
    _registrar(
        bitacora, "Ética",
        f"La regla IQR (1,5×) marca {df['Atípico IQR'].sum():,} filas de Profit como atípicas "
        f"({df['Atípico IQR'].mean():.0%} del total); {atipicos_neg.sum():,} de ellas son pérdidas.",
        int(df["Atípico IQR"].sum()),
        "Conservarlas todas y solo marcarlas (columna 'Atípico IQR').",
        "No son errores de digitación: son ventas reales con descuentos altos. "
        f"Esas filas concentran el {perdida_atipica / perdida_total:.0%} de las pérdidas del negocio.",
        "Eliminarlas haría ver un negocio más rentable de lo que es y escondería el problema de descuentos.",
    )

    # 9. Columnas derivadas -----------------------------------------------------
    df["Año"] = df["Order Date"].dt.year
    df["Mes"] = df["Order Date"].dt.to_period("M").dt.to_timestamp()
    df["Días de envío"] = (df["Ship Date"] - df["Order Date"]).dt.days
    df["Margen"] = np.where(df["Sales"] > 0, df["Profit"] / df["Sales"], np.nan)
    df["Tramo descuento"] = pd.cut(
        df["Discount"], bins=[-0.01, 0, 0.2, 0.4, 0.8],
        labels=["Sin descuento", "1–20%", "21–40%", "41–80%"],
    )
    _registrar(
        bitacora, "Calidad",
        "Faltan variables para responder las preguntas de negocio.",
        len(df),
        "Crear Año, Mes, Días de envío, Margen (Profit/Sales) y Tramo de descuento.",
        "El margen permite comparar rentabilidad entre segmentos de distinto tamaño.",
        "Ninguna pérdida de datos.",
    )

    # 10. Representatividad por estado -----------------------------------------
    filas_estado = df["State"].value_counts()
    estados_chicos = filas_estado[filas_estado < MIN_FILAS_ESTADO]
    df["Estado con muestra baja"] = df["State"].isin(estados_chicos.index)
    _registrar(
        bitacora, "Ética",
        f"{len(estados_chicos)} estados tienen menos de {MIN_FILAS_ESTADO} filas "
        f"(ej. Wyoming: {filas_estado.get('Wyoming', 0)}, West Virginia: {filas_estado.get('West Virginia', 0)}).",
        int(estados_chicos.sum()),
        "No sacar conclusiones a nivel de estado; el análisis geográfico se hace por región.",
        "Con tan pocas filas, un solo pedido cambia el margen del estado completo.",
        "Esos estados quedan sub-representados: ninguna decisión debería tomarse sobre ellos con este dataset.",
    )

    resumen = {
        "filas_iniciales": filas_iniciales,
        "filas_finales": len(df),
        "columnas_finales": df.shape[1],
        "periodo": f"{df['Order Date'].min():%d-%m-%Y} a {df['Order Date'].max():%d-%m-%Y}",
        "estados_muestra_baja": estados_chicos.to_dict(),
        "perdida_total": perdida_total,
        "perdida_en_atipicos": perdida_atipica,
    }
    return df, pd.DataFrame(bitacora), resumen


def efecto_eliminar_atipicos(df):
    """Compara el margen por región con y sin los atípicos IQR (reflexión ética)."""
    def margen(d):
        g = d.groupby("Region")[["Sales", "Profit"]].sum()
        return g["Profit"] / g["Sales"]

    tabla = pd.DataFrame({
        "Filas totales": df["Region"].value_counts(),
        "Filas que se eliminarían": df.loc[df["Atípico IQR"], "Region"].value_counts(),
        "Margen real": margen(df),
        "Margen sin atípicos": margen(df.loc[~df["Atípico IQR"]]),
    })
    tabla["% de filas perdidas"] = tabla["Filas que se eliminarían"] / tabla["Filas totales"]
    tabla["Diferencia (pp)"] = (tabla["Margen sin atípicos"] - tabla["Margen real"]) * 100
    return tabla.sort_values("Margen real")


if __name__ == "__main__":
    datos, bit, res = limpiar()
    pd.set_option("display.width", 200, "display.max_colwidth", 80)
    print(res)
    print(bit[["Dimensión", "Problema detectado", "Filas afectadas"]])
    print(efecto_eliminar_atipicos(datos))
