# -*- coding: utf-8 -*-
"""Donde el emparejador léxico se queda MUDO, ¿la notación da ruta?

DE DONDE SALE ESTA PREGUNTA
---------------------------
`sintaxis_de_consulta_contra_lemas.py` mide el PROMEDIO: los rasgos del árbol
suman +0,8 puntos sobre los n-gramas en las 22 117 consultas. Un promedio no
puede responder a la pregunta que importa, que es otra:

    en las consultas donde la prosa da poco, ¿es la NOTACION la que completa
    el recorrido por el grafo?

Sintaxis y semántica no son dos versiones de lo mismo compitiendo por el mismo
puesto: son dos vistas de la misma consulta, y lo interesante está donde una
calla y la otra habla. Un promedio suma las dos cosas y esconde el reparto.

EL ESTRATO SE DEFINE CON EL SISTEMA REAL, NO CON UN MODELO
----------------------------------------------------------
El corte no lo pone un clasificador entrenado aquí: lo pone
`_match_skills_to_query`, que es el emparejador que corre de verdad en
producción. Una consulta está MUDA cuando ese emparejador no activa NI UNA
skill — el fallo silencioso: el grafo no aporta nada y nadie se entera.

LA DESCOMPOSICION QUE HAY QUE HACER ANTES DE MEDIR NADA
-------------------------------------------------------
De las mudas, hay dos clases y confundirlas inflaría el número:

    muda CON notación    la sintaxis tiene de qué hablar
    muda SIN notación    no hay ni fórmula: ahí no puede ayudar nadie, y
                         contarla como fallo de la sintaxis sería tramposo

CORRECTUD Y COMPLETUD, QUE ES LO QUE SE MIDE DE VERDAD
------------------------------------------------------
    completud   de las consultas mudas, ¿a cuántas les da ruta la sintaxis?
    correctud   de esas rutas, ¿cuántas son la CORRECTA?

Las dos hacen falta. Dar ruta a todas y equivocarse siempre no es completar el
recorrido; acertar una de cada mil tampoco.

EL MODELO NULO. En el estrato mudo, responder siempre el área más frecuente.
Si la sintaxis no lo bate, no está leyendo la notación: está reproduciendo el
prior.

Y HAY QUE EQUILIBRAR, O EL BANCO NO PUEDE DECIDIR. La primera versión de este
script daba +0,0 puntos exactos, que es la firma de un instrumento degenerado:
el train es 93 % `algebra` (18 598 de 20 000) y el clasificador predecía
`algebra` para las 170 consultas mudas, sin excepción. Empatar con el nulo
prediciendo lo mismo que el nulo no es un resultado sobre la sintaxis, es un
resultado sobre el reparto de clases — el mismo fallo que §7.6 del informe.

Por eso se pesa por clase y se informa de ACIERTO EQUILIBRADO (la media de los
aciertos por área), cuyo nulo es 1/nº de áreas y no el 90 % de la mayoritaria.
Es la misma corrección que `reconocedor_area.json` ya llevaba en su columna
`combinado_equilibrado`.

No gasta API.
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import pathlib
import random
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

from nucleo.sintaxis.rasgos import rasgos_de_consulta

TRAIN = pathlib.Path("E:/datadeentrenamientovalidacion_test/all_train.jsonl")
TEST = pathlib.Path("E:/datadeentrenamientovalidacion_test/all_test.jsonl")
SALIDA = RAIZ / "data" / "sintaxis_donde_la_prosa_calla.json"

#: El mismo mapa que `medir_emparejamiento.py`, para que los dos números se
#: puedan poner uno al lado del otro. Sólo las categorías inequívocas.
MAPA = {
    "algebra": "algebra",
    "intermediate_algebra": "algebra",
    "prealgebra": "algebra",
    "geometry": "geometry",
    "number_theory": "number-theory",
    "counting_and_probability": "combinatorics",
    "precalculus": "analysis",
    "gsm8k": None,
}


def cargar(ruta, tope=0):
    fuera = []
    for linea in io.open(ruta, encoding="utf-8"):
        d = json.loads(linea)
        p, c = d.get("problem"), d.get("category")
        if not p or not c:
            continue
        area = MAPA.get(c, "")
        if not area:
            continue
        fuera.append((p, area))
        if tope and len(fuera) >= tope:
            break
    return fuera


def main(a) -> int:
    import numpy as np
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.linear_model import LogisticRegression

    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory

    print("cargando...")
    tr = cargar(a.train, a.train_tope)
    te_todo = cargar(a.test)
    random.seed(a.semilla)
    te = random.sample(te_todo, min(a.muestra, len(te_todo)))
    print("  train %d · test %d (de %d etiquetados)"
          % (len(tr), len(te), len(te_todo)))

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph

    # ── 1 · quién calla ────────────────────────────────────────────────────
    mudas, con_ruta = [], []
    for texto, area in te:
        skills = Nucleo._match_skills_to_query(n, texto, g)
        (con_ruta if skills else mudas).append((texto, area))

    print()
    print("1 · QUIEN CALLA  (el emparejador que corre en produccion)")
    print("   con ruta lexica      %5d  %5.1f %%"
          % (len(con_ruta), 100 * len(con_ruta) / len(te)))
    print("   MUDAS                %5d  %5.1f %%"
          % (len(mudas), 100 * len(mudas) / len(te)))
    if not mudas:
        print("   no hay estrato que medir")
        return 0

    # ── 2 · de las mudas, ¿cuántas tienen notación? ────────────────────────
    rasgos_mudas = [rasgos_de_consulta(t) for t, _ in mudas]
    con_notacion = [i for i, r in enumerate(rasgos_mudas)
                    if not r.get("sin_notacion", 1)]
    print()
    print("2 · DE LAS MUDAS, ¿DE QUE PUEDE HABLAR LA SINTAXIS?")
    print("   mudas CON notacion   %5d  %5.1f %% de las mudas"
          % (len(con_notacion), 100 * len(con_notacion) / len(mudas)))
    print("   mudas SIN notacion   %5d  %5.1f %%   <- aqui no puede ayudar"
          " nadie" % (len(mudas) - len(con_notacion),
                      100 * (len(mudas) - len(con_notacion)) / len(mudas)))

    # ── 3 · ¿acierta el área en el estrato mudo? ───────────────────────────
    print()
    print("3 · CORRECTUD EN EL ESTRATO MUDO — se entrena SOLO con sintaxis")
    vE = DictVectorizer(sparse=True)
    Xtr = vE.fit_transform([rasgos_de_consulta(t) for t, _ in tr])
    ytr = [ar for _, ar in tr]
    mo = LogisticRegression(max_iter=2000, C=1.0,
                            class_weight="balanced").fit(Xtr, ytr)

    frec = collections.Counter(ytr).most_common(1)[0][0]
    areas = sorted(set(ytr))
    print("   nulo crudo        = responder siempre «%s»" % frec)
    print("   nulo equilibrado  = 1/%d = %.1f %% (acertar por azar entre las"
          " areas)" % (len(areas), 100 / len(areas)))

    def evalua(sub, etiqueta):
        if not sub:
            return None
        X = vE.transform([rasgos_de_consulta(t) for t, _ in sub])
        pred = list(mo.predict(X))
        oro = [ar for _, ar in sub]
        acc = sum(1 for p, o in zip(pred, oro) if p == o) / len(sub)
        nulo = sum(1 for o in oro if o == frec) / len(sub)
        # ACIERTO EQUILIBRADO: la media de los aciertos POR AREA. Es lo que
        # impide que predecir siempre la mayoritaria parezca un 90 %.
        por_area = []
        for ar in sorted(set(oro)):
            idx = [i for i, o in enumerate(oro) if o == ar]
            por_area.append(sum(1 for i in idx if pred[i] == ar) / len(idx))
        eq = sum(por_area) / len(por_area)
        nulo_eq = 1.0 / len(set(oro))
        # EL RECALL POR AREA, SIEMPRE. El acierto equilibrado promedia clases
        # que aqui tienen tamanos absurdamente distintos —496 contra 18— y sin
        # ver el reparto un «+13,6 puntos» se lee como si el enrutado
        # funcionara. Con el reparto delante se ve que no: se recuperan 17 de
        # 18 de la minoritaria Y se pierden dos tercios de la mayoritaria.
        detalle = {ar: [sum(1 for i, o in enumerate(oro)
                            if o == ar and pred[i] == ar),
                        sum(1 for o in oro if o == ar)]
                   for ar in sorted(set(oro))}
        print("   %-24s n=%5d  crudo %5.1f %% (nulo %5.1f)  EQUILIBRADO"
              " %5.1f %% (nulo %5.1f)  %+5.1f"
              % (etiqueta, len(sub), 100 * acc, 100 * nulo,
                 100 * eq, 100 * nulo_eq, 100 * (eq - nulo_eq)))
        for ar, (bien, tot) in detalle.items():
            print("        %-16s %4d/%-5d = %5.1f %%"
                  % (ar, bien, tot, 100 * bien / tot))
        return {"n": len(sub), "sintaxis": round(100 * acc, 2),
                "nulo": round(100 * nulo, 2),
                "equilibrado": round(100 * eq, 2),
                "nulo_equilibrado": round(100 * nulo_eq, 2),
                "clases_predichas": len(set(pred)),
                "recall_por_area": detalle,
                "ventaja": round(100 * (eq - nulo_eq), 2)}

    fuera = {}
    fuera["mudas"] = evalua(mudas, "todas las mudas")
    fuera["mudas_con_notacion"] = evalua(
        [mudas[i] for i in con_notacion], "mudas CON notacion")
    fuera["mudas_sin_notacion"] = evalua(
        [mudas[i] for i in range(len(mudas)) if i not in set(con_notacion)],
        "mudas SIN notacion")
    fuera["con_ruta"] = evalua(con_ruta, "las que SI tenian ruta")

    # ── 4 · la lectura ─────────────────────────────────────────────────────
    print()
    print("4 · LA LECTURA")
    m = fuera["mudas_con_notacion"]
    if m and m["clases_predichas"] == 1:
        print("   INSTRUMENTO DEGENERADO: el clasificador predice UNA sola")
        print("   area para las %d consultas. Este banco no puede decidir"
              " nada" % m["n"])
        print("   sobre la sintaxis; el numero que da es el reparto de"
              " clases.")
    elif m and m["ventaja"] > 0:
        rec = m["recall_por_area"]
        peor = min(rec.items(), key=lambda kv: kv[1][0] / max(1, kv[1][1]))
        mejor = max(rec.items(), key=lambda kv: kv[1][0] / max(1, kv[1][1]))
        print("   En las %d consultas donde el grafo se queda mudo Y hay"
              " notacion," % m["n"])
        print("   la sintaxis da %.1f %% equilibrado contra %.1f %% del azar:"
              " %+.1f puntos." % (m["equilibrado"], m["nulo_equilibrado"],
                                  m["ventaja"]))
        print()
        print("   PERO MIRA EL REPARTO ANTES DE CREERTELO:")
        print("      recupera %d de %d de «%s», que el lexico perdia ENTERAS"
              % (mejor[1][0], mejor[1][1], mejor[0]))
        print("      y manda %d de %d de «%s» al area equivocada"
              % (peor[1][1] - peor[1][0], peor[1][1], peor[0]))
        print()
        print("   LECTURA: la senal es REAL —la notacion distingue algo que la"
              " prosa no—,")
        print("   pero este punto de operacion no sirve para enrutar solo. La"
              " sintaxis vale")
        print("   como SEGUNDA OPINION donde el lexico calla, no como"
              " sustituto suyo.")
    elif m:
        print("   La sintaxis NO bate al azar en el estrato mudo (%+.1f"
              " puntos)." % m["ventaja"])
        print("   Donde la prosa calla, la notacion tampoco dice el area.")

    pathlib.Path(a.salida).write_text(json.dumps({
        "test": len(te), "train": len(tr), "semilla": a.semilla,
        "mudas": len(mudas), "con_ruta": len(con_ruta),
        "mudas_con_notacion": len(con_notacion),
        "area_mas_frecuente": frec,
        "resultados": fuera,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print()
    print("escrito -> %s" % a.salida)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train", default=str(TRAIN))
    ap.add_argument("--test", default=str(TEST))
    ap.add_argument("--train-tope", type=int, default=20000)
    ap.add_argument("--muestra", type=int, default=3000)
    ap.add_argument("--semilla", type=int, default=20260901)
    ap.add_argument("--salida", default=str(SALIDA))
    raise SystemExit(main(ap.parse_args()))
