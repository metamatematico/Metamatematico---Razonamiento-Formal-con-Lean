# -*- coding: utf-8 -*-
"""Los sustantivos de Mathlib, indexados por modulo.

QUE RESUELVE
------------
`interpretacion.nombres_de_trabajo` devuelve "" para los 125 nodos generados,
y el comentario que lo justifica dice por que:

    «sus nombres estan DEDUCIDOS de la ruta del modulo, no comprobados. Al
     activarlos, la precision contra ProofNet caia de 13,5 % a 3,2 % con un
     nulo de 2,9 %. Se quedan fuera del prompt HASTA QUE PASEN POR LEAN.»

Esta lista es exactamente eso. Los nombres no se deducen de la ruta: se LEEN de
la declaracion en el fuente —si el fichero dice `class AddCommGroup`, el nombre
existe— y ademas se comprueban con `#check` sobre una muestra.

Deducir de `Mathlib/Algebra/Group/Basic.lean` que existe `Basic` es lo que
producia 95 nombres inexistentes de 447. Leer `def mul_comm` de ese fichero es
otra operacion, y por eso esta lista si puede inyectarse.

EL ORDEN EN QUE SE OFRECEN
--------------------------
Un modulo tiene cientos de sustantivos y en el prompt caben pocos, asi que el
orden decide todo. El primer intento ordenaba por TIPO y longitud —clases
antes que defs— y era ordenar por el azar de que se declaro primero:

    mathlib-analysis-real -> Real.Wallis.W, Hyperreal.st, Hyperreal.IsSt...

`Hyperreal.omega` no es lo que hace falta para una consulta sobre los reales.
Medido, esa version bajaba la precision contra ProofNet de 17,1 % a 12,0 %.

Ahora manda `citas`: cuantos ENUNCIADOS de Mathlib mencionan ese sustantivo,
contado sobre los 183 433 hechos. Es la propia biblioteca diciendo cuales usa.

    Finset 4813 · Set 2901 · Module 2690 · Filter.Tendsto 2562

APROXIMACION, y se dice: el conteo casa tambien por nombre corto, asi que
`Set` y `HasCardinalLT.Set` comparten cuenta. Y el filtro «4+ caracteres o con
`_` o `.`» es obligatorio — sin el, los mas citados salen `f`, `x`, `s` y `h`,
que son variables ligadas. Es el fallo de `the` como lema mas citado (§12.1),
que este proyecto ya cometio una vez.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

#: Desempate cuando dos sustantivos tienen las mismas citas: un enunciado
#: menciona clases y estructuras mas que defs auxiliares. Menor = antes.
_RANGO_TIPO = {"class": 0, "structure": 1, "inductive": 2, "abbrev": 3,
               "def": 4}

_POR_MODULO: Optional[dict[str, list[dict]]] = None
_POR_CONCEPTO: Optional[dict[str, list[dict]]] = None
_TODOS: Optional[list[dict]] = None


def _cargar() -> None:
    """Lee la lista una vez. Sin ella el sistema funciona igual, sin sustantivos."""
    global _POR_MODULO, _POR_CONCEPTO, _TODOS
    if _POR_MODULO is not None:
        return
    _POR_MODULO, _POR_CONCEPTO, _TODOS = {}, {}, []
    try:
        from nucleo.rutas import dato
        ruta = dato("sustantivos_mathlib.jsonl")
        with open(ruta, encoding="utf-8") as fh:
            for linea in fh:
                linea = linea.strip()
                if not linea:
                    continue
                r = json.loads(linea)
                _TODOS.append(r)
                _POR_MODULO.setdefault(r["modulo"], []).append(r)
                _POR_CONCEPTO.setdefault(r["concepto"], []).append(r)
    except Exception as e:                       # noqa: BLE001
        # Se avisa en WARNING, no en debug: una lista ausente que degrada en
        # silencio es justo el patron que este proyecto lleva cazando.
        logger.warning(
            "SIN LISTA DE SUSTANTIVOS (%s). El grafo seguira inyectando solo "
            "los nombres curados. Regenerar con: "
            "python scripts/construir_lista_sustantivos.py --escribir",
            type(e).__name__)
        return
    for d in (_POR_MODULO, _POR_CONCEPTO):
        for k in d:
            # MANDAN LAS CITAS. El tipo solo desempata.
            d[k].sort(key=lambda r: (-r.get("citas", 0),
                                     _RANGO_TIPO.get(r["tipo"], 9),
                                     len(r["corto"])))


def disponible() -> bool:
    _cargar()
    return bool(_TODOS)


def cuantos() -> int:
    _cargar()
    return len(_TODOS or ())


def de_modulo(modulo: str, k: int = 6) -> list[str]:
    """Los k sustantivos mas nombrables de un modulo, cualificados."""
    _cargar()
    return [r["nombre"] for r in (_POR_MODULO or {}).get(modulo, ())[:k]]


def de_concepto(concepto: str, k: int = 6) -> list[str]:
    """Igual, pero por concepto —`Algebra.Group`— que agrupa varios modulos."""
    _cargar()
    return [r["nombre"] for r in (_POR_CONCEPTO or {}).get(concepto, ())[:k]]


def para_nodo(metadata: dict, k: int = 6) -> list[str]:
    """Los sustantivos de un nodo del grafo, a partir de su metadata.

    Se prueba primero el modulo exacto y despues el concepto, que es mas
    ancho. Un nodo sin `modulo` —los curados— no pasa por aqui: esos ya
    tienen sus nombres comprobados a mano.
    """
    _cargar()
    mod = (metadata or {}).get("modulo") or ""
    if not mod:
        return []
    fuera = de_modulo(mod, k)
    if len(fuera) < k:
        concepto = ".".join(mod.replace("Mathlib.", "", 1).split(".")[:2])
        for n in de_concepto(concepto, k):
            if n not in fuera:
                fuera.append(n)
                if len(fuera) >= k:
                    break
    return fuera[:k]


_NOMBRES: Optional[set[str]] = None


def existe(nombre: str) -> bool:
    """¿Este identificador esta en la lista? Para la puerta previa a Lean.

    Acepta el nombre cualificado y el corto: el modelo escribe `Nat.succ_le`
    unas veces y `succ_le` otras, y las dos son citas legitimas segun el
    `open` que este vigente.
    """
    global _NOMBRES
    _cargar()
    if not _TODOS:
        return False
    if _NOMBRES is None:
        _NOMBRES = ({r["nombre"] for r in _TODOS}
                    | {r["corto"] for r in _TODOS})
    return nombre in _NOMBRES
