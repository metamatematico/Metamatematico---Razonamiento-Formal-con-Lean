# -*- coding: utf-8 -*-
"""Seleccion de premisas EN EL ESCENARIO REAL: lo que simp no sabe ya.

MATHLIB NO ETIQUETA POR RAMA DE LAS MATEMATICAS. Se busco y no existe: la rama
la lleva la jerarquia de modulos. Lo que Mathlib SI anota, con 83 111 lineas de
atributos, es QUE TACTICA PUEDE USAR CADA LEMA:

    @[simp]      40 736      @[gcongr]       575
    @[norm_cast]  2 257      @[grind]        547
    @[fun_prop]   1 796      @[aesop]        286
    @[ext]        1 133      @[continuity]   255

Es un indice herramienta -> lemas, curado por los mantenedores. Y tiene una
consecuencia inmediata para la seleccion de premisas:

    el 42,1 % de las premisas de oro YA estan etiquetadas @[simp]

`simp` las conoce sin que nadie se las cite. Pasarselas en `simp [...]` no
aporta nada, y encima ensucian la medida: un recuperador que las acierte parece
bueno y no esta ayudando.

ESTE SCRIPT MIDE LO QUE IMPORTA: recuperar el 57,9 % que simp NO conoce,
buscando solo entre los candidatos que tampoco conoce. Es el escenario en el
que un `simp [premisa]` o un `nlinarith [premisa]` cambian algo.

No gasta API.
"""
import argparse
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
LISTA = "E:/Metamatematico/data/lemas_mathlib.jsonl"
SALIDA = "E:/Metamatematico/data/premisas_sin_simp.json"
SEMILLA = 20260901

ATTR = re.compile(r"^@\[([^\]]+)\]")
DECL = re.compile(r"^(?:@\[[^\]]*\]\s*)?(?:private\s+|protected\s+"
                  r"|noncomputable\s+)*(?:theorem|lemma)\s+([A-Za-z_][\w.']*)")

from scripts.construir_lista_lemas import _sin_comentarios  # noqa: E402
from scripts.banco_premisas_mathlib import recolectar  # noqa: E402
from scripts.medir_recuperacion_lemas import _texto  # noqa: E402


def indice_atributos():
    """atributo -> nombres cortos que lo llevan."""
    etiq = collections.defaultdict(set)
    for r, _d, fs in os.walk(MATH):
        for f in fs:
            if not f.endswith(".lean"):
                continue
            try:
                ls = _sin_comentarios(
                    io.open(os.path.join(r, f), encoding="utf-8",
                            errors="replace").read()).splitlines()
            except Exception:
                continue
            pend = []
            for l in ls:
                m = ATTR.match(l)
                if m:
                    pend = [a.strip().split()[0]
                            for a in m.group(1).split(",") if a.strip()]
                    continue
                d = DECL.match(l)
                if d:
                    for a in pend:
                        etiq[a].add(d.group(1).split(".")[-1])
                    pend = []
    return etiq


def main(k, n_consultas):
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np

    print("indexando atributos de Mathlib...")
    etiq = indice_atributos()
    simp = etiq["simp"]
    print("  @[simp]: %d lemas · %d atributos distintos" % (len(simp), len(etiq)))

    lemas = [json.loads(l) for l in io.open(LISTA, encoding="utf-8")]
    cortos = {d["corto"] for d in lemas}
    largos = {d["nombre"] for d in lemas}

    # EL FONDO DE CANDIDATOS: solo lo que simp NO conoce.
    cand = [d for d in lemas if d["corto"] not in simp]
    nombres = [d["nombre"] for d in cand]
    print("  candidatos sin @[simp]: %d de %d" % (len(cand), len(lemas)))

    print("\nrecolectando teoremas con sus premisas...")
    casos = recolectar(cortos, largos, 40000)
    # EL ORO: solo las premisas que simp no conoce.
    for c in casos:
        c["premisas"] = [p for p in c["premisas"]
                         if p.split(".")[-1] not in simp]
    casos = [c for c in casos if c["premisas"]]
    print("  %d teoremas con premisas que simp NO conoce" % len(casos))

    random.seed(SEMILLA)
    muestra = random.sample(casos, min(n_consultas, len(casos)))
    oro = [c["premisas"] for c in muestra]
    print("  muestra: %d · k = %d\n" % (len(muestra), k))

    vec = TfidfVectorizer(lowercase=True, token_pattern=r"[A-Za-z]{2,}",
                          max_features=60000, sublinear_tf=True)
    M = vec.fit_transform(_texto(d) for d in cand)
    Q = vec.transform([c["enunciado"] for c in muestra])
    rec = []
    for i in range(0, Q.shape[0], 256):
        sims = (Q[i:i + 256] @ M.T).toarray()
        for fila in sims:
            idx = np.argpartition(-fila, k)[:k]
            rec.append([nombres[j] for j in idx[np.argsort(-fila[idx])]])

    cuenta = collections.Counter(x for c in casos for x in c["premisas"])
    top = [x for x, _ in cuenta.most_common(k)]
    hib = [top[:k // 2] + [x for x in r if x not in top[:k // 2]][:k - k // 2]
           for r in rec]

    def mide(r_):
        tp = fp = fn = toca = 0
        for r, o in zip(r_, oro):
            r, o = set(r), set(o)
            a = r & o
            tp += len(a); fp += len(r - o); fn += len(o - r)
            toca += 1 if a else 0
        return (100.0 * tp / max(1, tp + fn), 100.0 * tp / max(1, tp + fp),
                100.0 * toca / len(oro))

    res = {}
    for nombre, r_ in (("nulo", [top] * len(muestra)), ("lexico", rec),
                       ("HIBRIDO", hib)):
        c_, p_, t_ = mide(r_)
        res[nombre] = {"cobertura": c_, "precision": p_, "toca": t_}
        print("  %-10s cobertura %5.1f %%  ·  precision %5.1f %%  ·  toca %5.1f %%"
              % (nombre, c_, p_, t_))

    print("\n=== POR AREA ===\n")
    porarea = collections.defaultdict(list)
    for i, c in enumerate(muestra):
        porarea[c["area"]].append(i)
    filas = []
    for a, idxs in sorted(porarea.items(), key=lambda x: -len(x[1]))[:10]:
        so = [oro[i] for i in idxs]

        def cob(r_):
            tp = fn = 0
            for r, o in zip(r_, so):
                r, o = set(r), set(o)
                tp += len(r & o); fn += len(o - r)
            return 100.0 * tp / max(1, tp + fn)
        cl = cob([rec[i] for i in idxs])
        cn = cob([top] * len(idxs))
        ch = cob([hib[i] for i in idxs])
        print("  %-18s %4d casos · lexico %5.1f  nulo %5.1f  hibrido %5.1f  %s"
              % (a, len(idxs), cl, cn, ch,
                 "LEXICO GANA" if cl > cn else ""))
        filas.append({"area": a, "casos": len(idxs), "lexico": cl,
                      "nulo": cn, "hibrido": ch})

    json.dump({"k": k, "consultas": len(muestra), "global": res,
               "por_area": filas},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=20)
    ap.add_argument("--consultas", type=int, default=3000)
    a = ap.parse_args()
    sys.exit(main(a.k, a.consultas))
