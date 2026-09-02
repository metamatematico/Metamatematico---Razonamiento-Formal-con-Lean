# -*- coding: utf-8 -*-
"""Los 125 nodos sin interpretar: de dónde salió cada uno, para poder curarlos.

QUE SON. El grafo tiene 298 nodos: 173 curados a mano, con veredicto categórico
—«un objeto es un grupo, las flechas son homomorfismos»— y 125 generados desde
la taxonomía de Mathlib. Estos últimos llevan `interpretado=False` porque nadie
ha decidido qué son categóricamente: sólo dicen DÓNDE VIVE algo.

PARA QUE SIRVE ESTE INFORME. Para interpretarlos. Y para eso hace falta saber
de qué fuente salió cada dato, porque no todos merecen la misma confianza:

    docstring propio   el módulo tiene su `/-! # ... -/`. Fiable.
    Basic o Defs       se tomó del fichero base del concepto. Fiable.
    títulos            no había docstring propio y se juntaron los títulos del
                       subárbol. ORIENTATIVO — describe qué hay dentro, no qué
                       es el concepto.
    sólo palabras      no había ni títulos. El nombre y su vocabulario.
                       El más flojo, y el que primero hay que mirar.

Esa distinción es la mitad del valor del informe: un nodo descrito por su
propio docstring casi no necesita revisión, y uno descrito por palabras sueltas
la necesita entera.

TAMBIEN SE RASTREA:
  · cuántos teoremas hay debajo — el peso, y por qué entró (umbral 200)
  · el módulo exacto de Mathlib del que salió
  · sus dependencias, que vienen del DAG de imports y son REALES
  · los identificadores que propone, que están DEDUCIDOS de la ruta y NO
    comprobados con `#check` — por eso hoy no se inyectan

    python scripts/informe_nodos_sin_interpretar.py
"""
import argparse
import collections
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MATH = "E:/Metamatematico/.lake/packages/mathlib/Mathlib"
PDF = "E:/Metamatematico/docs/nodos_sin_interpretar.pdf"
CSV = "E:/Metamatematico/data/nodos_sin_interpretar.csv"
DOC = re.compile(r"/-!(.*?)-/", re.S)


def procedencia(modulo):
    """De qué fichero salió la descripción, y cuánto pesa el concepto."""
    base = MATH + "/" + modulo.replace("Mathlib.", "", 1).replace(".", "/")
    fuente = "sólo palabras"
    if os.path.exists(base + ".lean"):
        txt = io.open(base + ".lean", encoding="utf-8", errors="replace").read()
        if DOC.search(txt):
            fuente = "docstring propio"
    if fuente == "sólo palabras":
        for h in ("Basic", "Defs"):
            p = "%s/%s.lean" % (base, h)
            if os.path.exists(p):
                txt = io.open(p, encoding="utf-8", errors="replace").read()
                if DOC.search(txt):
                    fuente = h
                    break
    # peso: teoremas y ficheros bajo el subárbol
    teo = fich = 0
    if os.path.isdir(base):
        for r, _d, fs in os.walk(base):
            for f in fs:
                if not f.endswith(".lean"):
                    continue
                fich += 1
                try:
                    t = io.open(os.path.join(r, f), encoding="utf-8",
                                errors="replace").read()
                except Exception:
                    continue
                teo += len(re.findall(r"^\s*(?:@\[[^\]]*\]\s*)?"
                                      r"(?:private\s+|protected\s+)?"
                                      r"(?:theorem|lemma)\s+", t, re.M))
    if os.path.exists(base + ".lean"):
        fich += 1
    if fuente == "sólo palabras" and fich:
        fuente = "títulos del subárbol"
    return fuente, teo, fich


def main(_):
    from nucleo.pillars.mathlib_taxonomy import NODOS_MATHLIB
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, PageBreak)

    print("rastreando la procedencia de %d nodos..." % len(NODOS_MATHLIB))
    filas = []
    for n in NODOS_MATHLIB:
        f, teo, fich = procedencia(n.modulo)
        filas.append({
            "id": n.id, "nombre": n.name, "modulo": n.modulo,
            "descripcion": n.description, "fuente": f,
            "teoremas": n.teoremas, "teoremas_verificado": teo,
            "ficheros": fich, "pilar": n.pillar, "categoria": n.category,
            "deps": list(n.dependencies), "nombres": list(getattr(n, "nombres", [])),
            "keywords": list(n.keywords)[:8],
        })
    filas.sort(key=lambda r: -r["teoremas"])

    c = collections.Counter(r["fuente"] for r in filas)
    print("  procedencia de la descripción:", dict(c))
    print("  áreas:", dict(collections.Counter(r["categoria"] for r in filas)))

    # ── CSV, para poder trabajar sobre él ─────────────────────────────────
    import csv
    with io.open(CSV, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "modulo", "teoremas", "fuente_descripcion", "pilar",
                    "categoria", "descripcion", "dependencias", "nombres",
                    "INTERPRETACION_objeto", "INTERPRETACION_morfismos"])
        for r in filas:
            w.writerow([r["id"], r["modulo"], r["teoremas"], r["fuente"],
                        r["pilar"], r["categoria"], r["descripcion"],
                        " | ".join(r["deps"]), " | ".join(r["nombres"]),
                        "", ""])
    print("  -> %s" % CSV)

    # ── PDF ────────────────────────────────────────────────────────────────
    est = getSampleStyleSheet()
    H1 = ParagraphStyle("H1", parent=est["Title"], fontSize=17, leading=21,
                        spaceAfter=4, textColor=colors.HexColor("#1b1e17"))
    LEAD = ParagraphStyle("lead", parent=est["Normal"], fontSize=9.2, leading=13,
                          textColor=colors.HexColor("#4f5347"), spaceAfter=3)
    H2 = ParagraphStyle("H2", parent=est["Heading2"], fontSize=11.5, leading=14,
                        spaceBefore=10, spaceAfter=4,
                        textColor=colors.HexColor("#564c9e"))
    CEL = ParagraphStyle("cel", parent=est["Normal"], fontSize=7.1, leading=8.6)
    CELm = ParagraphStyle("celm", parent=CEL, fontName="Courier", fontSize=6.6,
                          leading=8.2)
    CAB = ParagraphStyle("cab", parent=CEL, fontSize=7, leading=8.5,
                         textColor=colors.white)

    doc = SimpleDocTemplate(PDF, pagesize=landscape(A4),
                            leftMargin=12 * mm, rightMargin=12 * mm,
                            topMargin=12 * mm, bottomMargin=12 * mm,
                            title="Los 125 nodos sin interpretar",
                            author="Metamatemático")
    el = []
    el.append(Paragraph("Los %d nodos sin interpretar" % len(filas), H1))
    el.append(Paragraph(
        "Generados desde la taxonomía de Mathlib y marcados "
        "<b>interpretado=False</b>: dicen <i>dónde vive</i> algo, no qué es "
        "categóricamente. Ordenados por peso — cuántos teoremas hay debajo — "
        "porque interpretar primero los grandes rinde más.", LEAD))
    el.append(Paragraph(
        "<b>La columna que decide cuánto revisar es «fuente».</b> "
        "<i>docstring propio</i> y <i>Basic/Defs</i> son texto que un "
        "matemático escribió para ese concepto. <i>títulos del subárbol</i> "
        "describe qué hay dentro, no qué es. <i>sólo palabras</i> es el nombre "
        "y su vocabulario: ésos hay que mirarlos enteros.", LEAD))
    el.append(Paragraph(
        "Las <b>dependencias son reales</b> — salen del DAG de imports de "
        "Mathlib, que es acíclico y no lo escribió nadie a mano. Los "
        "<b>nombres están deducidos</b> de la ruta del módulo y NO comprobados "
        "con <font face='Courier'>#check</font>: por eso hoy no se inyectan al "
        "prompt.", LEAD))
    el.append(Spacer(1, 4 * mm))

    resumen = [[Paragraph("<b>fuente de la descripción</b>", CEL),
                Paragraph("<b>cuántos</b>", CEL),
                Paragraph("<b>qué significa para la revisión</b>", CEL)]]
    QUE = {
        "docstring propio": "el módulo tiene su propio docstring · casi no necesita revisión",
        "Basic": "tomado de su fichero Basic · fiable",
        "Defs": "tomado de su fichero Defs · fiable",
        "títulos del subárbol": "sin docstring propio · describe el contenido, no el concepto",
        "sólo palabras": "sin docstring ni títulos · REVISAR ENTERO",
    }
    for f, k in c.most_common():
        resumen.append([Paragraph(f, CEL), Paragraph(str(k), CEL),
                        Paragraph(QUE.get(f, ""), CEL)])
    t = Table(resumen, colWidths=[42 * mm, 18 * mm, 120 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eee9dc")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#ddd6c2")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    el.append(t)
    el.append(PageBreak())

    # ── la tabla larga, por área ──────────────────────────────────────────
    ANCHOS = [40 * mm, 15 * mm, 26 * mm, 84 * mm, 50 * mm, 58 * mm]
    CABE = [Paragraph("<b>nodo · módulo de Mathlib</b>", CAB),
            Paragraph("<b>teoremas</b>", CAB),
            Paragraph("<b>fuente</b>", CAB),
            Paragraph("<b>descripción</b>", CAB),
            Paragraph("<b>depende de</b>", CAB),
            Paragraph("<b>nombres que propone · sin verificar</b>", CAB)]

    por_area = collections.defaultdict(list)
    for r in filas:
        por_area[r["categoria"]].append(r)

    for area in sorted(por_area, key=lambda a: -sum(x["teoremas"]
                                                    for x in por_area[a])):
        rs = por_area[area]
        el.append(Paragraph("%s — %d nodos · %d teoremas"
                            % (area, len(rs), sum(x["teoremas"] for x in rs)), H2))
        datos = [CABE]
        for r in rs:
            datos.append([
                Paragraph("<b>%s</b><br/><font face='Courier' size='6'>%s</font>"
                          % (r["id"].replace("mathlib-", ""), r["modulo"]), CEL),
                Paragraph("%d" % r["teoremas"], CEL),
                Paragraph(r["fuente"], CEL),
                Paragraph(r["descripcion"][:230], CEL),
                Paragraph(", ".join(d.replace("mathlib-", "")
                                    for d in r["deps"]) or "—", CELm),
                Paragraph(", ".join(r["nombres"]) or "—", CELm),
            ])
        t = Table(datos, colWidths=ANCHOS, repeatRows=1)
        est_t = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#564c9e")),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#ddd6c2")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ]
        # LAS QUE HAY QUE REVISAR ENTERAS, MARCADAS.
        #
        # Ninguna cayo en «solo palabras» —todas tienen al menos titulos— asi
        # que el escalon mas flojo presente es «titulos del subarbol»: 24
        # nodos descritos por lo que hay DENTRO y no por lo que SON. Esos son
        # los que necesitan la revision completa, y van marcados.
        DEBILES = ("títulos del subárbol", "sólo palabras")
        for i, r in enumerate(rs, start=1):
            if r["fuente"] in DEBILES:
                est_t.append(("BACKGROUND", (0, i), (-1, i),
                              colors.HexColor("#f6dfdc")))
            elif i % 2 == 0:
                est_t.append(("BACKGROUND", (0, i), (-1, i),
                              colors.HexColor("#faf9f5")))
        t.setStyle(TableStyle(est_t))
        el.append(t)

    doc.build(el)
    print("\n  -> %s (%.0f KB)" % (PDF, os.path.getsize(PDF) / 1024))
    debiles = sum(1 for r in filas
                  if r["fuente"] in ("títulos del subárbol", "sólo palabras"))
    print("     %d nodos · %d áreas" % (len(filas), len(por_area)))
    print("     %d marcados en rojizo: descritos por lo que contienen, no por "
          "lo que son" % debiles)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    a = ap.parse_args()
    sys.exit(main(a))
