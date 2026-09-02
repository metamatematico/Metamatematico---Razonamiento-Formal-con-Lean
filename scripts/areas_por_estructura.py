# -*- coding: utf-8 -*-
"""Las áreas, definidas por la estructura de Mathlib y no por mi corte.

EL PROBLEMA. Los nodos de cobertura se generaron colapsando los ficheros de
Mathlib a profundidad 2 —`Algebra.Order`, `Data.Set`— y eso metio 133 CICLOS en
el grafo:

    Topology.Instances -> Analysis.Asymptotics -> Analysis.Complex -> Topology.Instances

Los tres son ficheros distintos: `Analysis/Asymptotics/TVS.lean` importa
`Topology.Instances.ENNReal.Lemmas`, `Analysis/Complex/Asymptotics.lean`
importa `Analysis.Asymptotics.Theta`, y `Topology/Instances/Complex.lean`
importa `Analysis.Complex.Basic`. Nadie dio la vuelta: son tres dependencias
que solo se tocan porque yo meti cientos de ficheros en un mismo saco.

EL DAG DE MATHLIB ES ACICLICO — Lean prohibe imports circulares. Los ciclos son
MIOS, del corte, no de la matematica.

QUE SE HACE AQUI. En vez de imponer la profundidad 2, se dejan que las areas
las dicte la estructura: se colapsa el grafo por COMPONENTES FUERTEMENTE
CONEXAS. Cada componente es un conjunto de conceptos mutuamente dependientes,
que es la unidad de conocimiento real ahi, y el grafo de componentes es
aciclico POR CONSTRUCCION.

Se compara con el corte por directorio para ver cuanto cambia y donde.

No gasta API.
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
DOT = "E:/Metamatematico/data/mathlib_imports.dot"
SALIDA = "E:/Metamatematico/data/areas_por_estructura.json"
IMP = re.compile(r"^(?:public\s+|meta\s+|private\s+|protected\s+)*import\s+"
                 r"([A-Za-z_][\w.]*)", re.M)
IGNORAR = {"Tactic", "Util", "Testing", "Deprecated", "Mathport", "Init"}


def dag_desde_dot():
    """El grafo oficial, si `lake exe graph` ya lo genero."""
    if not os.path.exists(DOT):
        return None
    aristas = []
    pat = re.compile(r'"([^"]+)"\s*->\s*"([^"]+)"')
    for l in io.open(DOT, encoding="utf-8", errors="replace"):
        m = pat.search(l)
        if m:
            aristas.append((m.group(1), m.group(2)))
    return aristas or None


def dag_desde_fuente():
    """Respaldo: se lee del fuente, como veniamos haciendo."""
    aristas = []
    for r, _d, fs in os.walk(MATH):
        for f in fs:
            if not f.endswith(".lean"):
                continue
            rel = os.path.relpath(os.path.join(r, f), MATH).replace("\\", "/")
            mod = "Mathlib." + rel[:-5].replace("/", ".")
            try:
                t = io.open(os.path.join(r, f), encoding="utf-8",
                            errors="replace").read(8000)
            except Exception:
                continue
            for i in IMP.findall(t):
                if i.startswith("Mathlib."):
                    aristas.append((i, mod))     # importado -> importador
    return aristas


def concepto(m, prof=2):
    p = m.replace("Mathlib.", "", 1).split(".")
    return ".".join(p[:prof])


def tarjan(nodos, ady):
    """Componentes fuertemente conexas, iterativo para no reventar la pila."""
    indice = {}
    bajo = {}
    en_pila = set()
    pila = []
    comps = []
    cont = [0]
    for raiz in nodos:
        if raiz in indice:
            continue
        trabajo = [(raiz, iter(ady.get(raiz, ())))]
        indice[raiz] = bajo[raiz] = cont[0]
        cont[0] += 1
        pila.append(raiz)
        en_pila.add(raiz)
        while trabajo:
            v, it = trabajo[-1]
            avanzo = False
            for w in it:
                if w not in indice:
                    indice[w] = bajo[w] = cont[0]
                    cont[0] += 1
                    pila.append(w)
                    en_pila.add(w)
                    trabajo.append((w, iter(ady.get(w, ()))))
                    avanzo = True
                    break
                if w in en_pila:
                    bajo[v] = min(bajo[v], indice[w])
            if avanzo:
                continue
            trabajo.pop()
            if trabajo:
                u = trabajo[-1][0]
                bajo[u] = min(bajo[u], bajo[v])
            if bajo[v] == indice[v]:
                comp = []
                while True:
                    w = pila.pop()
                    en_pila.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                comps.append(comp)
    return comps


def main(prof):
    aristas = dag_desde_dot()
    fuente = "lake exe graph (.dot oficial)"
    if aristas is None:
        aristas = dag_desde_fuente()
        fuente = "fuente, leyendo los import (respaldo)"
    print("DAG: %d aristas · fuente: %s" % (len(aristas), fuente))

    # ── a nivel de MODULO: debe ser aciclico ───────────────────────────────
    ady_mod = collections.defaultdict(set)
    nodos_mod = set()
    for a, b in aristas:
        ady_mod[a].add(b)
        nodos_mod |= {a, b}
    comps_mod = tarjan(nodos_mod, ady_mod)
    grandes = [c for c in comps_mod if len(c) > 1]
    print("  a nivel de MODULO: %d nodos · %d componentes · %d no triviales"
          % (len(nodos_mod), len(comps_mod), len(grandes)))
    if grandes:
        print("    ATENCION: Lean prohibe imports circulares; si hay "
              "componentes no triviales aqui, el extractor esta mal")

    # ── colapsado a profundidad fija: aparecen los ciclos ─────────────────
    ady_c = collections.defaultdict(set)
    nodos_c = set()
    for a, b in aristas:
        ca, cb = concepto(a, prof), concepto(b, prof)
        if ca != cb and ca and cb:
            ady_c[ca].add(cb)
            nodos_c |= {ca, cb}
    comps_c = tarjan(nodos_c, ady_c)
    ciclicos = [c for c in comps_c if len(c) > 1]
    print("\n  colapsado a profundidad %d: %d conceptos · %d componentes"
          % (prof, len(nodos_c), len(comps_c)))
    print("    componentes NO TRIVIALES (o sea, ciclos): %d" % len(ciclicos))
    print("    conceptos atrapados en un ciclo: %d de %d"
          % (sum(len(c) for c in ciclicos), len(nodos_c)))

    print("\n  las componentes mas grandes — ESTAS son las areas reales:")
    for c in sorted(ciclicos, key=len, reverse=True)[:6]:
        print("     %2d conceptos: %s" % (len(c), ", ".join(sorted(c)[:6])
                                          + (" ..." if len(c) > 6 else "")))

    # el grafo de componentes SI es aciclico
    de_comp = {}
    for i, c in enumerate(comps_c):
        for x in c:
            de_comp[x] = i
    ady_comp = collections.defaultdict(set)
    for a, bs in ady_c.items():
        for b in bs:
            if de_comp[a] != de_comp[b]:
                ady_comp[de_comp[a]].add(de_comp[b])
    comps2 = tarjan(set(de_comp.values()), ady_comp)
    print("\n  el grafo de COMPONENTES tiene %d ciclos (debe ser 0)"
          % len([c for c in comps2 if len(c) > 1]))

    json.dump({"fuente": fuente, "aristas": len(aristas), "profundidad": prof,
               "conceptos": len(nodos_c), "componentes": len(comps_c),
               "ciclicas": len(ciclicos),
               "areas": [sorted(c) for c in
                         sorted(comps_c, key=len, reverse=True)[:60]]},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--profundidad", type=int, default=2)
    a = ap.parse_args()
    sys.exit(main(a.profundidad))
