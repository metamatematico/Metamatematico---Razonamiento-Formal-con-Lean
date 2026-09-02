# -*- coding: utf-8 -*-
"""¿Cuánto margen queda en el paso 3? Y ¿podría el grafo alcanzarlo?

LO QUE YA SE SABE. Un conjunto fijo de tres modulos —Mathlib.Tactic,
Data.Real.Basic, Data.Nat.Basic— hace elaborar el 90 % de los enunciados de
LeanWorkbook, y añadirle lo que el grafo propone no cambia nada: empate. Antes
de invertir mas trabajo en este punto hay que saber cuanto se puede ganar como
maximo.

EL TECHO ES 100 %: `import Mathlib` funciona siempre. Pero cuesta 742 s, mas
que el timeout, asi que no sirve como diagnostico caso por caso.

LA VIA BARATA. Cuando un enunciado no elabora, Lean DICE QUE IDENTIFICADOR le
falta: «unknown identifier 'Real.sqrt'», «unknown constant». Y
`data/lemas_mathlib.jsonl` dice en que modulo vive cada uno de los 183 433
hechos. O sea que el error se traduce en el import que faltaba, sin adivinar y
sin volver a llamar a Lean.

CON ESO SE CONTESTAN TRES COSAS:

  1. cuanto margen hay de verdad (que fraccion falla con el conjunto fijo)
  2. si esos fallos son POR IMPORTS o por otra cosa — un enunciado puede no
     elaborar por sintaxis, por `variable`s ausentes o por notacion, y eso no
     lo arregla ningun grafo
  3. si el modulo que faltaba estaba al alcance del grafo, o sea si un mejor
     emparejamiento lo habria encontrado

No gasta API.
"""
import argparse
import collections
import io
import json
import os
import random
import re
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAIZ = "E:/Metamatematico"
BANCO = RAIZ + "/data/banco_lemas.jsonl"
LISTA = RAIZ + "/data/lemas_mathlib.jsonl"
SALIDA = RAIZ + "/data/margen_paso3.json"
SEMILLA = 20260901
TIMEOUT = 240

FIJO = ["Mathlib.Tactic", "Mathlib.Data.Real.Basic", "Mathlib.Data.Nat.Basic"]

#: Los errores que SI se arreglan con un import, y los que no.
FALTA_NOMBRE = re.compile(
    r"unknown (?:identifier|constant) '([^']+)'"
    r"|unknown identifier `([^`]+)`", re.I)
#: Errores que NO son de imports: la sintaxis o el contexto estan mal.
NO_ES_IMPORT = re.compile(
    r"unexpected token|expected|unknown universe|failed to synthesize"
    r"|type mismatch|function expected", re.I)


def corre(imports, enunciado):
    ruta = RAIZ + "/_margen_check.lean"
    src = ("\n".join("import " + i for i in imports)
           + "\n\ntheorem _probe_ %s := by\n  sorry\n" % enunciado)
    io.open(ruta, "w", encoding="utf-8").write(src)
    t0 = time.time()
    try:
        p = subprocess.run(["lake", "env", "lean", ruta], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=TIMEOUT)
        salida = (p.stdout or "") + (p.stderr or "")
        ok = not re.search(r":\d+:\d+: error", salida)
        return ok, salida, time.time() - t0
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT", TIMEOUT
    finally:
        if os.path.exists(ruta):
            os.remove(ruta)


def main(n):
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory

    modulo_de = {}
    for l in io.open(LISTA, encoding="utf-8"):
        d = json.loads(l)
        modulo_de.setdefault(d["corto"], d["modulo"])
        modulo_de.setdefault(d["nombre"], d["modulo"])
    print("lista: %d nombres con modulo conocido" % len(modulo_de))

    nucleo = Nucleo.__new__(Nucleo)
    nucleo._graph = SkillCategory()
    Nucleo._load_foundational_skills(nucleo)
    g = nucleo._graph

    casos = [json.loads(l) for l in io.open(BANCO, encoding="utf-8")]
    random.seed(SEMILLA)
    muestra = random.sample(casos, min(n, len(casos)))
    print("muestra: %d enunciados\n" % len(muestra))

    ok = 0
    fallos = []
    for i, c in enumerate(muestra, 1):
        elab, salida, seg = corre(FIJO, c["enunciado"])
        if elab:
            ok += 1
            print("  %2d/%d  ok" % (i, len(muestra)))
            continue
        faltan = [a or b for a, b in FALTA_NOMBRE.findall(salida)]
        otro = bool(NO_ES_IMPORT.search(salida)) and not faltan
        mods = sorted({modulo_de[x] for x in faltan
                       if x in modulo_de} | {modulo_de[x.split(".")[-1]]
                                             for x in faltan
                                             if x.split(".")[-1] in modulo_de})
        skills = Nucleo._match_skills_to_query(nucleo, c["nl"], g)
        del_grafo = Nucleo._modulos_mathlib(
            nucleo, {"relevant_skills": skills}) or []
        alcanzable = bool(set(mods) & set(del_grafo))
        fallos.append({"id": c["id"], "faltan": faltan[:6],
                       "modulos_necesarios": mods[:6],
                       "no_es_import": otro,
                       "el_grafo_lo_tenia": alcanzable,
                       "grafo_propuso": del_grafo})
        print("  %2d/%d  FALLA  %s" % (
            i, len(muestra),
            ("no es de imports" if otro else
             ("falta " + ", ".join(faltan[:2])) if faltan else "sin diagnostico")))

    N = len(muestra)
    print("\n" + "=" * 62)
    print("  elabora con el conjunto fijo : %d de %d = %.1f %%"
          % (ok, N, 100.0 * ok / N))
    print("  MARGEN MAXIMO                : %.1f puntos" % (100.0 * len(fallos) / N))
    if fallos:
        de_import = [f for f in fallos if not f["no_es_import"] and f["faltan"]]
        otros = [f for f in fallos if f["no_es_import"] or not f["faltan"]]
        print("\n  de los %d fallos:" % len(fallos))
        print("     arreglables con un import : %d" % len(de_import))
        print("     NO son de imports         : %d  <- ningun grafo los arregla"
              % len(otros))
        con = [f for f in de_import if f["el_grafo_lo_tenia"]]
        print("\n  de los arreglables, el grafo YA proponia el modulo: %d de %d"
              % (len(con), len(de_import)))
        print("\n  que faltaba:")
        for f in de_import[:8]:
            print("     %-22s %s  ->  %s" % (
                f["id"][:20], ", ".join(f["faltan"][:2]),
                ", ".join(m.replace("Mathlib.", "") for m in
                          f["modulos_necesarios"][:2]) or "(sin modulo conocido)"))

    json.dump({"n": N, "elabora_fijo": ok, "fallos": fallos},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    a = ap.parse_args()
    sys.exit(main(a.n))
