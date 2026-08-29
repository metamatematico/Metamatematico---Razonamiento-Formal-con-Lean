# -*- coding: utf-8 -*-
"""
El estado de la interpretacion del grafo, en PDF.

REEMPLAZA a `generar_pdf_etiquetas.py` y `generar_pdf_decisiones.py`. Aquellos
dos hacian PREGUNTAS —que es arista y que es vertice, que morfismos tiene cada
etiqueta— y esas preguntas ya estan contestadas. Regenerarlos produciria una
lista de dudas resueltas.

Este genera el ESTADO, y lo genera leyendo `nucleo.graph.interpretacion`, que es
la unica fuente de verdad. Si la tabla cambia, el PDF cambia con ella: no puede
volver a desfasarse, que es exactamente lo que le paso a los dos anteriores.

    python -m scripts.generar_pdf_interpretacion
"""
import os
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from nucleo.graph.interpretacion import (
    C, S, F, O, T, VEREDICTO, VERTICES, VERTICES_ANADIDOS,
    DEGRADADAS_A_FLECHA, DEGRADADAS, FUSIONES, NOTA_FUSION,
    SUBCATEGORIA_PLENA, PATRONES_ESPURIOS, VECINO_VERDADERO,
    APICE_FALTANTE, MORFISMO_SIN_FIJAR, SIN_PUSHOUT,
    PUSHOUT_SI_DETERMINISTA, RESTRICCIONES, LAS_DEL_AUTOR,
    marca, vertices, vertices_tras_fusionar, resolver,
)

SALIDA = "E:/Metamatematico/docs/INTERPRETACION_DEL_GRAFO.pdf"

# La paleta del artefacto, para que los dos documentos se reconozcan.
TINTA = colors.HexColor("#1b1e17")
SUAVE = colors.HexColor("#4f5347")
GRIS = colors.HexColor("#7a7c6d")
ESTRUCTURA = colors.HexColor("#564c9e")
VERIFICA = colors.HexColor("#167a68")
LENGUAJE = colors.HexColor("#b4761f")
HUECO = colors.HexColor("#ae3b35")
LINEA = colors.HexColor("#ddd6c2")
FONDO = colors.HexColor("#f3f1ea")

COLOR_MARCA = {C: ESTRUCTURA, S: ESTRUCTURA, F: LENGUAJE, O: GRIS, T: HUECO}
NOMBRE_MARCA = {
    C: "categoria",
    S: "subcategoria plena",
    F: "funtor — es arista",
    O: "objeto dentro de una categoria",
    T: "nombre de un tema, sin objetos",
}


def _p(nombre, tam, color=TINTA, **kw):
    kw.setdefault("leading", tam * 1.45)
    return ParagraphStyle(nombre, fontName=kw.pop("fuente", "Helvetica"),
                          fontSize=tam, textColor=color, **kw)


H1 = _p("H1", 19, TINTA, fuente="Helvetica-Bold", spaceAfter=6)
H2 = _p("H2", 13, ESTRUCTURA, fuente="Helvetica-Bold",
        spaceBefore=16, spaceAfter=6)
H3 = _p("H3", 10.5, TINTA, fuente="Helvetica-Bold",
        spaceBefore=10, spaceAfter=3)
CUERPO = _p("Cuerpo", 9.3, SUAVE, spaceAfter=5)
PIE = _p("Pie", 8, GRIS, spaceAfter=3)
CELDA = _p("Celda", 7.6, SUAVE, leading=10)
CELDA_ID = _p("CeldaId", 7.6, TINTA, fuente="Courier-Bold", leading=10)
CELDA_MONO = _p("CeldaMono", 7.1, SUAVE, fuente="Courier", leading=9.5)


def _tabla(datos, anchos, cabecera=True):
    t = Table(datos, colWidths=anchos, repeatRows=1 if cabecera else 0)
    estilo = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINEA),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    if cabecera:
        estilo += [
            ("BACKGROUND", (0, 0), (-1, 0), FONDO),
            ("LINEBELOW", (0, 0), (-1, 0), 0.9, GRIS),
        ]
    t.setStyle(TableStyle(estilo))
    return t


def _th(txt):
    return Paragraph(
        '<font color="#7a7c6d"><b>%s</b></font>' % txt,
        _p("th", 7.2, GRIS, fuente="Helvetica-Bold"))


def construir():
    hist = Counter(e.marca for k, e in VEREDICTO.items()
                   if k not in VERTICES_ANADIDOS)
    fl = []

    # ── portada ───────────────────────────────────────────────────────────
    fl.append(Paragraph("La interpretación del grafo", H1))
    fl.append(Paragraph(
        "Qué es cada uno de los nodos, y qué se hizo con los que no eran "
        "nodos. Documento generado desde <font face='Courier'>nucleo/graph/"
        "interpretacion.py</font>: no se edita a mano.", CUERPO))

    fl.append(Paragraph("Por qué hubo que hacer esto", H2))
    fl.append(Paragraph(
        "Mientras el grafo fue una categoría delgada, las etiquetas eran solo "
        "nombres: para decidir si había co-cono bastaba con seguir aristas, y "
        "la maquinaria nunca miraba dentro de un nodo. En cuanto "
        "<font face='Courier'>Hom(a,b)</font> deja de ser un booleano eso se "
        "acaba — hay que saber <b>qué flecha</b> y <b>si conmuta</b>, y para "
        "eso hay que saber qué es cada nodo.", CUERPO))
    fl.append(Paragraph(
        "El caso que lo vuelve concreto: si <font face='Courier'>measure-"
        "theory</font> tiene por morfismos funciones medibles o núcleos "
        "<b>cambia qué colímites existen</b>. No es una preferencia de "
        "notación. Por eso cada etiqueta tuvo que declarar a cuál de cinco "
        "cosas corresponde.", CUERPO))

    fl.append(Paragraph("El reparto", H2))
    filas = [[_th("marca"), _th("qué es"), _th("¿vértice?"), _th("cuántas")]]
    for m in (C, S, F, O, T):
        filas.append([
            Paragraph('<font color="%s"><b>%s</b></font>'
                      % (COLOR_MARCA[m].hexval().replace('0x', '#'), m), CELDA_ID),
            Paragraph(NOMBRE_MARCA[m], CELDA),
            Paragraph("sí" if m in VERTICES else "no", CELDA),
            Paragraph(str(hist[m]), CELDA_ID),
        ])
    filas.append([
        Paragraph("", CELDA),
        Paragraph("<b>etiquetas del autor</b>", CELDA),
        Paragraph("<b>%d vértices</b>" % len(set(vertices()) - VERTICES_ANADIDOS), CELDA),
        Paragraph("<b>%d</b>" % sum(hist.values()), CELDA_ID),
    ])
    fl.append(_tabla(filas, [1.6*cm, 7.4*cm, 2.4*cm, 2.2*cm]))
    fl.append(Spacer(1, 4))
    fl.append(Paragraph(
        "Las %d marcadas <b>F</b> son el hallazgo que más movió: eran aristas "
        "ocupando el sitio de un vértice, y producían colímites falsos — el "
        "sistema «descubría» convergencias que eran errores de tipo."
        % hist[F], CUERPO))

    # ── lo que se hizo ────────────────────────────────────────────────────
    fl.append(Paragraph("Lo que se hizo con las que no eran vértices", H2))

    fl.append(Paragraph("Degradadas a flecha", H3))
    fl.append(Paragraph(
        "No se borran. Sus aristas se reparten según la dirección, y por eso "
        "no se pierde nada: las que entraban pasan al vértice que de verdad "
        "tenían encima, las que salían pasan a su codominio.", CUERPO))
    filas = [[_th("etiqueta"), _th("qué es en realidad")]]
    for k in sorted(DEGRADADAS_A_FLECHA):
        filas.append([Paragraph(k, CELDA_ID),
                      Paragraph(VEREDICTO[k].morfismos or "—", CELDA)])
    for k in sorted(DEGRADADAS):
        filas.append([
            Paragraph(k, CELDA_ID),
            Paragraph("entrantes → %s<br/>salientes → %s"
                      % (DEGRADADAS[k]["entrantes"][:110],
                         DEGRADADAS[k]["salientes"][:110]), CELDA)])
    fl.append(_tabla(filas, [3.4*cm, 10.2*cm]))

    fl.append(Paragraph("Fusionadas", H3))
    fl.append(Paragraph(
        "Etiquetas que nombran la misma categoría. Sobrevive la que nombra "
        "los <b>objetos</b>, no la rama; las retiradas quedan como alias, "
        "nunca se borran — si se borraran, las %d dejarían de mapear sobre el "
        "grafo." % LAS_DEL_AUTOR, CUERPO))
    filas = [[_th("se retira"), _th("sobrevive"), _th("por qué")]]
    for k in sorted(FUSIONES):
        v = FUSIONES[k]
        filas.append([Paragraph(k, CELDA_ID), Paragraph(v, CELDA_ID),
                      Paragraph(NOTA_FUSION.get(v, "")[:150], CELDA)])
    fl.append(_tabla(filas, [3.6*cm, 3.6*cm, 6.4*cm]))

    fl.append(Paragraph("Las que NO se fusionan", H3))
    fl.append(Paragraph(
        "La regla es condicional: fusiona <b>salvo</b> que alguna "
        "descomposición use precisamente esa distinción. Se activó en las dos "
        "de abajo, y en ambas uno de los miembros es el <b>ápice</b> y el otro "
        "una <b>componente</b>: fusionar habría colapsado el ápice dentro de "
        "su propio patrón.", CUERPO))
    filas = [[_th("subcategoría"), _th("ambiente"), _th("qué la recorta")]]
    for k in sorted(SUBCATEGORIA_PLENA):
        amb, rec = SUBCATEGORIA_PLENA[k]
        filas.append([Paragraph(k, CELDA_ID), Paragraph(amb, CELDA_ID),
                      Paragraph(rec, CELDA)])
    fl.append(_tabla(filas, [3.6*cm, 3.6*cm, 6.4*cm]))

    fl.append(PageBreak())

    # ── vertices que faltaban ─────────────────────────────────────────────
    fl.append(Paragraph("Los vértices que el grafo pedía", H2))
    fl.append(Paragraph(
        "El caso contrario, y el más interesante: descomposiciones que "
        "apuntaban a un sitio que no existía como vértice. El grafo tenía "
        "razón en que allí había algo y no tenía nombre para ello — lo había "
        "etiquetado con el invariante que ese sitio calcula, porque era la "
        "etiqueta más cercana disponible.", CUERPO))
    filas = [[_th("vértice"), _th("objeto"), _th("morfismo"), _th("Lean")]]
    for k in sorted(VERTICES_ANADIDOS):
        e = VEREDICTO[k]
        filas.append([Paragraph(k, CELDA_ID),
                      Paragraph(e.objeto, CELDA),
                      Paragraph(e.morfismos, CELDA),
                      Paragraph(e.lean or "—", CELDA_MONO)])
    fl.append(_tabla(filas, [3.2*cm, 3.6*cm, 3.4*cm, 3.4*cm]))
    fl.append(Spacer(1, 4))
    ap = APICE_FALTANTE["homology"]
    fl.append(Paragraph(
        "El primero es el ápice de %s. Sus tres patas son tres cosas "
        "<b>distintas</b> —%s— y ninguna es la homología: por eso la "
        "descomposición deja de ser circular y pasa a ser un teorema."
        % (", ".join(ap["componentes"]),
           "; ".join(v.split(",")[0] for v in ap["patas"].values())), CUERPO))

    # ── patrones espurios ─────────────────────────────────────────────────
    fl.append(Paragraph("Y los patrones que no se pegan", H2))
    fl.append(Paragraph(
        "No todo hueco es un concepto que falta. A veces el patrón no puede "
        "tener colímite, y entonces buscarle ápice es perder el tiempo.",
        CUERPO))
    for comps, motivo in PATRONES_ESPURIOS.items():
        fl.append(Paragraph("{%s}" % ", ".join(comps), H3))
        fl.append(Paragraph(motivo, CUERPO))
    for comps, v in VECINO_VERDADERO.items():
        viejo, nuevo = v["sustituir"]
        fl.append(Paragraph("Pero el primero tiene un vecino verdadero", H3))
        fl.append(Paragraph(
            "Sustituyendo <font face='Courier'>%s</font> —que es T, no nombra "
            "objetos— por <font face='Courier'>%s</font>, el ápice aparece y "
            "ya tenía etiqueta: <b>%s</b>, leída como %s."
            % (viejo, nuevo, v["apice"], v["lectura"]), CUERPO))
        filas = [[_th("componente"), _th("el funtor hacia el ápice")]]
        for c, pata in v["patas"].items():
            filas.append([Paragraph(c, CELDA_ID), Paragraph(pata, CELDA)])
        fl.append(_tabla(filas, [3.6*cm, 10.0*cm]))

    # ── lo que sigue abierto ──────────────────────────────────────────────
    fl.append(Paragraph("Lo que sigue abierto", H2))
    fl.append(Paragraph(
        "Etiquetas cuyos <b>morfismos</b> no se han fijado. La elección cambia "
        "qué colímites existen, así que no la puede tomar el código. Ninguna "
        "participa hoy en una descomposición, luego no bloquean nada — pero lo "
        "harán en cuanto entren.", CUERPO))
    filas = [[_th("etiqueta"), _th("las opciones")]]
    for k in MORFISMO_SIN_FIJAR:
        filas.append([Paragraph(k, CELDA_ID),
                      Paragraph(VEREDICTO[k].morfismos or "sin fijar", CELDA)])
    fl.append(_tabla(filas, [3.6*cm, 10.0*cm]))

    fl.append(Paragraph("Restricciones que no son opcionales", H3))
    for k, v in RESTRICCIONES.items():
        fl.append(Paragraph("<b>%s.</b> %s" % (k, v), CUERPO))
    fl.append(Paragraph(
        "Y dos vértices donde la forma del diagrama decide: sobre <font "
        "face='Courier'>%s</font> un pushout <b>no existe nunca</b> —lo que "
        "existe es el colímite homotópico, que es otra operación—; sobre <font "
        "face='Courier'>%s</font> existe solo si las flechas son "
        "deterministas."
        % (", ".join(sorted(SIN_PUSHOUT)),
           ", ".join(sorted(PUSHOUT_SI_DETERMINISTA))), CUERPO))

    # ── la lista exhaustiva ───────────────────────────────────────────────
    fl.append(PageBreak())
    fl.append(Paragraph("Las %d etiquetas, una por una" % LAS_DEL_AUTOR, H2))
    fl.append(Paragraph(
        "Ordenadas por marca y luego alfabéticamente. Los vértices añadidos "
        "van al final, marcados aparte.", CUERPO))

    orden = {C: 0, S: 1, F: 2, O: 3, T: 4}
    claves = sorted(
        (k for k in VEREDICTO if k not in VERTICES_ANADIDOS),
        key=lambda k: (orden[VEREDICTO[k].marca], k))

    filas = [[_th("etiqueta"), _th("m"), _th("objeto"), _th("morfismos"),
              _th("Lean")]]
    marca_actual = None
    for k in claves:
        e = VEREDICTO[k]
        if e.marca != marca_actual:
            marca_actual = e.marca
            filas.append([
                Paragraph('<font color="%s"><b>%s — %s</b></font>'
                          % (COLOR_MARCA[e.marca].hexval().replace('0x', '#'),
                             e.marca, NOMBRE_MARCA[e.marca].upper()),
                          _p("sep", 7.4, TINTA, fuente="Helvetica-Bold")),
                "", "", "", ""])
        etq = k
        if k in FUSIONES:
            etq = "%s<br/><font size='6' color='#7a7c6d'>→ %s</font>" % (
                k, resolver(k))
        elif k in DEGRADADAS_A_FLECHA or k in DEGRADADAS:
            etq = "%s<br/><font size='6' color='#b4761f'>degradada</font>" % k
        filas.append([
            Paragraph(etq, CELDA_ID),
            Paragraph('<font color="%s">%s</font>'
                      % (COLOR_MARCA[e.marca].hexval().replace('0x', '#'), e.marca), CELDA_ID),
            Paragraph(e.objeto or "—", CELDA),
            Paragraph(e.morfismos or "—", CELDA),
            Paragraph(e.lean or "—", CELDA_MONO),
        ])

    t = _tabla(filas, [3.0*cm, 0.7*cm, 3.5*cm, 3.4*cm, 3.0*cm])
    for i, f in enumerate(filas):
        if f[1] == "":
            t.setStyle(TableStyle([
                ("SPAN", (0, i), (-1, i)),
                ("BACKGROUND", (0, i), (-1, i), FONDO),
                ("TOPPADDING", (0, i), (-1, i), 6),
            ]))
    fl.append(t)

    fl.append(Spacer(1, 8))
    fl.append(Paragraph("Vértices añadidos — no estaban entre las %d"
                        % LAS_DEL_AUTOR, H3))
    filas = [[_th("etiqueta"), _th("m"), _th("objeto"), _th("morfismos"),
              _th("Lean")]]
    for k in sorted(VERTICES_ANADIDOS):
        e = VEREDICTO[k]
        filas.append([
            Paragraph(k, CELDA_ID),
            Paragraph('<font color="%s">%s</font>'
                      % (COLOR_MARCA[e.marca].hexval().replace('0x', '#'), e.marca), CELDA_ID),
            Paragraph(e.objeto, CELDA),
            Paragraph(e.morfismos, CELDA),
            Paragraph(e.lean or "—", CELDA_MONO)])
    fl.append(_tabla(filas, [3.0*cm, 0.7*cm, 3.5*cm, 3.4*cm, 3.0*cm]))

    fl.append(Spacer(1, 14))
    fl.append(Paragraph(
        "Generado desde nucleo/graph/interpretacion.py — %d etiquetas del "
        "autor, %d vértices añadidos, %d vértices tras fusionar. "
        "Reemplaza a LAS_172_ETIQUETAS.pdf y LO_QUE_HAY_QUE_DECIDIR.pdf, que "
        "hacían preguntas ya contestadas."
        % (LAS_DEL_AUTOR, len(VERTICES_ANADIDOS),
           len(set(vertices_tras_fusionar()) - VERTICES_ANADIDOS)), PIE))
    return fl


def main():
    doc = SimpleDocTemplate(
        SALIDA, pagesize=A4,
        leftMargin=2.0*cm, rightMargin=2.0*cm,
        topMargin=1.8*cm, bottomMargin=1.8*cm,
        title="La interpretación del grafo",
        author="Leonardo Jiménez Martínez")
    doc.build(construir())
    print("PDF -> %s (%.1f KB)" % (SALIDA, os.path.getsize(SALIDA) / 1024))


if __name__ == "__main__":
    main()
