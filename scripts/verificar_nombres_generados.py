# -*- coding: utf-8 -*-
"""¿Existen de verdad los nombres de los 125 nodos generados? Que lo diga Lean.

EL PENDIENTE QUE CIERRA. Los 125 nodos generados proponen 447 identificadores
distintos, y estan DEDUCIDOS de la ruta del modulo: el ultimo componente
—`Polynomial` de `Mathlib.Algebra.Polynomial`— y las declaraciones en CamelCase
que se encontraron debajo. Deducir no es comprobar, y por eso hoy no se
inyectan al prompt: al activarlos, la precision contra ProofNet cayo de 13,5 %
a 3,2 %, por debajo del modelo nulo.

La regla de la casa es que ningun nombre entra en el grafo sin que Lean lo
acepte. Los 117 del vocabulario curado pasaron por aqui —y 19 estaban caducos,
lo que subio la validez del 79 % al 95 %—. Estos 447 no han pasado nunca.

QUE SE ESPERA ENCONTRAR, y conviene decirlo antes de mirar: una parte
significativa NO deberia existir. El ultimo componente de una ruta de modulo es
muchas veces un NAMESPACE y no una declaracion — `Mathlib.Algebra.Order` da
`Order`, que agrupa cosas pero no es un identificador comprobable. Eso no es un
fallo del generador: es la diferencia entre «donde vive algo» y «como se llama
algo», que es justo lo que separa un nodo interpretado de uno que no lo esta.

COMO SE COMPRUEBA. Todos de una vez, con Mathlib entero importado y un `#check`
por nombre. Lean numera sus errores por linea, asi que se sabe cual fallo.

Y PARA LOS QUE FALLEN se distingue entre dos cosas distintas:
  · el nombre no existe en absoluto
  · el nombre es un NAMESPACE — existe como agrupacion pero no como termino,
    y eso se detecta porque hay declaraciones cualificadas bajo el

No gasta API. Tarda lo que tarde `import Mathlib` (~12 min).

    python scripts/verificar_nombres_generados.py
"""
import argparse
import collections
import io
import json
import os
import re
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAIZ = "E:/Metamatematico"
LISTA = RAIZ + "/data/lemas_mathlib.jsonl"
SALIDA = RAIZ + "/data/nombres_generados_verificados.json"
TIMEOUT = 2400


def verificar(nombres):
    """Los que Lean acepta como término. Una sola ejecución."""
    ruta = RAIZ + "/_nombres_check.lean"
    io.open(ruta, "w", encoding="utf-8").write(
        "import Mathlib\n" + "\n".join("#check @" + n for n in nombres) + "\n")
    t0 = time.time()
    try:
        p = subprocess.run(["lake", "env", "lean", ruta], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=TIMEOUT)
        salida = (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        print("  TIMEOUT tras %.0f s — sin veredicto, no se concluye nada"
              % (time.time() - t0))
        return None, ""
    finally:
        if os.path.exists(ruta):
            os.remove(ruta)
    malos = set()
    for m in re.finditer(r":(\d+):\d+: error", salida):
        i = int(m.group(1)) - 2          # linea 1 = import, el resto los #check
        if 0 <= i < len(nombres):
            malos.add(nombres[i])
    return {n for n in nombres if n not in malos}, salida


def main(_):
    from nucleo.pillars.mathlib_taxonomy import NODOS_MATHLIB

    por_nodo = {n.id: list(getattr(n, "nombres", None) or [])
                for n in NODOS_MATHLIB}
    nombres = sorted({x for v in por_nodo.values() for x in v})
    print("nodos: %d · nombres distintos: %d" % (len(por_nodo), len(nombres)))
    print("comprobando con Lean (import Mathlib, ~12 min)...\n")

    validos, _salida = verificar(nombres)
    if validos is None:
        return 1
    malos = [n for n in nombres if n not in validos]

    # ¿los que fallan son NAMESPACES? Se mira si la lista de hechos tiene
    # declaraciones cualificadas bajo ese prefijo.
    prefijos = collections.Counter()
    for l in io.open(LISTA, encoding="utf-8"):
        d = json.loads(l)
        p = d["nombre"].split(".")[0]
        if p:
            prefijos[p] += 1
    namespaces = [n for n in malos if prefijos.get(n, 0) >= 5]
    inexistentes = [n for n in malos if n not in namespaces]

    print("=" * 62)
    print("  existen como termino : %3d de %d = %.1f %%"
          % (len(validos), len(nombres), 100.0 * len(validos) / len(nombres)))
    print("  NO existen           : %3d" % len(malos))
    print("     de esos, son NAMESPACE  : %3d  (agrupan, no son un termino)"
          % len(namespaces))
    print("     no existen en absoluto  : %3d" % len(inexistentes))

    print("\n  los namespaces mas grandes (existen, pero no como termino):")
    for n in sorted(namespaces, key=lambda x: -prefijos[x])[:10]:
        print("     %-34s %5d declaraciones bajo el" % (n, prefijos[n]))

    if inexistentes:
        print("\n  NO EXISTEN EN ABSOLUTO — estos si son un fallo:")
        for n in inexistentes[:20]:
            print("     %s" % n)

    # por nodo: cuantos de sus nombres sobreviven
    print("\n=== POR NODO ===\n")
    sin_ninguno = []
    con_todos = 0
    for nid, ns in sorted(por_nodo.items()):
        if not ns:
            continue
        ok = [x for x in ns if x in validos]
        if not ok:
            sin_ninguno.append(nid)
        elif len(ok) == len(ns):
            con_todos += 1
    print("  nodos con TODOS sus nombres validos : %d de %d"
          % (con_todos, len(por_nodo)))
    print("  nodos que se quedan SIN NINGUNO     : %d" % len(sin_ninguno))
    if sin_ninguno:
        print("     " + ", ".join(x.replace("mathlib-", "")
                                  for x in sin_ninguno[:14]))

    json.dump({"nombres": len(nombres), "validos": sorted(validos),
               "namespaces": sorted(namespaces),
               "inexistentes": sorted(inexistentes),
               "nodos_sin_ningun_nombre": sin_ninguno},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    a = ap.parse_args()
    sys.exit(main(a))
