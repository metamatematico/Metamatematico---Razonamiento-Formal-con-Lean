# -*- coding: utf-8 -*-
"""φ: de qué conceptos del grafo habla un estado de prueba (paso 5).

QUÉ ES, Y QUÉ NO ES (§2 de la propuesta)
----------------------------------------
Un mapa de objetos φ : Ob(E) → 𝒫(Ob(C)): los conceptos del grafo cuyos nombres
VERIFICADOS de Mathlib aparecen en el estado, por coincidencia EXACTA y sin
expandir al espacio de nombres —la regla que hizo fiable a L4
(`scripts/l4_coocurrencia_verificada.py`)—. NO es un funtor, y no se trata
como tal: una táctica s → s′ no obliga a que haya relación en C entre φ(s) y
φ(s′).

Sirve para EXPLICAR, no para buscar: el alumno ve «este paso pasó de hablar de
subgrupos a hablar de órdenes», y la búsqueda no lo usa.

EL DETALLE QUE DECIDE SI FUNCIONA
---------------------------------
Lean imprime los estados con notación: `ℝ`, `∑`, `√`, `‖x‖`, y no `Real`,
`Finset.sum`, `Real.sqrt`, `Norm.norm`. Buscar los nombres del grafo en el
texto impreso pierde lo que la notación esconde. Así que φ tiene DOS lecturas,
y se miden una contra otra:

    phi_texto        los identificadores del estado impreso        (gratis)
    phi_constantes   las constantes que Lean dice que usa el estado (una táctica)

La segunda es la táctica `metamat_constantes` de abajo: se define una vez en
el entorno de la sesión y devuelve las constantes de las hipótesis y del
objetivo, que es lo que el estado ES y no cómo se imprime.
"""
from __future__ import annotations

import collections
import re
from typing import Optional

#: la táctica que lee las constantes de un estado. Se define con `comando` en
#: el entorno de la sesión ANTES de plantar el teorema; no cambia el estado,
#: sólo informa.
TACTICA_CONSTANTES = '''open Lean Elab Tactic Meta in
elab "metamat_constantes" : tactic => do
  let g ← getMainGoal
  g.withContext do
    let mut cs : NameSet := {}
    for d in ← getLCtx do
      unless d.isImplementationDetail do
        for c in (← instantiateMVars d.type).getUsedConstants do
          cs := cs.insert c
    for c in (← instantiateMVars (← g.getType)).getUsedConstants do
      cs := cs.insert c
    logInfo m!"METAMAT_CONSTANTES {cs.toList}"'''

_MARCA = "METAMAT_CONSTANTES"
_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_.']*")


def indice(grafo) -> dict:
    """nombre EXACTO de Mathlib -> conceptos que lo declaran (la regla de L4)."""
    from nucleo.graph.interpretacion import nombres_de_trabajo
    por_nombre = collections.defaultdict(set)
    for s in grafo.skill_ids:
        for p in re.split(r"[,+]", nombres_de_trabajo(s) or ""):
            p = p.strip().split()[0] if p.strip() else ""
            if p:
                por_nombre[p].add(s)
    return dict(por_nombre)


def conceptos(nombres, por_nombre: dict) -> set:
    fuera = set()
    for n in nombres:
        fuera |= por_nombre.get(n, set())
    return fuera


def phi_texto(estado: str, por_nombre: dict) -> set:
    """Los conceptos cuyos nombres aparecen en el estado IMPRESO."""
    return conceptos(set(_TOKEN.findall(estado or "")), por_nombre)


def leer_constantes(mensajes) -> list:
    """Los nombres del mensaje de `metamat_constantes`; [] si no lo hay."""
    for m in mensajes or []:
        txt = str((m or {}).get("data") or "")
        i = txt.find(_MARCA)
        if i < 0:
            continue
        cuerpo = txt[i + len(_MARCA):].strip().strip("[]")
        return [x.strip() for x in re.split(r"[,\s]+", cuerpo) if x.strip()]
    return []


def phi_constantes(sesion, proof_state: int, por_nombre: dict) -> Optional[set]:
    """Los conceptos cuyas constantes usa el estado. None si Lean no contestó."""
    r = sesion.tactica("metamat_constantes", proof_state, tope=30)
    nombres = leer_constantes(r.mensajes)
    if not nombres:
        return None
    return conceptos(nombres, por_nombre)


def explicar(pasos: list, etiquetas: list, nombre_de=None) -> list:
    """Una línea en castellano por paso de un camino ya verificado.

    `pasos` son las tácticas en orden; `etiquetas[i]` es φ del estado ANTES
    del paso i (y la última, la del estado que el último paso cerró). Dice qué
    conceptos APARECEN y cuáles DEJAN de estar: eso es lo que el paso hizo, en
    el vocabulario del alumno.
    """
    nom = nombre_de or (lambda c: c)
    fuera = []
    for i, t in enumerate(pasos):
        antes = etiquetas[i] if i < len(etiquetas) else set()
        despues = etiquetas[i + 1] if i + 1 < len(etiquetas) else set()
        cierra = i == len(pasos) - 1
        partes = ["Paso %d · `%s`" % (i + 1, t)]
        if antes:
            partes.append("el objetivo habla de %s" % ", ".join(sorted(nom(c) for c in antes)))
        if cierra:
            partes.append("y queda demostrado")
        else:
            nuevos, van = despues - antes, antes - despues
            if nuevos:
                partes.append("aparece %s" % ", ".join(sorted(nom(c) for c in nuevos)))
            if van:
                partes.append("deja de estar %s" % ", ".join(sorted(nom(c) for c in van)))
            if not nuevos and not van:
                partes.append("sin cambiar de conceptos")
        fuera.append(": ".join(partes[:1]) + (" — " + "; ".join(partes[1:]) if len(partes) > 1 else ""))
    return fuera


#: LOS TIPOS PORTADORES: la constante que nombra DÓNDE viven los números, y que
#: por eso aparece en casi todo. Medido en el paso 5: con ellos, 145 de 150
#: estados de LeanWorkbook se etiquetaban SÓLO con el tipo de número —`ℕ` daba
#: «elementary-number-theory», `ℝ` daba «real-analysis»—, y una etiqueta que
#: sale en todo no explica nada. Es el mismo fallo que L4 resolvió con `cic` y
#: `Type`. La lista nace de mirar esa medición, y se declara así: no es un
#: resultado confirmado, es una corrección que la revisión a mano tiene que
#: validar.
PORTADORES = frozenset({"Real", "Nat", "Int", "Rat", "Complex", "NNReal",
                        "ENNReal", "EReal", "PNat"})


def sin_portadores(nombres) -> list:
    return [n for n in nombres if n not in PORTADORES]


def constantes_de(sesion, proof_state: int) -> Optional[list]:
    """Las constantes que usa el estado, o None si Lean no contestó."""
    r = sesion.tactica("metamat_constantes", proof_state, tope=30)
    nombres = leer_constantes(r.mensajes)
    return nombres or None
