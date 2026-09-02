# -*- coding: utf-8 -*-
"""¿Sirve el núcleo? La mitad de la respuesta se puede medir sin gastar un peso.

LA PREGUNTA QUE LLEVA TODA LA SESION ABIERTA es si el nucleo contribuye. La
ablacion la contestaria, pero necesita el LLM y se quedo sin credito.

Y AHI ESTABA EL ERROR DE PLANTEAMIENTO. El nucleo aporta en tres puntos, y solo
UNO necesita al modelo:

    paso 1  vocabulario al prompt      necesita LLM
    paso 3  QUE MODULOS IMPORTA LEAN   no lo necesita   <- esto
    paso 6  orden de tacticas          no lo necesita

El paso 3 es la mitad de lo que el grafo hace en caliente, y nunca se ha
medido. Aqui se mide, con Lean como juez.

COMO. Se cogen enunciados Lean de oro —de LeanWorkbook, que son Lean 4 y
compilables— se le pide al grafo que elija modulos a partir del enunciado en
lenguaje natural, y se comprueba si el teorema ELABORA con esos imports.

    <imports elegidos>
    theorem _probe_ <enunciado> := by sorry

Si elabora, los imports bastaban. Si no, el grafo eligio mal y en produccion
eso es una verificacion perdida.

CUATRO ESTRATEGIAS, para que la cifra signifique algo:

    grafo     los modulos que el grafo sugiere para esa consulta
    fijo      un conjunto pequeño SIEMPRE IGUAL. Es el modelo nulo: si el
              grafo no lo bate, en este punto no esta aportando nada.
    azar      modulos al azar del catalogo — para saber que es la nada
    todo      `import Mathlib`. Funciona siempre y tarda 742 s medidos, mas
              que el timeout. Es el techo, y la razon de que haga falta elegir.

Lo que se mide no es solo si elabora: tambien CUANTO TARDA. El valor del paso 3
es precisamente evitar el `import Mathlib`, asi que el tiempo es la mitad del
resultado.

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
SALIDA = RAIZ + "/data/imports_contra_lean.json"
SEMILLA = 20260901
TIMEOUT = 240

#: El modelo nulo: lo que uno pondria sin pensar. Sale del header que el propio
#: cliente usa cuando nadie le dice nada.
FIJO = ["Mathlib.Tactic", "Mathlib.Data.Real.Basic", "Mathlib.Data.Nat.Basic"]


def corre(imports, enunciado):
    """(elabora, segundos). El cuerpo es `sorry`: solo se prueba el ENUNCIADO."""
    ruta = RAIZ + "/_imports_check.lean"
    src = ("\n".join("import " + i for i in imports)
           + "\n\ntheorem _probe_ %s := by\n  sorry\n" % enunciado)
    io.open(ruta, "w", encoding="utf-8").write(src)
    t0 = time.time()
    try:
        p = subprocess.run(["lake", "env", "lean", ruta], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=TIMEOUT)
        salida = (p.stdout or "") + (p.stderr or "")
        # `sorry` produce un WARNING, no un error. Solo miramos errores.
        ok = not re.search(r":\d+:\d+: error", salida)
        return ok, time.time() - t0
    except subprocess.TimeoutExpired:
        return False, TIMEOUT
    finally:
        if os.path.exists(ruta):
            os.remove(ruta)


def main(n, con_todo):
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory

    nucleo = Nucleo.__new__(Nucleo)
    nucleo._graph = SkillCategory()
    Nucleo._load_foundational_skills(nucleo)
    g = nucleo._graph

    # catalogo de modulos reales, para el azar
    mapa = json.load(io.open(RAIZ + "/data/mathlib_modulos.json",
                             encoding="utf-8"))["por_skill"]
    todos_modulos = sorted({m for v in mapa.values() for m in v})

    casos = [json.loads(l) for l in io.open(BANCO, encoding="utf-8")]
    random.seed(SEMILLA)
    muestra = random.sample(casos, min(n, len(casos)))
    print("muestra: %d enunciados de oro\n" % len(muestra))

    estrategias = ["grafo", "fijo", "azar"]
    if con_todo:
        estrategias.append("todo")

    res = collections.defaultdict(lambda: {"ok": 0, "n": 0, "seg": 0.0,
                                           "mods": 0})
    detalle = []
    for i, c in enumerate(muestra, 1):
        fila = {"id": c["id"]}
        skills = Nucleo._match_skills_to_query(nucleo, c["nl"], g)
        del_grafo = Nucleo._modulos_mathlib(
            nucleo, {"relevant_skills": skills}) or []
        for est in estrategias:
            if est == "grafo":
                imports = del_grafo or list(FIJO)
            elif est == "fijo":
                imports = list(FIJO)
            elif est == "azar":
                imports = random.sample(todos_modulos,
                                        max(1, len(del_grafo) or 3))
            else:
                imports = ["Mathlib"]
            ok, seg = corre(imports, c["enunciado"])
            r = res[est]
            r["ok"] += 1 if ok else 0
            r["n"] += 1
            r["seg"] += seg
            r["mods"] += len(imports)
            fila[est] = {"ok": ok, "seg": round(seg, 1), "n_mods": len(imports)}
        detalle.append(fila)
        print("  %2d/%d  %-22s %s" % (
            i, len(muestra), c["id"][:20],
            "  ".join("%s:%s" % (e, "ok" if fila[e]["ok"] else "--")
                      for e in estrategias)))

    print("\n" + "=" * 62)
    print("  %-8s %10s %10s %10s" % ("", "elabora", "segundos", "modulos"))
    for est in estrategias:
        r = res[est]
        print("  %-8s %9.1f %% %9.1f %10.1f"
              % (est, 100.0 * r["ok"] / max(1, r["n"]),
                 r["seg"] / max(1, r["n"]), r["mods"] / max(1, r["n"])))

    gr, fj = res["grafo"], res["fijo"]
    print("\n  LECTURA")
    print("    el modelo nulo (fijo) elabora el %.1f %%"
          % (100.0 * fj["ok"] / max(1, fj["n"])))
    print("    el grafo elabora el %.1f %%"
          % (100.0 * gr["ok"] / max(1, gr["n"])))
    if gr["ok"] > fj["ok"]:
        print("    EL GRAFO APORTA en el paso 3")
    elif gr["ok"] == fj["ok"]:
        print("    EMPATE: en este punto el grafo no aporta sobre un conjunto fijo")
    else:
        print("    EL GRAFO PERJUDICA: elige peor que un conjunto fijo")

    json.dump({"n": len(muestra), "semilla": SEMILLA,
               "resumen": {e: dict(res[e]) for e in estrategias},
               "detalle": detalle},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--con-todo", action="store_true",
                    help="incluye `import Mathlib` (742 s por caso)")
    a = ap.parse_args()
    sys.exit(main(a.n, a.con_todo))
