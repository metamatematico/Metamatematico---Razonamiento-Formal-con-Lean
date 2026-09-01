# -*- coding: utf-8 -*-
"""¿Acierta el sistema el ÁREA y las SKILLS de una consulta? Nunca se midió.

Los dos brazos del grafo en tiempo de consulta —los nombres de Mathlib que
entran en el prompt y los módulos que Lean importa— salen del MISMO sitio:
`_find_relevant_context` -> `_match_skills_to_query`. Y la cascada se ordena
con `classify_query`. Si ese emparejamiento falla, fallan los tres a la vez, y
da igual lo bueno que sea el vocabulario o lo bien medida que esté la tabla de
tácticas.

Se ha citado como «el cuello de botella» varias veces sin un número detrás.
Esto lo mide, con datos etiquetados que ya estaban en disco: el split de test
de MATH+GSM8K, 12 874 problemas con su categoría puesta por el dataset.

DOS MEDIDAS:
  A · classify_query(texto) vs la categoría del dataset — es lo que elige el
      orden de tácticas del área.
  B · las skills que activa `_match_skills_to_query`, ¿son del área correcta?
      Sin etiqueta por skill, se juzga por el `category` de la skill activada.
      También cuántas consultas no activan NINGUNA skill, que es el fallo
      silencioso: el grafo no aporta nada y nadie se entera.

AVISO: las categorías del dataset (`algebra`, `geometry`, `number_theory`,
`counting_and_probability`, `precalculus`, `intermediate_algebra`,
`prealgebra`, `gsm8k`) no son las once del grafo. El mapeo va explícito abajo y
las que no tienen equivalente se excluyen del recuento de aciertos en vez de
contarlas como fallo.

No gasta API.
"""
import collections
import io
import json
import os
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATOS = "E:/datadeentrenamientovalidacion_test/all_test.jsonl"
SALIDA = "E:/Metamatematico/data/emparejamiento.json"
MUESTRA = 3000
SEMILLA = 20260901

#: Categoria del dataset -> area del grafo. Solo las inequivocas.
MAPA = {
    "algebra": "algebra",
    "intermediate_algebra": "algebra",
    "prealgebra": "algebra",
    "geometry": "geometry",
    "number_theory": "number-theory",
    "counting_and_probability": "combinatorics",
    "precalculus": "analysis",
    "gsm8k": None,          # aritmetica de enunciado, sin area clara: se excluye
}


def cargar():
    filas = []
    for linea in io.open(DATOS, encoding="utf-8"):
        d = json.loads(linea)
        p, c = d.get("problem"), d.get("category")
        if p and c:
            filas.append((p, c))
    return filas


def main():
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    from nucleo.multi_agent.specialized_agent import classify_query

    print("cargando el split de test...")
    filas = cargar()
    print("  %d problemas etiquetados" % len(filas))
    if not filas:
        print("  ATENCION: no se leyo nada — revisa %s" % DATOS)
        return 1
    print("  categorias:", dict(collections.Counter(c for _, c in filas)))

    random.seed(SEMILLA)
    muestra = random.sample(filas, min(MUESTRA, len(filas)))
    print("  muestra: %d (semilla %d)\n" % (len(muestra), SEMILLA))

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph
    area_de_skill = {s.id: (s.metadata or {}).get("category") for s in g.skills}

    # ── A · el area ────────────────────────────────────────────────────────
    ok = mal = excl = 0
    confus = collections.Counter()
    # ── B · las skills ─────────────────────────────────────────────────────
    sin_skill = 0
    skill_ok = skill_mal = skill_sin_area = 0
    n_skills = []
    activadas = collections.Counter()

    for texto, cat in muestra:
        esperada = MAPA.get(cat, "")
        pred = classify_query(texto)
        if esperada is None or esperada == "":
            excl += 1
        elif pred == esperada:
            ok += 1
        else:
            mal += 1
            confus[(esperada, pred)] += 1

        skills = Nucleo._match_skills_to_query(n, texto, g)
        n_skills.append(len(skills))
        if not skills:
            sin_skill += 1
            continue
        for s in skills[:3]:
            activadas[s] += 1
        a = area_de_skill.get(skills[0])
        if esperada is None or esperada == "":
            pass
        elif a is None:
            skill_sin_area += 1
        elif a == esperada:
            skill_ok += 1
        else:
            skill_mal += 1

    N = len(muestra)
    med = ok + mal
    print("=== A · classify_query, el area que ordena las tacticas ===\n")
    print("  acierta   : %5d / %d = %5.1f %%" % (ok, med, 100.0 * ok / max(1, med)))
    print("  falla     : %5d / %d = %5.1f %%" % (mal, med, 100.0 * mal / max(1, med)))
    print("  excluidas : %5d  (categoria sin equivalente en el grafo)" % excl)
    print("\n  confusiones mas frecuentes (esperada -> predicha):")
    for (e, p), c in confus.most_common(8):
        print("     %-16s -> %-16s %d" % (e, p, c))

    print("\n=== B · las skills activadas, que alimentan prompt e imports ===\n")
    print("  consultas SIN NINGUNA skill : %5d / %d = %5.1f %%"
          % (sin_skill, N, 100.0 * sin_skill / N))
    print("  skills por consulta, media  : %.2f" % (sum(n_skills) / N))
    smed = skill_ok + skill_mal
    print("  la 1a skill es del area buena: %5d / %d = %5.1f %%"
          % (skill_ok, smed, 100.0 * skill_ok / max(1, smed)))
    print("  la 1a skill no tiene area   : %5d" % skill_sin_area)
    print("\n  skills mas activadas:")
    for s, c in activadas.most_common(10):
        print("     %-28s %5d  (%s)" % (s, c, area_de_skill.get(s)))

    json.dump({"muestra": N, "semilla": SEMILLA,
               "area_acierta": ok, "area_falla": mal, "area_excluidas": excl,
               "sin_skill": sin_skill, "skills_por_consulta": sum(n_skills) / N,
               "skill_area_ok": skill_ok, "skill_area_mal": skill_mal,
               "confusiones": {"%s->%s" % k: v for k, v in confus.most_common(20)},
               "mas_activadas": dict(activadas.most_common(20))},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
