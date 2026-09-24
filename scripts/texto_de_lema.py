# -*- coding: utf-8 -*-
"""Cómo se representa un lema de `data/lemas_mathlib.jsonl` para buscarlo.

Lo usan los bancos de premisas (`premisas_sin_simp.py`, que es la evidencia de
`premisas_hibridas`, `banco_premisas_mathlib.py` y
`orden_del_grafo_en_premisas.py`). Vivía en `medir_recuperacion_lemas.py`, el
banco de la recuperación léxica de lemas, que se quitó con su capacidad: medía
0,065 de precisión contra 7,78 de su nulo (ver `data/descartado.json`).
"""


def _texto(d):
    """Como se representa un lema para buscarlo: su nombre y su enunciado.

    El NOMBRE importa tanto como el enunciado: `sq_nonneg` lleva escrito
    «cuadrado» y «no negativo», que es justo lo que casa con la consulta.
    """
    nombre = d["nombre"].replace(".", " ").replace("_", " ")
    return nombre + " . " + d["enunciado"]
