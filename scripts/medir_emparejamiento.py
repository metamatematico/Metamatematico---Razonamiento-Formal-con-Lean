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

    #: (area esperada, area predicha), uno por consulta medida. Hace falta
    #: guardarlos y no solo el recuento: la exactitud EQUILIBRADA se calcula
    #: por area, y es la unica que sobrevive al desequilibrio de este banco.
    pares_area = []
    pares_skill = []

    for texto, cat in muestra:
        esperada = MAPA.get(cat, "")
        pred = classify_query(texto)
        if esperada is None or esperada == "":
            excl += 1
        elif pred == esperada:
            ok += 1
            pares_area.append((esperada, pred))
        else:
            mal += 1
            confus[(esperada, pred)] += 1
            pares_area.append((esperada, pred))

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
            pares_skill.append((esperada, a))
        else:
            skill_mal += 1
            pares_skill.append((esperada, a))

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

    # ── C · EL NULO, QUE FALTABA, Y SIN EL LAS DOS CIFRAS DE ARRIBA MIENTEN ─
    #
    # Las medidas A y B se publicaron como 61,2 % y 52,1 % durante meses sin
    # nadie calcular contra que. El banco esta 89 % dominado por `algebra`, o
    # sea que RESPONDER SIEMPRE «algebra», sin leer el enunciado, acierta el
    # 89,0 %. Las dos medidas pierden contra esa constante por 28 y 37 puntos.
    #
    # No significa que el emparejador no valga: significa que la exactitud
    # CRUDA sobre un banco asi no dice nada de el. La que si dice algo es la
    # EQUILIBRADA —la media de los aciertos dentro de cada area—, donde el
    # nulo de mayoria se hunde al 33,3 % (acierta un area de tres y falla las
    # otras dos) y el sistema se pone por encima.
    #
    # Es §12.2 aplicado a este medidor: comparar dos versiones de tu propia
    # idea no es una medicion. La cifra cruda se sigue imprimiendo, pero nunca
    # mas sola.
    dist = collections.Counter(e for e, _p in pares_skill)
    tot_d = sum(dist.values())
    may, cmay = (dist.most_common(1) or [("", 0)])[0]
    nulo_crudo = 100.0 * cmay / max(1, tot_d)
    nulo_eq = 100.0 / max(1, len(dist))

    def equilibrada(pares):
        """Media de los aciertos DENTRO de cada area. Inmune al desequilibrio."""
        por = collections.defaultdict(lambda: [0, 0])
        for esp, pr in pares:
            por[esp][1] += 1
            if esp == pr:
                por[esp][0] += 1
        if not por:
            return 0.0
        return sum(100.0 * a / t for a, t in por.values()) / len(por)

    eq_area = equilibrada(pares_area)
    eq_skill = equilibrada(pares_skill)

    print("\n=== C · EL NULO. Sin esto, A y B no dicen nada ===\n")
    print("  el banco esta desequilibrado:")
    for a, c in dist.most_common():
        print("     %-16s %5d  %5.1f %%" % (a, c, 100.0 * c / max(1, tot_d)))
    print("\n  NULO DE MAYORIA — responder siempre «%s», sin leer:" % may)
    print("     cruda %5.1f %%      equilibrada %5.1f %%" % (nulo_crudo, nulo_eq))
    print("\n  %-34s %8s %12s" % ("", "cruda", "equilibrada"))
    print("  %-34s %7.1f %% %11.1f %%"
          % ("A · classify_query", 100.0 * ok / max(1, med), eq_area))
    print("  %-34s %7.1f %% %11.1f %%"
          % ("B · area de la 1a skill", 100.0 * skill_ok / max(1, smed), eq_skill))
    print("  %-34s %7.1f %% %11.1f %%"
          % ("nulo de mayoria", nulo_crudo, nulo_eq))
    print("\n  EN CRUDA LAS DOS PIERDEN CONTRA LA CONSTANTE (%+.1f y %+.1f)."
          % (100.0 * ok / max(1, med) - nulo_crudo,
             100.0 * skill_ok / max(1, smed) - nulo_crudo))
    print("  En equilibrada ganan (%+.1f y %+.1f). Es la cifra que hay que citar."
          % (eq_area - nulo_eq, eq_skill - nulo_eq))

    json.dump({"muestra": N, "semilla": SEMILLA,
               "area_acierta": ok, "area_falla": mal, "area_excluidas": excl,
               "sin_skill": sin_skill, "skills_por_consulta": sum(n_skills) / N,
               "skill_area_ok": skill_ok, "skill_area_mal": skill_mal,
               # El nulo va EN EL FICHERO, no solo en la pantalla: quien lea
               # el json para citar una cifra tiene que tropezarse con el.
               "nulo_mayoria_area": may,
               "nulo_mayoria_cruda": round(nulo_crudo, 2),
               "nulo_mayoria_equilibrada": round(nulo_eq, 2),
               "area_equilibrada": round(eq_area, 2),
               "skill_area_equilibrada": round(eq_skill, 2),
               "distribucion_areas": dict(dist.most_common()),
               "confusiones": {"%s->%s" % k: v for k, v in confus.most_common(20)},
               "mas_activadas": dict(activadas.most_common(20))},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
