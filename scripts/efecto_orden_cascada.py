# -*- coding: utf-8 -*-
"""¿Sirvió de algo reordenar la cascada? Medido, antes y después.

Cambiar el orden de la cascada no puede hacer que Lean acepte nada falso —es
una permutacion— pero si cambia CUANTAS invocaciones de Lean hacen falta antes
de dar con la que cierra. Eso es lo unico que hay que medir, y se puede medir
gratis.

EL CONJUNTO DE PRUEBA LO DA MATHLIB. Cada lema que se cierra en una linea
(`:= by tac`) es un caso resuelto con respuesta conocida: el enunciado, el area
y la tactica que lo cerro. Para cada uno se pregunta en que POSICION de la
cascada queda esa tactica:

    orden viejo : el area primero, luego los patrones del objetivo
    orden nuevo : los patrones del objetivo primero, luego el area (medida)

Posicion mas baja = menos invocaciones de Lean antes de acertar.

AVISOS, dos:
  · el enunciado no es exactamente el goal que veria la cascada (el goal
    aparece tras `intro`s y reescrituras), pero es lo mas cercano que hay sin
    correr Lean sobre 173 684 pruebas;
  · Mathlib es una libreria de lemas definicionales, no problemas de usuario.
    Esto mide la mejora sobre la evidencia disponible, no sobre tu trafico.

No gasta API.
"""
import collections
import io
import json
import os
import random
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nucleo.lean.solver_cascade import SOLVER_CASCADE, GoalAnalyzer  # noqa: E402
from nucleo.multi_agent.colimit_agents import domain_tactic_order  # noqa: E402
from scripts.tacticas_reales_mathlib import AREA  # noqa: E402

MATH = "E:/Metamatematico/.lake/packages/mathlib/Mathlib"
MUESTRA = 6000
SEMILLA = 20260901

#: La tabla que habia antes de medir. Se conserva aqui, y solo aqui, para
#: poder comparar contra ella.
VIEJA = {
    "algebra": "ring", "analysis": "norm_num", "category-theory": "simp",
    "combinatorics": "omega", "computation": "decide", "geometry": "norm_num",
    "logic": "tauto", "number-theory": "norm_num", "optimization": "linarith",
    "probability": "norm_num", "set-theory": "simp", "topology": "simp",
}

DECL = re.compile(r"^\s*(?:@\[[^\]]*\]\s*)?(?:private\s+|protected\s+)?"
                  r"(?:theorem|lemma)\s+[\w.']+(.*?):=\s*by\b(.*)$")
PRIMERA = re.compile(r"^\s*([a-z_][A-Za-z0-9_]*)")
SOLVERS = [n for n, _ in SOLVER_CASCADE]


def _indent(l):
    return len(l) - len(l.lstrip())


def casos():
    """(enunciado, area, tactica que cerro) de las pruebas de una linea."""
    fuera = []
    for raiz, _d, fs in os.walk(MATH):
        for f in fs:
            if not f.endswith(".lean"):
                continue
            rel = os.path.relpath(os.path.join(raiz, f), MATH).replace("\\", "/")
            area = AREA.get(rel.split("/")[0])
            if not area:
                continue
            try:
                ls = io.open(os.path.join(raiz, f), encoding="utf-8",
                             errors="replace").read().splitlines()
            except Exception:
                continue
            for i, l in enumerate(ls):
                m = DECL.match(l)
                if not m:
                    continue
                enunciado, resto = m.group(1), m.group(2).strip()
                if not resto or not enunciado.strip():
                    continue
                sig = ls[i + 1] if i + 1 < len(ls) else ""
                if sig.strip() and _indent(sig) > _indent(l):
                    continue                      # la prueba sigue abajo
                p = PRIMERA.match(resto)
                if not p or p.group(1) not in SOLVERS:
                    continue                      # la cascada no la ofrece
                fuera.append((enunciado.strip(), area, p.group(1)))
    return fuera


def _cascada(prioridad):
    """De una lista de preferencias a la cascada entera, sin perder ninguna."""
    d = dict(SOLVER_CASCADE)
    orden, visto = [], set()
    for n in prioridad:
        if n in d and n not in visto:
            orden.append(n)
            visto.add(n)
    for n in SOLVERS:
        if n not in visto:
            orden.append(n)
    return orden


def orden_viejo(analizador, goal, area):
    """El area primero, luego los patrones. Como estaba."""
    pri = []
    t = VIEJA.get(area, "")
    if t in d_solvers:
        pri.append(t)
    for patron, tacticas in analizador.GOAL_PATTERNS:
        if re.search(patron, goal):
            pri.extend(x for x in tacticas if x not in pri)
            break
    return _cascada(pri)


def orden_nuevo(analizador, goal, area):
    return [n for n, _ in analizador.prioritize(
        goal, domain_order=domain_tactic_order(area))]


d_solvers = set(SOLVERS)


def main():
    print("extrayendo casos de Mathlib...")
    todos = casos()
    print("  %d pruebas de una linea con tactica de la cascada" % len(todos))
    if not todos:
        print("  ATENCION: ningun caso — revisa MATH=%s" % MATH)
        return 1
    random.seed(SEMILLA)
    muestra = random.sample(todos, min(MUESTRA, len(todos)))
    print("  muestra: %d (semilla %d)\n" % (len(muestra), SEMILLA))

    an = GoalAnalyzer()
    sv = sn = 0
    mejor = peor = igual = 0
    por_area = collections.defaultdict(lambda: [0, 0, 0])
    for enunciado, area, tac in muestra:
        v = orden_viejo(an, enunciado, area).index(tac) + 1
        n = orden_nuevo(an, enunciado, area).index(tac) + 1
        sv += v
        sn += n
        por_area[area][0] += v
        por_area[area][1] += n
        por_area[area][2] += 1
        if n < v:
            mejor += 1
        elif n > v:
            peor += 1
        else:
            igual += 1

    N = len(muestra)
    print("=== POSICION MEDIA DE LA TACTICA QUE CIERRA ===")
    print("    (cuantos solvers se prueban, de media, antes de acertar)\n")
    print("  orden viejo : %.2f" % (sv / N))
    print("  orden nuevo : %.2f" % (sn / N))
    print("  mejora      : %.2f posiciones  (%.1f %%)"
          % (sv / N - sn / N, 100.0 * (sv - sn) / sv))
    print("\n  casos que mejoran : %5d  (%.1f %%)" % (mejor, 100.0 * mejor / N))
    print("  casos que empeoran: %5d  (%.1f %%)" % (peor, 100.0 * peor / N))
    print("  sin cambio        : %5d  (%.1f %%)" % (igual, 100.0 * igual / N))

    print("\n=== POR AREA ===\n")
    print("  %-16s %8s %8s %8s  %s" % ("area", "viejo", "nuevo", "delta", "casos"))
    for a in sorted(por_area, key=lambda k: -por_area[k][2]):
        v, n, c = por_area[a]
        print("  %-16s %8.2f %8.2f %+8.2f  %d" % (a, v / c, n / c, n / c - v / c, c))

    json.dump({"muestra": N, "semilla": SEMILLA,
               "posicion_media_vieja": sv / N, "posicion_media_nueva": sn / N,
               "mejoran": mejor, "empeoran": peor, "igual": igual,
               "por_area": {a: {"viejo": v / c, "nuevo": n / c, "casos": c}
                            for a, (v, n, c) in por_area.items()}},
              io.open("E:/Metamatematico/data/efecto_orden_cascada.json", "w",
                      encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\n-> data/efecto_orden_cascada.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
