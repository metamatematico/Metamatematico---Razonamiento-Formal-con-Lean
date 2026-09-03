# -*- coding: utf-8 -*-
"""Localizar primero, elegir después. Y cuánto vale cada paso.

EL ORDEN IMPORTA Y YO LO MEDI MAL. La recuperacion de lemas se midio buscando
sobre los 183 433 hechos DE GOLPE, sin localizar antes, y fallaba: 0,6 % de
cobertura frente al 77 % de ofrecer siempre los mas citados.

Pero la arquitectura correcta es en dos etapas:

    consulta -> LOCALIZAR el area/sub-area -> ELEGIR enunciados DE ESA AREA

La primera etapa poda el espacio de busqueda antes de buscar. Un area tipica
tiene unos cientos de hechos, no ciento ochenta mil, y ahi la similitud si
puede discriminar. Medirlo todo junto confundia el fallo de la busqueda con la
ausencia de poda.

QUE SE MIDE, sobre teoremas reales de Mathlib con sus premisas conocidas:

    sin podar     buscar en los 183 433, como se hizo antes
    ORACULO       podar al area CORRECTA y buscar ahi. Es el techo: dice
                  cuanto vale la poda si la localizacion fuera perfecta
    real          podar al area que el sistema elige de verdad
    nulo          los mas citados, sin mirar nada

    ORACULO - real  =  lo que cuesta que la localizacion falle
    ORACULO - sin podar  =  lo que vale podar

Sin esa separacion no se puede saber si conviene mejorar la busqueda o el
emparejamiento — que son trabajos distintos.

No gasta API.
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

LISTA = "E:/Metamatematico/data/lemas_mathlib.jsonl"
SALIDA = "E:/Metamatematico/data/dos_etapas.json"
SEMILLA = 20260901


def main(k, n_consultas, subarea):
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
    from scripts.medir_recuperacion_lemas import _texto
    from scripts.banco_premisas_mathlib import recolectar
    from scripts.premisas_sin_simp import indice_atributos

    print("indexando atributos...")
    simp = indice_atributos()["simp"]
    lemas = [json.loads(l) for l in io.open(LISTA, encoding="utf-8")]
    cortos = {d["corto"] for d in lemas}
    largos = {d["nombre"] for d in lemas}

    # el catalogo: fuera los @[simp], que simp ya conoce
    catalogo = [d for d in lemas if d["corto"] not in simp]
    nombres = [d["nombre"] for d in catalogo]
    # LA UNIDAD DE PODA: area de primer nivel o SUB-AREA.
    #
    # Con el area de primer nivel el oraculo solo sumaba +0,6 puntos, y la
    # razon NO era que las premisas se dispersaran —el 77,1 % esta en la misma
    # area que el teorema—: es que el area es DEMASIADO GRANDE. `Algebra` tiene
    # 27 000 hechos, asi que podar de 140 000 a 27 000 divide por cinco y la
    # similitud sigue sin discriminar.
    #
    # La sub-area es dos ordenes de magnitud menor —`Algebra.Order` 5 140,
    # `Data.Nat` 1 916— y ademas es exactamente lo que son los 125 nodos
    # generados. Con `--subarea` se mide si la unidad fina si paga.
    if subarea:
        area_de_idx = [d["concepto"] for d in catalogo]
    else:
        area_de_idx = [d["concepto"].split(".")[0] for d in catalogo]
    print("  catalogo: %d hechos · %d areas"
          % (len(catalogo), len(set(area_de_idx))))

    print("recolectando teoremas con premisas...")
    casos = recolectar(cortos, largos, 60000)
    for c in casos:
        c["premisas"] = [p for p in c["premisas"]
                         if p.split(".")[-1] not in simp]
    casos = [c for c in casos if c["premisas"]]
    random.seed(SEMILLA)
    muestra = random.sample(casos, min(n_consultas, len(casos)))
    oro = [c["premisas"] for c in muestra]
    print("  %d casos · muestra %d · k=%d\n" % (len(casos), len(muestra), k))

    vec = TfidfVectorizer(lowercase=True, token_pattern=r"[A-Za-z]{2,}",
                          max_features=60000, sublinear_tf=True)
    M = vec.fit_transform(_texto(d) for d in catalogo)
    Q = vec.transform([c["enunciado"] for c in muestra])
    A = np.array(area_de_idx)

    def top(fila, mascara=None):
        f = fila if mascara is None else np.where(mascara, fila, -1.0)
        idx = np.argpartition(-f, min(k, len(f) - 1))[:k]
        return [nombres[j] for j in idx[np.argsort(-f[idx])] if f[j] > 0]

    #: el area de cada caso, y la que el sistema elegiria
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph
    #: nodo del grafo -> area de Mathlib, para traducir lo que el grafo diga
    area_de_nodo = {}
    for s in g.skills:
        m = (s.metadata or {}).get("modulo")
        if m:
            p = m.replace("Mathlib.", "", 1).split(".")
            area_de_nodo[s.id] = ".".join(p[:2]) if subarea else p[0]

    sin_podar, oraculo, real = [], [], []
    aciertos_loc = 0
    for i, c in enumerate(muestra):
        fila = (Q[i] @ M.T).toarray()[0]
        sin_podar.append(top(fila))
        objetivo = c.get("concepto") if subarea else c["area"]
        oraculo.append(top(fila, A == objetivo))
        # el area que el sistema elige, del enunciado
        skills = Nucleo._match_skills_to_query(n, c["enunciado"], g)
        areas = [area_de_nodo[s] for s in skills if s in area_de_nodo]
        elegida = areas[0] if areas else None
        if elegida == objetivo:
            aciertos_loc += 1
        real.append(top(fila, A == elegida) if elegida else top(fila))

    cuenta = collections.Counter(x for c in casos for x in c["premisas"])
    nulo = [[x for x, _ in cuenta.most_common(k)]] * len(muestra)

    def mide(rec):
        tp = fp = fn = toca = 0
        for r, o in zip(rec, oro):
            r, o = set(r), set(o)
            a = r & o
            tp += len(a)
            fp += len(r - o)
            fn += len(o - r)
            toca += 1 if a else 0
        return (100.0 * tp / max(1, tp + fn), 100.0 * tp / max(1, tp + fp),
                100.0 * toca / len(oro))

    res = {}
    print("  %-12s %10s %11s %8s" % ("", "cobertura", "precision", "toca"))
    for nombre, r in (("nulo", nulo), ("sin podar", sin_podar),
                      ("real", real), ("ORACULO", oraculo)):
        cob, pre, toc = mide(r)
        res[nombre] = {"cobertura": cob, "precision": pre, "toca": toc}
        print("  %-12s %9.1f %% %10.1f %% %7.1f %%" % (nombre, cob, pre, toc))

    print("\n  LECTURA")
    print("    localizacion correcta        : %.1f %% de los casos"
          % (100.0 * aciertos_loc / len(muestra)))
    print("    lo que VALE podar            : %+.1f puntos de cobertura"
          % (res["ORACULO"]["cobertura"] - res["sin podar"]["cobertura"]))
    print("    lo que CUESTA localizar mal  : %+.1f puntos"
          % (res["real"]["cobertura"] - res["ORACULO"]["cobertura"]))
    mejor = max(res, key=lambda x: res[x]["cobertura"])
    print("    mejor: %s (%.1f %%) · el nulo da %.1f %%"
          % (mejor, res[mejor]["cobertura"], res["nulo"]["cobertura"]))

    json.dump({"k": k, "consultas": len(muestra),
               "localizacion_correcta": 100.0 * aciertos_loc / len(muestra),
               "resultados": res},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=20)
    ap.add_argument("--consultas", type=int, default=2000)
    ap.add_argument("--subarea", action="store_true",
                    help="poda por sub-area (Algebra.Order) en vez de area")
    a = ap.parse_args()
    print("unidad de poda: %s\n" % ("SUB-AREA" if a.subarea else "área"))
    sys.exit(main(a.k, a.consultas, a.subarea))
