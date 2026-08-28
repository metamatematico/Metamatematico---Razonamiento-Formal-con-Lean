# -*- coding: utf-8 -*-
"""Genera el PDF con LAS 172 ETIQUETAS, exhaustivo y por prioridad."""
import sys, json, os
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conjeturas import CONJETURAS, PREFIJOS_TEMA

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)

DATOS = ("C:/Users/Leonardo/AppData/Local/Temp/claude/"
         "c--Users-Leonardo-OneDrive-Desktop-ProyectoPoloProofMAth-metamath-prover/"
         "08a7a56e-d06a-4e11-92c5-9201e41131dd/scratchpad/etiquetas.json")
SALIDA = "E:/Metamatematico/docs/LAS_172_ETIQUETAS.pdf"

TINTA  = colors.HexColor("#1b1e17")
SUAVE  = colors.HexColor("#4f5347")
GRIS   = colors.HexColor("#7a7c6d")
ACENTO = colors.HexColor("#564c9e")
VERDE  = colors.HexColor("#167a68")
ROJO   = colors.HexColor("#ae3b35")
LINEA  = colors.HexColor("#ddd6c2")
FONDO  = colors.HexColor("#f3f1ea")
HUECO  = colors.HexColor("#c9c4b4")

def P(n, **kw):
    b = dict(fontName="Helvetica", fontSize=10.2, leading=15,
             textColor=SUAVE, spaceAfter=8)
    b.update(kw)
    return ParagraphStyle(n, **b)

H1  = P("H1", fontName="Helvetica-Bold", fontSize=19, leading=23,
        textColor=TINTA, spaceAfter=4)
SUB = P("SUB", fontSize=11.5, leading=16, textColor=GRIS, spaceAfter=18)
H2  = P("H2", fontName="Helvetica-Bold", fontSize=13, leading=17,
        textColor=TINTA, spaceBefore=16, spaceAfter=6)
TXT = P("TXT")
NOTA = P("NOTA", fontSize=9.3, leading=13.2, textColor=GRIS)
CEL = P("CEL", fontSize=8.8, leading=11.6, spaceAfter=0)
CELM = P("CELM", fontName="Courier", fontSize=8.4, leading=11.6,
         textColor=TINTA, spaceAfter=0)
CELC = P("CELC", fontSize=8.4, leading=11.4, textColor=GRIS, spaceAfter=0)
CELT = P("CELT", fontSize=8.4, leading=11.4, textColor=ROJO, spaceAfter=0)
CAB = P("CAB", fontName="Helvetica-Bold", fontSize=8.6, leading=11,
        textColor=TINTA, spaceAfter=0)

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

d = json.load(open(DATOS, encoding="utf-8"))
meta = d["meta"]

def conjetura(eid):
    if eid.startswith(PREFIJOS_TEMA):
        return "TEMA — una táctica o estrategia de prueba, no una categoría"
    return CONJETURAS.get(eid, "")

def tabla(ids):
    filas = [[Paragraph("etiqueta", CAB), Paragraph("niv", CAB),
              Paragraph("un objeto de esta etiqueta es…", CAB),
              Paragraph("mi conjetura", CAB)]]
    for eid in ids:
        c = conjetura(eid)
        est = CELT if c.startswith("TEMA") else CELC
        filas.append([
            Paragraph(eid, CELM),
            Paragraph(str(meta[eid]["level"]), CEL),
            Paragraph("<font color='#c9c4b4'>______________</font>", CEL),
            Paragraph(c if c else "<font color='#c9c4b4'>—</font>", est),
        ])
    t = Table(filas, colWidths=[4.6 * cm, 0.9 * cm, 3.4 * cm, 7.3 * cm],
              repeatRows=1)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, TINTA),
        ("LINEBELOW", (0, 1), (-1, -2), 0.3, LINEA),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t

E = []
add = E.append

add(Paragraph("Las 172 etiquetas del grafo", H1))
add(Paragraph("Lista exhaustiva. Dime qué nombra cada una — o que no nombra "
              "nada matemático.", SUB))

add(Paragraph("Qué te pido", H2))
add(Paragraph(
    "Para cada etiqueta, completa la frase «<i>un objeto de esta etiqueta "
    "es…</i>». Ya puse mi conjetura al lado: si la das por buena, no escribas "
    "nada; solo corrige donde me equivoque.", TXT))
add(Paragraph(
    "Las marcadas en rojo como <font color='#ae3b35'><b>TEMA</b></font> son las "
    "que creo que <b>no nombran una colección de objetos matemáticos</b>, sino "
    "un tema del temario, una técnica o un teorema. Si acierto, esas quedan "
    "fuera de la maquinaria categórica — y eso es un resultado útil, no una "
    "pérdida.", TXT))

add(caja(Paragraph(
    "<b>La prueba para decidir si es TEMA o no.</b><br/><br/>"
    "Pregúntate: «¿puedo decir <i>sea X un ___</i>?»<br/><br/>"
    "«Sea <i>G</i> un grupo» — funciona. <font face=\"Courier\">group-theory</font> "
    "nombra objetos.<br/>"
    "«Sea <i>T</i> un teorema de incompletitud» — no funciona igual. "
    "<font face=\"Courier\">incompleteness</font> es un tema.", TXT)))

add(Paragraph("Cómo está ordenado", H2))
add(Paragraph(
    "Por urgencia. Puedes parar al final de cualquier bloque y ya me habrás "
    "desbloqueado ese tramo:", TXT))
t = Table([
    [Paragraph("<b>Bloque 1</b>", CEL), Paragraph("15 etiquetas", CEL),
     Paragraph("aparecen en las 17 preguntas pendientes — <b>me desbloquean ahora</b>", CEL)],
    [Paragraph("<b>Bloque 2</b>", CEL), Paragraph("32 etiquetas", CEL),
     Paragraph("participan en los 31 colímites — me desbloquean después", CEL)],
    [Paragraph("<b>Bloque 3</b>", CEL), Paragraph("125 etiquetas", CEL),
     Paragraph("el resto — sin prisa, pero hará falta algún día", CEL)],
], colWidths=[2.4 * cm, 2.6 * cm, 11.2 * cm])
t.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LINEBELOW", (0, 0), (-1, -2), 0.3, LINEA),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
]))
add(t)
add(Spacer(1, 8))
add(Paragraph(
    "La columna <b>niv</b> es el nivel taxonómico curado a mano: 0 fundacional, "
    "3 la rama más específica.", NOTA))

add(PageBreak())
add(Paragraph("Bloque 1 — Las 15 que me desbloquean ahora", H2))
add(Paragraph(
    "Estas quince aparecen en las diecisiete preguntas sobre caminos que tengo "
    "abiertas. Con estas puedo escribir las preguntas como matemáticas y "
    "llevarlas a Lean.", TXT))
add(tabla(d["b1"]))

add(PageBreak())
add(Paragraph("Bloque 2 — Las 32 de los colímites", H2))
add(Paragraph(
    "Son las componentes y los vértices de las 31 descomposiciones que el "
    "sistema ha descubierto. Serán las siguientes en hacer falta.", TXT))
add(tabla(d["b2"]))

add(PageBreak())
add(Paragraph("Bloque 3 — Las 125 restantes", H2))
add(Paragraph(
    "El resto del grafo. Sospecho que aquí está la mayoría de los TEMA, sobre "
    "todo entre las tácticas, las estrategias de prueba y los teoremas con "
    "nombre.", TXT))
add(tabla(d["b3"]))

add(PageBreak())
add(Paragraph("Qué haré con tus respuestas", H2))
t2 = Table([
    [Paragraph("<b>si dices…</b>", CAB), Paragraph("<b>entonces yo…</b>", CAB)],
    [Paragraph("«un objeto es un <i>tal</i>»", CEL),
     Paragraph("interpreto la etiqueta como esa categoría y puedo enunciar en "
               "Lean las preguntas sobre caminos que la involucran", CEL)],
    [Paragraph("«es TEMA»", CEL),
     Paragraph("retiro la etiqueta de la maquinaria categórica y lo dejo "
               "escrito, con el motivo — como hice con los cuatro certificados "
               "que tuve que retirar", CEL)],
    [Paragraph("«no lo sé»", CEL),
     Paragraph("la dejo pendiente y sigo con las demás; un hueco declarado "
               "vale más que una respuesta inventada", CEL)],
    [Paragraph("nada (aceptas mi conjetura)", CEL),
     Paragraph("la doy por buena y la marco como conjetura del sistema, no "
               "como decisión tuya", CEL)],
], colWidths=[4.4 * cm, 11.8 * cm])
t2.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LINEBELOW", (0, 0), (-1, 0), 0.8, TINTA),
    ("LINEBELOW", (0, 1), (-1, -2), 0.3, LINEA),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
]))
add(t2)

add(Spacer(1, 12))
add(caja(Paragraph(
    "<b>Si resulta que la mayoría son TEMA</b>, eso no invalida el trabajo: "
    "significa que el grafo mezcla dos clases de nodo —los que nombran "
    "categorías y los que nombran temas— y que la teoría de Ehresmann solo "
    "aplica a los primeros. Saberlo cambiaría el alcance de todo lo construido, "
    "y es justo el tipo de cosa que conviene descubrir pronto.",
    TXT), color=VERDE, relleno=colors.HexColor("#e6f2ef")))

add(Spacer(1, 12))
add(Paragraph(
    "Metamatemático &#183; 27 de agosto de 2026 &#183; rama "
    "<font face=\"Courier\">emergencia-colimites</font> &#183; "
    "172 etiquetas, 15 + 32 + 125", NOTA))

doc = SimpleDocTemplate(
    SALIDA, pagesize=A4,
    leftMargin=2.4 * cm, rightMargin=2.4 * cm,
    topMargin=2.0 * cm, bottomMargin=1.8 * cm,
    title="Las 172 etiquetas del grafo", author="Metamatemático",
)
doc.build(E)

n_tema = sum(1 for i in meta if conjetura(i).startswith("TEMA"))
n_conj = sum(1 for i in meta if conjetura(i))
print("PDF ->", SALIDA)
print(f"  etiquetas: {len(meta)}")
print(f"  con conjetura mía: {n_conj}   sin conjetura: {len(meta) - n_conj}")
print(f"  que creo TEMA: {n_tema}")
