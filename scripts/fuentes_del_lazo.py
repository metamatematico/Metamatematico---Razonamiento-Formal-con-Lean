# -*- coding: utf-8 -*-
"""¿Qué fuente de tácticas hace cerrar más al lazo? La ablación del paso 4.

El lazo del paso 3 busca con los proponentes que se le den. Aquí se le dan
CUATRO combinaciones, sobre los MISMOS estados raíz y con el MISMO
presupuesto, y cuenta cuántos enunciados verifica el fichero (I2):

    D0            la cascada, táctica a táctica           el nulo
    D0 + D1v      más las tácticas enteras de los vecinos de estado
    D0 + D2       más los «Try this» de `apply?` como sonda
    D0 + D1v + D2 todas

LA REGLA, ESCRITA ANTES DE CORRER
---------------------------------
    Una fuente entra si la combinación CON ella verifica más que D0 solo, con
    el McNemar exacto de los discordantes a la vista. Sin modelo: esto no mide
    D3, que es la puerta con API del paso 3.

LOS CASOS
---------
Los estados raíz de `recuperacion_por_estado.py` —enunciados de LeanWorkbook de
la partición de PRUEBA, ya plantados y comprobados como raíz—; el índice de
vecinos se construye con la de ENTRENAMIENTO. Van con la cabecera con que
LeanWorkbook los escribió (`import Mathlib`), y por eso el veredicto lo da un
fichero con ESA cabecera y no `check_code`, cuyo normalizador la cambiaría por
la estrecha y rechazaría enunciados que sí elaboran.

D1 DENSO (paso 5, `--con-densa`)
--------------------------------
Los mismos estados, el mismo presupuesto, y la misma regla, con estos brazos:

    D0 · D0 + D1v · D0 + D1d · D0 + D1v + D1d

D1d es el encoder de premisas (`nucleo/lazo/densa.py`). Entra si D0 + D1d
verifica más que D0, y SE QUEDA JUNTO A D1v sólo si D0 + D1v + D1d verifica más
que D0 + D1v: si lo que añade ya lo traían los vecinos, no añade. Va a
`data/fuentes_del_lazo.densa.json`, para no tocar la evidencia del paso 4. El
encoder se entrenó con Mathlib, y los casos son de LeanWorkbook: no hay fuga.

No gasta API.

    python -m scripts.fuentes_del_lazo --n 60
    python -m scripts.fuentes_del_lazo --n 60 --con-densa
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
import os
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

SALIDA = os.path.join(RAIZ, "data", "fuentes_del_lazo.json")
CASOS = os.path.join(RAIZ, "data", "recuperacion_por_estado.json")


class ClienteFichero:
    """El juez (I2) con la cabecera de LeanWorkbook: `lake env lean` a pelo."""

    def _normalize_code(self, codigo):
        return codigo

    async def check_code(self, codigo):
        from nucleo.lean.client import LeanResult, LeanResultStatus
        ruta = os.path.join(RAIZ, "_fuentes_del_lazo.lean")
        io.open(ruta, "w", encoding="utf-8").write(codigo + "\n")
        try:
            p = subprocess.run(["lake", "env", "lean", ruta], cwd=RAIZ,
                               capture_output=True, text=True, timeout=300,
                               encoding="utf-8", errors="replace")
            sal = (p.stdout or "") + (p.stderr or "")
        except subprocess.TimeoutExpired:
            sal, p = "error: TIMEOUT", None
        finally:
            try:
                os.remove(ruta)
            except OSError:
                pass
        errores = [l for l in sal.splitlines() if "error" in l.lower()]
        if errores:
            st = LeanResultStatus.ERROR
        elif "declaration uses 'sorry'" in sal:
            st = LeanResultStatus.SORRY
        else:
            st = LeanResultStatus.SUCCESS
        return LeanResult(status=st, output=sal,
                          messages=[{"severity": "error", "data": e} for e in errores])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--con-densa", action="store_true")
    args = ap.parse_args()
    salida = SALIDA.replace(".json", ".densa.json") if args.con_densa else SALIDA

    from sklearn.model_selection import train_test_split
    from nucleo.lean import nombres
    from nucleo.lean.sesion import SesionLean
    from nucleo.lean.solver_cascade import SolverCascade
    from nucleo.lazo.mediador import Mediador, Presupuesto
    from nucleo.lazo.proponentes import D0Cascada, D1Vecinos, D2Busqueda
    from nucleo.lazo.registro import Registro
    from nucleo.lazo.vecinos import IndiceDeVecinos
    from scripts.recuperacion_por_estado import (CABECERA, PRUEBA, SEMILLA,
                                                 cargar, mcnemar)

    ids = [f["id"] for f in json.load(io.open(CASOS, encoding="utf-8"))["filas"]][:args.n]
    filas = cargar()
    y = [f["cabeza"] for f in filas]
    itr, ite = train_test_split(list(range(len(filas))), test_size=PRUEBA,
                                random_state=SEMILLA, stratify=y)
    tr = [filas[i] for i in itr]
    por_id = {}
    for i in ite:
        por_id.setdefault(filas[i]["id"], filas[i])
    casos = [por_id[i] for i in ids if i in por_id]
    print("casos: %d (los estados raíz de recuperacion_por_estado)" % len(casos))

    indice = IndiceDeVecinos().construir([f["estado"] for f in tr], [f["tactica"] for f in tr])
    cl = ClienteFichero()
    casc = SolverCascade(cl)
    viva = {"s": None, "env": None, "cab": None}

    def abrir(cab):
        s = viva["s"]
        if s is None or not s.viva or viva["cab"] != cab:
            if s is not None:
                s.cerrar()
            s = SesionLean().abrir()
            viva.update(s=s, env=s.comando(cab, env=None).env, cab=cab)
        return viva["s"], viva["env"]

    configs = {
        "D0": lambda: [D0Cascada(casc)],
        "D0+D1v": lambda: [D0Cascada(casc), D1Vecinos(indice)],
        "D0+D2": lambda: [D0Cascada(casc), D2Busqueda()],
        "D0+D1v+D2": lambda: [D0Cascada(casc), D1Vecinos(indice), D2Busqueda()],
    }
    if args.con_densa:
        from nucleo.lazo.densa import D1Denso, IndiceDenso
        densa = IndiceDenso()
        if not densa.disponible():
            print("D1 denso no está: falta el modelo o `premisas.jsonl` "
                  "(scripts/bajar_encoders.py y scripts/alinear_premisas.py)")
            return 1
        configs = {
            "D0": configs["D0"], "D0+D1v": configs["D0+D1v"],
            "D0+D1d": lambda: [D0Cascada(casc), D1Denso(densa)],
            "D0+D1v+D1d": lambda: [D0Cascada(casc), D1Vecinos(indice), D1Denso(densa)],
        }
    p = Presupuesto(lean=30, llamadas=0, segundos=90, nodos=30, profundidad=4,
                    tope_tactica=15)
    bucle = asyncio.new_event_loop()
    res = {c: {} for c in configs}
    print("  %-26s %s" % ("id", "  ".join("%-10s" % c for c in configs)))
    try:
        for f in casos:
            codigo = CABECERA + "\n\n" + f["enunciado"]
            linea = []
            for c, props in configs.items():
                m = Mediador(abrir, cl, props(), p, registro=Registro(problema=f["id"]),
                             existe=nombres.existe, cerrar_al_final=False)
                r = bucle.run_until_complete(m.resolver(codigo))
                res[c][f["id"]] = {"v": r.veredicto, "lean": r.llamadas_lean,
                                   "seg": round(r.segundos, 1), "caminos": r.caminos}
                linea.append("%-10s" % ("SI" if r.veredicto == "verificado" else "·"))
            print("  %-26s %s" % (f["id"][:26], "  ".join(linea)))
            json.dump({"parcial": True, "res": res}, io.open(salida, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
    finally:
        if viva["s"] is not None:
            viva["s"].cerrar()
        bucle.close()

    ok = {c: {i for i, x in res[c].items() if x["v"] == "verificado"} for c in configs}
    base = ok["D0"]
    print("\n=== VERIFICADOS, MISMOS %d ESTADOS, MISMO PRESUPUESTO ===\n" % len(casos))
    resumen = {}
    for c in configs:
        b, d = len(ok[c] - base), len(base - ok[c])
        resumen[c] = {"verifica": len(ok[c]), "gana_a_D0": b, "pierde_con_D0": d,
                      "p": round(mcnemar(b, d), 4),
                      "lean_medio": round(sum(x["lean"] for x in res[c].values()) / max(1, len(res[c])), 1)}
        print("  %-10s %3d   +%d −%d frente a D0   p %.4f   %.1f llamadas por caso"
              % (c, len(ok[c]), b, d, resumen[c]["p"], resumen[c]["lean_medio"]))
    fuera = {"n": len(casos), "presupuesto": p.__dict__, "resumen": resumen, "res": res}
    fuera.update({c: len(ok[c]) for c in configs})
    if args.con_densa:
        # la segunda mitad de la regla: ¿añade D1d a lo que ya traen los vecinos?
        v, vd = ok["D0+D1v"], ok["D0+D1v+D1d"]
        b, d = len(vd - v), len(v - vd)
        fuera["densa_sobre_vecinos"] = {"gana": b, "pierde": d, "p": round(mcnemar(b, d), 4)}
        print("\n  D0+D1v+D1d frente a D0+D1v: +%d −%d   p %.4f" % (b, d, mcnemar(b, d)))
    json.dump(fuera, io.open(salida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n-> %s" % salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
