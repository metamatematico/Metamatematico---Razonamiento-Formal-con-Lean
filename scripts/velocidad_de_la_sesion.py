# -*- coding: utf-8 -*-
"""Cuánto cuesta una táctica con la sesión viva, frente a un compilado.

La cifra que hace viable el lazo por pasos es ésta, y hasta ahora sólo existía
en una sonda fuera del repositorio («0,02-0,63 s por táctica»). Una cifra que
se publica sin fichero de origen es la que envejece sin que nadie la relea, así
que se mide aquí y se guarda en `data/velocidad_de_la_sesion.json`.

Con la CABECERA ESTRECHA que pone `_normalize_code` —la del camino servido—,
no con `import Mathlib`: es la que la sesión carga en producción.

Se mide, sobre un mismo objetivo:
    cargar la cabecera                 una vez por proceso
    plantar el teorema con `sorry`     una vez por consulta
    una táctica que cierra, que progresa y que falla   por paso
    y el mismo teorema compilado como fichero, que es lo de hoy

No gasta API.

    python -m scripts.velocidad_de_la_sesion
"""
from __future__ import annotations

import asyncio
import datetime
import io
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

SALIDA = os.path.join(RAIZ, "data", "velocidad_de_la_sesion.json")
ENUNCIADO = "theorem sonda (a b : ℝ) : 2 * a * b ≤ a ^ 2 + b ^ 2 := by\n  sorry\n"
TACTICAS = [("cierra", "nlinarith [sq_nonneg (a - b)]"),
            ("progresa", "ring_nf"),
            ("falla", "linarith")]


def main():
    from nucleo.lean.cascada_sesion import partir
    from nucleo.lean.client import LeanClient
    from nucleo.lean.sesion import SesionLean

    cliente = LeanClient(project_path=RAIZ)
    cab, cuerpo, lineas_cab = partir(cliente._normalize_code(ENUNCIADO))
    doc = {"fecha": datetime.date.today().isoformat(), "cabecera": cab.splitlines()}

    with SesionLean() as s:
        t0 = time.time()
        env = s.comando(cab, env=None).env
        doc["segundos_cabecera"] = round(time.time() - t0, 2)
        t0 = time.time()
        r = s.comando(cuerpo, env=env)
        doc["segundos_plantar"] = round(time.time() - t0, 2)
        ps = r.sorries[0]["proofState"]
        doc["tacticas"] = []
        for esperado, tac in TACTICAS:
            # tres tomas; se guarda la mediana, y las tres
            tomas, clases = [], []
            for _ in range(3):
                x = s.tactica(tac, ps)
                tomas.append(round(x.segundos, 3))
                clases.append(x.clase)
            doc["tacticas"].append({"tactica": tac, "esperado": esperado,
                                    "clases": clases, "tomas": tomas,
                                    "mediana": sorted(tomas)[1]})

    bucle = asyncio.new_event_loop()
    try:
        t0 = time.time()
        rf = bucle.run_until_complete(cliente.check_code(
            ENUNCIADO.replace("sorry", TACTICAS[0][1])))
        doc["segundos_fichero"] = round(time.time() - t0, 1)
        doc["fichero_compila"] = bool(rf.is_success)
    finally:
        bucle.close()

    meds = [t["mediana"] for t in doc["tacticas"]]
    doc["tactica_min"], doc["tactica_max"] = min(meds), max(meds)
    print("cabecera %.1f s · plantar %.2f s" % (doc["segundos_cabecera"], doc["segundos_plantar"]))
    for t in doc["tacticas"]:
        print("  %-8s %-32s %s  mediana %.3f s" % (t["esperado"], t["tactica"],
                                                  t["clases"], t["mediana"]))
    print("el mismo teorema como fichero: %.1f s (compila=%s)"
          % (doc["segundos_fichero"], doc["fichero_compila"]))
    json.dump(doc, io.open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
