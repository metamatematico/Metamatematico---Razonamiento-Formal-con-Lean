# -*- coding: utf-8 -*-
"""¿Sirve el ORDEN del grafo para ordenar premisas? NO. Medido.

LA HIPOTESIS, Y POR QUE ERA RAZONABLE
-------------------------------------
El funtor del grafo al DAG de imports de Mathlib se confirma en el 78,1 % de
los 73 pares curados medibles, contra un nulo del 40,1 % (`data/funtor_
mathlib.json`). Es el unico resultado categorico del sistema que gana a su
nulo por un factor cercano a dos.

Si el orden del grafo coincide con el orden real de los imports, entonces sabe
QUE VIENE ANTES QUE QUE. Y eso es exactamente lo que hace falta para elegir
premisas: las de un enunciado sobre A viven en A o POR DEBAJO de A, nunca
encima. Convertir el unico resultado teorico que se sostiene en la mejora
practica que el puente LLM-Lean necesita.

LA CONTRAPRUEBA QUE YA HABIA, Y QUE DEBIO PESAR MAS
---------------------------------------------------
`scripts/dos_etapas_localizar_y_elegir.py` ya midio podar por AREA antes de
buscar, y su ORACULO —localizacion PERFECTA, el techo de esa familia— da
6,79 % de cobertura contra un nulo de 9,78 %. O sea que la senal topica en
este banco pierde contra «ofrecer los lemas mas citados» hasta en el mejor
caso imaginable.

La diferencia que se probaba aqui era REORDENAR en vez de PODAR: el nulo gana
porque las premisas son de cola pesada —unos pocos lemas se usan en todas
partes— y podar los mata, mientras que un boost los conserva.

EL RESULTADO
------------
No sirve. Sobre 1 500 teoremas reales de Mathlib con sus premisas conocidas,
buscando solo entre los 140 102 candidatos que `simp` NO conoce (k=20):

                          cobertura   precision   toca
    nulo                    11,46 %     1,01 %    16,7 %
    lexico                   6,98 %     0,61 %    10,9 %
    lexico + orden_grafo     6,68 %     0,59 %    10,4 %
    HIBRIDO (lo que corre)  14,08 %     1,24 %    21,5 %
    HIBRIDO + orden_grafo   13,89 %     1,22 %    21,3 %

Empeora las dos ramas. No es un empate del que se pueda decir «con mas ajuste
quiza»: va en la direccion contraria en las tres metricas a la vez.

POR QUE, PROBABLEMENTE. El funtor acierta sobre pares CURADOS de conceptos
—`group-theory` antes que `ring-theory`— y eso es una afirmacion sobre
TEORIAS. La premisa que cierra un objetivo concreto no se elige por teoria: se
elige por forma del enunciado, y ahi la cola pesada del nulo gana. Que el
orden sea correcto no lo hace informativo para esta pregunta.

EL PRIMER INTENTO ESTABA ROTO, Y ASI SE DETECTO
-----------------------------------------------
La primera version comparaba la RUTA COMPLETA del modulo. El grafo apunta a
ficheros hoja (`Mathlib.CategoryTheory.Functor.Basic`), asi que el boost
tocaba 74 de 140 102 candidatos —el 0,05 %— y salieron cifras IDENTICAS a la
base en las tres metricas. Identico a la base no es un resultado: es la firma
de un instrumento que no esta midiendo. Se recorto a 3 segmentos
(`Mathlib.CategoryTheory.Functor`, la subteoria), el boost paso a tener
alcance real, y entonces las cifras se movieron — hacia abajo.

Queda escrito para que nadie vuelva a proponerlo sin medirlo. Lo que el funtor
sostiene es la ESTRUCTURA del grafo; no sostiene, por si solo, ninguna mejora
en la seleccion de premisas.

No gasta API.

    python -m scripts.orden_del_grafo_en_premisas
    python -m scripts.orden_del_grafo_en_premisas --consultas 500
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

SALIDA = "E:/Metamatematico/data/orden_del_grafo_en_premisas.json"
SEMILLA = 20260901

#: Cuanto suma estar en una subteoria que el grafo alcanza. Las similitudes
#: TF-IDF de este banco viven en [0, 1], asi que 0,15 es un empujon grande a
#: proposito: si con esto no mueve nada, con menos tampoco.
BOOST = 0.15

#: Segmentos de la ruta que definen la SUBTEORIA. Ver la nota del instrumento
#: roto en el docstring: con la ruta entera el boost no alcanza nada.
SEGMENTOS = 3


def _sub(mod: str, n: int = SEGMENTOS) -> str:
    return ".".join((mod or "").split(".")[:n])


def main(n_consultas: int, k: int) -> int:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer

    from scripts.premisas_sin_simp import indice_atributos, LISTA
    from scripts.banco_premisas_mathlib import recolectar
    from scripts.texto_de_lema import _texto
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory

    simp = indice_atributos()["simp"]
    lemas = [json.loads(l) for l in io.open(LISTA, encoding="utf-8")]
    cortos = {d["corto"] for d in lemas}
    largos = {d["nombre"] for d in lemas}
    cand = [d for d in lemas if d["corto"] not in simp]
    nombres = [d["nombre"] for d in cand]
    pref = [_sub(d.get("modulo") or "") for d in cand]
    print("candidatos sin @[simp]: %d" % len(cand))

    casos = recolectar(cortos, largos, 40000)
    for c in casos:
        c["premisas"] = [p for p in c["premisas"]
                         if p.split(".")[-1] not in simp]
    casos = [c for c in casos if c["premisas"]]
    random.seed(SEMILLA)
    muestra = random.sample(casos, min(n_consultas, len(casos)))
    oro = [c["premisas"] for c in muestra]
    print("muestra %d · k=%d" % (len(muestra), k))

    vec = TfidfVectorizer(lowercase=True, token_pattern=r"[A-Za-z]{2,}",
                          max_features=60000, sublinear_tf=True)
    M = vec.fit_transform(_texto(d) for d in cand)
    Q = vec.transform([c["enunciado"] for c in muestra])

    cuenta = collections.Counter(x for c in casos for x in c["premisas"])
    top = [x for x, _ in cuenta.most_common(k)]

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph
    from nucleo.rutas import dato
    mods_por_skill = json.load(
        io.open(dato("mathlib_modulos.json"), encoding="utf-8"))["por_skill"]

    def subteorias(consulta: str) -> set:
        """Las subteorias que el ORDEN del grafo alcanza desde la consulta.

        Se incluyen las dependencias porque es ahi donde vive la hipotesis:
        el funtor dice que «A depende de B» en el grafo se corresponde con «B
        se importa antes que A» en Mathlib, luego las premisas estan en A o
        por debajo.
        """
        m = Nucleo._match_skills_to_query(n, consulta, g)
        alcance = list(m[:4])
        for s in m[:3]:
            for d in g.dependencies(s):
                if d not in alcance:
                    alcance.append(d)
        return {_sub(x) for s in alcance for x in (mods_por_skill.get(s) or [])}

    def recupera(con_boost: bool) -> list:
        out = []
        for i in range(0, Q.shape[0], 256):
            sims = (Q[i:i + 256] @ M.T).toarray()
            for j, fila in enumerate(sims):
                if con_boost:
                    subs = subteorias(muestra[i + j]["enunciado"])
                    if subs:
                        extra = np.fromiter(
                            (BOOST if p and p in subs else 0.0 for p in pref),
                            dtype=fila.dtype, count=len(pref))
                        fila = fila + extra
                idx = np.argpartition(-fila, k)[:k]
                out.append([nombres[t] for t in idx[np.argsort(-fila[idx])]])
        return out

    def mide(r_):
        tp = fp = fn = toca = 0
        for r, o in zip(r_, oro):
            r, o = set(r), set(o)
            a = r & o
            tp += len(a); fp += len(r - o); fn += len(o - r)
            toca += 1 if a else 0
        return (100.0 * tp / max(1, tp + fn), 100.0 * tp / max(1, tp + fp),
                100.0 * toca / len(oro))

    rec = recupera(False)
    rec_g = recupera(True)
    mitad = k // 2
    hib = [top[:mitad] + [x for x in r if x not in top[:mitad]][:k - mitad]
           for r in rec]
    hib_g = [top[:mitad] + [x for x in r if x not in top[:mitad]][:k - mitad]
             for r in rec_g]

    print()
    res = {}
    for nombre, r_ in (("nulo", [top] * len(muestra)),
                       ("lexico", rec),
                       ("lexico+orden_grafo", rec_g),
                       ("HIBRIDO", hib),
                       ("HIBRIDO+orden_grafo", hib_g)):
        c_, p_, t_ = mide(r_)
        res[nombre] = {"cobertura": c_, "precision": p_, "toca": t_}
        print("  %-22s cobertura %5.2f %%  precision %5.2f %%  toca %5.1f %%"
              % (nombre, c_, p_, t_))

    d_cob = res["HIBRIDO+orden_grafo"]["cobertura"] - res["HIBRIDO"]["cobertura"]
    print("\n  el orden del grafo mueve la cobertura del HIBRIDO en %+.2f puntos"
          % d_cob)
    print("  VEREDICTO: %s" % ("no aporta" if d_cob <= 0 else "REVISAR: ha subido"))

    json.dump({"consultas": len(muestra), "k": k, "semilla": SEMILLA,
               "boost": BOOST, "segmentos": SEGMENTOS, "resultados": res},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--consultas", type=int, default=1500)
    ap.add_argument("-k", type=int, default=20)
    a = ap.parse_args()
    raise SystemExit(main(a.consultas, a.k))
