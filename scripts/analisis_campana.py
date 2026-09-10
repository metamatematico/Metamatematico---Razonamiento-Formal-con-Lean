# -*- coding: utf-8 -*-
"""¿Aporta el sistema? ¿Y aporta el grafo dentro de él? Dos preguntas, dos pares.

LO QUE SE COMPARA, Y POR QUÉ HACEN FALTA TRES RAMAS
---------------------------------------------------
Durante mucho tiempo la única comparación fue «el sistema con el grafo» contra
«el sistema sin el grafo». Esa pareja contesta si el GRAFO aporta, y la
respuesta fue que no se ve. Pero no contesta si el SISTEMA aporta, porque la
rama sin grafo sigue llevando imports, premisas, cascada de tácticas,
revisión de sintaxis, RONDAS DE REPARACIÓN, ejemplos few-shot y cualificación
de nombres contra 217 419 identificadores. Es el sistema menos una pieza.

Faltaba el SUELO: el mismo modelo, una llamada, Lean juzga una vez, sin nada.
Lo produce `scripts/linea_base_llm.py` y entra aquí como `modelo-solo`.

    modelo-solo       el suelo. Sin sistema.
    sin-vocabulario   el sistema entero menos los nombres del grafo
    completo          el sistema tal como se sirve

    completo vs modelo-solo       ->  ¿aporta el APARATO?
    completo vs sin-vocabulario   ->  ¿aporta el GRAFO dentro del aparato?

CÓMO SE JUZGA. McNemar exacto sobre los pares discordantes. Con tan pocos
pares la aproximación chi-cuadrado no vale, y el SIGNO importa tanto como el
número: rescatar 8 y romper 0 no es lo mismo que rescatar 3 y romper 2 aunque
la diferencia neta se parezca.

Y se marca cuándo las dos ramas produjeron CÓDIGO IDÉNTICO: un empate por
identidad no es un empate, es un par que no podía separar nada.

No gasta API.

    python -m scripts.analisis_campana
"""
import argparse
import collections
import hashlib
import io
import json
import os
import sys
from math import comb

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CAMPANA = "E:/Metamatematico/data/campana_de_grabacion.json"
RESPALDO = "E:/Metamatematico/data/campana_completo.json"
LINEA_BASE = "E:/Metamatematico/data/linea_base_llm.json"
GRABACIONES = "E:/Metamatematico/data/grabaciones/formalizaciones.jsonl"
SALIDA = "E:/Metamatematico/data/analisis_campana.json"


def cargar_filas():
    """Las filas de las tres ramas, vengan de donde vengan.

    La tanda de control se corrió en su propia ejecución y con la versión del
    script que SOBRESCRIBÍA el fichero, así que `completo` puede estar sólo en
    el respaldo. Se unen las fuentes y se quita lo repetido.

    `linea_base_llm.json` no lleva campo `config` porque es otro script: se le
    pone `modelo-solo` al entrar.
    """
    filas, vistos = [], set()
    for ruta in (CAMPANA, RESPALDO):
        try:
            d = json.load(io.open(ruta, encoding="utf-8"))
        except Exception:                                      # noqa: BLE001
            continue
        for f in (d.get("filas") or []):
            clave = (f.get("config"), f.get("consulta"))
            if clave not in vistos:
                vistos.add(clave)
                filas.append(f)
    try:
        d = json.load(io.open(LINEA_BASE, encoding="utf-8"))
        for f in (d.get("filas") or []):
            g = dict(f)
            g["config"] = "modelo-solo"
            clave = ("modelo-solo", g.get("consulta"))
            if clave not in vistos:
                vistos.add(clave)
                filas.append(g)
    except Exception:                                          # noqa: BLE001
        pass
    return filas


def huellas_por_config():
    """consulta -> config -> huella del código que el modelo escribió.

    Si dos ramas producen el MISMO código, la pieza que las separa no movió
    nada en esa consulta y su empate de veredicto no dice nada sobre ella.
    """
    out = collections.defaultdict(dict)
    try:
        for linea in io.open(GRABACIONES, encoding="utf-8"):
            d = json.loads(linea)
            q, c, cod = d.get("consulta"), d.get("config"), d.get("codigo")
            if q and c and cod:
                out[q][c] = hashlib.sha1(
                    cod.strip().encode("utf-8")).hexdigest()[:10]
    except Exception as exc:                                   # noqa: BLE001
        print("  (sin grabaciones legibles: %s)" % exc)
    return out


def main() -> int:
    filas = cargar_filas()
    if not filas:
        print("No hay filas. Corre `scripts.campana_de_grabacion`.")
        return 1

    por = collections.defaultdict(dict)
    for f in filas:
        por[f["consulta"]][f["config"]] = f
    configs = sorted({f["config"] for f in filas})
    print("=== %d consultas · ramas: %s ===" % (len(por), ", ".join(configs)))

    def ok(f):
        return f is not None and f.get("veredicto", "").endswith("SUCCESS")

    print("\nVERIFICAN, POR RAMA")
    tot = {}
    orden = ["modelo-solo", "sin-vocabulario", "completo"]
    secuencia = ([x for x in orden if x in configs]
                 + [x for x in configs if x not in orden])
    for c in secuencia:
        fs = [f for f in filas if f["config"] == c]
        v = sum(1 for f in fs if ok(f))
        tot[c] = (v, len(fs))
        print("  %-18s %2d de %2d  (%3.0f %%)  ·  %.0f s de media"
              % (c, v, len(fs), 100.0 * v / max(1, len(fs)),
                 sum(f.get("seg", 0) for f in fs) / max(1, len(fs))))

    if len(configs) < 2:
        print("\n  Sólo hay una rama: no hay comparación que hacer.")
        return 0

    hue = huellas_por_config()

    def parear(a, b, etiq_a, etiq_b):
        gana = pierde = e_ok = e_mal = identicos = 0
        det = []
        print("\nPAREADO — %s frente a %s" % (a, b))
        for q, d in por.items():
            fa, fb = d.get(a), d.get(b)
            if fa is None or fb is None:
                continue
            va, vb = ok(fa), ok(fb)
            misma = (hue.get(q, {}).get(a) is not None
                     and hue.get(q, {}).get(a) == hue.get(q, {}).get(b))
            identicos += 1 if misma else 0
            if va and not vb:
                gana += 1
                marca = etiq_a
            elif vb and not va:
                pierde += 1
                marca = etiq_b
            elif va:
                e_ok += 1
                marca = "empatan verificando"
            else:
                e_mal += 1
                marca = "empatan fallando"
            det.append({"consulta": q, a: fa.get("veredicto"),
                        b: fb.get("veredicto"), "marca": marca,
                        "codigo_identico": misma})
            if not va or not vb:
                print("  %-24s %s%s" % (marca, q[:48],
                                        "  [mismo codigo]" if misma else ""))
        n = gana + pierde + e_ok + e_mal
        pv = 1.0
        if gana + pierde:
            pv = min(1.0, 2.0 * sum(comb(gana + pierde, k)
                                    for k in range(0, min(gana, pierde) + 1))
                     / 2 ** (gana + pierde))
        print("  --> %d pares · rescata %d · rompe %d · empatan %d · p=%.4f"
              % (n, gana, pierde, e_ok + e_mal, pv))
        return {"pares": n, "rescata": gana, "rompe": pierde,
                "empata_verificando": e_ok, "empata_fallando": e_mal,
                "codigo_identico": identicos, "p_mcnemar": pv, "detalle": det}

    salida = {"por_rama": {c: {"verifica": v, "n": t}
                           for c, (v, t) in tot.items()}}
    if "modelo-solo" in configs and "completo" in configs:
        salida["completo_vs_modelo_solo"] = parear(
            "completo", "modelo-solo",
            "el SISTEMA rescata", "el SISTEMA rompe")
    if "sin-vocabulario" in configs and "completo" in configs:
        salida["completo_vs_sin_vocabulario"] = parear(
            "completo", "sin-vocabulario",
            "GANA con vocabulario", "PIERDE con vocabulario")

    print("\nLECTURA")
    v = salida.get("completo_vs_modelo_solo")
    if v:
        print("  APORTA EL APARATO :  rescata %d, rompe %d, p=%.4f"
              % (v["rescata"], v["rompe"], v["p_mcnemar"]))
    w = salida.get("completo_vs_sin_vocabulario")
    if w:
        print("  APORTA EL GRAFO   :  rescata %d, rompe %d, p=%.4f"
              % (w["rescata"], w["rompe"], w["p_mcnemar"]))
        if w["codigo_identico"]:
            print("     (en %d par(es) el modelo escribio lo mismo con y sin "
                  "nombres)" % w["codigo_identico"])

    json.dump(salida, io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    raise SystemExit(main())
