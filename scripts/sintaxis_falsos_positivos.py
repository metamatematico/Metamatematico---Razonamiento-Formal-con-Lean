# -*- coding: utf-8 -*-
"""Cuanta notacion BUENA rechaza el revisor de sintaxis, y cuanta MALA caza.

POR QUE ESTAS DOS CIFRAS Y NO UNA
---------------------------------
Un revisor que acepta todo tiene cero falsos positivos y no sirve; uno que
rechaza todo caza el 100 % de los errores y tampoco. La unica lectura honesta
es el PAR: cuanto rechaza de lo bueno y cuanto caza de lo malo.

EL MODELO NULO. Un revisor que tirara una moneda con probabilidad p rechazaria
una fraccion p de lo bueno y cazaria una fraccion p de lo malo: caeria sobre la
diagonal caza = rechazo. La distancia POR ENCIMA de esa diagonal es todo lo que
este revisor aporta sobre no mirar nada. Sin esa referencia, «caza el 78 %» no
significa nada.

LOS DATOS
---------
BUENO: los 23 243 enunciados en lenguaje natural de `data/banco_lemas.jsonl`,
que vienen de LeanWorkbook y estan todos bien escritos —los formalizo alguien y
Lean los acepto. Cualquier rechazo ahi es un falso positivo, sin discusion.

MALO: los mismos enunciados, rotos a proposito de cuatro maneras: se quita un
delimitador de apertura, se quita uno de cierre, se borra un operando al lado
de un operador binario, o se dobla un operador. La semilla es fija.

LO QUE ESTA MEDIDA NO DICE. Algunas mutaciones caen en sitios que no rompen
nada —quitar un parentesis de `(x)` deja `x`, que sigue bien formado—, asi que
la caza medida es un SUELO, no un techo. Se dice porque la tentacion de
presentarla como techo es exactamente el error del §12.1.
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import pathlib
import random
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from nucleo.sintaxis.arbol import bien_formada
from nucleo.sintaxis.lexico import ABRE, CIERRA

BINARIOS_TEXTO = ["+", "-", "*", "/", "=", "<", ">"]


def romper(texto: str, rng: random.Random) -> tuple[str, str] | None:
    """Rompe el enunciado de una de cuatro maneras. None si no se pudo."""
    modos = ["abre", "cierra", "operando", "doble"]
    rng.shuffle(modos)
    for modo in modos:
        if modo == "abre":
            pos = [i for i, c in enumerate(texto) if c in ABRE]
        elif modo == "cierra":
            pos = [i for i, c in enumerate(texto) if c in CIERRA]
        elif modo == "operando":
            pos = [i for i, c in enumerate(texto)
                   if c in BINARIOS_TEXTO and i + 2 < len(texto)]
        else:
            pos = [i for i, c in enumerate(texto) if c in BINARIOS_TEXTO]
        if not pos:
            continue
        i = rng.choice(pos)
        if modo == "operando":
            # borra lo que sigue al operador hasta el siguiente hueco
            j = i + 1
            while j < len(texto) and texto[j] == " ":
                j += 1
            k = j
            while k < len(texto) and not texto[k].isspace():
                k += 1
            if k == j:
                continue
            return texto[:j] + texto[k:], modo
        if modo == "doble":
            return texto[:i] + texto[i] + texto[i:], modo
        return texto[:i] + texto[i + 1:], modo
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--banco", default=str(RAIZ / "data" / "banco_lemas.jsonl"))
    ap.add_argument("--n", type=int, default=0, help="0 = todos")
    ap.add_argument("--semilla", type=int, default=20260904)
    ap.add_argument("--salida",
                    default=str(RAIZ / "data" / "sintaxis_falsos_positivos.json"))
    a = ap.parse_args()

    textos = []
    with io.open(a.banco, encoding="utf-8") as fh:
        for linea in fh:
            linea = linea.strip()
            if not linea:
                continue
            nl = (json.loads(linea).get("nl") or "").strip()
            if nl:
                textos.append(nl)
    if a.n:
        textos = textos[:a.n]
    print("enunciados buenos: %d" % len(textos))

    rng = random.Random(a.semilla)

    # ── lo bueno ────────────────────────────────────────────────────────
    rechazados = 0
    sin_notacion = 0
    porque: collections.Counter = collections.Counter()
    for t in textos:
        d = bien_formada(t)
        if d.arbol is None and d.ok:
            sin_notacion += 1
        if not d.ok:
            rechazados += 1
            porque[d.fallos[0] if d.fallos else "?"] += 1
    fpr = rechazados / max(1, len(textos))

    # ── lo malo ─────────────────────────────────────────────────────────
    cazados = 0
    rotos = 0
    por_modo: collections.Counter = collections.Counter()
    caza_modo: collections.Counter = collections.Counter()
    for t in textos:
        r = romper(t, rng)
        if r is None:
            continue
        malo, modo = r
        rotos += 1
        por_modo[modo] += 1
        if not bien_formada(malo).ok:
            cazados += 1
            caza_modo[modo] += 1
    tpr = cazados / max(1, rotos)

    print()
    print("  BUENO  rechazados      %6d / %6d = %5.1f %%  <- falsos positivos"
          % (rechazados, len(textos), 100 * fpr))
    print("         sin notacion    %6d          = %5.1f %%"
          % (sin_notacion, 100 * sin_notacion / max(1, len(textos))))
    print("  MALO   cazados         %6d / %6d = %5.1f %%"
          % (cazados, rotos, 100 * tpr))
    print()
    print("  modelo nulo (moneda):  caza = rechazo = %5.1f %%" % (100 * fpr))
    print("  ventaja sobre el nulo: %+5.1f puntos" % (100 * (tpr - fpr)))
    print()
    print("  por que se rechaza lo BUENO (falsos positivos):")
    for k, v in porque.most_common(8):
        print("      %-26s %5d  (%4.1f %% del total bueno)"
              % (k, v, 100 * v / max(1, len(textos))))
    print()
    print("  caza por tipo de rotura:")
    for k, v in por_modo.most_common():
        print("      %-12s %5d rotos, %5d cazados = %5.1f %%"
              % (k, v, caza_modo[k], 100 * caza_modo[k] / max(1, v)))

    pathlib.Path(a.salida).write_text(json.dumps({
        "n": len(textos),
        "falsos_positivos": rechazados,
        "tasa_falsos_positivos": fpr,
        "sin_notacion": sin_notacion,
        "rotos": rotos,
        "cazados": cazados,
        "tasa_caza": tpr,
        "nulo_moneda": fpr,
        "ventaja_sobre_nulo": tpr - fpr,
        "motivos_falso_positivo": dict(porque),
        "caza_por_modo": {k: {"rotos": por_modo[k], "cazados": caza_modo[k]}
                          for k in por_modo},
        "semilla": a.semilla,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print()
    print("escrito -> %s" % a.salida)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
