# -*- coding: utf-8 -*-
"""La puerta del paso 5: ¿qué lectura de φ etiqueta los estados?

LAS DOS LECTURAS, SOBRE LOS MISMOS ESTADOS RAÍZ
-----------------------------------------------
    texto        los identificadores del estado IMPRESO por Lean
    constantes   las constantes que Lean dice que usa el estado
                 (`metamat_constantes`, `nucleo/lazo/phi.py`)

Los estados: las 20 consultas de la campaña —los enunciados que escribió el
modelo, reparados como en el camino servido— y los 150 estados raíz de
LeanWorkbook de `recuperacion_por_estado.py`. Todo en un entorno con
`import Mathlib`: etiquetar no verifica nada, así que una biblioteca ancha no
puede inflar ningún veredicto.

LA REGLA, ESCRITA ANTES DE CORRER
---------------------------------
La propuesta (§9) dice que φ «explica, no busca» y «se evalúa por exactitud,
no por cierres». Así que:

    1. AUTOMÁTICO · cobertura: estados con ≥ 1 concepto, texto contra
       constantes. La propuesta predice que el texto «pierde casi todo» por la
       notación. Si las constantes no cubren más, φ se queda en el texto.
    2. EXACTITUD · NO la decide este guion. Que un concepto sea PERTINENTE para
       un alumno —¿es «real-analysis» una buena etiqueta para 2ab ≤ a² + b²,
       sólo porque vive en ℝ?— lo decide alguien leyendo. Se genera
       `data/phi_muestra_para_revisar.json` con 40 estados y sus etiquetas, y
       hasta que alguien la revise la exactitud NO ESTÁ MEDIDA.

No gasta API.

    python -m scripts.phi_de_estados
"""
from __future__ import annotations

import io
import json
import os
import random
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

SALIDA = os.path.join(RAIZ, "data", "phi_de_estados.json")
MUESTRA = os.path.join(RAIZ, "data", "phi_muestra_para_revisar.json")
_IMPORT = re.compile(r"^\s*import\s", re.M)


def sin_imports(codigo: str) -> str:
    return "\n".join(l for l in codigo.split("\n") if not _IMPORT.match(l))


def estados_es():
    """Los enunciados de las 20 consultas, como los ve el camino servido."""
    from nucleo.lean import nombres
    from scripts.lazo_por_pasos import cargar_casos, enunciado_con_sorry
    fuera = []
    for q, g in cargar_casos():
        e = enunciado_con_sorry((g or {}).get("codigo") or "")
        if not e:
            continue
        try:
            e, _ = nombres.reparar_codigo(e)
        except Exception:                                      # noqa: BLE001
            pass
        fuera.append(("es", q, sin_imports(e)))
    return fuera


def estados_lw():
    from scripts.recuperacion_por_estado import cargar
    d = json.load(io.open(os.path.join(RAIZ, "data", "recuperacion_por_estado.json"),
                          encoding="utf-8"))
    ids = [f["id"] for f in d["filas"]]
    por_id = {}
    for f in cargar():
        por_id.setdefault(f["id"], f)
    abre = "open BigOperators Real Nat Topology Rat\n\n"
    return [("lw", i, abre + por_id[i]["enunciado"]) for i in ids if i in por_id]


def main():
    import logging
    logging.disable(logging.WARNING)
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    from nucleo.lean.sesion import SesionLean
    from nucleo.lazo import phi

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    ix = phi.indice(n._graph)
    print("índice de φ: %d nombres exactos, %d conceptos"
          % (len(ix), len({c for v in ix.values() for c in v})))

    casos = estados_es() + estados_lw()
    print("estados a etiquetar: %d\n" % len(casos))
    filas = []
    with SesionLean() as s:
        env = s.comando("import Mathlib\nimport Aesop", env=None).env
        r = s.comando(phi.TACTICA_CONSTANTES, env=env)
        if r.clase == "error":
            print("no se pudo definir la táctica: %s" % r.error)
            return 1
        env = r.env
        for fuente, clave, codigo in casos:
            r = s.comando(codigo, env=env)
            if r.clase == "error" or not r.sorries:
                filas.append({"fuente": fuente, "clave": clave, "elabora": False})
                continue
            raiz = r.sorries[0]
            txt = phi.phi_texto(raiz.get("goal") or "", ix)
            nombres = phi.constantes_de(s, raiz["proofState"]) or []
            cte = phi.conceptos(nombres, ix)
            esp = phi.conceptos(phi.sin_portadores(nombres), ix)
            filas.append({"fuente": fuente, "clave": clave, "elabora": True,
                          "estado": raiz.get("goal") or "",
                          "texto": sorted(txt), "constantes": sorted(cte),
                          "especificas": sorted(esp), "nombres": nombres,
                          "leidas": bool(nombres)})

    ok = [f for f in filas if f["elabora"]]
    resumen = {}
    for fuente in ("es", "lw", "todos"):
        fs = [f for f in ok if fuente == "todos" or f["fuente"] == fuente]
        if not fs:
            continue
        t = sum(1 for f in fs if f["texto"])
        c = sum(1 for f in fs if f["constantes"])
        e = sum(1 for f in fs if f["especificas"])
        resumen[fuente] = {
            "n": len(fs), "texto": t, "constantes": c, "especificas": e,
            "media_especificas": round(sum(len(f["especificas"]) for f in fs) / len(fs), 2),
            "solo_constantes": sum(1 for f in fs if f["constantes"] and not f["texto"]),
            "solo_texto": sum(1 for f in fs if f["texto"] and not f["constantes"]),
            "media_constantes": round(sum(len(f["constantes"]) for f in fs) / len(fs), 2),
            "media_texto": round(sum(len(f["texto"]) for f in fs) / len(fs), 2)}
    print("=== COBERTURA · estados con al menos un concepto ===\n")
    for k, v in resumen.items():
        print("  %-6s n %3d · texto %3d · constantes %3d · sin portadores %3d · "
              "conceptos por estado: constantes %.2f, sin portadores %.2f, texto %.2f"
              % (k, v["n"], v["texto"], v["constantes"], v["especificas"],
                 v["media_constantes"], v["media_especificas"], v["media_texto"]))
    print("  no elaboran: %d" % (len(filas) - len(ok)))

    # la muestra para revisar a mano: 20 y 20, con semilla
    rnd = random.Random(0)
    es = [f for f in ok if f["fuente"] == "es"]
    lw = [f for f in ok if f["fuente"] == "lw"]
    muestra = es[:20] + rnd.sample(lw, min(20, len(lw)))
    json.dump([{"fuente": f["fuente"], "clave": f["clave"], "estado": f["estado"],
                "etiquetas": f["constantes"], "sin_portadores": f["especificas"],
                "pertinente": None, "notas": ""}
               for f in muestra],
              io.open(MUESTRA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    t = resumen["todos"]
    gana = t["constantes"] > t["texto"]
    print("\n=== LA PUERTA ===\n")
    print("  cobertura: %s — constantes %d, texto %d de %d."
          % ("las constantes cubren MÁS" if gana else "las constantes NO cubren más",
             t["constantes"], t["texto"], t["n"]))
    print("  exactitud: SIN MEDIR. Muestra de %d estados en %s," % (len(muestra), MUESTRA))
    print("  con `pertinente: null` en cada uno hasta que alguien la lea.")
    json.dump({"resumen": resumen, "constantes": t["constantes"], "texto": t["texto"],
               "n": t["n"], "exactitud": None, "filas": filas},
              io.open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
