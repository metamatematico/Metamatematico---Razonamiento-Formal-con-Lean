# -*- coding: utf-8 -*-
"""¿Sabe el grafo que tactica de Lean va con cada area? Preguntaselo a Mathlib.

El grafo tiene 9 nodos de tactica y 167 morfismos dominio->tactica, y esos
morfismos SI llegan a la cascada: core.py saca la tactica del area y
GoalAnalyzer.prioritize la pone primera al rellenar un `sorry`. Pero los 167
salen de doce reglas escritas a mano por area ancha (CATEGORY_TACTIC_SKILL), y
nadie las ha comprobado nunca. El vocabulario tiene su 95 %, las dependencias
su 78 %; esto no tiene numero.

Mathlib si lo sabe: sus pruebas dicen que tactica se uso de verdad.

DOS MEDIDAS, y la segunda es la que importa:

  A · primera tactica de cada prueba — con que se empieza en esa area.
  B · pruebas que se cierran en UNA LINEA (`:= by tac`) — que tactica CIERRA
      sola. Es el analogo exacto de lo que hace la cascada: tiene un `sorry` y
      busca una tactica que lo cierre. Por eso B manda sobre A.

AVISO DE METODO: Mathlib son pruebas de libreria, no de competicion, y sus
enunciados ya vienen colocados para que la tactica corta funcione. La
frecuencia aqui es un proxy del acierto de la regla, no la verdad sobre que
cerraria un `sorry` cualquiera.

No gasta API.
"""
import collections
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MATH = "E:/Metamatematico/.lake/packages/mathlib/Mathlib"
SALIDA = "E:/Metamatematico/data/tacticas_reales.json"

#: Directorio de primer nivel de Mathlib -> categoria del grafo.
AREA = {
    "Algebra": "algebra", "RingTheory": "algebra", "GroupTheory": "algebra",
    "LinearAlgebra": "algebra", "FieldTheory": "algebra",
    "RepresentationTheory": "algebra",
    "Analysis": "analysis",
    "CategoryTheory": "category-theory",
    "Combinatorics": "combinatorics",
    "Computability": "computation",
    "Geometry": "geometry",
    "Logic": "logic", "ModelTheory": "logic",
    "NumberTheory": "number-theory",
    "Probability": "probability", "MeasureTheory": "probability",
    "Dynamics": "probability",
    "SetTheory": "set-theory", "Order": "set-theory",
    "Topology": "topology",
}

#: Tactica de Lean -> el nodo del grafo que la agrupa.
#:
#: Los nodos son CAJONES: `tactic-omega` documenta omega, norm_num y linarith
#: juntas, que son tres tacticas con dominios de aplicacion distintos. Se
#: respeta la agrupacion del grafo para que la comparacion sea justa con el.
_GRUPOS = {
    "tactic-simp": "simp simpa dsimp simp_all simp_rw norm_cast push_cast",
    "tactic-rewrite": "rw rwa nth_rewrite subst unfold erw",
    "tactic-exact": "exact refine rfl trivial assumption exact_mod_cast",
    "tactic-apply": "apply convert specialize use constructor",
    "tactic-induction": "induction cases rcases obtain by_cases",
    "tactic-omega": "omega norm_num linarith nlinarith positivity bound",
    "tactic-ring": "ring ring_nf field_simp abel module",
    "tactic-aesop": "aesop tauto decide measurability continuity fun_prop "
                    "gcongr filter_upwards",
    "tactic-calc": "calc",
}
CAJON = {}
for _c, _ts in _GRUPOS.items():
    for _t in _ts.split():
        CAJON.setdefault(_t, _c)

PRUEBA = re.compile(r":=\s*by\b(.*)$")
PRIMERA = re.compile(r"^\s*([a-z_][A-Za-z0-9_]*)")


def _indent(linea):
    return len(linea) - len(linea.lstrip())


def recorrer():
    """(primera tactica, tactica que cierra sola) por area."""
    A = collections.defaultdict(collections.Counter)
    B = collections.defaultdict(collections.Counter)
    ficheros = 0
    for raiz, _d, fs in os.walk(MATH):
        for f in fs:
            if not f.endswith(".lean"):
                continue
            rel = os.path.relpath(os.path.join(raiz, f), MATH).replace("\\", "/")
            area = AREA.get(rel.split("/")[0])
            if not area:
                continue
            ficheros += 1
            try:
                ls = io.open(os.path.join(raiz, f), encoding="utf-8",
                             errors="replace").read().splitlines()
            except Exception:
                continue
            for i, l in enumerate(ls):
                m = PRUEBA.search(l)
                if not m:
                    continue
                resto = m.group(1).strip()
                if resto:
                    # `:= by tac ...` en la misma linea
                    p = PRIMERA.match(resto)
                    if not p:
                        continue
                    tac = p.group(1)
                    A[area][tac] += 1
                    # ¿Se acabo la prueba aqui? La siguiente linea no continua
                    # el bloque si no esta mas indentada que esta.
                    sig = ls[i + 1] if i + 1 < len(ls) else ""
                    if not sig.strip() or _indent(sig) <= _indent(l):
                        B[area][tac] += 1
                else:
                    # `:= by` con la tactica en la linea de abajo
                    for j in range(i + 1, min(i + 3, len(ls))):
                        if ls[j].strip():
                            p = PRIMERA.match(ls[j])
                            if p:
                                A[area][p.group(1)] += 1
                            break
    return A, B, ficheros


def por_cajon(cnt):
    c = collections.Counter()
    for t, n in cnt.items():
        caj = CAJON.get(t)
        if caj:
            c[caj] += n
    return c


def main():
    from nucleo.pillars.math_domains import CATEGORY_TACTIC_SKILL
    print("recorriendo las pruebas de Mathlib...")
    A, B, ficheros = recorrer()
    print("  %d ficheros en areas mapeadas" % ficheros)
    print("  %d pruebas que cierran en una linea\n"
          % sum(sum(c.values()) for c in B.values()))
    if not ficheros:
        print("  ATENCION: ni un fichero — revisa MATH=%s" % MATH)
        return 1

    aciertos = fallos = 0
    print("=== B · QUE TACTICA CIERRA SOLA, POR AREA ===")
    print("    (la medida que importa: es lo que hace la cascada ante un sorry)\n")
    for area in sorted(CATEGORY_TACTIC_SKILL):
        regla = CATEGORY_TACTIC_SKILL[area]
        cnt = B.get(area)
        if not cnt:
            print("  %-16s regla=%-15s  — Mathlib no tiene esta area"
                  % (area, regla))
            continue
        caj = por_cajon(cnt)
        total = sum(caj.values()) or 1
        orden = [c for c, _ in caj.most_common()]
        pos = orden.index(regla) + 1 if regla in orden else 0
        if pos == 1:
            veredicto = "ACIERTA"
            aciertos += 1
        else:
            veredicto = ("2o de %d" % len(orden) if pos == 2 else
                         "FALLA (%do de %d)" % (pos, len(orden)) if pos else
                         "FALLA (0 usos)")
            fallos += 1
        print("  %-16s regla=%-15s  %s" % (area, regla, veredicto))
        print("       Mathlib usa : %s" % ", ".join(
            "%s %.0f%%" % (c.replace("tactic-", ""), 100.0 * n / total)
            for c, n in caj.most_common(4)))
        print("       en crudo    : %s" % ", ".join(
            "%s %d" % (t, n) for t, n in cnt.most_common(5)))
    print("\n  la regla acierta la mas frecuente en %d de %d areas"
          % (aciertos, aciertos + fallos))

    print("\n=== A · CON QUE TACTICA SE EMPIEZA (todas las pruebas) ===\n")
    for area in sorted(A):
        caj = por_cajon(A[area])
        total = sum(caj.values()) or 1
        print("  %-16s %s" % (area, ", ".join(
            "%s %.0f%%" % (c.replace("tactic-", ""), 100.0 * n / total)
            for c, n in caj.most_common(4))))

    json.dump({"cierran_solas": {a: dict(por_cajon(c)) for a, c in B.items()},
               "crudo": {a: dict(c.most_common(20)) for a, c in B.items()},
               "regla": CATEGORY_TACTIC_SKILL,
               "aciertos": aciertos, "fallos": fallos},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
