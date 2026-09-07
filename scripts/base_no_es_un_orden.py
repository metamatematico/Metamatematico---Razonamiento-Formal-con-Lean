# -*- coding: utf-8 -*-
"""Por que pi no es una fibracion, y por que añadir morfismos NO lo arregla.

EL DIAGNOSTICO QUE FALTABA. `fibracion_del_grafo.py` mide que solo 3 de 860
pares admiten levantamiento cartesiano —0,3 %, peor que el 6,1 % del azar— y
apunta a que «la base afirma de mas». La conclusion que se saco de ahi fue que
faltaban morfismos que cruzaran de area. Este script muestra que esa conclusion
es FALSA, y por que.

LA CAUSA. La base se construye como la imagen de las flechas del grafo y luego
se cierra transitivamente. Las flechas directas entre areas forman una
COMPONENTE FUERTEMENTE CONEXA de 21 de las 23 areas: Algebra depende de
Analysis (teoria espectral) y Analysis depende de Algebra (espacios con
producto interior); CategoryTheory depende de Algebra (algebra homologica) y
Algebra de CategoryTheory (categorias abelianas). Al cerrar, esas 63 relaciones
directas se convierten en 462 de las 506 posibles: el 91 %.

Una base asi NO ES UN ORDEN. Es un preorden con una clase de equivalencia
gigante, y sobre ella la condicion de fibracion exige que TODO objeto de
cualquiera de esas 21 areas se levante a cualquier otra — que es matematica
falsa: no todo concepto de algebra depende de uno de probabilidad.

Y POR ESO AÑADIR ARISTAS NO PUEDE AYUDAR. La clausura transitiva es monotona:
una arista nueva solo puede AÑADIR relaciones a la base, nunca quitarlas. Meter
mas morfismos que crucen de area agranda la componente fuertemente conexa y
empeora el problema. El script lo comprueba: añade las aristas cruzadas que
faltan y vuelve a medir.

LOS CICLOS SON MATEMATICA, NO ERRORES. Es el mismo hallazgo que ya dio
`areas_por_estructura.py` sobre la taxonomia de Mathlib —una mega-area con 918
de 1 358 conceptos— con otro disfraz: la descomposicion en ramas no es
recuperable de las dependencias, porque el orden en que se construye la
matematica no respeta la frontera entre algebra, topologia y analisis.

No gasta API.

    python -m scripts.base_no_es_un_orden
"""
import collections
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SALIDA = "E:/Metamatematico/data/base_no_es_un_orden.json"


def componentes_fuertes(nodos, ady):
    """Kosaraju, iterativo: el grafo de areas es pequeño pero no arriesgamos."""
    inv = collections.defaultdict(set)
    for u in nodos:
        for v in ady[u]:
            inv[v].add(u)
    visto, orden = set(), []
    for raiz in nodos:
        if raiz in visto:
            continue
        pila = [(raiz, iter(ady[raiz]))]
        visto.add(raiz)
        while pila:
            u, it = pila[-1]
            for v in it:
                if v not in visto:
                    visto.add(v)
                    pila.append((v, iter(ady[v])))
                    break
            else:
                orden.append(u)
                pila.pop()
    comp, visto2 = {}, set()
    for u in reversed(orden):
        if u in visto2:
            continue
        pila, grupo = [u], []
        visto2.add(u)
        while pila:
            x = pila.pop()
            grupo.append(x)
            for y in inv[x]:
                if y not in visto2:
                    visto2.add(y)
                    pila.append(y)
        for x in grupo:
            comp[x] = u
    return comp


def clausura(nodos, ady):
    fuera = set()
    for x in nodos:
        pila, vis = list(ady[x]), set()
        while pila:
            u = pila.pop()
            if u in vis:
                continue
            vis.add(u)
            pila.extend(ady[u])
        for y in vis:
            if y != x:
                fuera.add((x, y))
    return fuera


def main():
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    from nucleo.graph.functor import construir_funtor
    from nucleo.types import MorphismType as MT

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph
    pi = construir_funtor(g)

    directas = collections.Counter()
    testigos = {}
    for m in g.morphisms:
        if m.morphism_type is not MT.DEPENDENCY:
            continue
        x = pi.en_objetos.get(m.source_id)
        y = pi.en_objetos.get(m.target_id)
        if not x or not y or x == y:
            continue
        directas[(x, y)] += 1
        testigos.setdefault((x, y), (m.source_id, m.target_id))

    nodos = sorted({a for p in directas for a in p})
    ady = collections.defaultdict(set)
    for (x, y) in directas:
        ady[x].add(y)

    cer = clausura(nodos, ady)
    posibles = len(nodos) * (len(nodos) - 1)

    print("=" * 72)
    print("1 · LA BASE, TAL COMO SE CONSTRUYE")
    print("=" * 72)
    print("  areas                       %4d" % len(nodos))
    print("  relaciones DIRECTAS         %4d" % len(directas))
    print("  relaciones tras la CLAUSURA %4d  de %d posibles = %.0f %%"
          % (len(cer), posibles, 100.0 * len(cer) / posibles))

    comp = componentes_fuertes(nodos, ady)
    grupos = collections.defaultdict(list)
    for a, r in comp.items():
        grupos[r].append(a)
    fuertes = sorted((v for v in grupos.values() if len(v) > 1),
                     key=len, reverse=True)

    print()
    print("=" * 72)
    print("2 · Y NO ES UN ORDEN")
    print("=" * 72)
    if not fuertes:
        print("  el grafo de areas es un DAG: la base SI es un orden")
    for v in fuertes:
        print("  componente fuertemente conexa de %d areas —todas mutuamente"
              " «por debajo» unas de otras—:" % len(v))
        for a in sorted(v):
            print("     %s" % a)
    sueltas = [a for a in nodos if len(grupos[comp[a]]) == 1]
    print()
    print("  areas FUERA de la componente: %d %s"
          % (len(sueltas), sorted(sueltas)))

    print()
    print("  los ciclos son matematica correcta, no errores:")
    mostrados = 0
    for (x, y) in sorted(directas):
        if (y, x) in directas and x < y and mostrados < 6:
            print("     %-16s <-> %-16s" % (x, y))
            print("        %s -> %s" % testigos[(x, y)])
            print("        %s -> %s" % testigos[(y, x)])
            mostrados += 1

    print()
    print("=" * 72)
    print("3 · AÑADIR MORFISMOS NO PUEDE AYUDAR")
    print("=" * 72)
    print("  La clausura transitiva es MONOTONA: una arista nueva solo puede")
    print("  añadir relaciones a la base, nunca quitarlas. Comprobado:")
    faltan = [(x, y) for x in nodos for y in nodos
              if x != y and (x, y) not in directas]
    ady2 = collections.defaultdict(set)
    for k, v in ady.items():
        ady2[k] = set(v)
    import random
    random.Random(20260907).shuffle(faltan)
    for k in (10, 30, 60):
        prueba = collections.defaultdict(set)
        for a, v in ady2.items():
            prueba[a] = set(v)
        for (x, y) in faltan[:k]:
            prueba[x].add(y)
        c2 = clausura(nodos, prueba)
        comp2 = componentes_fuertes(nodos, prueba)
        g2 = collections.Counter(comp2.values())
        print("     +%2d aristas cruzadas -> clausura %3d (%.0f %%) · mayor"
              " componente %d areas"
              % (k, len(c2), 100.0 * len(c2) / posibles, max(g2.values())))

    print()
    print("  Conclusion: la fibracion no falla por falta de datos. Falla")
    print("  porque el AREA no ordena la matematica, y una base que no es un")
    print("  orden no puede sostener levantamientos cartesianos.")

    io.open(SALIDA, "w", encoding="utf-8").write(json.dumps({
        "areas": len(nodos),
        "relaciones_directas": len(directas),
        "relaciones_tras_clausura": len(cer),
        "relaciones_posibles": posibles,
        "mayor_componente_fuerte": max((len(v) for v in fuertes), default=1),
        "areas_fuera_de_la_componente": sorted(sueltas),
        "ciclos_de_ida_y_vuelta": sorted(
            "%s <-> %s" % (x, y) for (x, y) in directas
            if (y, x) in directas and x < y),
    }, ensure_ascii=False, indent=1))
    print()
    print("-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
