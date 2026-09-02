# -*- coding: utf-8 -*-
"""Compila el índice de premisas que el runtime consultará.

La medicion se hace sobre 183 433 hechos y un TF-IDF de 60 000 terminos. Eso no
puede cargarse en cada arranque del sistema, asi que aqui se destila a un
artefacto pequeño con lo unico que hace falta en caliente:

    por_area     las premisas mas citadas de cada area, en orden
    catalogo     los lemas no-@[simp] mas citados, con su texto para buscar

POR QUE NO-@[simp]. Medido: el 42,1 % de las premisas que citan las pruebas de
Mathlib ya llevan `@[simp]`, y `simp` las conoce sin que nadie se las pase.
Recuperarlas es trabajo tirado. Filtrarlas hizo que el hibrido pasara de
empatar con el prior de frecuencia (9,4 vs 9,2) a superarlo (14,0 vs 11,7).

POR QUE POR AREA. Tampoco es uniforme: en Combinatoria el contenido gana al
prior, en CategoryTheory el contenido saca 0,0 % —sus enunciados son diagramas,
no palabras— y el hibrido EMPEORA respecto al nulo. Una regla global seria peor
que ninguna, asi que el indice guarda que estrategia gana en cada area.

    python scripts/construir_indice_premisas.py
"""
import argparse
import collections
import io
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LISTA = "E:/Metamatematico/data/lemas_mathlib.jsonl"
MEDIDA = "E:/Metamatematico/data/premisas_sin_simp.json"
SALIDA = "E:/Metamatematico/data/indice_premisas.json"

#: Cuantos lemas entran en el catalogo consultable. Con 4 000 se cubre la
#: mayoria de las citas reales sin cargar 54 MB en memoria.
TOPE_CATALOGO = 4000
#: Cuantas premisas se guardan por area para el prior de frecuencia.
POR_AREA = 24

#: Area de Mathlib -> categoria del grafo, para que el runtime pueda pedir
#: premisas con la misma clave que ya usa para las tacticas.
CATEGORIA = {
    "Algebra": "algebra", "RingTheory": "algebra", "GroupTheory": "algebra",
    "LinearAlgebra": "algebra", "FieldTheory": "algebra",
    "RepresentationTheory": "algebra", "Data": "algebra",
    "Analysis": "analysis", "CategoryTheory": "category-theory",
    "Combinatorics": "combinatorics", "Computability": "computation",
    "Geometry": "geometry", "Logic": "logic", "ModelTheory": "logic",
    "NumberTheory": "number-theory", "Probability": "probability",
    "MeasureTheory": "probability", "Dynamics": "probability",
    "SetTheory": "set-theory", "Order": "set-theory", "Topology": "topology",
    "AlgebraicGeometry": "geometry", "AlgebraicTopology": "topology",
}


def main(_):
    from scripts.premisas_sin_simp import indice_atributos
    from scripts.banco_premisas_mathlib import recolectar

    t0 = time.time()
    print("indexando atributos...")
    simp = indice_atributos()["simp"]
    lemas = [json.loads(l) for l in io.open(LISTA, encoding="utf-8")]
    cortos = {d["corto"] for d in lemas}
    largos = {d["nombre"] for d in lemas}
    print("  @[simp]: %d lemas" % len(simp))

    print("recolectando premisas reales...")
    casos = recolectar(cortos, largos, 60000)
    for c in casos:
        c["premisas"] = [p for p in c["premisas"]
                         if p.split(".")[-1] not in simp]
    casos = [c for c in casos if c["premisas"]]
    print("  %d teoremas · %.0f s" % (len(casos), time.time() - t0))

    # ── el prior por area ───────────────────────────────────────────────────
    por_area_raw = collections.defaultdict(collections.Counter)
    global_cnt = collections.Counter()
    for c in casos:
        cat = CATEGORIA.get(c["area"])
        for p in c["premisas"]:
            global_cnt[p] += 1
            if cat:
                por_area_raw[cat][p] += 1
    por_area = {a: [p for p, _ in cnt.most_common(POR_AREA)]
                for a, cnt in por_area_raw.items()}

    # ── el catalogo consultable ────────────────────────────────────────────
    texto = {d["nombre"]: (d["nombre"].replace(".", " ").replace("_", " ")
                           + " . " + d["enunciado"])
             for d in lemas if d["corto"] not in simp}
    catalogo = []
    for nombre, _ in global_cnt.most_common(TOPE_CATALOGO):
        t = texto.get(nombre)
        if t:
            catalogo.append({"n": nombre, "t": t[:220]})
    print("  catalogo: %d lemas" % len(catalogo))

    # ── que estrategia gana en cada area, de la medicion ya hecha ──────────
    estrategia = {}
    if os.path.exists(MEDIDA):
        med = json.load(io.open(MEDIDA, encoding="utf-8"))
        for fila in med.get("por_area", []):
            cat = CATEGORIA.get(fila["area"])
            if not cat or fila["casos"] < 30:
                continue      # con menos de 30 casos no se decide nada
            opciones = {"hibrido": fila["hibrido"], "nulo": fila["nulo"],
                        "lexico": fila["lexico"]}
            estrategia[cat] = max(opciones, key=opciones.get)
    print("  estrategia por area:", estrategia)

    json.dump({"por_area": por_area, "global": [p for p, _ in
                                                global_cnt.most_common(POR_AREA)],
               "catalogo": catalogo, "estrategia": estrategia,
               "tope_catalogo": TOPE_CATALOGO},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n  -> %s (%.1f MB)" % (SALIDA, os.path.getsize(SALIDA) / 1e6))
    for a in sorted(por_area):
        print("     %-16s %s" % (a, ", ".join(por_area[a][:5])))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    a = ap.parse_args()
    sys.exit(main(a))
