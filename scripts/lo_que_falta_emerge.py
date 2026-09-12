# -*- coding: utf-8 -*-
"""¿Lo que falta EMERGE de lo que hay, siguiendo los morfismos del grafo?

LA PREGUNTA
-----------
De 203 enunciados reales de Mathlib, 62 nombran algo que el conjunto fijo de
imports no alcanza (`scripts/imports_que_discriminan.py`). La pregunta no es
si se puede importar mas —eso ya se sabe— sino otra, y es la que justifica
que el grafo sea una CATEGORIA y no una lista de etiquetas:

    partiendo de los conceptos que el enunciado YA nombra y que si tenemos,
    ¿se llega al que falta siguiendo morfismos?

Si se llega, lo que falta no hay que anadirlo: hay que RECORRERLO, y esa es
exactamente la promesa de la estructura funtorial. Si no se llega, el grafo
tiene un hueco y ningun recorrido lo va a recuperar — «ningun emparejador
recupera lo que no esta».

COMO SE MIDE
------------
Para cada caso con modulos que faltan:

    tenemos   nodos del grafo que cubren los modulos que el enunciado nombra
              Y que la cabecera fija SI alcanza
    falta     nodos que cubren los modulos que NO alcanza

y se pregunta si `falta` cae dentro de `reachable_from(tenemos)`.

EL PREORDEN, NO CUALQUIER FLECHA. Se recorre con `ORDER_MORPHISMS`, que es la
relacion teoria ⊃ subteoria y la unica con la que los colimites significan
algo. Siguiendo TRANSLATION entran las skills-tactica, que son sumideros, y
salen certificadas como cota superior de dominios arbitrarios: esta medido que
`join(large-cardinals, cohomology, algebraic-topology) = tactic-simp`.

LOS DOS MODELOS NULOS, Y HACEN FALTA LOS DOS
--------------------------------------------
«Es alcanzable» no dice nada si casi todo alcanza a casi todo. Medido sobre
este grafo el preorden es ESCASO —alcance medio del 1 %, mediana 0, y 246 de
321 nodos no alcanzan ningun otro—, asi que la pregunta tiene contenido.

    NULO 1  la misma CANTIDAD de nodos, tomados al azar.

Ese no basta, y comprobarlo cambio el resultado. Los nodos de partida reales
alcanzan 10,8 nodos de media frente a 4,2 de un nodo cualquiera: son mas
concentradores que el azar, asi que parte de la ventaja seria grado de salida
y no estructura.

    NULO 2  otros nodos que alcancen LO MISMO (mismo tramo, en potencias
            de dos). Controlado el grado, lo unico que queda es A DONDE lleva.

El nulo 2 es el que decide. Sin el se publicaria 5,58x donde lo defendible
es 4,61x.

No gasta API ni Lean.

    python -m scripts.lo_que_falta_emerge
"""
from __future__ import annotations

import argparse
import io
import json
import os
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

ENTRADA = os.path.join(RAIZ, "data", "imports_que_discriminan.json")
SALIDA = os.path.join(RAIZ, "data", "lo_que_falta_emerge.json")
SEMILLA = 20260911
REPETICIONES_NULO = 200


def _tramo(r: int) -> int:
    """Tramo de alcance, en potencias de dos.

    Emparejar por el valor exacto dejaria tramos de un solo nodo y el nulo
    se elegiria a si mismo. Por potencias de dos hay gemelos de sobra y la
    comparacion sigue controlando el grado de salida.
    """
    if r <= 0:
        return 0
    t, v = 1, 1
    while v < r:
        v *= 2
        t += 1
    return t


def _mismo_tramo(s: str, reach: dict, tramos: dict) -> list:
    """Otros nodos que alcanzan un numero parecido, excluido el propio."""
    return [x for x in tramos.get(_tramo(reach[s]), ()) if x != s]


def mapa_modulo_a_nodos(grafo) -> dict:
    """modulo de Mathlib -> nodos del grafo que lo cubren.

    Dos vias, y las dos cuentan:
      · un CONCEPTO cubre el modulo donde vive alguno de sus identificadores
      · un MODULO generado cubre el modulo del que se genero
    """
    from nucleo.graph.interpretacion import nombres_de_trabajo
    from nucleo.lean.nombres import modulo_de

    fuera = {}
    for sid, nodo in grafo._skills.items():
        s = nodo.skill
        meta = s.metadata or {}
        # via 1: los identificadores verificados del nodo
        for pieza in (nombres_de_trabajo(sid) or "").replace("+", ",").split(","):
            pieza = pieza.strip()
            if not pieza:
                continue
            mod = modulo_de(pieza)
            if mod:
                fuera.setdefault(mod, set()).add(sid)
        # via 2: los nodos generados llevan su ruta en los metadatos
        mod = meta.get("modulo") or meta.get("module") or ""
        if mod:
            fuera.setdefault(mod, set()).add(sid)
    return fuera


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.parse_args()

    import warnings
    import logging
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)

    if not os.path.exists(ENTRADA):
        print("falta %s. Corre antes:\n"
              "   python -m scripts.imports_que_discriminan --por-area 8"
              % ENTRADA)
        return 1

    from nucleo.graph.category import SkillCategory
    from nucleo.core import Nucleo
    from nucleo.lean import alcance

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph

    if not alcance.disponible():
        print("sin el DAG de imports no se puede clasificar. Se aborta.")
        return 1

    d = json.load(io.open(ENTRADA, encoding="utf-8"))
    casos = [c for c in d["casos"] if c.get("faltan")]
    fijo = d.get("fijo") or []
    ya = alcance.alcanza(fijo)
    m2n = mapa_modulo_a_nodos(g)

    print("casos con algo que falta : %d" % len(casos))
    print("modulos con nodo en el grafo: %d de %d que el grafo podria cubrir\n"
          % (len(m2n), len(g._skills)))

    rnd = random.Random(SEMILLA)
    ids = list(g._skills)

    cuenta = {"sin_nodo": 0, "emerge": 0, "no_emerge": 0, "ya_estaba": 0}
    nulo_aciertos = 0
    nulo_intentos = 0
    nulo2_aciertos = 0
    nulo2_intentos = 0
    detalle = []

    # Alcance de cada nodo, y los tramos para el nulo emparejado. Se calcula
    # una vez: son 321 cierres transitivos.
    reach = {s: len(g.reachable_from(s, g.ORDER_MORPHISMS)) for s in ids}
    tramos = {}
    for s, r in reach.items():
        tramos.setdefault(_tramo(r), []).append(s)

    for c in casos:
        # los modulos que el enunciado nombra, partidos en los que tenemos y
        # los que faltan
        nombra = c.get("mods_nombres") or []
        tenemos_mod = [m for m in nombra if m in ya]
        falta_mod = [m for m in nombra if m not in ya]

        tenemos = set()
        for m in tenemos_mod:
            tenemos |= m2n.get(m, set())
        objetivo = set()
        for m in falta_mod:
            objetivo |= m2n.get(m, set())

        if not objetivo:
            cuenta["sin_nodo"] += 1
            detalle.append({"nombre": c["nombre"], "veredicto": "sin_nodo",
                            "faltan": falta_mod})
            continue
        if objetivo & tenemos:
            cuenta["ya_estaba"] += 1
            detalle.append({"nombre": c["nombre"], "veredicto": "ya_estaba"})
            continue
        if not tenemos:
            cuenta["no_emerge"] += 1
            detalle.append({"nombre": c["nombre"], "veredicto": "sin_partida",
                            "faltan": falta_mod})
            continue

        alcanzable = set()
        for s in tenemos:
            alcanzable |= g.reachable_from(s, g.ORDER_MORPHISMS)
        emerge = bool(alcanzable & objetivo)
        cuenta["emerge" if emerge else "no_emerge"] += 1
        detalle.append({"nombre": c["nombre"],
                        "veredicto": "emerge" if emerge else "no_emerge",
                        "desde": len(tenemos), "objetivo": len(objetivo)})

        # LOS DOS NULOS, y el segundo es el que decide.
        #
        # El nulo uniforme —la misma CANTIDAD de nodos al azar— resulta
        # demasiado debil aqui: los nodos de partida reales alcanzan 10,8 de
        # media frente a 4,2 de un nodo cualquiera, o sea que son mas
        # concentradores que el azar. Con ese nulo, parte de la ventaja seria
        # solo grado de salida, no estructura.
        #
        # El nulo EMPAREJADO POR ALCANCE sustituye cada nodo de partida por
        # otro que alcance un numero parecido —mismo tramo—, asi que la unica
        # diferencia que queda es A DONDE lleva, que es lo que se quiere medir.
        for _ in range(REPETICIONES_NULO):
            muestra = rnd.sample(ids, min(len(tenemos), len(ids)))
            alc = set()
            for s in muestra:
                alc |= g.reachable_from(s, g.ORDER_MORPHISMS)
            nulo_aciertos += 1 if (alc & objetivo) else 0
            nulo_intentos += 1

        for _ in range(REPETICIONES_NULO):
            alc = set()
            for s in tenemos:
                gemelos = _mismo_tramo(s, reach, tramos)
                t = rnd.choice(gemelos) if gemelos else s
                alc |= g.reachable_from(t, g.ORDER_MORPHISMS)
            nulo2_aciertos += 1 if (alc & objetivo) else 0
            nulo2_intentos += 1

    print("=== DE DONDE VIENE LO QUE FALTA ===\n")
    tot = max(1, len(casos))
    print("  el grafo NO tiene nodo para eso     %3d  (%.0f %%)"
          % (cuenta["sin_nodo"], 100.0 * cuenta["sin_nodo"] / tot))
    print("  ya estaba entre lo que tenemos      %3d  (%.0f %%)"
          % (cuenta["ya_estaba"], 100.0 * cuenta["ya_estaba"] / tot))
    print("  EMERGE: se alcanza por morfismos    %3d  (%.0f %%)"
          % (cuenta["emerge"], 100.0 * cuenta["emerge"] / tot))
    print("  esta en el grafo y NO se alcanza    %3d  (%.0f %%)"
          % (cuenta["no_emerge"], 100.0 * cuenta["no_emerge"] / tot))

    decidibles = cuenta["emerge"] + cuenta["no_emerge"]
    print("\n=== CONTRA EL MODELO NULO ===\n")
    if decidibles and nulo_intentos and nulo2_intentos:
        real = 100.0 * cuenta["emerge"] / decidibles
        nulo = 100.0 * nulo_aciertos / nulo_intentos
        nulo2 = 100.0 * nulo2_aciertos / nulo2_intentos
        print("  desde los conceptos del enunciado            : %.1f %%"
              % real)
        print("  NULO 1  misma cantidad de nodos al azar      : %.1f %%  (%.2fx)"
              % (nulo, real / nulo if nulo else float("inf")))
        print("  NULO 2  mismo ALCANCE, otros nodos           : %.1f %%  (%.2fx)"
              % (nulo2, real / nulo2 if nulo2 else float("inf")))
        print()
        print("  El nulo 2 es el que decide. Los nodos de partida reales")
        print("  alcanzan mas que un nodo cualquiera, asi que parte de la")
        print("  ventaja sobre el nulo 1 es grado de salida y no estructura.")
        print("  Emparejando por alcance, lo unico que queda es A DONDE lleva.")
        print()
        if real <= nulo2:
            print("  NO APORTA: con el grado controlado, partir de los")
            print("  conceptos del enunciado no llega mas lejos que partir de")
            print("  cualquier otro nodo que alcance lo mismo.")
        else:
            print("  APORTA: con el grado controlado, la estructura sigue")
            print("  llevando a donde otros nodos igual de conectados no van.")
    else:
        print("  sin casos decidibles: no se da nota")

    print("\n=== LO QUE ESTO DICE QUE HAY QUE HACER ===\n")
    if cuenta["sin_nodo"] > decidibles:
        print("  El problema dominante NO es de recorrido: en %d de %d casos"
              % (cuenta["sin_nodo"], len(casos)))
        print("  el grafo no tiene ningun nodo que cubra lo que falta.")
        print("  Ningun recorrido recupera lo que no esta: hay que CURAR.")
    elif cuenta["no_emerge"] > cuenta["emerge"]:
        print("  Los nodos existen pero no se llega a ellos: faltan")
        print("  MORFISMOS, no conceptos.")
    else:
        print("  Lo que falta se alcanza desde lo que hay: el arreglo es")
        print("  RECORRER, no anadir.")

    json.dump({"casos": len(casos), "cuenta": cuenta, "detalle": detalle,
               "nulo_aciertos": nulo_aciertos, "nulo_intentos": nulo_intentos,
               "nulo2_aciertos": nulo2_aciertos, "nulo2_intentos": nulo2_intentos,
               "semilla": SEMILLA},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
