# -*- coding: utf-8 -*-
"""La retroalimentación: lo que el modelo ve de un estado, y cómo se lee su
respuesta.

Es el contrato entre el mediador y D3 (§5 de la propuesta), y es donde se juega
el lazo. El repositorio ya aprendió tres veces la misma lección en
`_revisar_con_lean`: el arreglo consistía en pasarle al modelo un dato que el
sistema ya tenía. Y `techo_de_la_restriccion.json` cierra la otra puerta:
cambiar un nombre inventado por el más parecido rescata 0 y rompe 0. Lo que le
falta al modelo no es el nombre, es la FORMA; por eso cada nombre que falló
viaja con su enunciado.

CADA CAMPO SE PUEDE QUITAR (`campos=`), y es a propósito: sin eso la ablación
que dice qué campo explica la mejora no se podría hacer desde los registros.
"""
from __future__ import annotations

import json
import re
from typing import Optional

#: todos los campos, en el orden en que se le presentan al modelo
CAMPOS = ("objetivos", "camino", "fallidos_aqui", "firmas", "ranker")

#: lo que se recorta de cada mensaje de Lean: suficiente para entender el
#: fallo, no tanto como para que `apply?` llene el prompt con 200 sugerencias
RECORTE = 300

SISTEMA = (
    "You are the tactic proposer inside a step-by-step Lean 4 proof search. "
    "You see ONE proof state and what has already failed on it. Propose single "
    "Lean 4 tactics for the MAIN goal. Rules: one tactic per candidate, on one "
    "line; never use sorry, admit, native_decide or apply?; do not repeat a "
    "tactic listed under fallidos_aqui; use only Mathlib names you are sure "
    "exist, and when a name failed, read its real signature under firmas. "
    "Answer ONLY with JSON: {\"candidatos\": [{\"tactica\": \"...\", "
    "\"razon\": \"...\"}]}")


def construir(nodo, k: int = 4, firmas: Optional[dict] = None,
              ranker: Optional[list] = None, campos=CAMPOS) -> dict:
    """El dict de la §5 para un nodo del mediador."""
    r: dict = {}
    if "objetivos" in campos:
        r["estado"] = {"id": nodo.id, "profundidad": nodo.profundidad,
                       "objetivos": list(nodo.objetivos)}
    if "camino" in campos:
        r["camino"] = list(nodo.camino)
    if "fallidos_aqui" in campos:
        r["fallidos_aqui"] = [
            {"tactica": f["tactica"], "clase": f["clase"],
             "lean": (f.get("lean") or "")[:RECORTE]}
            for f in nodo.fallos]
    if "firmas" in campos and firmas:
        r["firmas"] = dict(firmas)
    if "ranker" in campos and ranker:
        r["ranker"] = [[t, round(float(p), 2)] for t, p in ranker]
    r["pide"] = ("hasta %d tácticas para el objetivo principal; una táctica "
                 "por candidato" % k)
    return r


def prompt(retro: dict) -> str:
    return ("Proof state and feedback:\n\n"
            + json.dumps(retro, ensure_ascii=False, indent=1)
            + "\n\nReply with the JSON object only.")


_BLOQUE_JSON = re.compile(r"\{[\s\S]*\}")
_CERCA = re.compile(r"```(?:json|lean)?\s*([\s\S]*?)```")


def leer(texto: str, k: int = 4) -> list:
    """Las tácticas que el modelo propuso, en su orden, sin repetir.

    Primero el JSON que se pidió. Si el modelo no lo respetó, se acepta un
    bloque de código o una lista de líneas: perder una respuesta por su
    formato es perder una llamada pagada. Lo que se lee aquí NO se da por
    bueno —pasa por los filtros y por Lean—, así que ser tolerante al leer no
    compromete nada.
    """
    t = (texto or "").strip()
    fuera: list = []
    m = _BLOQUE_JSON.search(t)
    if m:
        try:
            d = json.loads(m.group(0))
            for c in d.get("candidatos") or []:
                tac = c.get("tactica") if isinstance(c, dict) else c
                if isinstance(tac, str):
                    fuera.append(tac.strip())
        except Exception:                                      # noqa: BLE001
            pass
    if not fuera:
        cuerpo = _CERCA.search(t)
        bruto = cuerpo.group(1) if cuerpo else t
        for l in bruto.splitlines():
            l = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", l).strip().strip("`")
            if l and not l.startswith(("{", "}", "#", "//")):
                fuera.append(l)
    vistos, unicos = set(), []
    for tac in fuera:
        if tac and tac not in vistos:
            vistos.add(tac)
            unicos.append(tac)
    return unicos[:k]
