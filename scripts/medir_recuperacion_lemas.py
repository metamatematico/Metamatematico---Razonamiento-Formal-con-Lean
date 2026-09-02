# -*- coding: utf-8 -*-
"""¿Se pueden encender los lemas correctos? Tres recuperadores contra el nulo.

LA PREGUNTA. La arquitectura propuesta es: una LISTA con los 183 433 hechos de
Mathlib, un GRAFO dormido de 298 nodos, y una consulta que enciende entradas de
la lista y despierta la rama correspondiente del grafo. Todo depende de un
paso: elegir cuales de los 183 433 se encienden.

QUE SE MIDE. Sobre 23 243 pruebas Lean 4 reales de las que se conocen los lemas
que citan (data/banco_lemas.jsonl):

    de los k lemas que se encienden, ¿cuantos cita la prueba de verdad?

CUATRO VARIANTES, y la primera es el liston:

  nulo       los k lemas mas citados de Mathlib, sin mirar la consulta.
             Da cobertura 77,4 % — porque `sq_nonneg` aparece en el 71,9 % de
             las pruebas. Es un modelo nulo MUY fuerte, y ese es el punto: si
             un recuperador no lo bate, no esta recuperando, esta memorizando
             la moda.
  lexico-nl  TF-IDF entre el enunciado en LENGUAJE NATURAL y el texto del lema.
             Es la entrada honesta: el grafo actua ANTES de formalizar.
  lexico-formal  lo mismo pero desde el enunciado LEAN. No esta disponible en
             produccion cuando el grafo actua, asi que va como COTA SUPERIOR:
             dice cuanto se pierde por trabajar sobre lenguaje natural.
  semantico  embeddings multilingues sobre lo mismo que lexico-nl.

METRICAS
  cobertura  de los lemas que hacian falta, cuantos se encendieron
  precision  de los k encendidos, cuantos hacian falta
  toca       en que fraccion de pruebas se enciende al menos uno correcto

AVISO DE ALCANCE: LeanWorkbook es matematica de competicion cargada de
desigualdades. Esto mide recuperacion de lemas EN ESE DOMINIO, no en general.

No gasta API.
"""
import argparse
import collections
import io
import json
import os
import random
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LISTA = "E:/Metamatematico/data/lemas_mathlib.jsonl"
BANCO = "E:/Metamatematico/data/banco_lemas.jsonl"
SALIDA = "E:/Metamatematico/data/recuperacion_lemas.json"
MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
SEMILLA = 20260901


def _texto(d):
    """Como se representa un lema para buscarlo: su nombre y su enunciado.

    El NOMBRE importa tanto como el enunciado: `sq_nonneg` lleva escrito
    «cuadrado» y «no negativo», que es justo lo que casa con la consulta.
    """
    nombre = d["nombre"].replace(".", " ").replace("_", " ")
    return nombre + " . " + d["enunciado"]


def cargar():
    lemas = [json.loads(l) for l in io.open(LISTA, encoding="utf-8")]
    banco = [json.loads(l) for l in io.open(BANCO, encoding="utf-8")]
    return lemas, banco


def evalua(nombre, recuperados, oro, k):
    tp = fp = fn = 0
    toca = 0
    for r, o in zip(recuperados, oro):
        r, o = set(r), set(o)
        a = r & o
        tp += len(a)
        fp += len(r - o)
        fn += len(o - r)
        if a:
            toca += 1
    n = len(oro)
    cob = 100.0 * tp / max(1, tp + fn)
    pre = 100.0 * tp / max(1, tp + fp)
    print("  %-16s cobertura %5.1f %%  ·  precision %5.1f %%  ·  toca %5.1f %%"
          % (nombre, cob, pre, 100.0 * toca / n))
    return {"cobertura": cob, "precision": pre, "toca": 100.0 * toca / n}


def main(k, n_consultas, sin_emb):
    lemas, banco = cargar()
    print("lista: %d hechos  ·  banco: %d pruebas" % (len(lemas), len(banco)))
    random.seed(SEMILLA)
    muestra = random.sample(banco, min(n_consultas, len(banco)))
    oro = [m["lemas"] for m in muestra]
    print("muestra: %d consultas · k = %d\n" % (len(muestra), k))

    nombres = [d["nombre"] for d in lemas]
    res = {}

    # ── el liston ──────────────────────────────────────────────────────────
    cuenta = collections.Counter(x for m in banco for x in m["lemas"])
    top = [x for x, _ in cuenta.most_common(k)]
    res["nulo"] = evalua("nulo", [top] * len(muestra), oro, k)

    # ── lexico ─────────────────────────────────────────────────────────────
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
    t0 = time.time()
    vec = TfidfVectorizer(lowercase=True, token_pattern=r"[A-Za-z]{2,}",
                          max_features=60000, sublinear_tf=True)
    M = vec.fit_transform(_texto(d) for d in lemas)
    print("\n  tfidf: %d x %d en %.0f s" % (M.shape[0], M.shape[1],
                                            time.time() - t0))

    def recupera_tfidf(consultas):
        Q = vec.transform(consultas)
        fuera = []
        for i in range(0, Q.shape[0], 256):
            sims = (Q[i:i + 256] @ M.T).toarray()
            for fila in sims:
                idx = np.argpartition(-fila, k)[:k]
                fuera.append([nombres[j] for j in idx[np.argsort(-fila[idx])]])
        return fuera

    res["lexico_nl"] = evalua("lexico-nl",
                              recupera_tfidf([m["nl"] for m in muestra]), oro, k)
    res["lexico_formal"] = evalua("lexico-formal (cota)",
                                  recupera_tfidf([m["enunciado"] for m in muestra]),
                                  oro, k)

    # ── semantico ──────────────────────────────────────────────────────────
    if not sin_emb:
        try:
            from sentence_transformers import SentenceTransformer
            mod = SentenceTransformer(MODELO)
            t0 = time.time()
            E = mod.encode([_texto(d) for d in lemas], normalize_embeddings=True,
                           batch_size=256, show_progress_bar=False)
            print("\n  embeddings de %d lemas en %.0f s" % (len(lemas),
                                                            time.time() - t0))
            Q = mod.encode([m["nl"] for m in muestra], normalize_embeddings=True,
                           batch_size=128, show_progress_bar=False)
            fuera = []
            for i in range(0, len(Q), 128):
                sims = Q[i:i + 128] @ E.T
                for fila in sims:
                    idx = np.argpartition(-fila, k)[:k]
                    fuera.append([nombres[j] for j in idx[np.argsort(-fila[idx])]])
            res["semantico"] = evalua("semantico", fuera, oro, k)
        except Exception as e:
            print("\n  sin semantico: %s: %s" % (type(e).__name__, e))

    print("\n  LECTURA")
    mejor = max((v["cobertura"], n) for n, v in res.items() if n != "nulo")
    print("    el liston del modelo nulo es %.1f %% de cobertura"
          % res["nulo"]["cobertura"])
    print("    mejor recuperador: %s con %.1f %%" % (mejor[1], mejor[0]))
    print("    %s" % ("LO SUPERA" if mejor[0] > res["nulo"]["cobertura"]
                      else "NO LO SUPERA — se esta memorizando la moda"))

    json.dump({"k": k, "consultas": len(muestra), "semilla": SEMILLA,
               "resultados": res},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=20)
    ap.add_argument("--consultas", type=int, default=2000)
    ap.add_argument("--sin-embeddings", action="store_true")
    a = ap.parse_args()
    sys.exit(main(a.k, a.consultas, a.sin_embeddings))
