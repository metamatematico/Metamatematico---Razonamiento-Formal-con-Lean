# -*- coding: utf-8 -*-
"""Cuanto cuesta `import Mathlib`, de verdad y con fecha.

POR QUE HACE FALTA ESTE GUION
------------------------------
Nueve sitios del codigo dicen que `import Mathlib` tarda **742 s** y de ahi
sacan una decision de diseño: `_normalize_code` BORRA esa linea y la sustituye
por una cabecera estrecha, porque 742 s pasa del timeout de 360 s y «siempre
expira».

El 742 no tiene procedencia recuperable. Entro en el codigo el 2026-08-05 y no
hay ninguna medicion guardada detras. La explicacion que parecia obvia —que se
midio con `.lake` en el disco USB— es FALSA: `.lake` es un enlace a
C:\\MetamatematicoLake desde el 2026-04-06, cuatro meses antes.

Una cifra sin procedencia que sostiene una decision es exactamente el fallo que
este repositorio ya tiene documentado («cifra coherente pero rancia»). Asi que
se vuelve a medir, se guarda con su fecha, y quien lea el numero puede llegar
hasta aqui.

QUE MIDE, Y QUE NO
------------------
Mide SEGUNDOS de `lake env lean` sobre un fichero con `import Mathlib`, varias
veces, separando la primera —cache del sistema de ficheros frio— de las demas.

NO mide si la cabecera ancha ACIERTA mas que la estrecha. Esa es otra pregunta,
con otro banco (`scripts/imports_que_discriminan.py`), y es la que de verdad
decide si `_normalize_code` debe seguir borrando la linea. El tiempo solo puede
tumbar el argumento «siempre expira»; no puede sostener el contrario.

No gasta API. Gasta ~2 min de Lean.

    python -m scripts.cuanto_cuesta_mathlib --veces 3
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

SALIDA = os.path.join(RAIZ, "data", "coste_de_mathlib.json")

#: el timeout que el codigo compara contra la cifra. Si el coste medido queda
#: por debajo, el argumento «siempre expira» se cae; si queda por encima, se
#: sostiene. Es el unico consumidor del numero.
TIMEOUT_DEL_SISTEMA = 360

CUERPO = ("theorem sonda_coste (a b : Real) : 2*a*b <= a^2 + b^2 := by\n"
          "  nlinarith [sq_nonneg (a-b)]\n")


def una_vuelta(cabecera: str, etiqueta: str):
    ruta = os.path.join(RAIZ, "_coste_%s.lean" % etiqueta)
    io.open(ruta, "w", encoding="utf-8").write(cabecera + "\n\n" + CUERPO)
    t0 = time.time()
    try:
        p = subprocess.run(["lake", "env", "lean", ruta], cwd=RAIZ,
                           capture_output=True, text=True, timeout=1800,
                           encoding="utf-8", errors="replace")
        ok, detalle = p.returncode == 0, ((p.stdout or "") + (p.stderr or ""))[:200]
    except subprocess.TimeoutExpired:
        ok, detalle = None, "TIMEOUT"
    seg = time.time() - t0
    try:
        os.remove(ruta)
    except OSError:
        pass
    return round(seg, 1), ok, detalle


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--veces", type=int, default=3)
    args = ap.parse_args()

    #: la cabecera estrecha REAL, la que `_normalize_code` pone hoy, para que
    #: la comparacion sea contra lo que el sistema hace y no contra un invento
    try:
        from nucleo.lean.client import LeanClient
        estrecha = LeanClient()._normalize_code("theorem x : 1 = 1 := rfl")
        estrecha = "\n".join(l for l in estrecha.splitlines()
                             if l.strip().startswith(("import", "open")))
    except Exception as e:                                     # noqa: BLE001
        print("no se pudo sacar la cabecera estrecha del cliente: %s" % e)
        estrecha = "import Mathlib.Tactic.NormNum\nimport Mathlib.Tactic.Linarith"
    print("cabecera estrecha (la que pone el sistema hoy):")
    for l in estrecha.splitlines():
        print("   %s" % l)
    print()

    tomas = {"ancha": [], "estrecha": []}
    for i in range(args.veces):
        s, ok, det = una_vuelta("import Mathlib", "ancha")
        tomas["ancha"].append({"seg": s, "compila": ok})
        print("  ancha    vuelta %d: %6.1f s  compila=%s%s"
              % (i + 1, s, ok, "" if ok else "  " + det[:70]))
        s, ok, det = una_vuelta(estrecha, "estrecha")
        tomas["estrecha"].append({"seg": s, "compila": ok})
        print("  estrecha vuelta %d: %6.1f s  compila=%s%s"
              % (i + 1, s, ok, "" if ok else "  " + det[:70]))

    def resumen(k):
        v = [t["seg"] for t in tomas[k]]
        #: la PRIMERA aparte: es la unica con el cache del sistema frio, y
        #: mezclarla con las demas esconde justo la diferencia que importa
        return {"primera": v[0], "resto": v[1:],
                "mediana_resto": sorted(v[1:])[len(v[1:]) // 2] if v[1:] else v[0],
                #: LA QUE SE PUBLICA. `mediana_resto` con dos tomas escoge la
                #: mayor, y el artefacto llego a decir 25 y 12 en una seccion y
                #: 24 y 11 en otra, del mismo fichero.
                "mediana": sorted(v)[len(v) // 2]}

    r_a, r_e = resumen("ancha"), resumen("estrecha")
    print("\n=== LO MEDIDO ===\n")
    print("  `import Mathlib`     primera %.1f s · resto %s"
          % (r_a["primera"], r_a["resto"]))
    print("  cabecera estrecha    primera %.1f s · resto %s"
          % (r_e["primera"], r_e["resto"]))

    print("\n=== CONTRA EL ARGUMENTO PUBLICADO ===\n")
    print("  el codigo dice 742 s, por encima del timeout de %d s,"
          % TIMEOUT_DEL_SISTEMA)
    print("  y de ahi concluye que `import Mathlib` SIEMPRE expira.\n")
    peor = max(t["seg"] for t in tomas["ancha"])
    if peor < TIMEOUT_DEL_SISTEMA:
        print("  La peor toma de hoy es %.1f s: por DEBAJO del timeout." % peor)
        print("  El argumento «siempre expira» no se sostiene con esta medida.")
        print("  Eso NO dice que la cabecera ancha sea mejor: dice que la")
        print("  razon publicada para descartarla no es la razon real. Quien")
        print("  quiera cambiar `_normalize_code` necesita el otro banco, el")
        print("  de aciertos, no este.")
    else:
        print("  La peor toma de hoy es %.1f s: por ENCIMA del timeout." % peor)
        print("  El argumento se sostiene, aunque la cifra concreta cambie.")

    doc = {"fecha": datetime.date.today().isoformat(),
           "timeout_del_sistema": TIMEOUT_DEL_SISTEMA,
           "cifra_publicada_antes": 742,
           "cabecera_estrecha": estrecha.splitlines(),
           "ancha": tomas["ancha"], "estrecha": tomas["estrecha"],
           "resumen_ancha": r_a, "resumen_estrecha": r_e,
           "peor_ancha": peor,
           "expira_siempre": bool(peor >= TIMEOUT_DEL_SISTEMA)}
    json.dump(doc, io.open(SALIDA, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
