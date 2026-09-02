# -*- coding: utf-8 -*-
"""¿Están de verdad conectados los dos grafos, o sólo comparten el suelo?

EL CASO QUE LO DESTAPO. `mathlib-linearalgebra-basis` alcanza 81 nodos hacia
arriba por prerrequisitos y NI UNO es curado: no pasa por `linear-algebra`, ni
por `module-theory`, ni por `ring-theory` —todos existen en el grafo y son
justo donde una base se apoya— sino que va directo a `zfc-axioms`.

LA CAUSA ESTA EN EL CARGADOR, y la escribi yo: los generados se enlazan ENTRE
ELLOS por el DAG de imports, y despues se cuelgan del nodo base de su pilar
«para no dejar islas». Nunca se conectaron con los 173 curados.

Si eso pasa en general, no hay un grafo de 298 nodos: hay DOS grafos que
comparten los diez fundacionales y nada mas. Un nodo colgado directo de ZFC no
hereda contexto de nada — no comparte vecindario con su area, no se activa
cuando se activa lo suyo, y su unico ancestro es el que tienen los 298.

QUE MIDE ESTE SCRIPT

  1. cuantas aristas CRUZAN entre curados y generados, sin contar el enganche
     al pilar — que es la costura artificial que puse yo
  2. cuantos generados alcanzan algun nodo curado por prerrequisitos
  3. cuantos cuelgan SOLO del pilar, sin ninguna dependencia propia
  4. y para los desconectados, si el DAG de imports DICE que deberian estarlo:
     si el modulo del generado importa (transitivamente) el del curado, la
     arista es real y solo falta ponerla

El punto 4 es el que convierte el diagnostico en algo accionable, y usa la
misma fuente que la auditoria que dio el 78 % de dependencias confirmadas.

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

DOT = "E:/Metamatematico/data/mathlib_imports.dot"
MAPA = "E:/Metamatematico/data/mathlib_modulos.json"
SALIDA = "E:/Metamatematico/data/conexion_curados_generados.json"


def dag_oficial():
    """El DAG de imports: prerrequisito -> dependiente."""
    if not os.path.exists(DOT):
        return None
    pat = re.compile(r'"([^"]+)"\s*->\s*"([^"]+)"')
    ady = collections.defaultdict(set)
    for l in io.open(DOT, encoding="utf-8", errors="replace"):
        m = pat.search(l)
        if m:
            ady[m.group(1)].add(m.group(2))
    return ady


def alcanza(ady, origen, destinos, tope=200000):
    """¿Se llega de `origen` a alguno de `destinos`? Devuelve el que encuentre."""
    from collections import deque
    q = deque([origen])
    vis = {origen}
    n = 0
    while q:
        u = q.popleft()
        n += 1
        if n > tope:
            return None
        for v in ady.get(u, ()):
            if v in destinos:
                return v
            if v not in vis:
                vis.add(v)
                q.append(v)
    return None


def main(_):
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    from nucleo.types import MorphismType as MT

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph

    gen = {s.id for s in g.skills if (s.metadata or {}).get("origen") == "mathlib"}
    cur = {s.id for s in g.skills} - gen
    L0 = {s.id for s in g.skills if s.level == 0}
    print("curados %d · generados %d · fundacionales %d\n"
          % (len(cur), len(gen), len(L0)))

    # ── 1 · las aristas que cruzan ────────────────────────────────────────
    cruzan = collections.Counter()
    costura = 0
    for m in g.morphisms:
        if m.morphism_type == MT.IDENTITY:
            continue
        a, b = m.source_id, m.target_id
        if a in L0 and b in gen:
            costura += 1          # el enganche al pilar que puse yo
            continue
        if (a in cur) != (b in cur):
            cruzan[("curado->generado" if a in cur else "generado->curado")] += 1
    print("=== 1 · ARISTAS QUE CRUZAN entre los dos grafos ===\n")
    print("  sin contar el enganche al pilar : %d" % sum(cruzan.values()))
    for k, v in cruzan.most_common():
        print("     %-20s %d" % (k, v))
    print("  enganches al pilar (la costura) : %d" % costura)

    # ── 2 y 3 · cierre de prerrequisitos de cada generado ─────────────────
    def cierre(sid):
        from collections import deque
        q = deque([sid])
        vis = set()
        while q:
            u = q.popleft()
            for d in g.dependencies(u):
                if d not in vis:
                    vis.add(d)
                    q.append(d)
        return vis

    sin_curado, solo_pilar = [], []
    for s in sorted(gen):
        c = cierre(s)
        if not (c & (cur - L0)):
            sin_curado.append(s)
        deps = [d for d in g.dependencies(s) if d not in L0]
        if not deps:
            solo_pilar.append(s)
    print("\n=== 2 · ¿ALCANZAN ALGUN CURADO? ===\n")
    print("  generados cuyo cierre NO contiene ningun curado: %d de %d"
          % (len(sin_curado), len(gen)))
    print("  generados que cuelgan SOLO del pilar           : %d"
          % len(solo_pilar))
    if solo_pilar:
        print("     " + ", ".join(x.replace("mathlib-", "")
                                  for x in solo_pilar[:10]))

    # ── 4 · ¿que dice el DAG que DEBERIA estar conectado? ─────────────────
    ady = dag_oficial()
    if ady is None:
        print("\n  (sin data/mathlib_imports.dot no se puede comprobar el 4)")
        return 0
    por_skill = json.load(io.open(MAPA, encoding="utf-8"))["por_skill"]
    mod_gen = {}
    from nucleo.pillars.mathlib_taxonomy import NODOS_MATHLIB
    for x in NODOS_MATHLIB:
        mod_gen[x.id] = x.modulo

    print("\n=== 3 · LO QUE EL DAG DICE QUE FALTA ===")
    print("    (si el modulo del generado importa el del curado, la arista es"
          " real)\n")
    #: modulo curado -> skill curada, para el camino inverso
    de_modulo = {}
    for sk, mods in por_skill.items():
        for m in mods:
            de_modulo.setdefault(m, sk)

    encontradas = collections.Counter()
    ejemplos = []
    for s in sin_curado:
        m = mod_gen.get(s)
        if not m:
            continue
        # ¿alguno de los modulos curados es prerrequisito de este?
        # el DAG va prerrequisito -> dependiente, asi que se busca hacia atras:
        # ¿se llega de un modulo curado a este?
        hallado = None
        for mc, sk in de_modulo.items():
            if mc == m:
                continue
            if m in ady.get(mc, ()):        # arista directa: barato primero
                hallado = (sk, mc)
                break
        if not hallado:
            hallado = None
            for mc, sk in list(de_modulo.items())[:40]:
                if alcanza(ady, mc, {m}, tope=8000):
                    hallado = (sk, mc)
                    break
        if hallado:
            encontradas[hallado[0]] += 1
            if len(ejemplos) < 12:
                ejemplos.append((s, hallado[0], hallado[1]))
    print("  generados con un prerrequisito curado REAL en el DAG: %d de %d"
          % (sum(encontradas.values()), len(sin_curado)))
    print("\n  ejemplos de aristas que faltan:")
    for s, sk, mc in ejemplos:
        print("     %-34s <- %-22s  (%s)"
              % (s.replace("mathlib-", ""), sk, mc.replace("Mathlib.", "")))

    json.dump({"curados": len(cur), "generados": len(gen),
               "cruzan": dict(cruzan), "costura_al_pilar": costura,
               "sin_curado_en_su_cierre": sin_curado,
               "cuelgan_solo_del_pilar": solo_pilar,
               "aristas_que_faltan": [{"generado": a, "curado": b, "modulo": c}
                                      for a, b, c in ejemplos]},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    a = ap.parse_args()
    sys.exit(main(a))
