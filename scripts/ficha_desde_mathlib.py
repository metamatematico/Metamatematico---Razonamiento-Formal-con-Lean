# -*- coding: utf-8 -*-
"""¿Sirve el texto de Mathlib como descripcion de una skill? A/B, sin crear nodos.

El emparejador semantico saco 11,9 % crudo y 21,1 % equilibrado, contra 20,0 %
del modelo nulo: informa por un punto, o sea nada. Una explicacion posible es
que el texto con el que se compara cada skill es pobre — un nombre y una linea
de descripcion escrita a mano:

    "Ring Theory. Rings, ideals, quotients, PIDs, UFDs, polynomial rings"

Mathlib tiene, para los mismos conceptos, el docstring del modulo y los nombres
de todas las declaraciones de debajo. Si esa es la causa, cambiar el texto debe
mover la cifra SIN tocar el grafo ni crear un solo nodo.

TRES VARIANTES, mismo modelo, mismo conjunto, misma metrica:
    A · la ficha escrita a mano (lo de hoy)
    B · texto derivado de Mathlib
    C · las dos juntas

METRICA: acierto EQUILIBRADO por area, que es el que vale con clases tan
desbalanceadas (el conjunto es 79 % algebra, y ahi «di siempre algebra» saca
79,4 % crudo sin informar nada; su equilibrado es 20 %).

AVISO: solo 76 de las 173 skills tienen modulo asignado, asi que solo esas
cambian de texto. Es lo realista, no una comparacion idealizada.

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

MATH = "E:/Metamatematico/.lake/packages/mathlib/Mathlib"
MAPA = "E:/Metamatematico/data/mathlib_modulos.json"
DATOS = "E:/datadeentrenamientovalidacion_test/all_test.jsonl"
SALIDA = "E:/Metamatematico/data/ficha_desde_mathlib.json"
MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
UMBRAL = 0.25
MUESTRA = 3000
SEMILLA = 20260901
MAX_DECL = 60          # nombres de declaracion por skill: mas es ruido

DOC = re.compile(r"/-!(.*?)-/", re.S)
DECL = re.compile(r"^\s*(?:@\[[^\]]*\]\s*)?(?:private\s+|protected\s+"
                  r"|noncomputable\s+)*"
                  r"(?:theorem|lemma|def|structure|class|abbrev)\s+"
                  r"([A-Za-z_][\w.']*)")
MAPA_CAT = {"algebra": "algebra", "geometry": "geometry",
            "number_theory": "number-theory", "combinatorics": "combinatorics",
            "analysis": "analysis"}


def _camel(n):
    """`isOpen_union` -> `is Open union`, para que el modelo lea palabras."""
    n = n.split(".")[-1]
    n = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", n)
    return n.replace("_", " ").lower()


def texto_mathlib(modulos):
    """Docstring del modulo y vocabulario de sus declaraciones."""
    docs, nombres = [], []
    for m in modulos:
        base = MATH + "/" + m.replace("Mathlib.", "", 1).replace(".", "/")
        rutas = []
        if os.path.exists(base + ".lean"):
            rutas.append(base + ".lean")
        padre = os.path.dirname(base)
        if os.path.isdir(padre):
            for f in sorted(os.listdir(padre))[:12]:
                if f.endswith(".lean"):
                    rutas.append(os.path.join(padre, f))
        for r in rutas[:12]:
            try:
                txt = io.open(r, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            d = DOC.search(txt)
            if d:
                # el docstring entero es largo; basta el titulo y el primer parrafo
                cuerpo = re.sub(r"[#*`]", " ", d.group(1)).strip()
                docs.append(" ".join(cuerpo.split())[:400])
            for l in txt.splitlines():
                mm = DECL.match(l)
                if mm:
                    nombres.append(_camel(mm.group(1)))
    vistos, unicos = set(), []
    for n in nombres:
        if n not in vistos:
            vistos.add(n)
            unicos.append(n)
        if len(unicos) >= MAX_DECL:
            break
    return " ".join(docs[:3]) + ". " + ", ".join(unicos)


def main():
    import numpy as np
    from sentence_transformers import SentenceTransformer
    from scripts.emparejador_semantico import texto_de, cargar_grafo

    n, g = cargar_grafo()
    skills = g.skills
    ids = [s.id for s in skills]
    area_de = {s.id: (s.metadata or {}).get("category") for s in skills}
    por_skill = json.load(io.open(MAPA, encoding="utf-8"))["por_skill"]

    print("construyendo texto desde Mathlib para %d skills..." % len(por_skill))
    tm = {}
    for sid, mods in por_skill.items():
        t = texto_mathlib(mods)
        if len(t.strip()) > 10:
            tm[sid] = t
    print("  con texto de Mathlib: %d de %d skills" % (len(tm), len(skills)))
    ej = next(iter(tm))
    print("\n  ejemplo · %s" % ej)
    print("     a mano : %s" % texto_de(g.get_skill(ej))[:150])
    print("     Mathlib: %s\n" % tm[ej][:150])

    filas = [json.loads(l) for l in io.open(DATOS, encoding="utf-8")]
    random.seed(SEMILLA)
    muestra = [d for d in random.sample(filas, MUESTRA)
               if MAPA_CAT.get(d.get("category") or "")]
    verdad = [MAPA_CAT[d["category"]] for d in muestra]
    print("evaluables: %d" % len(muestra))

    m = SentenceTransformer(MODELO)
    Q = m.encode([d["problem"] for d in muestra], normalize_embeddings=True,
                 batch_size=64, show_progress_bar=False)

    def evalua(nombre, textos):
        M = m.encode(textos, normalize_embeddings=True, batch_size=64,
                     show_progress_bar=False)
        sims = Q @ M.T
        ac, tot = collections.Counter(), collections.Counter()
        sin = 0
        for fila, esp in zip(sims, verdad):
            tot[esp] += 1
            i = int(np.argmax(fila))
            if fila[i] < UMBRAL:
                sin += 1
                continue
            if area_de.get(ids[i]) == esp:
                ac[esp] += 1
        crudo = 100.0 * sum(ac.values()) / len(verdad)
        equil = sum(100.0 * ac[a] / tot[a] for a in tot) / len(tot)
        print("\n  %s" % nombre)
        print("     crudo %5.1f %%  ·  EQUILIBRADO %5.1f %%  ·  sin skill %4.1f %%"
              % (crudo, equil, 100.0 * sin / len(verdad)))
        print("     " + "  ".join("%s %.0f%%" % (a, 100.0 * ac[a] / tot[a])
                                  for a in sorted(tot)))
        return crudo, equil

    print("\n=== REFERENCIA ===")
    print("  modelo nulo: crudo 79.4 %  ·  EQUILIBRADO 20.0 %")
    print("\n=== VARIANTES ===")
    A = [texto_de(s) for s in skills]
    B = [tm.get(s.id) or texto_de(s) for s in skills]
    C = [(texto_de(s) + ". " + tm[s.id]) if s.id in tm else texto_de(s)
         for s in skills]
    r = {}
    r["A_a_mano"] = evalua("A · ficha a mano (hoy)", A)
    r["B_mathlib"] = evalua("B · texto de Mathlib", B)
    r["C_ambas"] = evalua("C · las dos juntas", C)

    mejor = max(r, key=lambda k: r[k][1])
    print("\n  mejor por equilibrado: %s (%.1f %%)" % (mejor, r[mejor][1]))
    print("  liston del modelo nulo: 20.0 %")

    json.dump({"modelo": MODELO, "evaluables": len(muestra),
               "skills_con_texto_mathlib": len(tm),
               "resultados": {k: {"crudo": v[0], "equilibrado": v[1]}
                              for k, v in r.items()}},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
