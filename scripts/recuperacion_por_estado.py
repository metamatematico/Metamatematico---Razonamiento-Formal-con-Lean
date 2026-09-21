# -*- coding: utf-8 -*-
"""La puerta del paso 4 para los vecinos de estado: ¿baten al rankeador?

DOS MEDIDAS, Y LA QUE DECIDE ES LA SEGUNDA
------------------------------------------
    1 · la de la propuesta (§9), sin Lean. La MISMA partición que
        `ranker_en_la_cascada.py` —semilla 0, 20 % estratificado—, los mismos
        casos cuya táctica está en la cascada, el mismo repertorio. Se compara
        en qué posición queda el NOMBRE que cierra: rankeador contra vecinos.
        Mide a los vecinos en el terreno del rankeador, que es ordenar nombres.

    2 · la que importa, con Lean y sin API. Lo que los vecinos aportan no es el
        nombre sino los ARGUMENTOS —`nlinarith [sq_nonneg (a - b), …]`—, y eso
        sólo lo juzga Lean. Sobre estados RAÍZ de prueba (el enunciado recién
        plantado, cuyo objetivo coincide con el `state_before`), cada rama
        tiene TRES intentos en la sesión:
            R   las 3 primeras del rankeador, desnudas
            V   las 3 primeras tácticas completas de los vecinos
            F   la fusión: V1, R1, V2
        y un cierre exige `proofStatus` «Completed».

LA REGLA, ESCRITA ANTES DE CORRER
---------------------------------
    `tacticas_por_vecinos` entra si en la medida 2 V cierra MÁS que R, con el
    McNemar exacto de los discordantes a la vista. La medida 1 se informa y no
    decide: un kNN no tiene por qué ordenar nombres mejor que un clasificador
    entrenado para eso, y no es lo que se le pide.

LA FUGA POSIBLE, Y CÓMO SE MIRA
-------------------------------
LeanWorkbook tiene problemas casi repetidos con ids distintos. Si el vecino más
cercano de un estado de prueba es ESE MISMO estado (normalizado) en el
entrenamiento, copiar su táctica es recordar, no generalizar. Se informa el
resultado con y sin esos casos. El índice se construye sólo con la partición
de entrenamiento.

No gasta API. La medida 2 gasta ~15-25 min de Lean.

    python -m scripts.recuperacion_por_estado --n 150
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import math
import os
import random
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

ORIGEN = r"E:\MetamatematicoDataSet\LeanWorkbook"
SALIDA = os.path.join(RAIZ, "data", "recuperacion_por_estado.json")
SEMILLA, PRUEBA, MIN_CLASE = 0, 0.2, 40
#: la cabecera con la que LeanWorkbook escribió sus enunciados
CABECERA = ("import Mathlib\nimport Aesop\nset_option maxHeartbeats 400000\n"
            "open BigOperators Real Nat Topology Rat")
_CAB = re.compile(r"^([a-zA-Z_][\w']*)")


def _cabeza(t):
    m = _CAB.match((t or "").strip())
    return m.group(1) if m else None


def cargar():
    """Las filas que CIERRAN, con el MISMO filtro y orden que ranker_en_la_cascada."""
    from datasets import load_from_disk
    ds = load_from_disk(ORIGEN)
    ds = ds[list(ds.keys())[0]] if hasattr(ds, "keys") else ds
    filas = []
    for f in ds:
        e = (f.get("state_before") or "").strip()
        cab = _cabeza(f.get("tactic") or "")
        if e and cab and (f.get("state_after") or "").strip() == "no goals":
            filas.append({"estado": e, "cabeza": cab, "tactica": (f.get("tactic") or "").strip(),
                          "id": f.get("id"), "enunciado": f.get("formal_statement") or ""})
    cuenta = collections.Counter(f["cabeza"] for f in filas)
    return [f for f in filas if cuenta[f["cabeza"]] >= MIN_CLASE]


def posicion(orden, verdadera):
    for i, n in enumerate(orden, 1):
        if n == verdadera:
            return i
    return len(orden) + 1


def mcnemar(b, c):
    """p exacto a dos colas sobre los discordantes."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def medida_1(tr, te, ranker, indice, cascada):
    en = set(cascada)
    casos = [f for f in te if f["cabeza"] in en]
    frec = collections.Counter(f["cabeza"] for f in tr if f["cabeza"] in en)
    resto = [t for t, _ in frec.most_common()] + [t for t in cascada if t not in frec]
    from nucleo.lean.solver_cascade import SOLVER_CASCADE
    pr, pv, pf = [], [], []
    for f in casos:
        orden_r = [s for s, _ in ranker.rank(f["estado"], SOLVER_CASCADE)]
        cabs = []
        for t in indice.proponer(f["estado"], k=40, vecinos=80):
            c = _cabeza(t)
            if c in en and c not in cabs:
                cabs.append(c)
        orden_v = cabs + [t for t in resto if t not in cabs]
        # fusión por rango recíproco de los dos órdenes
        pts = collections.defaultdict(float)
        for o in (orden_r, orden_v):
            for i, n in enumerate(o):
                pts[n] += 1.0 / (60 + i)
        orden_f = sorted(pts, key=lambda n: -pts[n])
        pr.append(posicion(orden_r, f["cabeza"]))
        pv.append(posicion(orden_v, f["cabeza"]))
        pf.append(posicion(orden_f, f["cabeza"]))
    m = lambda p: round(sum(p) / len(p), 3)
    return {"n": len(casos), "rankeador": m(pr), "vecinos": m(pv), "fusion": m(pf)}


def medida_2(te, ranker, indice, n, tope):
    from nucleo.graph.estados import normalizar
    from nucleo.lean.sesion import SesionLean
    from nucleo.lean.solver_cascade import SOLVER_CASCADE, _ADMITEN_CON_SORRY
    from nucleo.lazo.filtros import revisar

    rnd = random.Random(SEMILLA)
    pool = [f for f in te if f["enunciado"]]
    rnd.shuffle(pool)
    repertorio = [s for s in SOLVER_CASCADE if s[0] not in _ADMITEN_CON_SORRY]

    def abrir():
        s = SesionLean().abrir()
        return s, s.comando(CABECERA, env=None).env

    s, env = abrir()
    filas, no_raiz = [], 0
    try:
        for f in pool:
            if len(filas) >= n:
                break
            r = s.comando(f["enunciado"], env=env)
            if r.clase == "error" or len(r.sorries) != 1:
                no_raiz += 1
                continue
            raiz = r.sorries[0]
            if normalizar(raiz.get("goal") or "") != normalizar(f["estado"]):
                no_raiz += 1
                continue
            ps = raiz["proofState"]
            R = [t for t, _ in ranker.rank(f["estado"], repertorio)][:3]
            V = [t for t in indice.proponer(f["estado"], k=8) if revisar(t) is None][:3]
            Fz = [x for x in (V[:1] + R[:1] + V[1:2]) if x][:3]
            memo, res = {}, {}
            for rama, cands in (("R", R), ("V", V), ("F", Fz)):
                ok = None
                for c in cands:
                    if c not in memo:
                        x = s.tactica(c, ps, tope=tope)
                        if "TIMEOUT" in (x.error or ""):
                            s.cerrar()
                            s, env = abrir()
                            memo[c] = False
                            # el proofState ya no vale: se replanta
                            ps = s.comando(f["enunciado"], env=env).sorries[0]["proofState"]
                        else:
                            memo[c] = (x.clase == "cierra")
                    if memo[c]:
                        ok = c
                        break
                res[rama] = ok
            filas.append({"id": f["id"], "R": res["R"], "V": res["V"], "F": res["F"],
                          "R_cands": R, "V_cands": V,
                          "tactica_real": f["tactica"][:200]})
            print("  %-26s R %-5s V %-5s F %-5s" % (
                (f["id"] or "")[:26], "si" if res["R"] else "·",
                "si" if res["V"] else "·", "si" if res["F"] else "·"))
    finally:
        s.cerrar()
    return filas, no_raiz


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--tope", type=int, default=20)
    args = ap.parse_args()
    from sklearn.model_selection import train_test_split
    from nucleo.graph.estados import normalizar
    from nucleo.lean.solver_cascade import SOLVER_CASCADE, TacticRanker
    from nucleo.lazo.vecinos import IndiceDeVecinos

    print("cargando LeanWorkbook...")
    filas = cargar()
    idx = list(range(len(filas)))
    y = [f["cabeza"] for f in filas]
    itr, ite = train_test_split(idx, test_size=PRUEBA, random_state=SEMILLA, stratify=y)
    tr, te = [filas[i] for i in itr], [filas[i] for i in ite]
    print("  cierran %d · entrenamiento %d · prueba %d" % (len(filas), len(tr), len(te)))

    indice = IndiceDeVecinos().construir([f["estado"] for f in tr], [f["tactica"] for f in tr])
    ranker = TacticRanker()
    if not ranker.disponible:
        print("no hay rankeador")
        return 1

    # la fuga: estados de prueba que ESTÁN, normalizados, en el entrenamiento
    en_tr = {normalizar(f["estado"]) for f in tr}
    dup = {f["id"] for f in te if normalizar(f["estado"]) in en_tr}

    print("\n=== MEDIDA 1 · posición del nombre que cierra (sin Lean) ===")
    m1 = medida_1(tr, te, ranker, indice, [s for s, _ in SOLVER_CASCADE])
    print("  n %d · rankeador %.2f · vecinos %.2f · fusión %.2f"
          % (m1["n"], m1["rankeador"], m1["vecinos"], m1["fusion"]))

    print("\n=== MEDIDA 2 · cierres de verdad, 3 intentos por rama ===")
    f2, no_raiz = medida_2(te, ranker, indice, args.n, args.tope)
    for f in f2:
        f["duplicado"] = f["id"] in dup

    def cuenta(fs):
        r = sum(1 for f in fs if f["R"])
        v = sum(1 for f in fs if f["V"])
        fz = sum(1 for f in fs if f["F"])
        b = sum(1 for f in fs if f["V"] and not f["R"])
        c = sum(1 for f in fs if f["R"] and not f["V"])
        return {"n": len(fs), "R": r, "V": v, "F": fz, "solo_V": b, "solo_R": c,
                "p": round(mcnemar(b, c), 4)}

    todo = cuenta(f2)
    sin_dup = cuenta([f for f in f2 if not f["duplicado"]])
    for nombre, c in (("todos", todo), ("sin duplicados", sin_dup)):
        print("  %-15s n %3d · R %3d · V %3d · F %3d · sólo V %d · sólo R %d · p %.4f"
              % (nombre, c["n"], c["R"], c["V"], c["F"], c["solo_V"], c["solo_R"], c["p"]))
    print("  descartados por no ser raíz o no elaborar: %d" % no_raiz)

    pasa = todo["V"] > todo["R"]
    print("\n=== LA PUERTA ===\n")
    print("  %s: V cierra %d y R %d en los mismos %d estados (p = %.4f)."
          % ("PASA" if pasa else "NO PASA", todo["V"], todo["R"], todo["n"], todo["p"]))
    if sin_dup["n"] and (sin_dup["V"] > sin_dup["R"]) != pasa:
        print("  OJO: sin los duplicados el sentido CAMBIA; el resultado es de memoria.")

    json.dump({"medida_1": m1, "medida_2": todo, "medida_2_sin_duplicados": sin_dup,
               "descartados": no_raiz, "pasa": pasa,
               "V": todo["V"], "R": todo["R"], "filas": f2},
              io.open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
