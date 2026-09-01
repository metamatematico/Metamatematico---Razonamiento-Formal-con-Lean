# -*- coding: utf-8 -*-
"""Emparejar la consulta con el grafo por SEMÁNTICA, no por palabras.

POR QUE. Dos estrategias de busqueda lexica ya fallaron, y por la misma causa:

    buscador plano (hoy)       area de la 1a skill  43,9 %
    descenso anclado (probado) area de la hoja      11,8 %
    modelo nulo, decir siempre «algebra»            79,4 %

Los dos por debajo del modelo nulo. Y 15 de 24 consultas REALES no activan
ninguna skill: `(a+b)^2 = a^2+2ab+b^2` no contiene una sola palabra del
vocabulario del grafo. El problema no es como se recorre el grafo —plano o
jerarquico— sino que la funcion de comparacion no tiene señal que seguir.
Reorganizar el recorrido no crea informacion que no esta.

Añade ademas una barrera de idioma: las consultas son en español y el
vocabulario del grafo es mayormente ingles.

QUE HACE ESTO. Un modelo multilingue local convierte a vector la consulta y la
descripcion de cada skill, y se comparan por coseno. Sin API, sin coste por
consulta, sin red una vez bajado el modelo.

CRITERIOS, LOS MISMOS de antes y fijados antes de medir:

    banco : >= 20 de 24 consultas con alguna skill    (hoy 9)
    MATH  : area de la 1a skill >= 80 %                (hoy 43,9 %; nulo 79,4 %)
    MATH  : consultas sin nada < 10 %                  (hoy 27,1 %)

El que decide es el segundo: si no supera el 79,4 % del modelo nulo, esta via
tambien se declara fallida.

    python scripts/emparejador_semantico.py            # mide
    python scripts/emparejador_semantico.py --guardar  # y cachea los vectores
"""
import argparse
import collections
import io
import json
import os
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#: Multilingue y pequeño: cruza español<->ingles, que es medio problema.
MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DATOS = "E:/datadeentrenamientovalidacion_test/all_test.jsonl"
VECTORES = "E:/Metamatematico/data/vectores_skills.npz"
SALIDA = "E:/Metamatematico/data/emparejador_semantico.json"
MUESTRA = 3000
SEMILLA = 20260901
UMBRAL = 0.25          # coseno minimo para considerar que casa algo
TOPK = 6

MAPA_CAT = {"algebra": "algebra", "geometry": "geometry",
            "number_theory": "number-theory", "combinatorics": "combinatorics",
            "analysis": "analysis"}


def texto_de(skill):
    """Lo que representa a la skill: nombre, descripcion y terminos declarados.

    Se incluyen las keywords ES+EN porque son lo unico escrito en español que
    tiene el grafo, y la mitad del problema es que las consultas lo estan.
    """
    md = skill.metadata or {}
    partes = [skill.name, skill.description or ""]
    kws = md.get("keywords") or []
    if kws:
        partes.append(", ".join(kws))
    cat = md.get("category")
    if cat:
        partes.append(cat.replace("-", " "))
    return ". ".join(p for p in partes if p)


def cargar_grafo():
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    return n, n._graph


def main(guardar):
    import numpy as np
    from sentence_transformers import SentenceTransformer

    n, g = cargar_grafo()
    skills = g.skills
    ids = [s.id for s in skills]
    area_de = {s.id: (s.metadata or {}).get("category") for s in skills}

    print("cargando %s ..." % MODELO)
    modelo = SentenceTransformer(MODELO)
    print("  vectorizando %d skills..." % len(skills))
    M = modelo.encode([texto_de(s) for s in skills], normalize_embeddings=True,
                      batch_size=64, show_progress_bar=False)
    if guardar:
        np.savez_compressed(VECTORES, ids=np.array(ids), vectores=M)
        print("  -> %s" % VECTORES)

    def emparejar(consultas):
        Q = modelo.encode(consultas, normalize_embeddings=True, batch_size=64,
                          show_progress_bar=False)
        sims = Q @ M.T
        fuera = []
        for fila in sims:
            orden = np.argsort(-fila)[:TOPK]
            fuera.append([(ids[i], float(fila[i])) for i in orden
                          if fila[i] >= UMBRAL])
        return fuera

    # ── las 24 consultas reales ────────────────────────────────────────────
    from scripts.banco_fidelidad import CASOS
    from nucleo.core import Nucleo as _N
    preguntas = [c["pregunta"] if isinstance(c, dict) else c[1] for c in CASOS]
    res = emparejar(preguntas)
    print("\n=== LAS 24 CONSULTAS REALES ===\n")
    vacias = plano = 0
    for q, r in zip(preguntas, res):
        if not r:
            vacias += 1
        if not _N._match_skills_to_query(n, q, g):
            plano += 1
        print("  %-44s %s" % (q[:42], ", ".join(
            "%s %.2f" % (i, v) for i, v in r[:3]) or "(nada)"))
    print("\n  sin ninguna skill, semantico : %d de %d" % (vacias, len(CASOS)))
    print("  sin ninguna skill, lexico hoy: %d de %d" % (plano, len(CASOS)))

    # ── MATH ───────────────────────────────────────────────────────────────
    filas = [json.loads(l) for l in io.open(DATOS, encoding="utf-8")]
    random.seed(SEMILLA)
    muestra = random.sample(filas, min(MUESTRA, len(filas)))
    print("\nvectorizando %d problemas de MATH..." % len(muestra))
    res = emparejar([d["problem"] for d in muestra])

    ok = mal = sin = 0
    activadas = collections.Counter()
    for d, r in zip(muestra, res):
        if not r:
            sin += 1
            continue
        for i, _ in r[:3]:
            activadas[i] += 1
        esp = MAPA_CAT.get(d.get("category") or "")
        if not esp:
            continue
        if area_de.get(r[0][0]) == esp:
            ok += 1
        else:
            mal += 1

    N = len(muestra)
    print("\n=== MATH, %d problemas etiquetados ===\n" % N)
    print("  sin ninguna skill        : %5d = %5.1f %%   (criterio: < 10 %%)"
          % (sin, 100.0 * sin / N))
    print("  area de la 1a skill      : %5d / %d = %5.1f %%   (criterio: >= 80 %%)"
          % (ok, ok + mal, 100.0 * ok / max(1, ok + mal)))
    print("     modelo nulo 79.4 %  ·  lexico plano 43.9 %  ·  descenso 11.8 %")
    print("\n  skills mas activadas:")
    for s, c in activadas.most_common(8):
        print("     %-28s %5d  (%s)" % (s, c, area_de.get(s)))

    pct = 100.0 * ok / max(1, ok + mal)
    print("\n  VEREDICTO: %s" % (
        "SUPERA el modelo nulo" if pct >= 79.4 else
        "NO supera el modelo nulo (%.1f < 79.4)" % pct))

    json.dump({"modelo": MODELO, "muestra": N, "semilla": SEMILLA,
               "umbral": UMBRAL, "topk": TOPK,
               "sin_skill": sin, "area_ok": ok, "area_mal": mal,
               "banco_sin_skill": vacias, "banco_sin_skill_lexico": plano,
               "mas_activadas": dict(activadas.most_common(20))},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--guardar", action="store_true",
                    help="cachea los vectores de las skills en disco")
    a = ap.parse_args()
    sys.exit(main(a.guardar))
