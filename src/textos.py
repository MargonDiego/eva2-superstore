"""
Textos del informe: contexto, interpretación de negocio de cada gráfico y
reflexión ética. Las cifras se calculan desde los datos limpios.
"""
import graficos as g


def _usd(x):
    return g._usd(x)


def _miles(n):
    return f"{int(n):,}".replace(",", ".")


def _pct(x, d=0):
    return g._pct(x, d)


CONTEXTO = {
    "titulo": "Rentabilidad y política de descuentos en Superstore",
    "curso": "Visualización de Datos (TIEL16) · EVA2 · Unidad 2",
    "dataset": "Sample - Superstore (Kaggle)",
    "fuente": "https://www.kaggle.com/datasets/vivek468/superstore-dataset-final",
    "descripcion": (
        "Superstore es una tienda minorista de Estados Unidos que vende muebles, artículos de oficina "
        "y tecnología. El dataset tiene una fila por línea de pedido entre 2014 y 2017, con fecha, "
        "cliente, producto, región, venta, cantidad, descuento y utilidad."
    ),
    "pregunta_central": (
        "Las ventas suben cada año, pero ¿la empresa gana dinero con todo lo que vende? "
        "El informe busca dónde se pierde utilidad y qué decisiones ayudarían a recuperarla."
    ),
}


def ficha_visualizaciones(df):
    """Una ficha por gráfico: pregunta, tipo, justificación, configuración, lectura y decisión."""
    _, d1 = g.g1_utilidad_subcategoria(df)
    _, d2 = g.g2_estacionalidad(df)
    _, d3 = g.g3_descuento_margen(df)
    _, d4 = g.g4_composicion_descuento(df)
    _, d5 = g.g5_mapa_margen(df)
    import matplotlib.pyplot as plt
    plt.close("all")

    # --- cifras G1
    perdedoras = d1[d1["Profit"] < 0]
    ventas_perd = perdedoras["Sales"].sum()
    mesas = d1.loc["Mesas"]
    rank_mesas = int(d1["Sales"].rank(ascending=False)["Mesas"])
    ordinal = {1: "primera", 2: "segunda", 3: "tercera", 4: "cuarta", 5: "quinta", 6: "sexta"}
    top_utilidad = ", ".join(d1.index[-3:][::-1])

    # --- cifras G2
    anual = d2["anual"]
    crec_16 = anual[2016] / anual[2015] - 1
    crec_17 = anual[2017] / anual[2016] - 1
    q4 = d2["trimestre"][4]

    # --- cifras G3
    tr = d3["tramos"]
    alto = df["Discount"] > 0.2
    perdida_alto = df.loc[alto, "Profit"].sum()
    util_total = df["Profit"].sum()
    lineas_alto = alto.mean()
    con_perdida_alto = (df.loc[alto, "Profit"] < 0).mean()

    # --- cifras G4
    da = d4["descuento_alto"]

    # --- cifras G5
    sc = d5["solo_central"]
    central = df[df["Region"] == "Central"]
    estados = (central.groupby("State")
                      .agg(Lineas=("Sales", "size"), Descuento=("Discount", "mean"), Utilidad=("Profit", "sum"))
                      .sort_values("Utilidad"))
    tx, il = estados.loc["Texas"], estados.loc["Illinois"]
    resto = central[~central["State"].isin(["Texas", "Illinois"])]

    return [
        {
            "id": "g1",
            "funcion": g.g1_utilidad_subcategoria,
            "tipo": "Comparación",
            "pregunta": "¿Qué líneas de producto venden mucho pero no dejan utilidad?",
            "grafico": "Barras horizontales ordenadas",
            "por_que": (
                "Son 17 subcategorías con nombres largos, así que usé barras horizontales: los nombres "
                "caben sin rotarlos y, ordenadas por utilidad, el ranking se lee de arriba hacia abajo. "
                "El rojo marca las que pierden y el azul las que ganan."
            ),
            "configuracion": (
                "Figura de 9 × 6,2 pulgadas; eje X en dólares con punto como separador de miles; línea "
                "vertical en cero; etiquetas de venta y margen solo en las barras con pérdida."
            ),
            "lectura": (
                f"Tres subcategorías pierden dinero: Mesas ({_usd(mesas.Profit)}), Libreros e Insumos. "
                f"Juntas venden {_usd(ventas_perd)}, así que no son productos marginales. "
                f"Mesas es la {ordinal.get(rank_mesas, f'{rank_mesas}ª')} subcategoría en ventas "
                f"({_usd(mesas.Sales)}) y tiene el peor resultado, con un margen de {_pct(mesas.Margen, 1)}."
            ),
            "decision": (
                "Revisar precios y descuentos de Mesas y Libreros antes de seguir impulsando su venta. "
                f"Si el margen no mejora, conviene destinar el esfuerzo comercial a las que más utilidad "
                f"dejan ({top_utilidad})."
            ),
        },
        {
            "id": "g2",
            "funcion": g.g2_estacionalidad,
            "tipo": "Tendencia",
            "pregunta": "¿Cómo evolucionan las ventas y en qué meses se concentran?",
            "grafico": "Líneas superpuestas por año (gráfico estacional)",
            "por_que": (
                "Una sola línea de 2014 a 2017 muestra el crecimiento, pero tapa la estacionalidad. "
                "Al superponer los cuatro años sobre los mismos 12 meses se ve cuánto sube cada año "
                "y qué meses repiten el peak."
            ),
            "configuracion": (
                "Paleta de un solo tono en que el más oscuro es el año más reciente, porque los años son "
                "una variable ordenada; franja gris en septiembre–diciembre; el año rotulado al final de "
                "cada línea para no depender solo del color."
            ),
            "lectura": (
                f"Las ventas bajan levemente en 2015 y luego crecen {_pct(crec_16)} en 2016 y "
                f"{_pct(crec_17)} en 2017. Los cuatro años tienen el mismo patrón: septiembre, noviembre "
                f"y diciembre son los meses más altos. Entre septiembre y diciembre se concentra el "
                f"{_pct(d2['sep_dic'])} de las ventas; solo el último trimestre aporta el {_pct(q4)}."
            ),
            "decision": (
                "Tener el inventario y el personal de bodega listos en agosto. Las campañas de febrero, "
                "el mes más bajo, podrían compensar parte de la caída de inicio de año."
            ),
        },
        {
            "id": "g3",
            "funcion": g.g3_descuento_margen,
            "tipo": "Relación (con dimensiones adicionales)",
            "pregunta": "¿El descuento está destruyendo el margen?",
            "grafico": "Dispersión con color, tamaño y línea de tendencia",
            "por_que": (
                "Para ver la relación entre dos variables numéricas (descuento y margen) corresponde una "
                "dispersión. Le agregué dos dimensiones: el color es la categoría y el tamaño del punto "
                "es el monto de la venta. La línea negra une el margen agregado de cada nivel de descuento, "
                "porque con 9.993 puntos el patrón se pierde a simple vista."
            ),
            "configuracion": (
                "Transparencia de 55 % y un pequeño desplazamiento horizontal aleatorio (jitter), porque el "
                "descuento tiene solo 12 valores distintos y los puntos se superponen; fondo rojo bajo "
                "0 % de margen; línea punteada en 20 %; dos leyendas, una para el color y otra para el tamaño."
            ),
            "lectura": (
                f"Hasta 20 % de descuento el margen sigue siendo positivo. Sobre 20 %, el "
                f"{_pct(con_perdida_alto)} de las líneas pierde dinero. Esas líneas son solo el "
                f"{_pct(lineas_alto)} del total, pero restan {_usd(-perdida_alto)} a la utilidad: sin "
                f"ellas la utilidad ({_usd(util_total)}) sería {_pct(-perdida_alto / util_total)} mayor. "
                "La pérdida aparece en las tres categorías, así que el problema no es un producto "
                "sino la política de descuentos."
            ),
            "decision": (
                "Fijar un tope de 20 % para descuentos sin autorización y pedir aprobación de la gerencia "
                "comercial para cualquier descuento mayor."
            ),
        },
        {
            "id": "g4",
            "funcion": g.g4_composicion_descuento,
            "tipo": "Composición",
            "pregunta": "¿Cómo se componen las ventas de cada región según el descuento aplicado?",
            "grafico": "Barras apiladas al 100 %",
            "por_que": (
                "Quería comparar proporciones entre regiones que venden montos distintos, y la barra "
                "apilada al 100 % lo permite. Con tortas habría que comparar ángulos entre cuatro gráficos."
            ),
            "configuracion": (
                "Escala de azul claro a oscuro, porque los tramos de descuento tienen un orden; regiones "
                "ordenadas por su participación de descuentos altos; porcentaje escrito en los tramos de "
                "5 % o más."
            ),
            "lectura": (
                f"En Central el {_pct(da['Central'])} de las ventas se hace con más de 20 % de descuento. "
                f"En Este es el {_pct(da['Este'])} y en Sur el {_pct(da['Sur'])}. Oeste casi no los usa "
                f"({_pct(da['Oeste'])}) y es la región con mejor margen."
            ),
            "decision": (
                "Llevar a Central y Este la práctica de Oeste, que vende con descuentos de hasta 20 %. "
                "Las metas de los vendedores deberían medir margen y no solo volumen."
            ),
        },
        {
            "id": "g5",
            "funcion": g.g5_mapa_margen,
            "tipo": "Comparación avanzada (dos dimensiones)",
            "pregunta": "¿En qué combinaciones de región y producto se pierde dinero?",
            "grafico": "Mapa de calor con escala divergente",
            "por_que": (
                "Una tabla de 17 × 4 tiene 68 márgenes y es difícil de leer. El mapa de calor cruza "
                "subcategoría y región, y la escala divergente (rojo pérdida, gris cero, azul ganancia) "
                "deja ver de inmediato dónde se pierde. Es la visualización avanzada del informe."
            ),
            "configuracion": (
                "Escala divergente centrada en 0 % y acotada a ±30 %, para que los valores extremos no "
                "oculten las diferencias pequeñas; valor escrito en cada celda; subcategorías ordenadas "
                "por margen promedio."
            ),
            "lectura": (
                f"Hay {len(sc)} subcategorías que ganan en las otras tres regiones y pierden solo en "
                f"Central: {', '.join(sc.index)}. La pérdida se concentra en dos estados: Texas "
                f"(descuento promedio {_pct(tx.Descuento)}, utilidad {_usd(tx.Utilidad)}) e Illinois "
                f"(descuento promedio {_pct(il.Descuento)}, utilidad {_usd(il.Utilidad)}). El resto de "
                f"los estados de Central suma {_usd(resto['Profit'].sum())}."
            ),
            "decision": (
                "Revisar la política de descuentos de Texas e Illinois antes de evaluar a Central como "
                "región. Los datos apuntan a cómo se fijan los precios, no a los productos ni a las personas."
            ),
        },
    ]


def reflexion_etica(df, tabla_atipicos, resumen):
    perdida_total = resumen["perdida_total"]
    perdida_atip = resumen["perdida_en_atipicos"]
    central = tabla_atipicos.loc["Central"]
    alto = df["Discount"] > 0.2
    perdida_alto = df.loc[alto, "Profit"].sum()
    perdida_alto_limpia = df.loc[alto & ~df["Atípico IQR"], "Profit"].sum()
    estados_chicos = resumen["estados_muestra_baja"]
    return [
        {
            "decision": "Conservar los valores atípicos en vez de eliminarlos",
            "contexto": (
                f"La regla del rango intercuartil (IQR) marca "
                f"{_miles(tabla_atipicos['Filas que se eliminarían'].sum())} filas "
                f"({_pct(df['Atípico IQR'].mean())} del dataset) como atípicas. Esas filas concentran el "
                f"{_pct(perdida_atip / perdida_total)} de todas las pérdidas."
            ),
            "consecuencia": (
                f"Si se hubieran eliminado, el margen de Central habría pasado de "
                f"{_pct(central['Margen real'], 1)} a {_pct(central['Margen sin atípicos'], 1)}, y la "
                f"pérdida de las ventas con más de 20 % de descuento habría bajado de {_usd(-perdida_alto)} "
                f"a {_usd(-perdida_alto_limpia)}. El hallazgo principal casi desaparece. Por eso las dejé "
                "y solo las marqué: son ventas reales con descuentos altos, no errores de digitación."
            ),
        },
        {
            "decision": "No concluir a nivel de estado; analizar por región",
            "contexto": (
                f"{len(estados_chicos)} estados tienen menos de 30 líneas de pedido "
                f"(Wyoming tiene 1, West Virginia 4, Maine 8)."
            ),
            "consecuencia": (
                "Con tan pocas filas, un solo pedido cambia el margen del estado completo, y un ranking los "
                "mostraría como los mejores o los peores sin evidencia suficiente. Quedan sub-representados: "
                "el informe lo declara y no recomienda decisiones sobre ellos. Texas e Illinois son la "
                "excepción, porque tienen datos de sobra para sostener la conclusión."
            ),
        },
        {
            "decision": "Separar la política de descuentos de la evaluación de personas",
            "contexto": (
                "El mapa de calor apunta a la región Central, y alguien podría concluir que su equipo "
                "comercial lo está haciendo mal."
            ),
            "consecuencia": (
                "El dataset no dice quién aprobó cada descuento ni por qué; pudo ser una instrucción de la "
                "gerencia o una respuesta a la competencia local. Por eso las recomendaciones apuntan a la "
                "regla de descuentos y no a un equipo: evaluar personas con estos datos iría más allá de "
                "lo que muestran."
            ),
        },
        {
            "decision": "Declarar las transformaciones visuales",
            "contexto": (
                "En la dispersión desplacé cada punto hasta ±1,2 puntos porcentuales en el eje del "
                "descuento (jitter) y limité el tamaño de los puntos a ventas de US$ 5.000."
            ),
            "consecuencia": (
                "Sin esta aclaración alguien podría creer que existen descuentos de 19 % o 21 %. Todos los "
                "cálculos usan el descuento original, no el desplazado."
            ),
        },
    ]


def conclusiones(df):
    alto = df["Discount"] > 0.2
    return [
        "Las ventas crecen, pero parte de ese crecimiento se logra con descuentos que generan pérdidas.",
        f"Las ventas con más de 20 % de descuento son el {_pct(alto.mean())} de las líneas y restan "
        f"{_usd(-df.loc[alto, 'Profit'].sum())} a la utilidad.",
        "El problema es la política de descuentos y no una categoría; se concentra en Texas e Illinois.",
        "Decisiones prioritarias: tope de 20 % con aprobación sobre ese nivel, revisión de precios de "
        "Mesas y Libreros, e inventario listo para septiembre–diciembre.",
    ]
