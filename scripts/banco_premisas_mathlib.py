# -*- coding: utf-8 -*-
"""¿Falla la recuperación de lemas SIEMPRE, o sólo en desigualdades?

LA PREGUNTA. Sobre LeanWorkbook —matematica de competicion— la recuperacion por
contenido saco 0,6 % de cobertura frente al 77 % de ofrecer siempre los 20
lemas mas citados. La causa quedo clara mirando los casos: `sq_nonneg` no
aparece en el enunciado ni tiene por que; es una HERRAMIENTA que ese tipo de
problema necesita, no un concepto del que hable. No hay parecido que encontrar.

Pero eso puede ser propio de las desigualdades. En algebra abstracta o
topologia los lemas citados deberian depender del enunciado —`Subgroup.card_dvd`
para un problema de subgrupos— y ahi la recuperacion por contenido si tendria
de que agarrarse.

ProofNet no sirve para decidirlo: trae la prueba en lenguaje natural, no en
Lean, asi que no hay lemas citados que extraer. Mathlib SI: 183 433 teoremas
con su prueba, repartidos por TODAS las areas.

QUE SE MIDE. Para cada teorema: consulta = su enunciado Lean; oro = los lemas
que su prueba cita. Es seleccion de premisas, que es justo lo que alimentaria
un `simp [...]` o un `nlinarith [...]`.

DOS CAUTELAS QUE HACEN LA MEDIDA HONESTA:

  · NO SE CITA A SI MISMO. Un teorema no puede recuperarse como premisa de su
    propia prueba.
  · NO SE MIRA AL FUTURO. Solo cuentan como premisas los lemas declarados
    ANTES en el orden del recorrido; un lema posterior no existia cuando se
    escribio esta prueba.

Y SE INFORMA POR AREA, que es el punto: si el contenido funciona en algebra
abstracta y falla en desigualdades, la conclusion no es «el metodo no sirve»
sino «el metodo no sirve ahi».

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
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MATH = "E:/Metamatematico/.lake/packages/mathlib/Mathlib"
LISTA = "E:/Metamatematico/data/lemas_mathlib.jsonl"
SALIDA = "E:/Metamatematico/data/premisas_mathlib.json"
SEMILLA = 20260901

DECL = re.compile(r"^(?:@\[[^\]]*\]\s*)?(?:private\s+|protected\s+"
                  r"|noncomputable\s+)*(theorem|lemma)\s+([A-Za-z_][\w.']*)")
IDENT = re.compile(r"\b([A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*)\b")
IGNORAR = {"Tactic", "Util", "Testing", "Deprecated", "Mathport", "Init"}

from scripts.construir_lista_lemas import _sin_comentarios  # noqa: E402
from scripts.construir_banco_lemas import _es_cita  # noqa: E402


def recolectar(cortos, largos, tope):
    """(area, enunciado, premisas citadas) por teorema, en orden de recorrido."""
    casos = []
    vistos = set()          # lo declarado ANTES: no se mira al futuro
    for raiz, _d, fs in os.walk(MATH):
        for f in sorted(fs):
            if not f.endswith(".lean"):
                continue
            rel = os.path.relpath(os.path.join(raiz, f), MATH).replace("\\", "/")
            area = rel.split("/")[0]
            if area in IGNORAR:
                continue
            try:
                txt = _sin_comentarios(
                    io.open(os.path.join(raiz, f), encoding="utf-8",
                            errors="replace").read())
            except Exception:
                continue
            ls = txt.splitlines()
            # los limites de cada declaracion: de una a la siguiente
            marcas = [i for i, l in enumerate(ls) if DECL.match(l)]
            for k, i in enumerate(marcas):
                m = DECL.match(ls[i])
                nombre = m.group(2)
                fin = marcas[k + 1] if k + 1 < len(marcas) else len(ls)
                bloque = "\n".join(ls[i:fin])
                if ":=" not in bloque:
                    vistos.add(nombre)
                    continue
                enunciado, cuerpo = bloque.split(":=", 1)
                enunciado = " ".join(enunciado.split())
                enunciado = re.sub(r"^.*?(?:theorem|lemma)\s+\S+\s*", "",
                                   enunciado)
                premisas = set()
                for mm in IDENT.finditer(cuerpo):
                    x = mm.group(1)
                    corto = x.split(".")[-1]
                    if corto == nombre or x == nombre:
                        continue                    # no se cita a si mismo
                    if not _es_cita(x, cortos, largos):
                        continue
                    if corto not in vistos and x not in vistos:
                        continue                    # aun no existia
                    premisas.add(x)
                vistos.add(nombre)
                if premisas and len(enunciado) > 10:
                    casos.append({"nombre": nombre, "area": area,
                                  "enunciado": enunciado[:400],
                                  "premisas": sorted(premisas)})
            if len(casos) > tope:
                return casos
    return casos


def main(k, n_consultas):
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
    from scripts.medir_recuperacion_lemas import _texto

    print("cargando la lista...")
    lemas = [json.loads(l) for l in io.open(LISTA, encoding="utf-8")]
    cortos = {d["corto"] for d in lemas}
    largos = {d["nombre"] for d in lemas}
    nombres = [d["nombre"] for d in lemas]
    print("  %d hechos" % len(lemas))

    t0 = time.time()
    print("recolectando teoremas con sus premisas...")
    casos = recolectar(cortos, largos, 200000)
    print("  %d teoremas con premisas, en %.0f s" % (len(casos), time.time() - t0))
    if not casos:
        print("  ATENCION: ninguno — el recolector esta roto")
        return 1
    print("  premisas por teorema: %.1f de media"
          % (sum(len(c["premisas"]) for c in casos) / len(casos)))
    print("  por area:", dict(collections.Counter(
        c["area"] for c in casos).most_common(8)))

    random.seed(SEMILLA)
    muestra = random.sample(casos, min(n_consultas, len(casos)))
    oro = [c["premisas"] for c in muestra]
    print("\nmuestra: %d consultas · k = %d\n" % (len(muestra), k))

    vec = TfidfVectorizer(lowercase=True, token_pattern=r"[A-Za-z]{2,}",
                          max_features=60000, sublinear_tf=True)
    M = vec.fit_transform(_texto(d) for d in lemas)
    Q = vec.transform([c["enunciado"] for c in muestra])
    recuperado = []
    for i in range(0, Q.shape[0], 256):
        sims = (Q[i:i + 256] @ M.T).toarray()
        for fila in sims:
            idx = np.argpartition(-fila, k)[:k]
            recuperado.append([nombres[j] for j in idx[np.argsort(-fila[idx])]])

    cuenta = collections.Counter(x for c in casos for x in c["premisas"])
    top = [x for x, _ in cuenta.most_common(k)]

    def mide(rec):
        tp = fp = fn = toca = 0
        for r, o in zip(rec, oro):
            r, o = set(r), set(o)
            a = r & o
            tp += len(a); fp += len(r - o); fn += len(o - r)
            toca += 1 if a else 0
        return (100.0 * tp / max(1, tp + fn), 100.0 * tp / max(1, tp + fp),
                100.0 * toca / len(oro))

    # HIBRIDO: mitad frecuencia, mitad contenido. Es la comparacion que
    # decide, porque los dos aciertan cosas DISTINTAS — el nulo pone las
    # herramientas universales, el lexico las especificas del enunciado.
    hibrido = [top[:k // 2] + [x for x in r if x not in top[:k // 2]][:k - k // 2]
               for r in recuperado]

    cn, pn, tn = mide([top] * len(muestra))
    cl, pl, tl = mide(recuperado)
    print("  %-12s cobertura %5.1f %%  ·  precision %5.1f %%  ·  toca %5.1f %%"
          % ("nulo", cn, pn, tn))
    print("  %-12s cobertura %5.1f %%  ·  precision %5.1f %%  ·  toca %5.1f %%"
          % ("lexico", cl, pl, tl))
    ch, ph, th = mide(hibrido)
    print("  %-12s cobertura %5.1f %%  ·  precision %5.1f %%  ·  toca %5.1f %%"
          % ("HIBRIDO", ch, ph, th))
    import random as _r
    _r.seed(SEMILLA)
    azar = [[nombres[j] for j in _r.sample(range(len(nombres)), k)]
            for _ in muestra]
    ca, _pa, _ta = mide(azar)
    print("  %-12s cobertura %5.2f %%   (para saber que es la nada)" % ("azar", ca))

    print("\n=== POR AREA — el punto de todo esto ===\n")
    porarea = collections.defaultdict(list)
    for idx, c in enumerate(muestra):
        porarea[c["area"]].append(idx)
    filas = []
    for a, idxs in sorted(porarea.items(), key=lambda x: -len(x[1]))[:12]:
        sub_oro = [oro[i] for i in idxs]
        sub_rec = [recuperado[i] for i in idxs]
        cob_l = mide2(sub_rec, sub_oro)
        cob_n = mide2([top] * len(idxs), sub_oro)
        print("  %-20s %4d casos · lexico %5.1f %%  ·  nulo %5.1f %%  %s"
              % (a, len(idxs), cob_l, cob_n,
                 "GANA" if cob_l > cob_n else ""))
        filas.append({"area": a, "casos": len(idxs), "lexico": cob_l,
                      "nulo": cob_n})

    json.dump({"k": k, "consultas": len(muestra),
               "global": {"lexico": cl, "nulo": cn},
               "por_area": filas},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


def mide2(rec, oro):
    tp = fn = 0
    for r, o in zip(rec, oro):
        r, o = set(r), set(o)
        tp += len(r & o)
        fn += len(o - r)
    return 100.0 * tp / max(1, tp + fn)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=20)
    ap.add_argument("--consultas", type=int, default=3000)
    a = ap.parse_args()
    sys.exit(main(a.k, a.consultas))
