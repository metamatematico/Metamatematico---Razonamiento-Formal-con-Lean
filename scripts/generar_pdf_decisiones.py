# -*- coding: utf-8 -*-
"""Genera el PDF con lo que hay que decidir, sin notacion categorica."""
import sys
sys.stdout.reconfigure(encoding="utf-8")

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether,
)

SALIDA = "E:/Metamatematico/docs/LO_QUE_HAY_QUE_DECIDIR.pdf"

TINTA   = colors.HexColor("#1b1e17")
SUAVE   = colors.HexColor("#4f5347")
GRIS    = colors.HexColor("#7a7c6d")
ACENTO  = colors.HexColor("#564c9e")
VERDE   = colors.HexColor("#167a68")
ROJO    = colors.HexColor("#ae3b35")
LINEA   = colors.HexColor("#ddd6c2")
FONDO   = colors.HexColor("#f3f1ea")

def P(nombre, **kw):
    base = dict(fontName="Helvetica", fontSize=10.2, leading=15.2,
                textColor=SUAVE, spaceAfter=8)
    base.update(kw)
    return ParagraphStyle(nombre, **base)

H1   = P("H1", fontName="Helvetica-Bold", fontSize=19, leading=23,
         textColor=TINTA, spaceAfter=4, spaceBefore=0)
SUB  = P("SUB", fontSize=11.5, leading=16, textColor=GRIS, spaceAfter=20)
H2   = P("H2", fontName="Helvetica-Bold", fontSize=13, leading=17,
         textColor=TINTA, spaceBefore=18, spaceAfter=7)
H3   = P("H3", fontName="Helvetica-Bold", fontSize=10.6, leading=14,
         textColor=ACENTO, spaceBefore=12, spaceAfter=5)
TXT  = P("TXT")
NOTA = P("NOTA", fontSize=9.4, leading=13.6, textColor=GRIS)
MONO = P("MONO", fontName="Courier", fontSize=9, leading=13.4, textColor=TINTA)
PREG = P("PREG", fontName="Helvetica-Bold", fontSize=10.4, leading=14.6,
         textColor=TINTA, spaceAfter=4)

def caja(flow, color=LINEA, relleno=FONDO):
    t = Table([[flow]], colWidths=[16.2 * cm])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, color),
        ("BACKGROUND", (0, 0), (-1, -1), relleno),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t

def regla():
    t = Table([[""]], colWidths=[16.2 * cm], rowHeights=[0.6])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LINEA)]))
    return t

E = []
add = E.append

# ── portada ────────────────────────────────────────────────────────────────
add(Paragraph("Lo que necesito que decidas", H1))
add(Paragraph("Cuatro definiciones y cuatro preguntas sobre caminos del grafo. "
              "Ninguna requiere leer código.", SUB))

add(Paragraph("En una frase", H2))
add(Paragraph(
    "Necesito saber <b>qué objetos matemáticos nombra</b> cada una de cuatro "
    "etiquetas del grafo, y si ciertos caminos del grafo describen "
    "<b>la misma construcción o construcciones distintas</b>.", TXT))

# ── por qué ────────────────────────────────────────────────────────────────
add(Paragraph("Por qué hace falta", H2))
add(Paragraph(
    "Un nodo del grafo es una etiqueta. <font face=\"Courier\">group-theory</font> "
    "no es un objeto matemático: es el nombre de un tema. Mientras no digamos "
    "qué colección de objetos nombra, una flecha entre dos etiquetas no "
    "significa nada — y preguntar si dos caminos «son iguales» es preguntar si "
    "dos cosas sin definir coinciden.", TXT))
add(Paragraph(
    "Eso es exactamente lo que te pregunté mal la vez anterior. Aquí está bien "
    "planteado.", NOTA))

# ── la regla ───────────────────────────────────────────────────────────────
add(Paragraph("La regla que ya elegiste", H2))
add(caja(Paragraph(
    "Elegiste la opción <b>(A)</b>. En castellano llano:<br/><br/>"
    "La flecha <font face=\"Courier\">a &#8594; b</font> del grafo se lee "
    "«<i>b</i> requiere <i>a</i>», y significa:<br/><br/>"
    "<b>una manera de obtener un objeto de <i>a</i> partiendo de un objeto de "
    "<i>b</i></b>.<br/><br/>"
    "Ojo: la construcción va <b>al revés</b> que la flecha. La flecha dice quién "
    "depende de quién; la construcción dice qué se extrae de qué.", TXT)))

# ── ejemplo ────────────────────────────────────────────────────────────────
add(Paragraph("Un ejemplo entero, para que se vea la forma", H2))
add(Paragraph(
    "Este par ya está resuelto y verificado. Sirve de plantilla: una respuesta "
    "tuya con esta forma es una respuesta completa.", TXT))

add(Paragraph("Las etiquetas", H3))
add(Paragraph(
    "El grafo tiene la flecha <font face=\"Courier\">group-theory &#8594; "
    "ring-theory</font>, o sea «la teoría de anillos requiere la de grupos».", TXT))

add(Paragraph("Qué nombra cada etiqueta", H3))
tabla_ej = Table([
    [Paragraph("<font face=\"Courier\">group-theory</font>", TXT),
     Paragraph("Un objeto es <b>un grupo</b>.", TXT)],
    [Paragraph("<font face=\"Courier\">ring-theory</font>", TXT),
     Paragraph("Un objeto es <b>un anillo</b>.", TXT)],
], colWidths=[5.2 * cm, 11 * cm])
tabla_ej.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LINEBELOW", (0, 0), (-1, -2), 0.4, LINEA),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
]))
add(tabla_ej)

add(Paragraph("Qué significa la flecha", H3))
add(Paragraph(
    "Por la regla (A): <b>una manera de sacar un grupo a partir de un "
    "anillo</b>. Y hay varias maneras clásicas, no una:", TXT))
tabla_m = Table([
    [Paragraph("<b>manera</b>", NOTA), Paragraph("<b>qué grupo sale</b>", NOTA),
     Paragraph("<b>sobre los enteros módulo 5</b>", NOTA)],
    [Paragraph("el grupo aditivo", TXT),
     Paragraph("los elementos del anillo, con la suma", TXT),
     Paragraph("<b>5</b> elementos", TXT)],
    [Paragraph("el grupo de unidades", TXT),
     Paragraph("solo los invertibles, con el producto", TXT),
     Paragraph("<b>4</b> elementos", TXT)],
    [Paragraph("el grupo trivial", TXT),
     Paragraph("siempre un único elemento", TXT),
     Paragraph("<b>1</b> elemento", TXT)],
], colWidths=[4.4 * cm, 7 * cm, 4.8 * cm])
tabla_m.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LINEBELOW", (0, 0), (-1, 0), 0.8, TINTA),
    ("LINEBELOW", (0, 1), (-1, -2), 0.4, LINEA),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
]))
add(tabla_m)
add(Spacer(1, 8))
add(Paragraph(
    "Cinco, cuatro y uno son distintos, así que las tres maneras son "
    "genuinamente distintas. Lean lo comprobó. <b>Eso es una respuesta "
    "completa</b>: qué nombra cada etiqueta, y cuántas maneras distintas hay.",
    TXT))

# ── PARTE 1 ────────────────────────────────────────────────────────────────
add(regla())
add(Paragraph("Parte 1 — Cuatro definiciones", H2))
add(Paragraph(
    "Completa la frase «<i>Un objeto de esta etiqueta es…</i>» para cada una. "
    "Con estas cuatro cierro quince de las diecisiete preguntas que quedan.", TXT))

filas = [[Paragraph("<b>etiqueta del grafo</b>", NOTA),
          Paragraph("<b>un objeto de esta etiqueta es…</b>", NOTA),
          Paragraph("<b>mi conjetura</b>", NOTA)]]
for etq, conj in [
    ("functors", "¿una categoría? ¿un funtor entre dos categorías fijas? "
                 "¿o no es una colección de objetos?"),
    ("homological-algebra", "¿un complejo de cadenas sobre un anillo?"),
    ("homological-algebra-cat", "¿una categoría abeliana?"),
    ("homology", "¿un grupo abeliano graduado?"),
]:
    filas.append([
        Paragraph(f"<font face=\"Courier\">{etq}</font>", TXT),
        Paragraph("<font color='#aaaaaa'>_______________________</font>", TXT),
        Paragraph(conj, NOTA),
    ])
t1 = Table(filas, colWidths=[4.9 * cm, 5.3 * cm, 6 * cm])
t1.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LINEBELOW", (0, 0), (-1, 0), 0.8, TINTA),
    ("LINEBELOW", (0, 1), (-1, -2), 0.4, LINEA),
    ("TOPPADDING", (0, 0), (-1, -1), 7),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
]))
add(t1)
add(Spacer(1, 10))
add(caja(Paragraph(
    "<b>«Esa etiqueta no nombra una colección de objetos, es un tema del "
    "temario»</b> es una respuesta válida, y de las más útiles. Significaría "
    "que el grafo mezcla nodos-categoría con nodos-tema, y que esta maquinaria "
    "solo aplica a los primeros. Sería un resultado, no un fracaso.",
    TXT), color=ROJO, relleno=colors.HexColor("#f8ece9")))

# ── PARTE 2 ────────────────────────────────────────────────────────────────
add(regla())
add(Paragraph("Parte 2 — Cuatro grupos de caminos", H2))
add(Paragraph(
    "El grafo tiene varios caminos entre las mismas dos etiquetas. Cada camino, "
    "leído con la regla (A), describe una manera de extraer un objeto. "
    "La pregunta es siempre la misma: <b>¿describen todos la misma manera, o "
    "maneras distintas?</b>", TXT))
add(Paragraph(
    "Recuerda que se leen de derecha a izquierda: el camino "
    "<font face=\"Courier\">a &#8594; x &#8594; b</font> significa «de un objeto "
    "de <i>b</i> saco uno de <i>x</i>, y de ese saco uno de <i>a</i>».", NOTA))

GRUPOS = [
    ("homological-algebra", "homology",
     [["homological-algebra", "homology"],
      ["homological-algebra", "algebraic-topology", "homology"]],
     "Partiendo de un objeto de <font face=\"Courier\">homology</font>, "
     "¿sacar directamente un objeto de <font face=\"Courier\">homological-algebra"
     "</font> es lo mismo que pasar antes por "
     "<font face=\"Courier\">algebraic-topology</font>?"),
    ("field-theory", "arithmetic-geometry",
     [["field-theory", "arithmetic-geometry"],
      ["field-theory", "algebraic-number-theory", "arithmetic-geometry"]],
     "¿Da lo mismo extraer el cuerpo directamente que pasar antes por la "
     "teoría algebraica de números?"),
    ("fol-deduction", "strategy-contradiction",
     [["fol-deduction", "strategy-contradiction"],
      ["fol-deduction", "cic", "tactic-exact", "strategy-contradiction"]],
     "Aquí sospecho que la respuesta es que la pregunta no tiene sentido: "
     "estas etiquetas son tácticas y estrategias de prueba, no categorías. "
     "Si es así, dímelo y las retiro."),
    ("functors", "homological-algebra-cat",
     [["functors", "homological-algebra-cat"],
      ["functors", "homological-algebra", "homological-algebra-cat"],
      ["functors", "algebraic-geometry", "homological-algebra-cat"],
      ["functors", "limits", "homological-algebra-cat"],
      ["functors", "operator-theory", "homological-algebra-cat"]],
     "<b>Este grupo es el grueso: catorce de las diecisiete preguntas.</b> Hay "
     "cinco caminos distintos por los nodos; las comparaciones salen a catorce "
     "porque entre algunos pares hay más de una flecha. Si me dices «todos "
     "coinciden» o «ninguno coincide», cierro el grupo entero de golpe."),
]

for origen, destino, rutas, comentario in GRUPOS:
    bloque = [
        Paragraph(f"De <font face=\"Courier\">{destino}</font> "
                  f"hacia <font face=\"Courier\">{origen}</font>", H3),
        Paragraph(f"<b>{len(rutas)} caminos</b> en el grafo:", TXT),
    ]
    for r in rutas:
        bloque.append(Paragraph("&nbsp;&nbsp;&#183;&nbsp; " +
                                " &#8594; ".join(r), MONO))
    bloque.append(Spacer(1, 6))
    bloque.append(Paragraph(comentario, TXT))
    bloque.append(Spacer(1, 4))
    add(KeepTogether(bloque))

# ── cómo contestar ─────────────────────────────────────────────────────────
add(regla())
add(Paragraph("Cómo contestar", H2))
add(Paragraph(
    "No hace falta formato ni rigor. Basta con frases como estas:", TXT))
for ej in [
    "«Un objeto de <font face=\"Courier\">homology</font> es un grupo abeliano graduado.»",
    "«<font face=\"Courier\">functors</font> no es una categoría, es un tema del temario.»",
    "«En el grupo de <font face=\"Courier\">functors</font>, todos los caminos coinciden.»",
    "«Los dos primeros coinciden, el de <font face=\"Courier\">operator-theory</font> no.»",
    "«No lo sé.»",
]:
    add(Paragraph("&nbsp;&nbsp;&#183;&nbsp; " + ej, TXT))

add(Spacer(1, 6))
add(caja(Paragraph(
    "<b>«No lo sé» también sirve.</b> Prefiero un hueco declarado a una "
    "respuesta inventada — es la misma regla que hemos seguido todo el tiempo "
    "con Lean.", TXT), color=VERDE, relleno=colors.HexColor("#e6f2ef")))

# ── qué haré ───────────────────────────────────────────────────────────────
add(Paragraph("Qué haré con cada respuesta", H2))
t2 = Table([
    [Paragraph("<b>si contestas…</b>", NOTA), Paragraph("<b>entonces yo…</b>", NOTA)],
    [Paragraph("qué es cada etiqueta", TXT),
     Paragraph("escribo las preguntas de caminos como matemáticas de verdad y "
               "las llevo a Lean", TXT)],
    [Paragraph("que los caminos coinciden", TXT),
     Paragraph("lo declaro como relación de la congruencia y migro "
               "<font face=\"Courier\">find_colimit</font>", TXT)],
    [Paragraph("que NO coinciden", TXT),
     Paragraph("mejor todavía: es multiplicidad real, y es lo que puede "
               "producir emergencia", TXT)],
    [Paragraph("que la etiqueta no es una categoría", TXT),
     Paragraph("retiro ese nodo de la maquinaria y lo dejo escrito, como hice "
               "con los cuatro certificados retirados", TXT)],
], colWidths=[5.4 * cm, 10.8 * cm])
t2.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LINEBELOW", (0, 0), (-1, 0), 0.8, TINTA),
    ("LINEBELOW", (0, 1), (-1, -2), 0.4, LINEA),
    ("TOPPADDING", (0, 0), (-1, -1), 7),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
]))
add(t2)

add(Spacer(1, 14))
add(Paragraph(
    "Metamatemático &#183; generado el 27 de agosto de 2026 &#183; "
    "rama <font face=\"Courier\">emergencia-colimites</font>, commit "
    "<font face=\"Courier\">dd6b049</font>", NOTA))

doc = SimpleDocTemplate(
    SALIDA, pagesize=A4,
    leftMargin=2.4 * cm, rightMargin=2.4 * cm,
    topMargin=2.2 * cm, bottomMargin=2.0 * cm,
    title="Lo que hay que decidir",
    author="Metamatemático",
)
doc.build(E)
print("PDF ->", SALIDA)
