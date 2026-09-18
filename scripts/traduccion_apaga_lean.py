# -*- coding: utf-8 -*-
"""Cuantas consultas en español dejaban de ser matematicas al traducirse.

EL FALLO
--------
La consulta canonica del proyecto:

    «Demuestra que la raiz cuadrada de 2 es irracional»

El traductor —`Helsinki-NLP/opus-mt-es-en`, 74 M de parametros— la convierte
en «It shows that the square root of 2 is irrational.»: el IMPERATIVO se
vuelve DECLARATIVO. Y `_is_mathematical` se evaluaba sobre esa traduccion, no
sobre lo que escribio el alumno, asi que contestaba False y la consulta no
llegaba a Lean. Devolvia prosa plausible SIN VERIFICAR — exactamente lo que
este sistema existe para no hacer.

Las dos piezas estaban bien por separado: el traductor traduce y el
clasificador clasifica. Lo que estaba mal era el ORDEN.

QUE MIDE ESTE SCRIPT
--------------------
Sobre un banco de consultas en español, cuantas cambian de veredicto al pasar
por el traductor. Es el tamaño del agujero, y es determinista: no gasta API ni
Lean.

    python -m scripts.traduccion_apaga_lean
"""
from __future__ import annotations

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

#: Consultas como las escribe un alumno: en español y en imperativo.
#:
#: No son inventadas para que fallen — son las formas que usa quien pide una
#: demostracion. El imperativo es justo lo que el traductor pierde.
CONSULTAS = [
    "Demuestra que la raiz cuadrada de 2 es irracional",
    "Demuestra que la raíz cuadrada de 2 es irracional",
    "Demuestra que todo espacio vectorial tiene una base",
    "Demuestra que hay infinitos numeros primos",
    "Demuestra que todo grupo de orden primo es ciclico",
    "Prueba que la suma de dos numeros pares es par",
    "Prueba que el conjunto vacio es subconjunto de cualquier conjunto",
    "Demuestra el teorema de Pitagoras",
    "Demuestra que la funcion identidad es continua",
    "Verifica que 17 es un numero primo",
    "Demuestra que todo anillo conmutativo con unidad tiene un ideal maximal",
    "Prueba por induccion que la suma de los primeros n naturales es n(n+1)/2",
]


def main() -> int:
    import warnings
    import logging
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)

    from nucleo.core import Nucleo
    from nucleo.graph.traductor import al_ingles

    n = Nucleo.__new__(Nucleo)

    print("%-52s %-6s %-6s" % ("consulta (original)", "orig", "trad"))
    print("-" * 78)
    rotas = []
    for q in CONSULTAS:
        antes = Nucleo._is_mathematical(n, q)
        try:
            en, _ = al_ingles(q)
        except Exception as exc:                                # noqa: BLE001
            print("  traductor no disponible: %s" % exc)
            return 1
        despues = Nucleo._is_mathematical(n, en)
        marca = "  <-- SE APAGA" if (antes and not despues) else ""
        print("  %-50s %-6s %-6s%s" % (q[:50], antes, despues, marca))
        if antes and not despues:
            rotas.append((q, en))

    print("\n%d de %d consultas dejaban de ser matematicas al traducirse"
          % (len(rotas), len(CONSULTAS)))
    for q, en in rotas:
        print("\n   %s" % q)
        print("   -> %s" % en)

    print("\nCON EL ARREGLO —preguntar tambien por el original— las %d vuelven "
          "a\nformalizarse: `_es_consulta_matematica` mira las dos, y ante la "
          "duda\nformaliza, porque un falso positivo cuesta una compilacion y "
          "un falso\nnegativo apaga el producto." % len(rotas))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
