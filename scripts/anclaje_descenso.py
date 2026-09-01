# -*- coding: utf-8 -*-
"""Prototipo: anclar la consulta en un PILAR y descender por el arbol.

LO QUE HAY HOY es una busqueda plana: `_match_skills_to_query` puntua los 173
nodos por solapamiento de palabras y devuelve los diez mejores, sin mirar el
nivel. Consecuencias medidas:

    15 de 24 consultas reales no activan NINGUNA skill
    los 10 nodos fundacionales no se activan NUNCA (0 de 24)
    el area de la primera skill acierta el 43,9 % en MATH,
      cuando decir siempre «algebra» acierta el 79,4 %

Y sin embargo la jerarquia existe: los 163 dominios alcanzan una base por
prerrequisitos, `zfc-axioms` domina 148 nodos. El grafo tiene el camino y el
buscador lo esquiva.

LO QUE SE PRUEBA AQUI es lo contrario: primero se decide en que teoria base
vive la consulta —conjuntos, categorias, tipos, logica— y desde ahi se BAJA
mientras la semantica aguante. El resultado no es una lista suelta de nodos:
es un CAMINO, que dice en que teoria se esta trabajando.

    consulta -> pilar -> hijo -> hijo -> ... -> hoja

CRITERIOS FIJADOS ANTES DE MEDIR, para no moverlos despues:

    banco : >= 20 de 24 consultas con camino no vacio   (hoy 9)
    MATH  : area de la hoja >= 80 %                      (hoy 43,9 %; nulo 79,4 %)
    MATH  : consultas sin nada < 10 %                    (hoy 27,1 %)

El de cobertura se cumple por construccion —siempre hay ancla— asi que el que
decide es el de acierto de area contra el 79,4 % del modelo nulo. Si no lo
supera, el descenso lexico se declara fallido y se pasa a embeddings.

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

DATOS = "E:/datadeentrenamientovalidacion_test/all_test.jsonl"
SALIDA = "E:/Metamatematico/data/anclaje_descenso.json"
MUESTRA = 3000
SEMILLA = 20260901
PROFUNDIDAD = 4

#: Tokens que traen los NOMBRES de las skills y no distinguen nada. Sin
#: quitarlos, «Eigenvalues and Eigenvectors» aporta `and`, que aparece en 1583
#: de 3000 problemas de MATH y activa eigen-theory en todos.
VACIAS = {
    "and", "the", "for", "with", "from", "into", "over", "its", "their",
    "sobre", "para", "con", "sin", "del", "las", "los", "una", "uno", "que",
    "por", "entre", "theory", "theories", "teoria", "basic", "basics",
    "general", "advanced", "study", "properties", "structure", "structures",
    "methods", "spaces", "space",
}

#: Pistas explicitas de cada pilar. Cortas y sin ambiguedad: son el ancla, y
#: equivocarse aqui arrastra todo el descenso.
PISTAS = {
    "LOG": ["proposicion", "proposiciones", "implica", "implicacion", "tautologia",
            "cuantificador", "cuantificadores", "predicado", "logica",
            "primer orden", "segundo orden", "demostrable", "consistencia",
            "completitud", "satisfacible", "modelo", "proposition", "implies",
            "tautology", "quantifier", "predicate", "logic", "first-order"],
    "CAT": ["categoria", "categorias", "funtor", "funtores", "morfismo",
            "morfismos", "natural", "colimite", "limite categorico", "adjuncion",
            "objeto inicial", "objeto terminal", "category", "functor",
            "morphism", "colimit", "adjunction"],
    "TYPE": ["tipo", "tipos", "dependiente", "curry", "howard", "lambda",
             "calculo lambda", "constructivo", "intuicionista", "lean",
             "tactica", "tacticas", "type", "dependent", "constructive",
             "intuitionistic", "tactic"],
    "SET": ["conjunto", "conjuntos", "union", "interseccion", "complemento",
            "subconjunto", "pertenece", "cardinal", "ordinal", "zfc",
            "set", "sets", "union", "intersection", "subset", "cardinality"],
}

#: Si nada casa, la matematica ordinaria vive sobre conjuntos. Es el suelo:
#: mejor anclar en lo general que devolver silencio, que es lo que pasa hoy en
#: 15 de 24 consultas reales.
POR_DEFECTO = "SET"

MAPA_CAT = {"algebra": "algebra", "geometry": "geometry",
            "number_theory": "number-theory", "combinatorics": "combinatorics",
            "analysis": "analysis"}


def tokens_query(q):
    return {t for t in q.lower().replace("-", " ").replace("_", " ").split()
            if len(t) > 2}


def _tokens_skill(sk):
    t = set(sk.id.lower().replace("-", " ").split()
            + sk.name.lower().replace("-", " ").split())
    return t - VACIAS


def puntua(sk, qt, ql):
    """Cuanto casa esta skill con la consulta. Keyword declarada pesa mas."""
    p = len(qt & _tokens_skill(sk))
    for kw in (sk.metadata or {}).get("keywords", []) or []:
        kw = kw.lower().strip()
        if not kw:
            continue
        if " " in kw:
            if re.search(r"\b%s\b" % re.escape(kw), ql):
                p += 3
        elif kw in qt:
            p += 3
    return p


def ancla(ql):
    """En que teoria base vive la consulta."""
    marcas = collections.Counter()
    for pilar, pistas in PISTAS.items():
        for w in pistas:
            if " " in w:
                if re.search(r"\b%s\b" % re.escape(w), ql):
                    marcas[pilar] += 2
            elif re.search(r"\b%s\b" % re.escape(w), ql):
                marcas[pilar] += 1
    if not marcas:
        return POR_DEFECTO, False
    return marcas.most_common(1)[0][0], True


def descender(g, ql, qt, pilar, profundidad=PROFUNDIDAD):
    """Del pilar hacia abajo, mientras algun hijo case. Devuelve el CAMINO."""
    frente = [s.id for s in g.skills if s.level == 0 and s.pillar.name == pilar]
    if not frente:
        return []
    # de los nodos base del pilar, el que mas case (o el que mas hijos tenga)
    raiz = max(frente, key=lambda i: (puntua(g.get_skill(i), qt, ql),
                                      len(g.dependents(i))))
    camino = [raiz]
    actual = raiz
    for _ in range(profundidad):
        hijos = g.dependents(actual)
        if not hijos:
            break
        puntuados = [(h, puntua(g.get_skill(h), qt, ql)) for h in hijos
                     if g.get_skill(h)]
        puntuados = [(h, p) for h, p in puntuados if p > 0]
        if not puntuados:
            break
        puntuados.sort(key=lambda x: -x[1])
        actual = puntuados[0][0]
        camino.append(actual)
    return camino


def main():
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph
    area_de = {s.id: (s.metadata or {}).get("category") for s in g.skills}

    # ── el banco: las consultas reales ─────────────────────────────────────
    from scripts.banco_fidelidad import CASOS
    print("=== LAS 24 CONSULTAS REALES ===\n")
    vacios = plano_vacio = 0
    for c in CASOS:
        q = c["pregunta"] if isinstance(c, dict) else c[1]
        ql, qt = q.lower(), tokens_query(q)
        p, explicito = ancla(ql)
        cam = descender(g, ql, qt, p)
        if len(cam) <= 1:
            vacios += 1
        if not Nucleo._match_skills_to_query(n, q, g):
            plano_vacio += 1
        print("  %-44s %-5s %s" % (q[:42], p + ("" if explicito else "*"),
                                   " -> ".join(cam) or "(nada)"))
    print("\n  * = ancla por defecto, sin pista explicita")
    print("  camino de un solo nodo (solo la base): %d de %d" % (vacios, len(CASOS)))
    print("  con el buscador plano de hoy, SIN NADA: %d de %d"
          % (plano_vacio, len(CASOS)))

    # ── MATH: el acierto de area ───────────────────────────────────────────
    filas = [json.loads(l) for l in io.open(DATOS, encoding="utf-8")]
    random.seed(SEMILLA)
    muestra = random.sample(filas, min(MUESTRA, len(filas)))
    ok = mal = sin = 0
    prof = []
    pilar_por_cat = collections.defaultdict(collections.Counter)
    for d in muestra:
        q = d["problem"]
        ql, qt = q.lower(), tokens_query(q)
        p, _ = ancla(ql)
        cam = descender(g, ql, qt, p)
        prof.append(len(cam))
        esp = MAPA_CAT.get(d.get("category") or "")
        if esp:
            pilar_por_cat[esp][p] += 1
        if len(cam) <= 1:
            sin += 1
            continue
        if not esp:
            continue
        if area_de.get(cam[-1]) == esp:
            ok += 1
        else:
            mal += 1

    N = len(muestra)
    print("\n=== MATH, %d problemas etiquetados ===\n" % N)
    print("  solo la base, sin descender : %5d = %5.1f %%" % (sin, 100.0 * sin / N))
    print("  profundidad media del camino: %.2f" % (sum(prof) / N))
    print("  area de la HOJA acierta     : %5d / %d = %5.1f %%"
          % (ok, ok + mal, 100.0 * ok / max(1, ok + mal)))
    print("     modelo nulo (siempre algebra) : 79.4 %")
    print("     buscador plano de hoy         : 43.9 %")

    print("\n=== ¿SON DISTINGUIBLES LOS PILARES? ===")
    print("    (si la fila es igual para todas las categorias, el ancla no informa)\n")
    for cat, cnt in sorted(pilar_por_cat.items()):
        tot = sum(cnt.values())
        print("  %-16s %s" % (cat, ", ".join(
            "%s %.0f%%" % (k, 100.0 * v / tot) for k, v in cnt.most_common())))

    json.dump({"muestra": N, "semilla": SEMILLA, "sin_descender": sin,
               "profundidad_media": sum(prof) / N,
               "area_ok": ok, "area_mal": mal,
               "banco_camino_trivial": vacios, "banco_plano_vacio": plano_vacio,
               "pilar_por_categoria": {k: dict(v) for k, v in pilar_por_cat.items()}},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
