# -*- coding: utf-8 -*-
"""La huella del grafo: que una medicion sepa a que grafo se refiere.

EL FALLO QUE CIERRA
-------------------
`data/banco_herald.json` decia «10,3 % de precision» y la documentacion lo
citaba como la cifra de hoy. Pero se midio el 12 de septiembre, sobre un grafo
de 352 nodos que todavia tenia `sequent-calculus`, `recursion-theory` y
`cardinal-arithmetic`. El grafo de hoy tiene 353 y ninguno de los tres.

Ni el fichero ni la documentacion mentian por separado: el fichero decia lo
que midio y la documentacion lo copiaba bien. Lo que faltaba era la pregunta
«¿y esto se midio sobre que?», que nadie podia hacerse porque el dato no
estaba escrito en ningun sitio.

Es la misma disciplina que ya aplica el proyecto a los numeros —cada cifra con
su modelo nulo— pero una vuelta mas arriba: cada cifra con SU GRAFO.

QUE ES LA HUELLA, Y POR QUE NO BASTA CON LA FECHA
--------------------------------------------------
Una fecha no dice si el grafo cambio; dice cuando se corrio. Dos mediciones
del mismo dia pueden estar sobre grafos distintos, y dos de meses distintos
sobre el mismo. Asi que la huella es del CONTENIDO: cuantos nodos, cuantos
morfismos, y un hash de los ids y de los nombres que cada uno ofrece al
prompt.

Los nombres entran a proposito. Un grafo con los mismos nodos pero con
`Continuous` movido de `lean` a `evidencia` NO es el mismo grafo para una
medicion de recuperacion de vocabulario — es justo el cambio que movio la
cobertura 1,1 puntos.
"""
from __future__ import annotations

import hashlib
from typing import Optional


def huella(graph) -> dict:
    """La huella del grafo que se le pase: `{nodos, morfismos, hash}`."""
    from nucleo.graph.interpretacion import nombres_de_trabajo

    ids = sorted(graph.skill_ids)
    piezas = []
    for sid in ids:
        piezas.append(sid + "|" + (nombres_de_trabajo(sid) or ""))
    h = hashlib.sha256("\n".join(piezas).encode("utf-8")).hexdigest()[:16]
    return {
        "nodos": len(ids),
        "morfismos": len(graph.morphisms),
        "hash": h,
    }


def huella_viva() -> dict:
    """La huella del grafo que carga el sistema ahora mismo."""
    import logging
    import warnings
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    return huella(n._graph)


def desajuste(guardada: Optional[dict], viva: Optional[dict] = None):
    """Que cambio entre la huella guardada y la viva; `None` si coinciden.

    Devuelve un texto legible y no un booleano a proposito: quien lea el
    informe necesita saber SI el grafo crecio, encogio o solo se le movieron
    los nombres, porque las tres cosas invalidan una medicion de maneras
    distintas.
    """
    if viva is None:
        viva = huella_viva()
    if not guardada:
        return "sin huella: no se sabe sobre que grafo se midio"

    # LOS TRES CAMPOS DECIDEN, NO SOLO EL HASH.
    #
    # Esto devolvia `None` en cuanto el hash coincidia, y el hash cubre los ids
    # y los nombres que cada nodo ofrece — NO LAS ARISTAS. `nodos` y
    # `morfismos` se guardaban y se enseñaban, pero solo se leian DESPUES de
    # que el hash hubiera fallado: no decidian nada.
    #
    # Consecuencia: un cambio que solo toca aristas era invisible. Paso de
    # verdad — al reconectar dependencias el grafo paso de 1585 a 1586
    # morfismos y tres mediciones guardadas con 1585 seguian dandose por
    # buenas, con el auditor diciendo «las seis miden el grafo de hoy».
    #
    # Reordenar prerrequisitos, invertir una dependencia o recuperar una arista
    # perdida cambian lo que un banco mide y no mueven el hash ni un bit.
    partes = []
    for campo in ("nodos", "morfismos"):
        a, b = guardada.get(campo), viva.get(campo)
        if a != b:
            partes.append("%s %s -> %s" % (campo, a, b))
    if not partes:
        if guardada.get("hash") == viva.get("hash"):
            return None
        partes.append("mismos nodos y morfismos, pero cambiaron los nombres "
                      "que se ofrecen")
    return "; ".join(partes)
